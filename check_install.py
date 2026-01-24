#!/usr/bin/env python3
"""Script de vérification de l'installation."""

import sys
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python."""
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ requis, vous avez {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Vérifie les dépendances."""
    dependencies = {
        'ttkbootstrap': 'Interface utilisateur',
        'rapidfuzz': 'Matching de chaînes',
        'yaml': 'Configuration YAML',
        'dotenv': 'Variables d\'environnement'
    }
    
    all_ok = True
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module:20} - {description}")
        except ImportError:
            print(f"❌ {module:20} - {description} (MANQUANT)")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """Vérifie la structure du projet."""
    required_files = [
        'src/main.py',
        'src/ui/main_window.py',
        'src/database/connection.py',
        'src/matching/fuzzy_matcher.py',
        'requirements.txt',
        'config.yaml.example'
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (MANQUANT)")
            all_ok = False
    
    return all_ok

def check_config():
    """Vérifie la configuration."""
    config_path = Path('config.yaml')
    if config_path.exists():
        print(f"✅ config.yaml trouvé")
        return True
    else:
        print(f"⚠️  config.yaml non trouvé (utiliser config.yaml.example)")
        return False

def main():
    """Exécute toutes les vérifications."""
    print("=" * 60)
    print("Vérification de l'installation")
    print("=" * 60)
    print()
    
    print("1️⃣  Python")
    print("-" * 60)
    python_ok = check_python_version()
    print()
    
    print("2️⃣  Dépendances")
    print("-" * 60)
    deps_ok = check_dependencies()
    print()
    
    print("3️⃣  Structure du projet")
    print("-" * 60)
    struct_ok = check_project_structure()
    print()
    
    print("4️⃣  Configuration")
    print("-" * 60)
    config_ok = check_config()
    print()
    
    print("=" * 60)
    if python_ok and deps_ok and struct_ok:
        if config_ok:
            print("✅ Installation OK! Vous pouvez lancer: python -m src.main")
        else:
            print("⚠️  Installation OK mais config.yaml manquant")
            print("   Exécutez: cp config.yaml.example config.yaml")
    else:
        print("❌ L'installation n'est pas complète")
        print("   Exécutez: pip install -r requirements.txt")
    print("=" * 60)

if __name__ == '__main__':
    main()
