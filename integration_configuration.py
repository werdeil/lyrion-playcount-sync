#!/usr/bin/env python3
"""
Integration Guide - Configuration et Logging System

Ce script montre comment intégrer le système de configuration et logging
dans l'application existante (MainWindow).
"""

from pathlib import Path
import logging
from src.utils.config import Config
from src.utils.logger import setup_logger


class ApplicationWithConfig:
    """
    Exemple d'application utilisant le système de configuration et logging.
    """
    
    def __init__(self, config_file: str = 'config.yaml'):
        """
        Initialiser l'application avec configuration et logging.
        
        Args:
            config_file: Chemin du fichier de configuration
        """
        # 1. Charger la configuration
        self.config = Config.instance()
        self.load_config(config_file)
        
        # 2. Configurer le logging
        self.setup_logging()
        
        # 3. Logger
        self.logger = self.get_logger('app')
        self.logger.info("Application initialized")
    
    def load_config(self, config_file: str) -> bool:
        """Charger la configuration depuis un fichier YAML."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            # Utiliser les defaults si le fichier n'existe pas
            print(f"Config file not found: {config_file}, using defaults")
            return False
        
        success = self.config.load_from_file(config_file)
        if success:
            print(f"✓ Configuration loaded from {config_file}")
        else:
            print(f"✗ Failed to load configuration from {config_file}")
        
        return success
    
    def setup_logging(self):
        """Configurer le logging selon les paramètres de configuration."""
        log_file = self.config.logging.file
        log_level = self.config.logging.level
        
        # Créer le répertoire de logs si nécessaire
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configurer le logger principal
        setup_logger('app', log_level, log_file)
        print(f"✓ Logging configured: level={log_level}, file={log_file}")
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Récupérer un logger pour un module."""
        from src.utils.logger import get_logger
        return get_logger(name)
    
    def run(self):
        """Exemple de fonctionnement."""
        self.logger.info("Application started")
        
        # Exemple: afficher les paramètres
        self.logger.debug(f"Database: {self.config.database.path}")
        self.logger.debug(f"Matching threshold: {self.config.matching.auto_match_threshold}")
        self.logger.debug(f"UI theme: {self.config.ui.theme}")
        
        # Exemple: utiliser la configuration
        if self.config.database.auto_backup:
            self.logger.info("Database auto-backup is enabled")
        
        self.logger.info("Application finished")


def example_integration_mainwindow():
    """
    Exemple d'intégration dans MainWindow.
    
    Ajouter à votre MainWindow.__init__():
    
        # Charger configuration et logging
        self.config = Config.instance()
        self.config.load_from_file('config.yaml')
        
        # Configurer logging
        log_level = self.config.logging.level
        log_file = self.config.logging.file
        setup_logger('mainwindow', log_level, log_file)
        self.logger = get_logger('mainwindow')
        
        # Utiliser la configuration
        self.geometry(self.config.ui.window_size)
        self.style.theme_use(self.config.ui.theme)
    """
    pass


def example_integration_sync_detector():
    """
    Exemple d'intégration dans SyncDetector.
    
    Ajouter à votre SyncDetector.__init__():
    
        from src.utils.logger import get_logger
        from src.utils.config import Config
        
        self.config = Config.instance()
        self.logger = get_logger('syncdetector')
        
        # Utiliser la configuration
        self.threshold = self.config.matching.auto_match_threshold
        self.delete_after_sync = self.config.sync.delete_after_sync
    """
    pass


def example_integration_track_matcher():
    """
    Exemple d'intégration dans TrackMatcher.
    
    Ajouter à votre TrackMatcher.__init__():
    
        from src.utils.logger import get_logger
        from src.utils.config import Config
        
        self.config = Config.instance()
        self.logger = get_logger('trackmatcher')
        
        # Utiliser les poids du matching
        self.weights = self.config.matching.weights
        self.suggestion_min_score = self.config.matching.suggestion_min_score
    """
    pass


def example_integration_sync_operations():
    """
    Exemple d'intégration dans SyncOperations.
    
    Ajouter à votre SyncOperations.__init__():
    
        from src.utils.logger import get_logger
        from src.utils.config import Config
        
        self.config = Config.instance()
        self.logger = get_logger('syncoperations')
        
        # Utiliser la configuration
        self.db_path = self.config.database.path
        self.default_action = self.config.sync.default_action
        
        # Exemple de log
        self.logger.info(f"Using database: {self.db_path}")
    """
    pass


def setup_module_logging(module_name: str) -> logging.Logger:
    """
    Fonction utilitaire pour configurer le logging d'un module.
    
    À appeler dans chaque module qui a besoin de logging:
    
        logger = setup_module_logging(__name__)
        logger.info("Module loaded")
    """
    from src.utils.logger import get_logger
    return get_logger(module_name)


# ============================================================================
# INSTRUCTIONS D'INTÉGRATION
# ============================================================================

"""
ÉTAPE 1: Créer config.yaml
----
cp config.yaml.example config.yaml
Adaptez les paramètres à votre environnement.

ÉTAPE 2: Intégrer dans MainWindow
----
# Ajouter en haut de src/main_window.py
from src.utils.config import Config
from src.utils.logger import setup_logger, get_logger

# Ajouter dans __init__:
def __init__(self):
    super().__init__()
    
    # Configuration
    self.config = Config.instance()
    self.config.load_from_file('config.yaml')
    
    # Logging
    log_level = self.config.logging.level
    log_file = self.config.logging.file
    setup_logger('mainwindow', log_level, log_file)
    self.logger = get_logger('mainwindow')
    
    self.logger.info("MainWindow initialized")
    
    # Appliquer la configuration
    self.geometry(self.config.ui.window_size)
    self.style.theme_use(self.config.ui.theme)
    
    # ... reste du code ...

ÉTAPE 3: Intégrer dans SyncDetector, TrackMatcher, SyncOperations
----
# Dans chaque module:
from src.utils.config import Config
from src.utils.logger import get_logger

class MyClass:
    def __init__(self):
        self.config = Config.instance()
        self.logger = get_logger(self.__class__.__name__)
        
        # Utiliser la configuration
        self.threshold = self.config.matching.auto_match_threshold

ÉTAPE 4: Tester l'intégration
----
python3 run.py

Vous devriez voir:
- La configuration chargée depuis config.yaml
- Les logs dans la console ET dans le fichier ./logs/sync.log
- Les paramètres de config appliqués (thème, taille fenêtre, etc.)

ÉTAPE 5: Production
----
- Vérifier que config.yaml existe
- Vérifier que le répertoire ./logs/ est accessible
- Vérifier que config.yaml ne contient pas de données sensibles
"""


if __name__ == '__main__':
    print("=" * 70)
    print("Exemple d'intégration: Configuration et Logging")
    print("=" * 70)
    
    # Créer une instance d'application exemple
    print("\nCréation d'une application avec configuration et logging...")
    app = ApplicationWithConfig('config.yaml.example')
    
    print("\nExécution de l'application...")
    app.run()
    
    print("\nIntégration réussie!")
    print("Consultez les fichiers:")
    print("- CONFIGURATION.md pour la documentation complète")
    print("- examples_configuration.py pour 10 exemples détaillés")
    print("- src/utils/config.py et src/utils/logger.py pour le code")
    print("=" * 70)
