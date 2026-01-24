FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    x11-apps \
    x11-common \
    x11-utils \
    xauth \
    supervisor \
    supervisor-doc \
    tigervnc-standalone-server \
    xfce4 \
    xfce4-terminal \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires VNC
RUN mkdir -p /root/.vnc \
    && mkdir -p /root/.config/xfce4

# Configuration VNC (mot de passe par défaut: password)
RUN echo "password" | vncpasswd -f > /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd

# Configuration supervisord
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Port VNC
EXPOSE 5901

# Commande de démarrage
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
