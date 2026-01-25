# 🎵 Lyrion Playcount Sync

**Outil desktop pour synchroniser les playcounts entre `tracks_persistent` et `alternativeplaycount` dans Lyrion** (anciennement Logitech Media Server).

> **⚠️ IMPORTANT** : Arrêtez Lyrion avant toute synchronisation pour éviter la corruption de la base de données.

## 📚 Documentation

**Accédez à la documentation complète dans le dossier [`docs/`](docs/)**

| Besoin | Lien |
|--------|------|
| **Démarrage rapide** | [Quick Start](docs/01-getting-started/QUICKSTART.md) |
| **Vue d'ensemble** | [Overview](docs/01-getting-started/OVERVIEW.md) |
| **Installation Docker** | [Docker Guide](docs/02-installation/DOCKER.md) |
| **Installation locale** | [Local Setup](docs/02-installation/LOCAL.md) |
| **Configuration** | [Configuration Guide](docs/03-configuration/CONFIG.md) |
| **Guide utilisateur** | [User Guide](docs/04-usage/USER_GUIDE.md) |
| **Architecture** | [Technical Overview](docs/05-architecture/OVERVIEW.md) |
| **Dépannage** | [Troubleshooting](docs/02-installation/TROUBLESHOOTING.md) |
| **Index complet** | [Documentation Index](docs/INDEX.md) |

## 🎯 Problème Résolu

Lyrion utilise deux tables pour stocker les playcounts :

- **`tracks_persistent`** : Compteurs internes de Lyrion
- **`alternativeplaycount`** : Compteurs importés (Last.fm, ListenBrainz, etc.)

Parfois, des morceaux existent dans `tracks_persistent` mais pas dans `alternativeplaycount`, créant des **incohérences entre les sources**.

### Cette application :

✅ **Détecte** les morceaux manquants dans `alternativeplaycount`  
🔍 **Propose** des correspondances via matching fuzzy (titre/artiste/album)  
✏️ **Synchronise** manuellement ou automatiquement  
🗑️ **Nettoie** `tracks_persistent` après synchronisation  
💾 **Sauvegarde** automatiquement avant toute modification  

## 📸 Interface

L'application offre une interface graphique intuitive pour :

- 📊 Visualiser les statistiques de synchronisation
- 🔄 Scanner la base pour détecter les incohérences
- 🎯 Voir les matches proposés avec scores de confiance
- ☑️ Corriger individuellement ou en masse
- 📋 Suivre les opérations via logs détaillés

## 🚀 Installation Rapide

### Prérequis

- Docker & Docker Compose **OU** Python 3.9+
- Accès en **lecture/écriture** à `persist.db` de Lyrion
- ⚠️ **Lyrion ARRÊTÉ** (critique!)

### Option 1 : Docker (Recommandé)

```bash
# Cloner le repo
git clone https://github.com/ton-user/lyrion-playcount-sync.git
cd lyrion-playcount-sync

# Configurer
cp .env.example .env
nano .env
# ➜ Modifier LYRION_DATA_PATH selon votre système

# Lancer
docker-compose up -d

# Accéder
# 🌐 Navigateur : http://localhost:6080/vnc.html
# 🖥️ Client VNC  : vnc://localhost:5900
```

**Arrêter l'application :**
```bash
docker-compose down
```

### Option 2 : Installation Locale (Développement)

```bash
# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Configurer
cp config.yaml.example config.yaml
nano config.yaml

# Lancer
python3 src/main.py
```

## 📖 Guide d'Utilisation

### 1️⃣ Scan Initial

1. Cliquer sur **"🔄 Scanner"** pour détecter les incohérences
2. Les **statistiques** s'affichent en haut :
   - Nombre de morceaux à synchroniser
   - Matches trouvés
   - Taux de succès

### 2️⃣ Analyse des Suggestions

Double-cliquer sur un morceau pour voir les **matches proposés**.

