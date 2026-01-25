FROM python:3.11-slim

# Installation dépendances système pour Tkinter + VNC
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11vnc \
    xvfb \
    fluxbox \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code application
COPY src/ ./src/
COPY config.yaml.example ./config.yaml.example
COPY run.py ./run.py

# Script d'entrée pour VNC + app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ports VNC et noVNC
EXPOSE 5900 6080

# Variables d'environnement par défaut
ENV DISPLAY=:99
ENV LYRION_DB_PATH=/lyrion-data/persist.db
ENV VNC_PASSWORD=changeme
ENV VNC_WIDTH=1280
ENV VNC_HEIGHT=1024
ENV VNC_DEPTH=24

# Point d'entrée
ENTRYPOINT ["/entrypoint.sh"]# Configuration supervisord
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Port VNC
EXPOSE 5901

# Commande de démarrage
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
