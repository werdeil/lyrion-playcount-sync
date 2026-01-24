"""Point d'entrée de l'application Lyrion Playcount Sync."""

import tkinter as tk
import sys
import yaml
from pathlib import Path
from typing import Optional

import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *

from src.ui import MainWindow
from src.utils import setup_logger
from src.database import DatabaseManager, DatabaseConnectionError, PlaycountQueries
from src.matching import FuzzyMatcher

logger = setup_logger(__name__)


class Application:
    """Classe principale de l'application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'application.
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        logger.info("Application initialisée")
        
        # Initialisation des composants
        try:
            self.db = DatabaseManager(
                db_path=self.config['database'].get('path'),
                auto_detect=True
            )
            logger.info("Gestionnaire de base de données initialisé")
        except DatabaseConnectionError as e:
            logger.error(f"Erreur : {e}")
            raise
        
        self.matcher = FuzzyMatcher(
            threshold=self.config['matching']['similarity_threshold'],
            method=self.config['matching']['ratio_method']
        )
        
        # Initialisation de l'UI
        self.root = ttk_bs.Window(themename="darkly")
        self.main_window = MainWindow(self.root)
    
    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """
        Charge la configuration.
        
        Args:
            config_path: Chemin vers le fichier de configuration
            
        Returns:
            Dictionnaire de configuration
        """
        # Configuration par défaut
        default_config = {
            'database': {
                'path': '/var/lib/squeezeboxserver/prefs/server.prefs',
                'backup': True
            },
            'matching': {
                'similarity_threshold': 85,
                'ratio_method': 'token_sort_ratio'
            },
            'sync': {
                'direction': 'merge',
                'auto_apply': False,
                'backup_before_sync': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'playcount_sync.log'
            }
        }
        
        # Charge la configuration depuis le fichier si fourni
        if config_path:
            try:
                config_file = Path(config_path)
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        loaded_config = yaml.safe_load(f) or {}
                        # Fusion avec la configuration par défaut
                        self._merge_config(default_config, loaded_config)
                    logger.info(f"Configuration chargée depuis {config_path}")
            except Exception as e:
                logger.warning(f"Impossible de charger la configuration : {e}")
        
        return default_config
    
    @staticmethod
    def _merge_config(base: dict, override: dict) -> None:
        """
        Fusionne deux dictionnaires de configuration.
        
        Args:
            base: Dictionnaire de base (modifié en place)
            override: Dictionnaire à fusionner
        """
        for key, value in override.items():
            if isinstance(value, dict) and key in base:
                Application._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _setup_logging(self) -> None:
        """Configure le logging."""
        log_config = self.config['logging']
        setup_logger(
            'src',
            log_level=log_config['level'],
            log_file=log_config.get('file')
        )
    
    def run(self) -> None:
        """Démarre l'application."""
        logger.info("Démarrage de l'application")
        self.main_window.run()


def main():
    """Point d'entrée principal."""
    try:
        # Cherche le fichier de configuration
        config_file = Path("config.yaml")
        config_path = str(config_file) if config_file.exists() else None
        
        app = Application(config_path=config_path)
        app.run()
    except Exception as e:
        logger.error(f"Erreur fatale : {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
