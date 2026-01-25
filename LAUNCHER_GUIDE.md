# 🚀 LAUNCHER - Guide d'Exécution Simple

**Objectif** : Lancer l'application en donnant **seulement** le chemin vers `persist.db`

---

## ⚡ Utilisation Rapide

### Bash (Recommandé pour scripts)
```bash
bash scripts/launch.sh /path/to/lyrion/prefs
```

### Python (Recommandé pour usage interactif)
```bash
python3 scripts/launch.py /path/to/lyrion/prefs
```

### Docker-compose directement
```bash
cd /path/to/project
PROJECT_ROOT=$(pwd) LYRION_DATA_PATH=/path/to/lyrion/prefs \
  docker-compose -f config/docker-compose.yml up -d
```

---

## 📋 Exemples par Plateforme

### Synology NAS
```bash
bash scripts/launch.sh /volume1/docker/squeezebox-lms/prefs
```

### Linux Standalone
```bash
bash scripts/launch.sh /var/lib/squeezeboxserver/prefs
```

### macOS
```bash
bash scripts/launch.sh ~/Library/Application\ Support/Squeezebox/prefs
```

### Windows (WSL)
```bash
bash scripts/launch.sh /mnt/c/Users/YourName/AppData/Local/Squeezebox/prefs
```

---

## 🎮 Commandes Disponibles

### Bash Script
```bash
# Démarrer (par défaut)
bash scripts/launch.sh /path/to/prefs

# Arrêter
bash scripts/launch.sh /path/to/prefs stop

# Redémarrer
bash scripts/launch.sh /path/to/prefs restart

# Voir les logs
bash scripts/launch.sh /path/to/prefs logs

# Vérifier le statut
bash scripts/launch.sh /path/to/prefs status
```

### Python Script
```bash
# Démarrer (par défaut)
python3 scripts/launch.py /path/to/prefs

# Arrêter
python3 scripts/launch.py /path/to/prefs --stop

# Redémarrer
python3 scripts/launch.py /path/to/prefs --restart

# Voir les logs
python3 scripts/launch.py /path/to/prefs --logs

# Suivre les logs en temps réel
python3 scripts/launch.py /path/to/prefs --logs --follow

# Vérifier le statut
python3 scripts/launch.py /path/to/prefs --status

# Mode verbose (pour déboguer)
python3 scripts/launch.py /path/to/prefs --verbose
```

---

## ✅ Ce que fait le Launcher

### Validation Automatique
- ✅ Vérifie que le répertoire Lyrion existe
- ✅ Vérifie que `persist.db` existe
- ✅ Crée le dossier `logs/` s'il n'existe pas
- ✅ Copie `config.yaml.example` → `config.yaml` si manquant
- ✅ Vérifie que `docker-compose.yml` existe

### Configuration Automatique
- ✅ Détecte le chemin du projet automatiquement
- ✅ Passe les bonnes variables à Docker
- ✅ Gère les chemins absolus correctement
- ✅ Lance Docker-compose depuis le bon répertoire

### Accès Après Démarrage
```
🌐 Accès:
  🖥️  VNC Client : vnc://localhost:5900
  🌐 Navigateur : http://localhost:6080/vnc.html
```

---

## 🔧 Configuration Automatique

Le launcher configure **automatiquement**:

1. **Variables d'environnement**
   ```bash
   PROJECT_ROOT=/path/to/project
   LYRION_DATA_PATH=/path/to/lyrion/prefs
   ```

2. **Chemins Docker**
   ```yaml
   volumes:
     - ${PROJECT_ROOT}/config.yaml:/app/config.yaml
     - ${PROJECT_ROOT}/logs:/app/logs
     - ${LYRION_DATA_PATH}:/lyrion-data
   ```

3. **Ports**
   ```
   VNC Direct   : localhost:5900
   NoVNC Web    : localhost:6080
   ```

---

## 🐳 Modifications Docker-compose

Le `config/docker-compose.yml` a été amélioré pour :

