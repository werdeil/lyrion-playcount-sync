# 📂 Structure du Projet

Guide de navigation dans la structure du projet réorganisée.

## 🎯 Points d'Entrée

- **[README.md](README.md)** - Vue d'ensemble et démarrage rapide
- **[docs/INDEX.md](docs/INDEX.md)** - Documentation complète (🎯 COMMENCER ICI)
- **[requirements.txt](requirements.txt)** - Dépendances Python

## 📁 Dossiers Principaux

### `docs/` - 📖 Documentation
**Consultez ceci pour**: Installation, configuration, utilisation, architecture

```
docs/
├── INDEX.md                    # 🎯 Hub central
├── 01-getting-started/         # ⚡ Démarrage
├── 02-installation/            # 📥 Installation
├── 03-configuration/           # ⚙️  Configuration
├── 04-usage/                   # 🎮 Utilisation
├── 05-architecture/            # 🏗️  Architecture
├── 06-docker/                  # 🐳 Docker
├── 07-development/             # 👨‍💻 Développement
└── 08-reference/               # 📚 Référence
```

**Pour démarrer**: [docs/01-getting-started/QUICKSTART.md](docs/01-getting-started/QUICKSTART.md)

### `src/` - 💻 Code Source
**Consultez ceci pour**: Comprendre le code, contribuer

```
src/
├── main.py                     # Orchestrateur principal
├── models/                     # Modèles métier
│   ├── sync_detector.py
│   └── track_matcher.py
├── gui/                        # Interface graphique
│   ├── main_window.py
│   └── match_dialog.py
├── database/                   # Opérations base de données
│   └── sync_operations.py
└── utils/                      # Utilitaires
    ├── config.py
    ├── logger.py
    └── decorators.py
```

### `tests/` - 🧪 Tests
**Consultez ceci pour**: Tester, vérifier la qualité

```
tests/
├── test_sync_detector.py
├── test_track_matcher.py
├── test_models.py
└── ... (autres tests)
```

**Lancer les tests**:
```bash
pytest tests/
```

### `config/` - ⚙️ Configuration
**Consultez ceci pour**: Configuration application et déploiement

```
config/
├── .env.example                # Variables d'environnement
├── config.yaml.example         # Configuration application
├── Dockerfile                  # Image Docker
├── docker-compose.yml          # Orchestration Docker
└── supervisord.conf            # Supervision (optionnel)
```

**Utiliser**:
```bash
cp config/.env.example .env
cp config/config.yaml.example config.yaml
docker-compose -f config/docker-compose.yml up
```

### `scripts/` - 📝 Scripts
**Consultez ceci pour**: Installation, maintenance

```
scripts/
├── run.py                      # Lancer l'application
├── setup.sh                    # Installation Linux/macOS
├── setup.bat                   # Installation Windows
├── deploy.py                   # Déploiement
├── entrypoint.sh               # Point d'entrée Docker
└── cleanup_docs.sh             # Nettoyage documentation
```

**Exemples d'utilisation**:
```bash
# Lancer l'application
python3 scripts/run.py

# Installer (Linux/macOS)
bash scripts/setup.sh

# Déployer
python3 scripts/deploy.py
```

### `examples/` - 📚 Exemples
**Consultez ceci pour**: Voir des exemples de code

```
examples/
├── examples_configuration.py
├── examples_models.py
├── examples_sync_detector.py
├── examples_track_matcher.py
├── examples_match_dialog.py
├── examples_sync_operations.py
└── integration_configuration.py
```

### `.archive/` - 📦 Archive
**Consultez ceci pour**: Historique (fichiers obsolètes)

Contient tous les anciens fichiers de documentation et de développement qui ne sont plus à jour.

**Ne pas éditer** - Pour l'historique uniquement.

## 🔍 Fichiers à la Racine

Seuls les fichiers essentiels restent à la racine:

| Fichier | Utilisé Pour |
|---------|-------------|
| **README.md** | Vue d'ensemble principal |
| **requirements.txt** | Dépendances Python |
| **LICENSE** | Licence MIT |
| **.gitignore** | Exclusions Git |
| **.gitattributes** | Attributs Git |

## 🗺️ Flux de Navigation

### 👤 Nouvel Utilisateur

```
README.md
    ↓
docs/INDEX.md
    ↓
docs/01-getting-started/QUICKSTART.md
    ↓
docs/02-installation/DOCKER.md
```

### 🔧 Admin/DevOps

```
docs/INDEX.md
    ↓
docs/02-installation/DOCKER.md
    ↓
config/docker-compose.yml
    ↓
docs/03-configuration/CONFIG.md
```

### 👨‍💻 Développeur

```
docs/INDEX.md
    ↓
docs/07-development/CONTRIBUTING.md
    ↓
src/
    ↓
tests/
```

### 🏗️ Architecte

```
docs/05-architecture/OVERVIEW.md
    ↓
src/
    ↓
docs/05-architecture/MODULES.md
```

## 📊 Avant vs Après Réorganisation

### ❌ Avant
```
Racine (40+ fichiers)
├── 30+ fichiers MD obsolètes
├── 7 fichiers Python exemple
├── 7 fichiers Python test
├── 5 fichiers configuration
├── 5 fichiers script
└── CHAOS 😱
```

### ✅ Après
```
Racine (3 fichiers)
├── README.md
├── requirements.txt
├── LICENSE
│
├── docs/ ..................... 📖 Documentation (8 sections)
├── src/ ....................... 💻 Code source
├── tests/ ..................... 🧪 Tests
├── config/ .................... ⚙️  Configuration
├── scripts/ ................... 📝 Scripts
├── examples/ .................. 📚 Exemples
├── .archive/ .................. 📦 Archive (40+ obsolètes)
└── STRUCTURE CLAIRE ✅
```

## 🎯 Résumé Structure

| Élément | Chemin | Pourquoi |
|---------|--------|---------|
| **Démarrer** | [docs/INDEX.md](docs/INDEX.md) | Point d'entrée unique |
| **Code** | `src/` | Ensemble du code |
| **Tests** | `tests/` | Validation |
| **Config** | `config/` | Centralisée |
| **Scripts** | `scripts/` | Utilitaires |
| **Exemples** | `examples/` | Référence |
| **Archive** | `.archive/` | Historique |

## 🚀 Commandes Utiles

### Naviguer
```bash
# Voir la structure
tree -L 2 -I '__pycache__|.git|venv_sync|logs'

# Voir les fichiers racine uniquement
ls -la | grep "^-"

# Voir les dossiers
ls -d */
```

### Développer
```bash
# Activer environnement
source venv_sync/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Lancer l'app
python3 scripts/run.py

# Lancer les tests
pytest tests/
```

### Docker
```bash
# Utiliser la config Docker
docker-compose -f config/docker-compose.yml up -d

# Voir les variables
cat config/.env.example
```

## 📞 Besoin d'Aide ?

| Question | Réponse |
|----------|---------|
| "Par où je commence ?" | → [docs/INDEX.md](docs/INDEX.md) |
| "Comment installer ?" | → [docs/02-installation/](docs/02-installation/) |
| "Où est le code ?" | → [src/](src/) |
| "Comment tester ?" | → [tests/](tests/) |
| "Comment déployer ?" | → [config/](config/) |
| "Voir un exemple ?" | → [examples/](examples/) |
| "Fichier ancien ?" | → [.archive/](.archive/) |

---

**Date réorganisation**: 25 janvier 2026  
**Status**: ✅ Structure organisée et prête
