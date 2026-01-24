#!/usr/bin/env python3
"""
Exemples d'utilisation du système de configuration et logging.
"""

import logging
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import setup_logger, get_logger, LEVEL_NAMES


def example_1_basic_config():
    """Exemple 1: Configuration de base."""
    print("\n=== Exemple 1: Configuration de Base ===")
    
    # Créer une instance de configuration
    config = Config.instance()
    
    # Afficher les valeurs par défaut
    print(f"Database path: {config.database.path}")
    print(f"Auto-match threshold: {config.matching.auto_match_threshold}")
    print(f"Default sync action: {config.sync.default_action}")
    print(f"Log level: {config.logging.level}")


def example_2_load_from_yaml():
    """Exemple 2: Charger la configuration depuis un fichier YAML."""
    print("\n=== Exemple 2: Charger depuis YAML ===")
    
    config = Config.instance()
    
    # Charger depuis le fichier d'exemple
    if Path('config.yaml.example').exists():
        config.load_from_file('config.yaml.example')
        print(f"✓ Configuration chargée depuis config.yaml.example")
        print(f"  - Database: {config.database.path}")
        print(f"  - Threshold: {config.matching.auto_match_threshold}")
    else:
        print("✗ Fichier config.yaml.example non trouvé")


def example_3_dot_notation():
    """Exemple 3: Accès par notation pointée."""
    print("\n=== Exemple 3: Notation Pointée ===")
    
    config = Config.instance()
    
    # Getter avec notation pointée
    threshold = config.get('matching.auto_match_threshold')
    print(f"Récupérer: matching.auto_match_threshold = {threshold}")
    
    # Getter avec valeur par défaut
    custom = config.get('ui.custom_field', 'default_value')
    print(f"Récupérer inexistant: ui.custom_field = {custom}")
    
    # Setter avec notation pointée
    config.set('matching.auto_match_threshold', 80)
    print(f"Définir: matching.auto_match_threshold = 80")
    print(f"Vérifier: {config.get('matching.auto_match_threshold')}")


def example_4_validation():
    """Exemple 4: Validation de configuration."""
    print("\n=== Exemple 4: Validation ===")
    
    config = Config.instance()
    
    # Tester la validation avec des poids invalides
    config.matching.weights = {'title': 80, 'artist': 10, 'album': 5}  # Total: 95
    print(f"Poids avant: {config.matching.weights}")
    print(f"  Somme: {sum(config.matching.weights.values())}")
    
    # Valider et corriger
    config.matching.validate()
    print(f"Poids après validation: {config.matching.weights}")
    print(f"  Somme: {sum(config.matching.weights.values())}")


def example_5_save_config():
    """Exemple 5: Sauvegarder la configuration."""
    print("\n=== Exemple 5: Sauvegarder ===")
    
    import tempfile
    config = Config.instance()
    
    # Modifier la configuration
    config.set('matching.auto_match_threshold', 75)
    config.set('ui.theme', 'bootstrap')
    
    # Sauvegarder dans un fichier temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_file = f.name
    
    config.save_to_file(temp_file)
    print(f"✓ Configuration sauvegardée: {temp_file}")
    
    # Relire le fichier
    config2 = Config()
    config2.load_from_file(temp_file)
    print(f"✓ Configuration relue")
    print(f"  - Threshold: {config2.matching.auto_match_threshold}")
    print(f"  - Theme: {config2.ui.theme}")
    
    # Nettoyer
    Path(temp_file).unlink()


def example_6_logging_basic():
    """Exemple 6: Logging basique."""
    print("\n=== Exemple 6: Logging Basique ===")
    
    # Créer un logger
    logger = setup_logger('myapp', 'INFO')
    
    # Utiliser le logger
    logger.debug("Message debug (non affiché)")
    logger.info("Message info")
    logger.warning("Message d'avertissement")
    logger.error("Message d'erreur")


def example_7_logging_file():
    """Exemple 7: Logging avec fichier."""
    print("\n=== Exemple 7: Logging avec Fichier ===")
    
    import tempfile
    
    # Créer un logger avec fichier
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'app.log'
        logger = setup_logger('fileapp', 'DEBUG', str(log_file))
        
        logger.debug("Message debug")
        logger.info("Message info")
        logger.warning("Message warning")
        
        # Lire le fichier
        print(f"✓ Fichier de log créé: {log_file}")
        print(f"  Contenu:")
        for line in log_file.read_text().split('\n')[:3]:
            if line:
                print(f"    {line}")


def example_8_logging_levels():
    """Exemple 8: Différents niveaux de logging."""
    print("\n=== Exemple 8: Niveaux de Logging ===")
    
    # Afficher les niveaux disponibles
    print("Niveaux disponibles:")
    for level_name, level_value in LEVEL_NAMES.items():
        print(f"  {level_name}: {level_value}")
    
    # Créer des loggers avec différents niveaux
    debug_logger = setup_logger('debug_app', 'DEBUG')
    info_logger = setup_logger('info_app', 'INFO')
    error_logger = setup_logger('error_app', 'ERROR')
    
    print("\nTest DEBUG logger:")
    debug_logger.debug("Visible")
    
    print("\nTest INFO logger:")
    info_logger.debug("Non visible")
    info_logger.info("Visible")
    
    print("\nTest ERROR logger:")
    error_logger.info("Non visible")
    error_logger.error("Visible")


def example_9_reuse_logger():
    """Exemple 9: Réutiliser un logger existant."""
    print("\n=== Exemple 9: Réutiliser Logger ===")
    
    # Créer et récupérer
    setup_logger('shared', 'INFO')
    logger1 = get_logger('shared')
    logger2 = get_logger('shared')
    
    print(f"Même instance? {logger1 is logger2}")  # True
    logger1.info("Message depuis logger1")
    logger2.info("Message depuis logger2 (même logger)")


def example_10_full_workflow():
    """Exemple 10: Workflow complet."""
    print("\n=== Exemple 10: Workflow Complet ===")
    
    import tempfile
    import yaml
    
    # 1. Créer une configuration YAML
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / 'config.yaml'
        log_file = Path(tmpdir) / 'app.log'
        
        yaml_data = {
            'database': {'path': '/tmp/test.db'},
            'matching': {'auto_match_threshold': 88, 'weights': {'title': 75, 'artist': 15, 'album': 10}},
            'logging': {'level': 'DEBUG', 'file': str(log_file)}
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(yaml_data, f)
        
        print(f"✓ Config créée: {config_file}")
        
        # 2. Charger la configuration
        config = Config()
        config.load_from_file(str(config_file))
        print(f"✓ Config chargée")
        
        # 3. Créer un logger avec les paramètres
        logger = setup_logger(
            'workflow',
            config.logging.level,
            config.logging.file
        )
        print(f"✓ Logger créé")
        
        # 4. Utiliser
        logger.debug(f"Database: {config.database.path}")
        logger.info(f"Threshold: {config.matching.auto_match_threshold}")
        
        # 5. Vérifier les logs
        print(f"✓ Contenu du fichier log ({log_file}):")
        for line in log_file.read_text().strip().split('\n')[:2]:
            print(f"    {line}")


if __name__ == '__main__':
    print("=" * 60)
    print("EXEMPLES: Configuration et Logging")
    print("=" * 60)
    
    try:
        example_1_basic_config()
        example_2_load_from_yaml()
        example_3_dot_notation()
        example_4_validation()
        example_5_save_config()
        example_6_logging_basic()
        example_7_logging_file()
        example_8_logging_levels()
        example_9_reuse_logger()
        example_10_full_workflow()
        
        print("\n" + "=" * 60)
        print("✓ Tous les exemples complétés")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
