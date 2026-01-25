#!/bin/bash

###############################################################################
# LAUNCHER - Lyrion Playcount Sync
# 
# Usage:
#   bash scripts/launch.sh /path/to/lyrion/prefs [start|stop|logs|status]
#
# Examples:
#   bash scripts/launch.sh /volume1/docker/squeezebox-lms/prefs
#   bash scripts/launch.sh /var/lib/squeezeboxserver/prefs start
#   bash scripts/launch.sh /path/to/prefs logs
#   bash scripts/launch.sh /path/to/prefs stop
#
###############################################################################

set -e  # Exit on error

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION ARGUMENTS
# ═══════════════════════════════════════════════════════════════════════════

if [ $# -lt 1 ]; then
    echo -e "${RED}❌ Usage: bash scripts/launch.sh /path/to/lyrion/prefs [action]${NC}"
    echo ""
    echo "Actions disponibles:"
    echo "  start    - Démarrer le conteneur (par défaut)"
    echo "  stop     - Arrêter le conteneur"
    echo "  restart  - Redémarrer le conteneur"
    echo "  logs     - Afficher les logs"
    echo "  status   - Afficher le statut"
    echo ""
    echo "Exemples:"
    echo "  bash scripts/launch.sh /volume1/docker/squeezebox-lms/prefs"
    echo "  bash scripts/launch.sh /var/lib/squeezeboxserver/prefs start"
    echo "  bash scripts/launch.sh /path/to/prefs logs"
    exit 1
fi

# Variables
LYRION_DATA_PATH="$1"
ACTION="${2:-start}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config"
COMPOSE_FILE="$CONFIG_DIR/docker-compose.yml"

# ═══════════════════════════════════════════════════════════════════════════
# VÉRIFICATIONS PRÉALABLES
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}🔍 Vérification de la configuration...${NC}"

# Vérifier que le chemin Lyrion existe et contient persist.db
if [ ! -d "$LYRION_DATA_PATH" ]; then
    echo -e "${RED}❌ Erreur: Répertoire Lyrion non trouvé: $LYRION_DATA_PATH${NC}"
    exit 1
fi

if [ ! -f "$LYRION_DATA_PATH/persist.db" ]; then
    echo -e "${RED}❌ Erreur: persist.db non trouvé dans: $LYRION_DATA_PATH${NC}"
    exit 1
fi

# Vérifier que docker-compose existe
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ Erreur: docker-compose.yml non trouvé: $COMPOSE_FILE${NC}"
    exit 1
fi

# Vérifier que config.yaml existe
if [ ! -f "$PROJECT_ROOT/config.yaml" ]; then
    echo -e "${YELLOW}⚠️  config.yaml non trouvé, création depuis le template...${NC}"
    if [ ! -f "$CONFIG_DIR/config.yaml.example" ]; then
        echo -e "${RED}❌ Erreur: config.yaml.example non trouvé${NC}"
        exit 1
    fi
    cp "$CONFIG_DIR/config.yaml.example" "$PROJECT_ROOT/config.yaml"
fi

# Vérifier que le dossier logs existe
if [ ! -d "$PROJECT_ROOT/logs" ]; then
    echo -e "${YELLOW}⚠️  Dossier logs non trouvé, création...${NC}"
    mkdir -p "$PROJECT_ROOT/logs"
fi

echo -e "${GREEN}✅ Configuration validée${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# AFFICHER LES PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  Projet      : $PROJECT_ROOT"
echo "  Config      : $COMPOSE_FILE"
echo "  Lyrion DB   : $LYRION_DATA_PATH/persist.db"
echo "  Action      : $ACTION"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# EXÉCUTER L'ACTION
# ═══════════════════════════════════════════════════════════════════════════

case "$ACTION" in
    start)
        echo -e "${BLUE}🚀 Démarrage du conteneur...${NC}"
        cd "$PROJECT_ROOT"
        PROJECT_ROOT="$PROJECT_ROOT" LYRION_DATA_PATH="$LYRION_DATA_PATH" \
            docker-compose -f "$COMPOSE_FILE" up -d
        echo -e "${GREEN}✅ Conteneur démarré${NC}"
        echo ""
        echo -e "${BLUE}🌐 Accès:${NC}"
        echo "  🖥️  VNC Client : vnc://localhost:5900"
        echo "  🌐 Navigateur : http://localhost:6080/vnc.html"
        echo ""
        echo -e "${YELLOW}⏳ Patientez 10-15 secondes pour que le service soit prêt...${NC}"
        ;;
        
    stop)
        echo -e "${BLUE}🛑 Arrêt du conteneur...${NC}"
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" down
        echo -e "${GREEN}✅ Conteneur arrêté${NC}"
        ;;
        
    restart)
        echo -e "${BLUE}🔄 Redémarrage du conteneur...${NC}"
        cd "$PROJECT_ROOT"
        PROJECT_ROOT="$PROJECT_ROOT" LYRION_DATA_PATH="$LYRION_DATA_PATH" \
            docker-compose -f "$COMPOSE_FILE" restart
        echo -e "${GREEN}✅ Conteneur redémarré${NC}"
        ;;
        
    logs)
        echo -e "${BLUE}📜 Logs du conteneur:${NC}"
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" logs -f lyrion-sync
        ;;
        
    status)
        echo -e "${BLUE}📊 Statut du conteneur:${NC}"
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
        
    *)
        echo -e "${RED}❌ Action inconnue: $ACTION${NC}"
        echo "Actions valides: start, stop, restart, logs, status"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Opération terminée${NC}"
