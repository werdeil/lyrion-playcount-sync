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
import shutil
import tkinter as tk
from pathlib import Path
from typing import Optional

# Imports locaux
from lyrion_playcount_sync.ui.main_window import MainWindow
from lyrion_playcount_sync.database.connection import DatabaseManager
from lyrion_playcount_sync.database.queries import SyncDetector
from lyrion_playcount_sync.matching.fuzzy_matcher import TrackMatcher
from lyrion_playcount_sync.utils.logger import setup_logger
from lyrion_playcount_sync.utils.config import Config
from lyrion_playcount_sync import (
    example_config_path,
    resolve_config_path,
    user_config_path,
)


# Exemple embarqué dans le package (fallback si aucun config.yaml n'est trouvé)
DEFAULT_CONFIG_EXAMPLE = str(example_config_path())


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
        # Résoudre le chemin du config indépendamment du répertoire courant
        # (script GUI installé, lancement depuis le Finder, etc.).
        self.config_file = str(resolve_config_path(config_file))
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

                # Aucun config trouvé : on en crée un persistant dans le dossier
                # de config utilisateur à partir de l'exemple embarqué. Ainsi les
                # réglages (dont le serveur distant) saisis dans l'app seront
                # sauvegardés et retrouvés au prochain lancement.
                if Path(DEFAULT_CONFIG_EXAMPLE).exists():
                    target = user_config_path()
                    try:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(DEFAULT_CONFIG_EXAMPLE, target)
                        self.config_file = str(target)
                        self.logger.info(
                            f"Configuration initialisée depuis l'exemple: {target}"
                        )
                    except OSError as e:
                        # Échec d'écriture : on charge l'exemple en lecture seule
                        self.logger.warning(
                            f"Impossible de créer {target} ({e}); "
                            f"utilisation de l'exemple en lecture seule"
                        )
                        target = Path(DEFAULT_CONFIG_EXAMPLE)
                        self.config_file = str(target)
                    self.config.load_from_file(str(target))
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

        Une base absente ou invalide n'est PAS fatale : on démarre quand même
        l'interface avec ``self.db = None``. L'utilisateur peut alors récupérer
        la base distante (« ↓ Récupérer ») ou pointer vers une base valide,
        au lieu de se heurter à un crash au démarrage.

        Returns:
            bool: True (le démarrage n'est jamais bloqué par la BD)
        """
        db_path = self.config.database.path
        self.logger.info(f"Connexion à la base de données: {db_path}")

        # Créer le gestionnaire de BD et établir la connexion.
        try:
            self.db = DatabaseManager(db_path)
            self.db.connect()
        except Exception as e:
            self.logger.warning(
                f"Base de données indisponible ({e}). "
                f"Démarrage sans connexion — utilisez « ↓ Récupérer » "
                f"pour charger une base."
            )
            self.db = None
            return True

        self.logger.info("✓ Connexion établie")

        # La sauvegarde n'est plus créée au démarrage : elle est posée
        # à la demande, juste avant la première modification de la base
        # (voir DatabaseManager.backup_if_needed()).

        # Vérifier le schéma
        if not self.db.verify_schema():
            self.logger.warning(
                "Schéma Lyrion invalide : la base n'est pas une BD Lyrion "
                "valide. Démarrage sans connexion."
            )
            try:
                self.db.close()
            except Exception:
                pass
            self.db = None
            return True

        self.logger.info("✓ Schéma vérifié")
        return True
    
    def initialize_components(self) -> bool:
        """
        Étape 4: Initialiser les composants métier.
        
        Returns:
            bool: True si succès
        """
        try:
            self.logger.info("Initialisation des composants...")
            
            # SyncDetector est une classe utilitaire avec méthodes statiques
            # Pas besoin d'instanciation, juste la garder comme référence
            self.detector = SyncDetector
            self.logger.info("✓ Détecteur de sync initialisé")
            
            # Initialiser le matcher de pistes
            self.matcher = TrackMatcher()
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
            
            # Créer la fenêtre principale (MainWindow hérite de tk.Tk)
            db_path = str(self.config.database.path)
            self.window = MainWindow(
                db_path=db_path, 
                db_manager=self.db,
                matcher=self.matcher
            )
            
            self.logger.info("✓ Interface chargée")
            
            # Appliquer la configuration UI
            if self.config.ui.window_size:
                try:
                    self.window.geometry(self.config.ui.window_size)
                except Exception as e:
                    self.logger.warning(f"Impossible d'appliquer la taille: {e}")
            
            # Appliquer le thème
            if hasattr(self.window, 'style') and self.config.ui.theme:
                try:
                    self.window.style.theme_use(self.config.ui.theme)
                except Exception as e:
                    self.logger.warning(f"Impossible d'appliquer le thème: {e}")
            
            self.logger.info("Démarrage de la boucle événementielle...")
            self.window.mainloop()
            
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
