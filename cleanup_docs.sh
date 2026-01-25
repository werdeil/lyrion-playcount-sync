#!/bin/bash
# Script de nettoyage de la documentation
# Ce script archive les anciens documents MD dans un dossier OLD_DOCS/

set -e

echo "🧹 Nettoyage documentation..."
echo "================================="

# Créer dossier archive
mkdir -p OLD_DOCS

# Liste des fichiers à archiver
OLD_FILES=(
    "ARCHITECTURE.md"
    "CHANGELOG.md"
    "CONFIGURATION.md"
    "CONFIGURATION_STATUS.md"
    "DATABASE.md"
    "DATABASE_API.md"
    "DELIVERY_SUMMARY.md"
    "DEVELOPMENT_COMPLETE.md"
    "DOCKER.md"
    "EXAMPLES.md"
    "IMPLEMENTATION_SYNCDETECTOR.md"
    "INSTALLATION.md"
    "INDEX.md"
    "INTEGRATION_CHECKLIST.md"
    "MAINWINDOW.md"
    "MAINWINDOW_README.txt"
    "MAINWINDOW_SUMMARY.md"
    "MAIN_ORCHESTRATION.md"
    "MANIFEST.md"
    "MATCHDIALOG.md"
    "MATCHDIALOG_COMPLETION.md"
    "MATCHDIALOG_FINAL_REPORT.txt"
    "MATCHDIALOG_README.txt"
    "MATCHDIALOG_SUMMARY.md"
    "MODELS.md"
    "MODELS_README.txt"
    "MODELS_SUMMARY.md"
    "MODULE_DATABASE_SUMMARY.md"
    "NAVIGATION_DATABASE.md"
    "PRODUCTION.md"
    "PROJECT_SUMMARY.md"
    "QUICKSTART.md"
    "STATISTICS.md"
    "SUMMARY.md"
    "SYNCDETECTOR.md"
    "SYNCDETECTOR_QUICKSTART.md"
    "SYNCDETECTOR_STATUS.txt"
    "SYNCDETECTOR_SUMMARY.md"
    "SYNCOPERATIONS.md"
    "TRACKMATCHER.md"
    "TRACKMATCHER_QUICKSTART.md"
    "TRACKMATCHER_SUMMARY.md"
    "COMPLETION_REPORT.md"
    "CHANGELOG_DATABASE.md"
)

# Archiver les fichiers
count=0
for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📦 Archivage: $file"
        mv "$file" "OLD_DOCS/"
        ((count++))
    fi
done

echo ""
echo "✅ Archivage terminé:"
echo "   • $count fichiers archivés dans OLD_DOCS/"
echo ""
echo "📁 Structure finale:"
echo "   • README.md (mise à jour avec liens docs/)"
echo "   • docs/INDEX.md (point d'entrée documentation)"
echo "   • docs/01-getting-started/ (démarrage)"
echo "   • docs/02-installation/ (installation)"
echo "   • docs/03-configuration/ (configuration)"
echo "   • docs/04-usage/ (utilisation)"
echo "   • docs/05-architecture/ (architecture)"
echo "   • docs/06-docker/ (Docker)"
echo "   • docs/07-development/ (développement)"
echo "   • docs/08-reference/ (référence)"
echo "   • OLD_DOCS/ (anciens fichiers archivés)"
echo ""
echo "🎉 Documentation nettoyée et réorganisée!"
echo ""
echo "👉 Lire: docs/INDEX.md pour débuter"
