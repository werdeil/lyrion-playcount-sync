# Docker - Lyrion Playcount Sync

Guide de déploiement et d'utilisation de Lyrion Playcount Sync en conteneur Docker avec accès GUI via VNC.

## 📋 Prérequis

- Docker et Docker Compose installés
- Serveur Lyrion/Squeezebox arrêté (⚠️ Important!)
- Chemin de la base de données Lyrion accessible
- Ports 5900 (VNC) et 6080 (noVNC) disponibles

## 🚀 Installation Rapide

### 1. Configuration

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env et adapter:
# - VNC_PASSWORD: Votre mot de passe VNC
# - LYRION_DATA_PATH: Chemin vers votre installation Lyrion
nano .env
```

### 2. Démarrage du Conteneur

```bash
# Construire et démarrer
docker-compose up -d

# Vérifier le statut
docker-compose ps

# Consulter les logs
docker-compose logs -f lyrion-sync
```

### 3. Accès GUI

**VNC Client (direct):**
```
vnc://localhost:5900
Mot de passe: <VNC_PASSWORD>
```

**Navigateur (noVNC):**
```
http://localhost:6080/vnc.html
Mot de passe: <VNC_PASSWORD>
```

## 📁 Structure des Volumes

### Volumes Montés

```
lyrion-playcount-sync/
├── config.yaml              → Montée dans /app/config.yaml
├── logs/                    → Montée dans /app/logs
└── LYRION_DATA_PATH/        → Montée dans /lyrion-data
    └── persist.db           → Base de données Lyrion
```

## 🔧 Configuration

### Variables d'Environnement (.env)

| Variable | Défaut | Description |
|----------|--------|-------------|
| VNC_PASSWORD | changeme | Mot de passe d'accès VNC |
| VNC_PORT | 5900 | Port VNC direct |
| NOVNC_PORT | 6080 | Port accès web |
| VNC_WIDTH | 1280 | Largeur écran virtuel |
| VNC_HEIGHT | 1024 | Hauteur écran virtuel |
| VNC_DEPTH | 24 | Profondeur couleur (bits) |
| LYRION_DATA_PATH | - | Chemin base de données Lyrion |
| TZ | Europe/Paris | Fuseau horaire |

### Configuration Application (config.yaml)

La configuration de l'application se fait comme en mode standalone:

```bash
# Copier depuis l'exemple
cp config.yaml.example config.yaml

# Éditer les paramètres
nano config.yaml
```

## 🖥️ Interface Graphique

### Accès VNC

L'interface graphique est accessible via:

1. **Client VNC natif** (plus rapide)
   - macOS: Finder → Cmd+K → `vnc://localhost:5900`
   - Linux: `vncviewer localhost:5900`
   - Windows: TightVNC Viewer ou UltraVNC

2. **Navigateur Web** (noVNC - plus simple)
   - Accéder à http://localhost:6080/vnc.html
   - Pas de client à installer

## 🔐 Sécurité

### Recommandations

1. **Mot de passe VNC fort**
   ```bash
   VNC_PASSWORD="VotreMDPSecurise123!"
   ```

2. **Limiter l'accès réseau**
   - Ne pas exposer les ports VNC directement
   - Utiliser un reverse proxy (Traefik, nginx)
   - Firewall: autoriser seulement IP autorisées

3. **Données sensibles**
   - Ne pas inclure .env en git
   - .env.example fourni en exemple
   - Protéger le chemin LYRION_DATA_PATH

### Utilisation avec Traefik

Pour utiliser derrière Traefik:

1. **Éditer docker-compose.yml:**
```yaml
networks:
  homelab:
    external: true

labels:
  - "traefik.enable=true"
  - "traefik.http.routers.lyrion-sync.rule=Host(`lyrion-sync.local`)"
  - "traefik.http.services.lyrion-sync.loadbalancer.server.port=6080"
```

2. **Créer le réseau externe:**
```bash
docker network create homelab
```

3. **Redémarrer:**
```bash
docker-compose down
docker-compose up -d
```