**Code couleur des matches :**

| Couleur | Score | Signification |
|---------|-------|---------------|
| 🟢 **Vert** | >90% | Sync automatique recommandée |
| 🟠 **Orange** | 60-90% | Vérifier avant sync |
| 🔴 **Rouge** | <60% | Correspondance douteuse |

### 3️⃣ Correction Manuelle

Pour **chaque morceau** :

1. **Sélectionner** le morceau dans la liste
2. **Choisir** le match approprié parmi les suggestions
3. **Définir l'action** :
   - **Copier** : Remplace le playcount dans `alternativeplaycount`
   - **Fusionner** : Additionne les deux playcounts
4. ☑️ Cocher **"Supprimer de `tracks_persistent`"** (optionnel)
5. Cliquer **"Appliquer"**

### 4️⃣ Corrections en Masse

Pour **synchroniser plusieurs morceaux** :

1. **Sélectionner** plusieurs morceaux (Ctrl+Clic ou Maj+Clic)
2. Cliquer **"Corriger sélection"**
3. Approuver chaque match **OU** approuver tout automatiquement si score > 90%

## ⚙️ Configuration

### Fichier `config.yaml`

```yaml
# Paramètres de matching
matching:
  auto_match_threshold: 90      # Score min pour auto-sync
  suggestion_min_score: 50       # Score min pour afficher une suggestion
  max_suggestions: 5             # Nombre max de matches à afficher

# Comportement de sync
sync:
  default_action: "COPY"         # Action par défaut: COPY ou MERGE
  delete_after_sync: true        # Supprimer de tracks_persistent après sync

# Chemins (auto-configurés)
database:
  path: "/lyrion-data/persist.db"
  backup_dir: "/app/backups"

# Logging
logging:
  level: "INFO"                  # DEBUG, INFO, WARNING, ERROR
  file: "/app/logs/sync.log"
```

### Variables d'Environnement (Docker)

Éditer `.env` :

```env
# VNC Configuration
VNC_PASSWORD=changeme
VNC_PORT=5900
NOVNC_PORT=6080
VNC_WIDTH=1280
VNC_HEIGHT=1024
VNC_DEPTH=24

# Lyrion Database
LYRION_DATA_PATH=/path/to/lyrion/config

# Timezone
TZ=Europe/Paris
```

## 🔍 Architecture Technique

### Structure du Projet

```
lyrion-playcount-sync/
├── src/
│   ├── main.py                 # Orchestrateur principal
│   ├── models/
│   │   ├── __init__.py
│   │   ├── sync_detector.py    # Détection des incohérences
│   │   └── track_matcher.py    # Matching fuzzy
│   ├── gui/
│   │   ├── main_window.py      # Interface principale
│   │   └── match_dialog.py     # Dialog des matches
│   ├── database/
│   │   ├── sync_operations.py  # Opérations DB
│   │   └── backups.py          # Gestion backups
│   └── utils/
│       ├── config.py           # Gestion configuration
│       ├── logger.py           # Logging
│       └── decorators.py       # Utilitaires
├── tests/                      # Suite de tests (31 tests ✅)
├── config.yaml.example         # Template configuration
├── requirements.txt            # Dépendances Python
├── Dockerfile                  # Image Docker
├── docker-compose.yml          # Orchestration Docker
├── .env.example                # Variables d'environnement
├── entrypoint.sh              # Script de démarrage
├── run.py                      # Point d'entrée smart
└── README.md                   # Ce fichier
```

### Composants Clés

| Module | Responsabilité |
|--------|-----------------|
| **SyncDetector** | Détecte morceaux manquants via requêtes SQL |
| **TrackMatcher** | Matching fuzzy (RapidFuzz) titre/artiste/album |
| **MainWindow** | Interface GUI (ttkbootstrap) |
| **SyncOperations** | Opérations DB sécurisées avec transactions |
| **ConfigManager** | Gestion YAML de la configuration |
| **Logger** | Logs rotatifs dans `./logs/sync.log` |

