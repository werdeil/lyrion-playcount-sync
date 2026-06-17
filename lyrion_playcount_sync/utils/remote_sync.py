"""
Récupération automatique de la base de données depuis un hôte distant via SCP.
"""

import os
import shlex
import subprocess
import shutil
import logging
from dataclasses import dataclass
from pathlib import Path

# On rattache les messages au logger applicatif ('app') configuré dans main.py,
# sinon les erreurs distantes (scp/ssh/sudo) ne seraient écrites ni dans la
# console ni dans logs/sync.log et resteraient invisibles.
logger = logging.getLogger("app")


class RemoteBusyError(Exception):
    """Levée quand la BD distante n'est pas dans un état sûr (WAL/SHM présents)."""


@dataclass
class RemoteConfig:
    """Configuration de la source distante."""
    host: str = ""
    user: str = ""
    db_path: str = "/var/lib/squeezeboxserver/prefs/persist.db"
    ssh_port: int = 22
    timeout: int = 30
    use_sudo: bool = False

    def is_configured(self) -> bool:
        return bool(self.host and self.user)


class RemoteSync:
    """Copie persist.db depuis un hôte distant via SCP."""

    def __init__(self, config: RemoteConfig):
        self.config = config

    def fetch(self, local_path: str, sudo_password: str | None = None) -> bool:
        """
        Télécharge le fichier distant vers local_path.

        Refuse le transfert si des fichiers WAL/SHM (`-wal`, `-shm`) traînent à
        côté de la BD distante : cela signifie que LMS tourne encore ou s'est mal
        arrêté, et que `persist.db` sur disque ne contient pas les dernières
        écritures. Récupérer le `.db` seul donnerait une base périmée.

        Si use_sudo est activé, la copie passe par /tmp (via `sudo cp`) car
        l'utilisateur SSH n'a pas le droit de lire directement la BD : LMS la
        régénère avec un mode 0600 appartenant à squeezeboxserver. Voir
        _fetch_via_sudo.

        Args:
            local_path: Destination locale du fichier.
            sudo_password: Mot de passe sudo de l'utilisateur SSH distant.
                Requis uniquement si use_sudo est activé.

        Returns:
            True si le transfert a réussi.

        Raises:
            RemoteBusyError: Si la BD distante n'est pas dans un état consolidé.
        """
        if not self.config.is_configured():
            return True

        if not shutil.which("scp"):
            logger.error("scp introuvable — impossible de récupérer la BD distante")
            return False

        if self._remote_wal_present():
            raise RemoteBusyError(
                "La base distante a des fichiers WAL en attente "
                "(persist.db-wal / -shm).\n\n"
                "LMS est probablement encore en cours d'exécution ou s'est mal "
                "arrêté. Arrêtez LMS sur l'hôte distant et réessayez."
            )

        dest = str(Path(local_path))
        # Créer le répertoire parent si besoin
        Path(dest).parent.mkdir(parents=True, exist_ok=True)

        if self.config.use_sudo:
            return self._fetch_via_sudo(dest, sudo_password)
        return self._fetch_direct(dest)

    def _fetch_direct(self, dest: str) -> bool:
        source = f"{self.config.user}@{self.config.host}:{self.config.db_path}"
        cmd = [
            "scp",
            "-P", str(self.config.ssh_port),
            "-o", "BatchMode=yes",           # pas de prompt interactif
            "-o", "ConnectTimeout={}".format(self.config.timeout),
            "-o", "StrictHostKeyChecking=no",
            source,
            dest,
        ]

        logger.info(f"Récupération distante: {source} → {dest}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout + 5,
            )
            if result.returncode == 0:
                logger.info("✓ Base de données récupérée depuis l'hôte distant")
                return True
            else:
                logger.error(
                    f"scp a échoué (code {result.returncode}): {result.stderr.strip()}"
                )
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"Délai dépassé lors de la connexion à {self.config.host}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors du transfert SCP: {e}")
            return False

    def _fetch_via_sudo(self, dest: str, sudo_password: str | None) -> bool:
        """
        Récupération en deux étapes quand l'utilisateur SSH n'a pas le droit de
        lire la BD (mode 0600 / squeezeboxserver, régénérée par LMS) :

        1. SSH + `sudo -S` (mot de passe lu sur stdin) qui, en une seule
           commande root, copie la BD vers /tmp puis donne la propriété du
           fichier temporaire à l'utilisateur SSH (afin qu'il puisse le lire).
        2. SCP du fichier temporaire vers le poste local.
        3. Suppression du fichier temporaire distant (best effort).
        """
        if not sudo_password:
            logger.error(
                "use_sudo est activé mais aucun mot de passe sudo n'a été fourni"
            )
            return False

        remote_tmp = f"/tmp/persist_fetch_{os.getpid()}.db"

        # Étape 1 : copie privilégiée vers /tmp, rendue lisible par l'utilisateur SSH.
        src = self.config.db_path
        inner = (
            f"SRC={shlex.quote(src)}; TMP={shlex.quote(remote_tmp)}; "
            f"USER={shlex.quote(self.config.user)}; "
            'cp "$SRC" "$TMP" || exit 1; '
            'chown "$USER" "$TMP"; '
            "exit 0"
        )
        remote_cmd = f"sudo -S -p '' sh -c {shlex.quote(inner)}"
        ssh_cmd = [
            "ssh",
            "-p", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.config.timeout}",
            "-o", "StrictHostKeyChecking=no",
            f"{self.config.user}@{self.config.host}",
            remote_cmd,
        ]
        logger.info(f"sudo cp {src} → {remote_tmp} (lecture via {self.config.user})")
        try:
            result = subprocess.run(
                ssh_cmd,
                input=sudo_password + "\n",
                capture_output=True,
                text=True,
                timeout=self.config.timeout + 5,
            )
            if result.returncode != 0:
                err = result.stderr.strip()
                if "incorrect password" in err or "Sorry, try again" in err:
                    err = "mot de passe sudo incorrect"
                logger.error(f"Copie privilégiée vers /tmp a échoué : {err}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Délai dépassé lors de la copie privilégiée vers /tmp")
            return False
        except Exception as e:
            logger.error(f"Erreur SSH : {e}")
            return False

        # Étape 2 : SCP du fichier temporaire vers le poste local.
        source = f"{self.config.user}@{self.config.host}:{remote_tmp}"
        scp_cmd = [
            "scp",
            "-P", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.config.timeout}",
            "-o", "StrictHostKeyChecking=no",
            source,
            dest,
        ]
        logger.info(f"Récupération distante: {source} → {dest}")
        ok = False
        try:
            result = subprocess.run(
                scp_cmd, capture_output=True, text=True, timeout=self.config.timeout + 5,
            )
            if result.returncode == 0:
                logger.info("✓ Base de données récupérée depuis l'hôte distant")
                ok = True
            else:
                logger.error(
                    f"scp depuis /tmp a échoué (code {result.returncode}): "
                    f"{result.stderr.strip()}"
                )
        except subprocess.TimeoutExpired:
            logger.error(f"Délai dépassé lors de la connexion à {self.config.host}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors du transfert SCP: {e}")

        # Étape 3 : nettoyage du fichier temporaire distant (best effort).
        subprocess.run(
            ["ssh", "-p", str(self.config.ssh_port),
             "-o", "BatchMode=yes",
             f"{self.config.user}@{self.config.host}",
             f"rm -f {shlex.quote(remote_tmp)}"],
            capture_output=True, timeout=10,
        )
        return ok

    def _remote_wal_present(self) -> bool:
        """
        Indique si des fichiers WAL/SHM existent à côté de la BD distante.

        En cas d'erreur de connexion, retourne False : la vérification ne doit
        pas bloquer le transfert, c'est le scp qui remontera l'échec réel.
        """
        if not shutil.which("ssh"):
            return False

        wal = f"{self.config.db_path}-wal"
        shm = f"{self.config.db_path}-shm"
        # Sort 0 si l'un des deux existe, 1 sinon.
        test = f"[ -e {shlex.quote(wal)} ] || [ -e {shlex.quote(shm)} ]"
        ssh_cmd = [
            "ssh",
            "-p", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.config.timeout}",
            "-o", "StrictHostKeyChecking=no",
            f"{self.config.user}@{self.config.host}",
            test,
        ]
        try:
            result = subprocess.run(
                ssh_cmd, capture_output=True, text=True, timeout=self.config.timeout + 5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Vérification WAL distante impossible : {e}")
            return False

    def upload(self, local_path: str, sudo_password: str | None = None) -> bool:
        """
        Envoie local_path vers le chemin distant configuré.

        Si use_sudo est activé, effectue un SCP vers /tmp puis un `sudo mv`
        (mot de passe lu sur stdin via `sudo -S`) pour contourner les
        restrictions de permissions sur la destination.

        Args:
            local_path: Fichier local à envoyer.
            sudo_password: Mot de passe sudo de l'utilisateur SSH distant.
                Requis uniquement si use_sudo est activé.

        Returns:
            True si le transfert a réussi.
        """
        if not self.config.is_configured():
            return True

        if not shutil.which("scp"):
            logger.error("scp introuvable — impossible d'envoyer la BD distante")
            return False

        if not Path(local_path).exists():
            logger.error(f"Fichier local introuvable : {local_path}")
            return False

        if self.config.use_sudo:
            return self._upload_via_sudo(local_path, sudo_password)
        return self._upload_direct(local_path)

    def _upload_direct(self, local_path: str) -> bool:
        dest = f"{self.config.user}@{self.config.host}:{self.config.db_path}"
        cmd = [
            "scp",
            "-P", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.config.timeout}",
            "-o", "StrictHostKeyChecking=no",
            str(local_path),
            dest,
        ]
        logger.info(f"Envoi distant: {local_path} → {dest}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.config.timeout + 5,
            )
            if result.returncode == 0:
                logger.info("✓ Base de données envoyée vers l'hôte distant")
                return True
            logger.error(f"scp a échoué (code {result.returncode}): {result.stderr.strip()}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"Délai dépassé lors de la connexion à {self.config.host}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors du transfert SCP: {e}")
            return False

    def _upload_via_sudo(self, local_path: str, sudo_password: str | None) -> bool:
        """
        Upload en deux étapes pour contourner les restrictions de permissions
        sans relâcher les droits du serveur ni exiger un sudo NOPASSWD :

        1. SCP vers /tmp (accessible à l'utilisateur SSH).
        2. SSH + `sudo -S` (mot de passe lu sur stdin) qui, en une seule
           commande root :
             - lit le propriétaire actuel de la BD,
             - déplace le fichier temporaire à la place de la BD,
             - restaure ce propriétaire (pour ne pas casser Lyrion au redémarrage),
             - supprime les fichiers WAL/SHM distants périmés (`-wal`, `-shm`),
               sinon SQLite réapplique l'ancien WAL par-dessus la nouvelle base
               et annule la synchronisation.
        """
        if not sudo_password:
            logger.error(
                "use_sudo est activé mais aucun mot de passe sudo n'a été fourni"
            )
            return False

        remote_tmp = f"/tmp/persist_sync_{os.getpid()}.db"
        scp_dest = f"{self.config.user}@{self.config.host}:{remote_tmp}"

        # Étape 1 : SCP vers /tmp
        scp_cmd = [
            "scp",
            "-P", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.config.timeout}",
            "-o", "StrictHostKeyChecking=no",
            str(local_path),
            scp_dest,
        ]
        logger.info(f"Envoi vers /tmp distant : {scp_dest}")
        try:
            result = subprocess.run(
                scp_cmd, capture_output=True, text=True, timeout=self.config.timeout + 5,
            )
            if result.returncode != 0:
                logger.error(f"scp vers /tmp a échoué : {result.stderr.strip()}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Délai dépassé lors du SCP vers /tmp")
            return False
        except Exception as e:
            logger.error(f"Erreur SCP : {e}")
            return False

        # Étape 2 : déplacement privilégié en une seule transaction root.
        # Le script tourne entièrement sous `sudo -S sh -c`, on évite ainsi tout
        # problème de quoting du propriétaire et le bug du chaînage `&&`
        # (un OWNER vide ne doit pas faire échouer la commande).
        dest = self.config.db_path
        inner = (
            f"DEST={shlex.quote(dest)}; TMP={shlex.quote(remote_tmp)}; "
            'OWNER=$(stat -c "%U:%G" "$DEST" 2>/dev/null); '
            'mv "$TMP" "$DEST" || exit 1; '
            '[ -n "$OWNER" ] && chown "$OWNER" "$DEST"; '
            'rm -f "$DEST-wal" "$DEST-shm"; '
            "exit 0"
        )
        # `sudo -S` lit le mot de passe sur stdin ; `-p ''` supprime l'invite.
        remote_cmd = f"sudo -S -p '' sh -c {shlex.quote(inner)}"
        ssh_cmd = [
            "ssh",
            "-p", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.config.timeout}",
            "-o", "StrictHostKeyChecking=no",
            f"{self.config.user}@{self.config.host}",
            remote_cmd,
        ]
        logger.info(f"sudo mv {remote_tmp} → {dest} (+ nettoyage WAL distant)")
        try:
            result = subprocess.run(
                ssh_cmd,
                input=sudo_password + "\n",
                capture_output=True,
                text=True,
                timeout=self.config.timeout + 5,
            )
            if result.returncode != 0:
                err = result.stderr.strip()
                if "incorrect password" in err or "Sorry, try again" in err:
                    err = "mot de passe sudo incorrect"
                logger.error(f"Déplacement privilégié a échoué : {err}")
                # Nettoyage du fichier temporaire (best effort)
                subprocess.run(
                    ["ssh", "-p", str(self.config.ssh_port),
                     "-o", "BatchMode=yes",
                     f"{self.config.user}@{self.config.host}",
                     f"rm -f {shlex.quote(remote_tmp)}"],
                    capture_output=True, timeout=10,
                )
                return False
            logger.info("✓ Base de données envoyée (via sudo mv)")
            return True
        except subprocess.TimeoutExpired:
            logger.error("Délai dépassé lors du déplacement privilégié")
            return False
        except Exception as e:
            logger.error(f"Erreur SSH : {e}")
            return False
