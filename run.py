#!/usr/bin/env python3
"""
Script de démarrage de Lyrion Playcount Sync.

Utilisation:
    python run.py              # Lancer l'application
    python run.py --check      # Vérifier l'installation
    python run.py --help       # Afficher l'aide
"""

import sys
import os
import argparse
from pathlib import Path

def check_installation():
    """Vérifie que l'installation est complète."""
    print("Vérification de l'installation...")
    
    # Vérifier les modules
    try:
        import ttkbootstrap
        print("✅ ttkbootstrap")
    except ImportError:
        print("❌ ttkbootstrap manquant")
        return False
    
    try:
        import rapidfuzz
        print("✅ rapidfuzz")
    except ImportError:
        print("❌ rapidfuzz manquant")
        return False
    
    try:
        import yaml
        print("✅ pyyaml")
    except ImportError:
        print("❌ pyyaml manquant")
        return False
    
    try:
        import dotenv
        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv manquant")
        return False
    
    # Vérifier la structure
    required_dirs = [
        'src',
        'src/database',
        'src/matching',
        'src/models',
        'src/ui',
        'src/utils'
    ]
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ manquant")
            return False
    
    # Vérifier les fichiers principaux
    required_files = [
        'src/main.py',
        'config.yaml.example',
        'requirements.txt'
    ]
    
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} manquant")
            return False
    
    print("\n✅ Installation OK!")
    return True

def setup_config():
    """Configure l'application pour la première fois."""
    config_path = Path('config.yaml')
    config_example = Path('config.yaml.example')
    
    if config_path.exists():
        print(f"✅ config.yaml existe déjà")
        return True
    
    if not config_example.exists():
        print("❌ config.yaml.example non trouvé")
        return False
    
    print("Création de config.yaml...")
    config_path.write_text(config_example.read_text())
    print("✅ config.yaml créé à partir de l'exemple")
    print("⚠️  N'oubliez pas de configurer le chemin database.path!")
    return True

def run_app():
    """Lance l'application."""
    print("Démarrage de Lyrion Playcount Sync...")
    try:
        from src.main import Application
        app = Application()
        app.run()
    except Exception as e:
        print(f"❌ Erreur lors du démarrage : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Lyrion Playcount Sync",
        epilog="Pour plus d'information, consultez README.md"
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Vérifier l\'installation'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Configurer pour la première fois'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    if args.check:
        success = check_installation()
        sys.exit(0 if success else 1)
    
    if args.setup:
        success = setup_config()
        sys.exit(0 if success else 1)
    
    # Vérifier la configuration
    if not Path('config.yaml').exists():
        print("⚠️  config.yaml non trouvé. Création...")
        if not setup_config():
            sys.exit(1)
    
    # Vérifier l'installation
    if not check_installation():
        print("\n❌ Installation incomplète!")
        print("Exécutez : pip install -r requirements.txt")
        sys.exit(1)
    
    # Lancer l'application
    run_app()

if __name__ == '__main__':
    main()
