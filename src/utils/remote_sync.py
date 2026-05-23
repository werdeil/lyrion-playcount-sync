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

logger = logging.getLogger(__name__)


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

    def fetch(self, local_path: str) -> bool:
        """
        Télécharge le fichier distant vers local_path.

        Returns:
            True si le transfert a réussi.
        """
        if not self.config.is_configured():
            return True

        if not shutil.which("scp"):
            logger.error("scp introuvable — impossible de récupérer la BD distante")
            return False

        source = f"{self.config.user}@{self.config.host}:{self.config.db_path}"
        dest = str(Path(local_path))

        # Créer le répertoire parent si besoin
        Path(dest).parent.mkdir(parents=True, exist_ok=True)

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

    def upload(self, local_path: str) -> bool:
        """
        Envoie local_path vers le chemin distant configuré.

        Si use_sudo est activé, effectue un SCP vers /tmp puis un sudo mv
        pour contourner les restrictions de permissions sur la destination.

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
            return self._upload_via_sudo(local_path)
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

    def _upload_via_sudo(self, local_path: str) -> bool:
        """
        Upload en deux étapes pour contourner les restrictions de permissions :
        1. SCP vers /tmp (accessible à l'utilisateur SSH)
        2. SSH + sudo mv vers la destination finale
        """
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

        # Étape 2 : sudo mv vers la destination finale (+ restauration du propriétaire)
        # On lit le propriétaire original avant d'écraser pour éviter de casser les
        # droits de Lyrion au redémarrage.
        ssh_move = (
            f"OWNER=$(stat -c '%U:%G' {shlex.quote(self.config.db_path)} 2>/dev/null); "
            f"sudo mv {shlex.quote(remote_tmp)} {shlex.quote(self.config.db_path)} && "
            f"[ -n \"$OWNER\" ] && sudo chown \"$OWNER\" {shlex.quote(self.config.db_path)}"
        )
        ssh_cmd = [
            "ssh",
            "-p", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.config.timeout}",
            "-o", "StrictHostKeyChecking=no",
            f"{self.config.user}@{self.config.host}",
            ssh_move,
        ]
        logger.info(f"sudo mv {remote_tmp} → {self.config.db_path}")
        try:
            result = subprocess.run(
                ssh_cmd, capture_output=True, text=True, timeout=self.config.timeout + 5,
            )
            if result.returncode != 0:
                logger.error(f"sudo mv a échoué : {result.stderr.strip()}")
                # Nettoyage du fichier temporaire
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
            logger.error("Délai dépassé lors du sudo mv")
            return False
        except Exception as e:
            logger.error(f"Erreur SSH : {e}")
            return False