## 🔒 Sécurité & Fiabilité

✅ **Backup automatique** avant toute modification  
✅ **Transactions SQL** (rollback en cas d'erreur)  
✅ **Logs détaillés** dans `./logs/sync.log`  
✅ **Validation** de tous les matches avant sync  
✅ **Permissions vérifiées** sur persist.db  

⚠️ **RÈGLE D'OR** : **Toujours arrêter Lyrion avant utilisation**

```bash
# Vérifier que Lyrion n'est pas en cours d'exécution
ps aux | grep -i lyrion
ps aux | grep -i squeezebox
```

## 📊 Structure Lyrion Database

### Tables Utilisées

```sql
-- Playcounts internes Lyrion
CREATE TABLE tracks_persistent (
    urlmd5 TEXT PRIMARY KEY,
    playcount INTEGER DEFAULT 0,
    lastplayed INTEGER DEFAULT 0,
    rating INTEGER DEFAULT 0
);

-- Playcounts importés (Last.fm, ListenBrainz, etc.)
CREATE TABLE alternativeplaycount (
    urlmd5 TEXT PRIMARY KEY,
    playcount INTEGER DEFAULT 0,
    lastplayed INTEGER DEFAULT 0,
    source TEXT
);

-- Métadonnées des morceaux
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY,
    url TEXT,
    urlmd5 TEXT,
    title TEXT,
    album INTEGER
);

-- Informations albums
CREATE TABLE albums (
    id INTEGER PRIMARY KEY,
    title TEXT,
    artwork TEXT,
    artist INTEGER
);

-- Informations artistes
CREATE TABLE contributors (
    id INTEGER PRIMARY KEY,
    name TEXT,
    role TEXT
);
```

## 🐛 Troubleshooting

### "Database is locked"

**Cause** : Lyrion est en cours d'exécution.

```bash
# Arrêter Lyrion et ses processus
sudo killall squeezebox
sudo killall -9 perl
# OU via interface de Lyrion: Settings → Server → Stop Server

# Attendre 5 secondes
sleep 5

# Relancer l'application
docker-compose restart lyrion-sync
```

### "Permission denied" sur persist.db

**Cause** : Permissions insuffisantes sur le fichier.

```bash
# Vérifier
ls -la /path/to/lyrion/persist.db

# Corriger (macOS/Linux)
chmod 666 /path/to/lyrion/persist.db
chmod 755 /path/to/lyrion/

# Corriger (Docker)
docker-compose exec lyrion-sync chmod 666 /lyrion-data/persist.db
```

### Aucune suggestion de match

**Cause** : Score minimum trop élevé.

```yaml
# Réduire dans config.yaml
matching:
  suggestion_min_score: 30  # Au lieu de 50
  auto_match_threshold: 70  # Au lieu de 90
```

### Interface VNC lente

**Cause** : noVNC moins performant que client natif.

**Solution** : Utiliser un client VNC natif :

- **macOS** : Finder → Cmd+K → `vnc://localhost:5900`
- **Linux** : `vncviewer localhost:5900` ou `remmina`
- **Windows** : TightVNC Viewer ou UltraVNC

### Application crash lors du sync

**Solution** :

1. Consulter les logs :
   ```bash
   docker-compose logs -f lyrion-sync | grep -i error
   ```

2. Vérifier la configuration :
   ```bash
   docker-compose exec lyrion-sync python3 run.py --check
   ```

3. Restaurer depuis backup :
   ```bash
   docker-compose exec lyrion-sync ls -la /app/backups/
   ```

## 📝 Cas d'Usage

### Synology NAS

```bash
# .env
LYRION_DATA_PATH=/volume1/docker/squeezebox-lms/prefs

# Démarrer
docker-compose up -d
```

### Linux Standalone

```bash
# .env
LYRION_DATA_PATH=/var/lib/squeezeboxserver/prefs

# Avec sudo si nécessaire
sudo docker-compose up -d

# Permissions
sudo chmod 666 /var/lib/squeezeboxserver/prefs/persist.db
```

### macOS avec Squeezebox

```bash
# .env
LYRION_DATA_PATH=/Users/$(whoami)/Library/Application Support/Squeezebox/prefs

# Lancer
docker-compose up -d
```

### Windows

```powershell
# .env (utiliser chemin Windows)
LYRION_DATA_PATH=C:\Users\YourUsername\AppData\Local\Squeezebox\prefs

# Lancer
docker-compose up -d
```

## 🔄 Mise à Jour

### Mettre à jour l'application

```bash
# Récupérer les derniers changements
git pull origin main

# Reconstruire l'image Docker
docker-compose build --no-cache

# Redémarrer
docker-compose up -d
```

### Sauvegarde Avant Mise à Jour

```bash
# Sauvegarder configuration
cp config.yaml config.yaml.backup

# Sauvegarder les logs
cp -r logs logs_backup

# Sauvegarder la BD
docker-compose exec lyrion-sync cp /lyrion-data/persist.db \
  /lyrion-data/persist.db.backup.$(date +%Y%m%d)

# Vérifier les backups
ls -la /app/backups/
```

## 🤝 Contribution

Les contributions sont bienvenues ! Voici comment :

```bash
# 1. Fork le projet sur GitHub
# 2. Cloner votre fork
git clone https://github.com/votre-user/lyrion-playcount-sync.git
cd lyrion-playcount-sync

# 3. Créer une branche
git checkout -b feature/votre-feature

# 4. Faire vos modifications
# 5. Lancer les tests
pytest tests/

# 6. Commit
git commit -am 'Ajout: description de la feature'

# 7. Push
git push origin feature/votre-feature

# 8. Ouvrir une Pull Request sur GitHub
```

### Directives

- ✅ Suivre le style de code (PEP 8)
- ✅ Ajouter des tests pour les nouvelles fonctionnalités
- ✅ Documenter les changements majeurs
- ✅ Respecter la structure existante

## 📚 Documentation

| Document | Contenu |
|----------|---------|
| [CONFIGURATION.md](CONFIGURATION.md) | Configuration détaillée |
| [DOCKER.md](DOCKER.md) | Guide Docker & Compose |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architecture technique |
| [MAIN_ORCHESTRATION.md](MAIN_ORCHESTRATION.md) | Orchestration application |

## 📋 Roadmap

- [ ] Support pour multiples sources (Last.fm, ListenBrainz, AcousticBrainz)
- [ ] Interface web alternative à VNC
- [ ] API REST pour intégrations
- [ ] Support Lyrion Nightingale (future version)
- [ ] Sync bidirectionnel Last.fm ↔ Lyrion
- [ ] Base de données SQLite locale pour cache

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 Crédits & Remerciements

- **[Lyrion](https://lyrion.org/)** - Serveur de musique moderne
- **[RapidFuzz](https://github.com/maxbachmann/RapidFuzz)** - Matching fuzzy haute performance
- **[ttkbootstrap](https://ttkbootstrap.readthedocs.io/)** - UI moderne pour Tkinter
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM Python robuste
- **[Docker](https://www.docker.com/)** - Containerization

## 💬 Support & Contact

- 📧 Email : support@example.com
- 🐙 GitHub Issues : [Créer une issue](https://github.com/ton-user/lyrion-playcount-sync/issues)
- 💬 Discussions : [GitHub Discussions](https://github.com/ton-user/lyrion-playcount-sync/discussions)

## ⭐ Si Ce Projet Vous Plaît

N'hésitez pas à **⭐ Star** ce repository pour montrer votre soutien !

---

**Dernière mise à jour** : 25 janvier 2026  
**Version** : 1.0.0  
**Status** : ✅ Production Ready
