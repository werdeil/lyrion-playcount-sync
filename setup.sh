#!/bin/bash
# Script de configuration du projet

echo "🚀 Installation de Lyrion Playcount Sync"
echo "=========================================="
echo ""

# Vérifier Python 3.11+
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Créer l'environnement virtuel
if [ -d "venv" ]; then
    echo "ℹ Environnement virtuel existant trouvé"
else
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement
echo "📦 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer/mettre à jour pip
echo "📦 Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Créer la configuration
if [ -f "config.yaml" ]; then
    echo "ℹ Fichier config.yaml existant trouvé"
else
    echo "📝 Création du fichier config.yaml..."
    cp config.yaml.example config.yaml
    echo "⚠️  N'oubliez pas de configurer config.yaml avec vos chemins!"
fi

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Prochaines étapes:"
echo "1. Configurer config.yaml avec vos chemins Lyrion"
echo "2. Lancer l'application: python -m src.main"
echo ""
