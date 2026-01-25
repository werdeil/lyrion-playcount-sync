#!/bin/bash
#
# Script d'entrée pour le conteneur Docker
# Démarre Xvfb, VNC, noVNC et l'application Python
#

set -e

echo "=========================================="
echo "Lyrion Playcount Sync - Docker Entrypoint"
echo "=========================================="
echo ""

# Configuration
DISPLAY_NUMBER=99
DISPLAY=":${DISPLAY_NUMBER}"
SCREEN_GEOMETRY="${VNC_WIDTH:-1280}x${VNC_HEIGHT:-1024}x${VNC_DEPTH:-24}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
VNC_PASSWORD="${VNC_PASSWORD:-changeme}"

echo "Configuration:"
echo "  DISPLAY: $DISPLAY"
echo "  Screen: $SCREEN_GEOMETRY"
echo "  VNC Port: $VNC_PORT"
echo "  noVNC Port: $NOVNC_PORT"
echo ""

# 1. Démarrage du serveur X virtuel (Xvfb)
echo "[1/6] Démarrage du serveur X virtuel (Xvfb)..."
Xvfb "$DISPLAY" -screen 0 "$SCREEN_GEOMETRY" &
XVFB_PID=$!
sleep 2
echo "  ✓ Xvfb démarré (PID: $XVFB_PID)"
echo ""

# 2. Démarrage du gestionnaire de fenêtres (fluxbox)
echo "[2/6] Démarrage du gestionnaire de fenêtres..."
DISPLAY="$DISPLAY" fluxbox &
FLUXBOX_PID=$!
sleep 1
echo "  ✓ Fluxbox démarré (PID: $FLUXBOX_PID)"
echo ""

# 3. Configuration du mot de passe VNC
echo "[3/6] Configuration VNC..."
mkdir -p /root/.vnc

# Créer le fichier de mot de passe
echo -n "$VNC_PASSWORD" | x11vnc -storepasswd /dev/stdin /root/.vnc/passwd
chmod 600 /root/.vnc/passwd
echo "  ✓ Mot de passe VNC configuré"
echo ""

# 4. Démarrage du serveur VNC (x11vnc)
echo "[4/6] Démarrage du serveur VNC..."
DISPLAY="$DISPLAY" \
  x11vnc \
    -display "$DISPLAY" \
    -forever \
    -shared \
    -rfbport "$VNC_PORT" \
    -rfbauth /root/.vnc/passwd \
    -noprimary \
    -noclipboard \
    -noxfixes \
    -noxdamage \
    -noxkb \
    -noxdamage \
    -nocursorshape \
    -log "*.off:*vnc*:*.off" \
    &
X11VNC_PID=$!
sleep 2
echo "  ✓ x11vnc démarré (PID: $X11VNC_PID)"
echo "  ✓ VNC disponible sur: localhost:$VNC_PORT"
echo ""

# 5. Démarrage du serveur noVNC (accès web)
echo "[5/6] Démarrage de noVNC (web interface)..."
/usr/share/novnc/utils/launch.sh \
  --vnc localhost:"$VNC_PORT" \
  --listen "$NOVNC_PORT" \
  &
NOVNC_PID=$!
sleep 2
echo "  ✓ noVNC démarré (PID: $NOVNC_PID)"
echo "  ✓ noVNC disponible sur: http://localhost:$NOVNC_PORT/vnc.html"
echo ""

# 6. Lancement de l'application Python
echo "[6/6] Lancement de l'application Lyrion Playcount Sync..."
echo ""
cd /app

# Vérifier si config.yaml existe
if [ ! -f "config.yaml" ]; then
    echo "  ⚠️  config.yaml non trouvé, utilisation de config.yaml.example"
    if [ -f "config.yaml.example" ]; then
        cp config.yaml.example config.yaml
        echo "  ✓ config.yaml créé depuis l'exemple"
    fi
fi

# Mettre à jour le chemin de la base de données si nécessaire
if [ -n "$LYRION_DB_PATH" ]; then
    echo "  📁 Base de données: $LYRION_DB_PATH"
fi

echo ""
echo "=========================================="
echo "Lancement de l'application..."
echo "=========================================="
echo ""

# Exécuter l'application
export DISPLAY="$DISPLAY"
python3 run.py

# Si l'application s'arrête, garder le conteneur actif pour VNC
echo ""
echo "Application arrêtée. Conteneur toujours accessible via VNC."
echo "Pour arrêter, utiliser 'docker stop <container_id>'"
echo ""

# Garder les processus en arrière-plan actifs
wait