## 🛠️ Commandes Utiles

### Gestion du Conteneur

```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart lyrion-sync

# Voir les logs
docker-compose logs -f lyrion-sync

# Accéder au shell
docker-compose exec lyrion-sync bash

# Reconstruire l'image
docker-compose build --no-cache
```

### Gestion des Volumes

```bash
# Vérifier les volumes
docker volume ls

# Nettoyer les volumes inutilisés
docker volume prune

# Sauvegarder les logs
docker cp lyrion-playcount-sync:/app/logs ./logs_backup
```

## 📊 Ressources

Le conteneur est configuré avec:

- **Limite CPU:** 2 cores
- **Limite Mémoire:** 2 GB
- **Réservation CPU:** 1 core
- **Réservation Mémoire:** 1 GB

À adapter dans docker-compose.yml selon votre système.

## 🐛 Dépannage

### Problème: "Cannot connect to VNC"

**Solution:**
```bash
# Vérifier les ports
docker-compose ps

# Vérifier les logs
docker-compose logs lyrion-sync | grep -i vnc

# Redémarrer
docker-compose restart lyrion-sync
```

### Problème: "Database locked"

**Cause:** Lyrion est encore en exécution
**Solution:**
```bash
# Arrêter Lyrion/Squeezebox
# Puis relancer le conteneur
docker-compose restart lyrion-sync
```

### Problème: "Permission denied" sur LYRION_DATA_PATH

**Cause:** Permissions insuffisantes
**Solution:**
```bash
# Vérifier les permissions
ls -la /path/to/lyrion/config

# Ajuster les permissions
chmod 755 /path/to/lyrion/config
chmod 644 /path/to/lyrion/config/persist.db
```

### Problème: "Application quits immediately"

**Cause:** Erreur de configuration
**Solution:**
```bash
# Voir les logs détaillés
docker-compose logs -f lyrion-sync

# Vérifier config.yaml
docker-compose exec lyrion-sync cat config.yaml

# Tester configuration
docker-compose exec lyrion-sync python3 run.py --check
```

## 📝 Cas d'Usage

### Synology NAS

```bash
# .env
LYRION_DATA_PATH=/volume1/docker/squeezebox-lms/prefs

# docker-compose.yml
volumes:
  - /volume1/docker/squeezebox-lms/prefs:/lyrion-data
```

### Linux Standalone

```bash
# .env
LYRION_DATA_PATH=/var/lib/squeezeboxserver/prefs

# sudo pour les permissions
sudo docker-compose up -d
```

### macOS avec Squeezebox

```bash
# .env
LYRION_DATA_PATH=/Users/$(whoami)/Library/Application\ Support/Squeezebox/prefs

# Définir la variable
LYRION_DATA_PATH=$HOME/Library/Application\ Support/Squeezebox/prefs
```

## 🔄 Mise à Jour

### Mettre à jour l'application

```bash
# Récupérer les derniers changements
git pull

# Reconstruire l'image
docker-compose build --no-cache

# Redémarrer
docker-compose up -d
```

### Sauvegarde Avant Mise à Jour

```bash
# Sauvegarder la configuration
cp config.yaml config.yaml.backup

# Sauvegarder les logs
cp -r logs logs_backup

# Sauvegarder la BD (optionnel)
docker-compose exec lyrion-sync cp /lyrion-data/persist.db /lyrion-data/persist.db.backup
```

## 📞 Support

Pour les problèmes:

1. Consulter les logs: `docker-compose logs lyrion-sync`
2. Vérifier la configuration: `docker-compose exec lyrion-sync python3 run.py --check`
3. Tester la connexion VNC manuellement
4. Consulter README.md principal

## 📚 Documentation Additionnelle

- [README.md](../README.md) - Guide principal
- [CONFIGURATION.md](../CONFIGURATION.md) - Configuration application
- [Dockerfile](./Dockerfile) - Définition image Docker
- [docker-compose.yml](./docker-compose.yml) - Configuration services

---

**Date:** 25 janvier 2026  
**Status:** ✅ Docker prêt pour production
