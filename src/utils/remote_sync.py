"""
Récupération automatique de la base de données depuis un hôte distant via SCP.
"""

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

    def is_configured(self) -> bool:
        return bool(self.host and self.user)
    ssh_port: int = 22
    timeout: int = 30


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

        dest = f"{self.config.user}@{self.config.host}:{self.config.db_path}"

        cmd = [
            "scp",
            "-P", str(self.config.ssh_port),
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout={}".format(self.config.timeout),
            "-o", "StrictHostKeyChecking=no",
            str(local_path),
            dest,
        ]

        logger.info(f"Envoi distant: {local_path} → {dest}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout + 5,
            )
            if result.returncode == 0:
                logger.info("✓ Base de données envoyée vers l'hôte distant")
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