1. **Chemins relatifs fixes**
   ```yaml
   build:
     context: ..              # Remonte au répertoire parent
     dockerfile: config/Dockerfile  # Chemin correct
   ```

2. **Variables d'environnement**
   ```yaml
   volumes:
     - ${PROJECT_ROOT}/config.yaml:/app/config.yaml
     - ${PROJECT_ROOT}/logs:/app/logs
     - ${LYRION_DATA_PATH}:/lyrion-data
   ```

3. **Pas de chemins en dur**
   - ❌ Ancien: `./config.yaml` (ne fonctionnait pas depuis config/)
   - ✅ Nouveau: `${PROJECT_ROOT}/config.yaml` (flexible)

---

## 📊 Cas d'Usage Complets

### Setup Initial sur Synology
```bash
# 1. Cloner le projet
git clone https://github.com/ton-user/lyrion-playcount-sync.git
cd lyrion-playcount-sync

# 2. Lancer simplement avec le chemin Lyrion
bash scripts/launch.sh /volume1/docker/squeezebox-lms/prefs

# 3. Accéder via navigateur
# http://localhost:6080/vnc.html
```

### Migration vers une Autre Machine
```bash
# Sur l'ancienne machine
bash scripts/launch.sh /var/lib/squeezeboxserver/prefs stop

# Sur la nouvelle machine
bash scripts/launch.sh /nouveau/chemin/prefs start
```

### Dépannage
```bash
# Voir les logs détaillés
bash scripts/launch.sh /path/to/prefs logs

# Suivre en temps réel (Python)
python3 scripts/launch.py /path/to/prefs --logs --follow

# Redémarrer
bash scripts/launch.sh /path/to/prefs restart
```

---

## ✨ Avantages

| Aspect | Avant | Après |
|--------|-------|-------|
| **Complexité** | 10 étapes | 1 commande |
| **Erreurs config** | Courantes | Impossible |
| **Flexibilité** | Fixe | N'importe quel chemin |
| **Machines différentes** | Reconfigurer | Même commande |
| **Apprentissage** | Élevé | Facile |

---

## 🚨 Dépannage

### Erreur: "Répertoire Lyrion non trouvé"
```bash
# Vérifier le chemin
ls /path/to/prefs/persist.db

# Ou afficher le chemin correct
find / -name persist.db 2>/dev/null
```

### Erreur: "persist.db non trouvé"
```bash
# S'assurer que le chemin pointe à la bonne location
# Exemples:
# ✅ /volume1/docker/squeezebox-lms/prefs
# ❌ /volume1/docker/squeezebox-lms (trop haut)
```

### Docker ne répond pas
```bash
# Vérifier que Docker est en cours d'exécution
docker ps

# Vérifier les logs
bash scripts/launch.sh /path/to/prefs logs

# Redémarrer
bash scripts/launch.sh /path/to/prefs restart
```

---

## 📝 Notes

1. **Permissions**: Utiliser `sudo` si nécessaire pour Docker
   ```bash
   sudo bash scripts/launch.sh /path/to/prefs
   ```

2. **Variables d'environnement**: Peut aussi passer en `.env`
   ```bash
   cat > .env << EOF
   LYRION_DATA_PATH=/path/to/prefs
   PROJECT_ROOT=$(pwd)
   EOF
   docker-compose -f config/docker-compose.yml up -d
   ```

3. **Affichage NoVNC**: Accéder à `http://localhost:6080/vnc.html`
   - Mot de passe VNC: défini dans `.env` (VNC_PASSWORD)
   - Par défaut: `changeme`

---

## 🔗 Références Rapides

- **Configuration** : `config/docker-compose.yml`
- **Image Docker** : `config/Dockerfile`
- **Variables** : `.env` (copier depuis `config/.env.example`)
- **App config** : `config.yaml` (copier depuis `config/config.yaml.example`)
- **Logs app** : `logs/` (créé automatiquement)

---

**Version** : 1.0  
**Date** : 25 janvier 2026  
**Status** : Production-Ready ✅
