#!/usr/bin/env python3
"""
Script de démarrage de Lyrion Playcount Sync.

Utilisation:
    python run.py              # Lancer l'application
    python run.py --check      # Vérifier l'installation
    python run.py --setup      # Configurer pour la première fois
    python run.py --help       # Afficher l'aide
"""

import sys
import os
import argparse
from pathlib import Path


def check_installation() -> bool:
    """
    Vérifie que l'installation est complète.
    
    Returns:
        bool: True si l'installation est complète
    """
    print("Vérification de l'installation...")
    all_ok = True
    
    # Vérifier les dépendances principales
    dependencies = [
        ('tkinter', 'tkinter (inclus dans Python)'),
        ('ttkbootstrap', 'ttkbootstrap'),
        ('rapidfuzz', 'rapidfuzz'),
        ('yaml', 'pyyaml'),
        ('dotenv', 'python-dotenv'),
    ]
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError:
            print(f"  ❌ {display_name} (manquant)")
            all_ok = False
    
    # Vérifier la structure des répertoires
    required_dirs = [
        'src',
        'src/database',
        'src/matching',
        'src/models',
        'src/ui',
        'src/utils',
        'tests',
    ]
    
    print("\nStructure des répertoires:")
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (manquant)")
            all_ok = False
    
    # Vérifier les fichiers principaux
    required_files = [
        'src/main.py',
        'src/utils/config.py',
        'src/utils/logger.py',
        'config.yaml.example',
        'requirements.txt',
    ]
    
    print("\nFichiers principaux:")
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (manquant)")
            all_ok = False
    
    if all_ok:
        print("\n✅ Installation vérifiée!")
    else:
        print("\n❌ Certains éléments sont manquants!")
        print("Exécutez: pip install -r requirements.txt")
    
    return all_ok


def setup_config() -> bool:
    """
    Configure l'application pour la première fois.
    
    Returns:
        bool: True si succès
    """
    config_path = Path('config.yaml')
    config_example = Path('config.yaml.example')
    
    if config_path.exists():
        print(f"✅ config.yaml existe déjà")
        return True
    
    if not config_example.exists():
        print("❌ config.yaml.example non trouvé")
        return False
    
    print("Création de config.yaml...")
    try:
        config_path.write_text(config_example.read_text())
        print("✅ config.yaml créé à partir de l'exemple")
        print("\n⚠️  Configuration par défaut appliquée.")
        print("   Adaptez les paramètres selon votre environnement:")
        print("   - database.path: chemin de la base de données Lyrion")
        print("   - matching.auto_match_threshold: seuil d'auto-matching")
        print("   - ui.theme: thème de l'interface")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False


def run_app(config_file: str = None) -> int:
    """
    Lance l'application.
    
    Args:
        config_file: Chemin optionnel du fichier de configuration
    
    Returns:
        int: Code de sortie (0 = succès, 1 = erreur)
    """
    try:
        from src.main import main
        return main(config_file)
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        print("   Vérifiez que vous êtes dans le bon répertoire")
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        return 0
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Fonction principale du script de démarrage."""
    parser = argparse.ArgumentParser(
        prog='Lyrion Playcount Sync',
        description='Synchronise les playcounts entre Lyrion et les pistes locales',
        epilog='Pour plus d\'information, consultez README.md'
    )
    
    parser.add_argument(
        'config',
        nargs='?',
        default=None,
        help='Chemin du fichier de configuration (défaut: config.yaml)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Vérifier l\'installation et les dépendances'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Créer config.yaml depuis l\'exemple'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Vérifier l'installation
    if args.check:
        success = check_installation()
        sys.exit(0 if success else 1)
    
    # Configurer
    if args.setup:
        success = setup_config()
        sys.exit(0 if success else 1)
    
    # Vérifier la configuration avant de lancer
    if not Path(args.config or 'config.yaml').exists():
        print("⚠️  Fichier de configuration non trouvé")
        if Path('config.yaml.example').exists():
            print("   Création de config.yaml depuis l'exemple...")
            if not setup_config():
                sys.exit(1)
        else:
            print("❌ Impossible de créer la configuration")
            sys.exit(1)
    
    # Vérifier l'installation minimale
    if not check_installation():
        print("\n❌ Installation incomplète!")
        print("   Exécutez: pip install -r requirements.txt")
        sys.exit(1)
    
    # Lancer l'application
    print("\n" + "=" * 70)
    exit_code = run_app(args.config)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

