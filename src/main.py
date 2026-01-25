#!/usr/bin/env python3
"""
Orchestrateur Principal - Lyrion Playcount Sync

Point d'entrée de l'application qui coordonne:
1. Configuration et logging
2. Connexion base de données
3. Initialisation des composants
4. Lancement de l'interface utilisateur
5. Cleanup et arrêt propre
"""

import sys
import os
import tkinter as tk
from pathlib import Path
from typing import Optional

# Imports locaux
from src.ui.main_window import MainWindow
from src.database.connection import DatabaseManager
from src.database.queries import SyncDetector
from src.matching.fuzzy_matcher import TrackMatcher
from src.utils.logger import setup_logger, get_logger
from src.utils.config import Config


# Configuration par défaut
DEFAULT_CONFIG_FILE = 'config.yaml'
DEFAULT_CONFIG_EXAMPLE = 'config.yaml.example'


class Application:
    """
    Orchestrateur principal de l'application.
    
    Gère l'initialisation, le cycle de vie et l'arrêt propre de l'application.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialiser l'application.
        
        Args:
            config_file: Chemin du fichier de configuration (défaut: config.yaml)
        """
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.logger = None
        self.config = None
        self.db = None
        self.detector = None
        self.matcher = None
        self.window = None
    
    def setup_logging(self) -> bool:
        """
        Étape 1: Configurer le système de logging.
        
        Returns:
            bool: True si succès
        """
        try:
            # Créer le logger principal
            self.logger = setup_logger('app', 'INFO', './logs/sync.log')
            self.logger.info("=" * 70)
            self.logger.info("Démarrage - Lyrion Playcount Sync")
            self.logger.info("=" * 70)
            return True
        except Exception as e:
            print(f"✗ Erreur initialisation logging: {e}")
            return False
    
    def load_configuration(self) -> bool:
        """
        Étape 2: Charger la configuration depuis le fichier YAML.
        
        Returns:
            bool: True si succès
        """
        try:
            # Charger la configuration
            self.config = Config.instance()
            
            # Override database path from environment if set
            lyrion_path = os.getenv('LYRION_DATA_PATH')
            if lyrion_path:
                persist_db = Path(lyrion_path) / 'persist.db'
                self.config.database.path = str(persist_db)
            
            # Vérifier si le fichier de config existe
            config_path = Path(self.config_file)
            if not config_path.exists():
                self.logger.warning(
                    f"Fichier config non trouvé: {self.config_file}"
                )
                
                # Vérifier s'il existe un exemple
                if Path(DEFAULT_CONFIG_EXAMPLE).exists():
                    self.logger.info(
                        f"Utilisation du fichier d'exemple: {DEFAULT_CONFIG_EXAMPLE}"
                    )
                    self.config.load_from_file(DEFAULT_CONFIG_EXAMPLE)
                else:
                    self.logger.error(
                        "Aucun fichier de configuration trouvé! "
                        "Créez config.yaml depuis config.yaml.example"
                    )
                    return False
            else:
                # Charger la config
                success = self.config.load_from_file(self.config_file)
                if not success:
                    self.logger.error("Impossible de charger la configuration")
                    return False
            
            # Réappliquer l'override après le chargement du fichier
            if lyrion_path:
                persist_db = Path(lyrion_path) / 'persist.db'
                self.config.database.path = str(persist_db)
            
            # Valider la configuration
            self.config.validate()
            
            # Afficher les paramètres principaux
            self.logger.info(f"Base de données: {self.config.database.path}")
            self.logger.info(f"Seuil matching: {self.config.matching.auto_match_threshold}%")
            self.logger.info(f"Thème UI: {self.config.ui.theme}")
            self.logger.info(f"Niveau log: {self.config.logging.level}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configuration: {e}")
            return False
    
    def connect_database(self) -> bool:
        """
        Étape 3: Établir la connexion à la base de données.
        
        Returns:
            bool: True si succès
        """
        try:
            db_path = self.config.database.path
            self.logger.info(f"Connexion à la base de données: {db_path}")
            
            # Créer le gestionnaire de BD
            self.db = DatabaseManager(db_path)
            
            # Établir la connexion
            if not self.db.connect():
                self.logger.error("Impossible de se connecter à la base de données")
                return False
            
            self.logger.info("✓ Connexion établie")
            
            # Créer une sauvegarde si configuré
            if self.config.database.backup_on_startup:
                try:
                    backup_path = self.db.backup_database()
                    self.logger.info(f"✓ Sauvegarde créée: {backup_path}")
                except Exception as e:
                    self.logger.warning(f"Erreur sauvegarde: {e}")
            
            # Vérifier le schéma
            if not self.db.verify_schema():
                self.logger.error(
                    "Schéma Lyrion invalide! "
                    "La base de données n'est pas une BD Lyrion valide."
                )
                return False
            
            self.logger.info("✓ Schéma vérifié")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur connexion BD: {e}", exc_info=True)
            return False
    
    def initialize_components(self) -> bool:
        """
        Étape 4: Initialiser les composants métier.
        
        Returns:
            bool: True si succès
        """
        try:
            self.logger.info("Initialisation des composants...")
            
            # Initialiser le détecteur de synchronisation
            self.detector = SyncDetector(self.db)
            self.logger.info("✓ Détecteur de sync initialisé")
            
            # Initialiser le matcher de pistes
            self.matcher = TrackMatcher(self.config.matching)
            self.logger.info("✓ Matcher de pistes initialisé")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation composants: {e}", exc_info=True)
            return False
    
    def launch_ui(self) -> bool:
        """
        Étape 5: Lancer l'interface utilisateur.
        
        Returns:
            bool: True si succès
        """
        try:
            self.logger.info("Lancement de l'interface utilisateur...")
            
            # Créer la fenêtre principale
            root = tk.Tk()
            self.window = MainWindow(
                root,
                db=self.db,
                detector=self.detector,
                matcher=self.matcher,
                config=self.config
            )
            
            self.logger.info("✓ Interface chargée")
            
            # Appliquer la configuration UI
            if self.config.ui.window_size:
                try:
                    root.geometry(self.config.ui.window_size)
                except Exception as e:
                    self.logger.warning(f"Impossible d'appliquer la taille: {e}")
            
            # Appliquer le thème
            if hasattr(self.window, 'style') and self.config.ui.theme:
                try:
                    self.window.style.theme_use(self.config.ui.theme)
                except Exception as e:
                    self.logger.warning(f"Impossible d'appliquer le thème: {e}")
            
            self.logger.info("Démarrage de la boucle événementielle...")
            root.mainloop()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur UI: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """
        Étape 6: Nettoyage et arrêt propre.
        
        Appelée en toutes circonstances (succès, erreur, interruption).
        """
        try:
            if self.db:
                self.db.close()
                self.logger.info("✓ Base de données fermée")
            
            self.logger.info("=" * 70)
            self.logger.info("Arrêt propre")
            self.logger.info("=" * 70)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur pendant le cleanup: {e}")
    
    def run(self) -> int:
        """
        Exécuter l'application complète.
        
        Returns:
            int: Exit code (0 = succès, 1 = erreur)
        """
        try:
            # Étape 1: Setup logging
            if not self.setup_logging():
                return 1
            
            # Étape 2: Charger configuration
            if not self.load_configuration():
                return 1
            
            # Étape 3: Connecter BD
            if not self.connect_database():
                return 1
            
            # Étape 4: Initialiser composants
            if not self.initialize_components():
                return 1
            
            # Étape 5: Lancer UI
            if not self.launch_ui():
                return 1
            
            return 0
            
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Interruption utilisateur (Ctrl+C)")
            return 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur non gérée: {e}", exc_info=True)
            else:
                print(f"Erreur non gérée: {e}")
            return 1
            
        finally:
            # Toujours faire le cleanup
            self.cleanup()


def main(config_file: Optional[str] = None) -> int:
    """
    Point d'entrée principal de l'application.
    
    Args:
        config_file: Chemin optionnel du fichier de configuration
    
    Returns:
        int: Exit code (0 = succès, 1 = erreur)
    """
    app = Application(config_file)
    return app.run()


if __name__ == "__main__":
    # Récupérer le fichier de config depuis les arguments si fourni
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Exécuter l'application
    exit_code = main(config_file)
    
    # Quitter avec le code d'erreur approprié
    sys.exit(exit_code)
