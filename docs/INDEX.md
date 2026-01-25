# 📚 Documentation - Lyrion Playcount Sync

Index complet de la documentation du projet.

## 🚀 Démarrage Rapide

**Lire en premier :**
- [Quick Start](01-getting-started/QUICKSTART.md) - 5 min pour démarrer
- [Installation Docker](02-installation/DOCKER.md) - Déploiement recommandé
- [Installation Locale](02-installation/LOCAL.md) - Pour développement

## 📋 Structure de la Documentation

### 1️⃣ [Getting Started](01-getting-started/)
Premiers pas avec l'application

- **[QUICKSTART.md](01-getting-started/QUICKSTART.md)** - Installation en 5 min
- **[OVERVIEW.md](01-getting-started/OVERVIEW.md)** - Vue d'ensemble du projet
- **[REQUIREMENTS.md](01-getting-started/REQUIREMENTS.md)** - Prérequis et dépendances

### 2️⃣ [Installation](02-installation/)
Guide d'installation détaillé

- **[DOCKER.md](02-installation/DOCKER.md)** - Installation Docker (recommandé)
- **[LOCAL.md](02-installation/LOCAL.md)** - Installation locale (dev)
- **[TROUBLESHOOTING.md](02-installation/TROUBLESHOOTING.md)** - Dépannage installation

### 3️⃣ [Configuration](03-configuration/)
Configuration de l'application

- **[CONFIG.md](03-configuration/CONFIG.md)** - Fichier config.yaml
- **[ENVIRONMENT.md](03-configuration/ENVIRONMENT.md)** - Variables d'environnement
- **[DATABASE.md](03-configuration/DATABASE.md)** - Configuration Lyrion

### 4️⃣ [Usage](04-usage/)
Guide d'utilisation

- **[USER_GUIDE.md](04-usage/USER_GUIDE.md)** - Guide complet d'utilisation
- **[WORKFLOWS.md](04-usage/WORKFLOWS.md)** - Cas d'usage et workflows
- **[TROUBLESHOOTING.md](04-usage/TROUBLESHOOTING.md)** - Dépannage

### 5️⃣ [Architecture](05-architecture/)
Architecture technique

- **[OVERVIEW.md](05-architecture/OVERVIEW.md)** - Vue d'ensemble architecture
- **[MODULES.md](05-architecture/MODULES.md)** - Description des modules
- **[DATABASE_SCHEMA.md](05-architecture/DATABASE_SCHEMA.md)** - Schéma base de données
- **[API.md](05-architecture/API.md)** - API interne

### 6️⃣ [Docker](06-docker/)
Documentation Docker

- **[GUIDE.md](06-docker/GUIDE.md)** - Guide Docker complet
- **[COMPOSE.md](06-docker/COMPOSE.md)** - Configuration docker-compose
- **[VNC.md](06-docker/VNC.md)** - Accès GUI via VNC
- **[TROUBLESHOOTING.md](06-docker/TROUBLESHOOTING.md)** - Dépannage Docker

### 7️⃣ [Development](07-development/)
Guide de développement

- **[SETUP.md](07-development/SETUP.md)** - Environnement de développement
- **[TESTING.md](07-development/TESTING.md)** - Tests et QA
- **[CONTRIBUTING.md](07-development/CONTRIBUTING.md)** - Contribuer au projet
- **[CODE_STYLE.md](07-development/CODE_STYLE.md)** - Style de code

### 8️⃣ [Reference](08-reference/)
Références techniques

- **[CHANGELOG.md](08-reference/CHANGELOG.md)** - Historique des versions
- **[API_REFERENCE.md](08-reference/API_REFERENCE.md)** - Référence API complète
- **[DATABASE_REFERENCE.md](08-reference/DATABASE_REFERENCE.md)** - Tables Lyrion
- **[GLOSSARY.md](08-reference/GLOSSARY.md)** - Glossaire des termes

## 🎯 Quick Links

| Besoin | Fichier |
|--------|---------|
| **Démarrer rapidement** | [QUICKSTART.md](01-getting-started/QUICKSTART.md) |
| **Installer Docker** | [DOCKER.md](02-installation/DOCKER.md) |
| **Configurer l'app** | [CONFIG.md](03-configuration/CONFIG.md) |
| **Utiliser l'interface** | [USER_GUIDE.md](04-usage/USER_GUIDE.md) |
| **Comprendre l'architecture** | [OVERVIEW.md](05-architecture/OVERVIEW.md) |
| **Déployer en production** | [DOCKER.md](06-docker/GUIDE.md) |
| **Contribuer** | [CONTRIBUTING.md](07-development/CONTRIBUTING.md) |
| **Référence API** | [API_REFERENCE.md](08-reference/API_REFERENCE.md) |

## 📖 Documents Racine

Les documents principaux sont à la racine du projet :

- **[README.md](../README.md)** - Vue d'ensemble et démarrage
- **[CHANGELOG.md](../CHANGELOG.md)** - Historique des versions
- **[LICENSE](../LICENSE)** - Licence MIT

## 🔍 Recherche par Sujet

### Synchronisation
- [Workflows - Sync](04-usage/WORKFLOWS.md#synchronisation)
- [SyncDetector Module](05-architecture/MODULES.md#syncdetector)
- [SyncOperations API](08-reference/API_REFERENCE.md#syncoperations)

### Matching
- [TrackMatcher Module](05-architecture/MODULES.md#trackmatcher)
- [Algorithmes de Matching](05-architecture/OVERVIEW.md#matching)
- [Configuration Matching](03-configuration/CONFIG.md#matching)

### Base de Données
- [Schéma Lyrion](05-architecture/DATABASE_SCHEMA.md)
- [Requêtes SQL](08-reference/DATABASE_REFERENCE.md)
- [Configuration DB](03-configuration/DATABASE.md)

### Interface Graphique
- [MainWindow Module](05-architecture/MODULES.md#mainwindow)
- [MatchDialog Module](05-architecture/MODULES.md#matchdialog)
- [Guide Utilisateur](04-usage/USER_GUIDE.md)

### Déploiement
- [Installation Docker](02-installation/DOCKER.md)
- [Installation Locale](02-installation/LOCAL.md)
- [VNC & GUI](06-docker/VNC.md)

### Dépannage
- [Installation - Troubleshooting](02-installation/TROUBLESHOOTING.md)
- [Usage - Troubleshooting](04-usage/TROUBLESHOOTING.md)
- [Docker - Troubleshooting](06-docker/TROUBLESHOOTING.md)

## 📊 Vue d'Ensemble des Fichiers

```
docs/
├── 01-getting-started/
│   ├── QUICKSTART.md          # Démarrage en 5 min
│   ├── OVERVIEW.md            # Vue d'ensemble
│   └── REQUIREMENTS.md        # Prérequis
├── 02-installation/
│   ├── DOCKER.md              # Installation Docker
│   ├── LOCAL.md               # Installation locale
│   └── TROUBLESHOOTING.md     # Dépannage install
├── 03-configuration/
│   ├── CONFIG.md              # Configuration application
│   ├── ENVIRONMENT.md         # Variables d'env
│   └── DATABASE.md            # Configuration DB
├── 04-usage/
│   ├── USER_GUIDE.md          # Guide complet
│   ├── WORKFLOWS.md           # Cas d'usage
│   └── TROUBLESHOOTING.md     # Dépannage usage
├── 05-architecture/
│   ├── OVERVIEW.md            # Vue d'ensemble
│   ├── MODULES.md             # Description modules
│   ├── DATABASE_SCHEMA.md     # Schéma DB
│   └── API.md                 # API interne
├── 06-docker/
│   ├── GUIDE.md               # Guide Docker
│   ├── COMPOSE.md             # docker-compose
│   ├── VNC.md                 # Accès GUI
│   └── TROUBLESHOOTING.md     # Dépannage Docker
├── 07-development/
│   ├── SETUP.md               # Dev environment
│   ├── TESTING.md             # Tests
│   ├── CONTRIBUTING.md        # Contribution
│   └── CODE_STYLE.md          # Style de code
├── 08-reference/
│   ├── CHANGELOG.md           # Historique
│   ├── API_REFERENCE.md       # Référence API
│   ├── DATABASE_REFERENCE.md  # Tables Lyrion
│   └── GLOSSARY.md            # Glossaire
└── INDEX.md                   # Ce fichier
```

## 🤝 Contribution Documentation

La documentation peut être améliorée ! Pour contribuer :

1. **Lire** [CONTRIBUTING.md](07-development/CONTRIBUTING.md)
2. **Modifier** le fichier approprié dans `docs/`
3. **Tester** les liens et syntaxe Markdown
4. **Commiter** avec message clair

Exemples :
```bash
git add docs/
git commit -m "docs: Amélioration section installation"
git commit -m "docs: Ajout FAQ troubleshooting"
```

## 📞 Support

- 📖 **Documentation** : Vous êtes ici
- 🐙 **Issues** : [GitHub Issues](https://github.com/ton-user/lyrion-playcount-sync/issues)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/ton-user/lyrion-playcount-sync/discussions)
- 📧 **Email** : support@example.com

## ✨ Conseils de Lecture

**👤 Pour les nouveaux utilisateurs :**
1. [QUICKSTART.md](01-getting-started/QUICKSTART.md)
2. [DOCKER.md](02-installation/DOCKER.md) ou [LOCAL.md](02-installation/LOCAL.md)
3. [USER_GUIDE.md](04-usage/USER_GUIDE.md)

**🏗️ Pour comprendre l'architecture :**
1. [OVERVIEW.md](05-architecture/OVERVIEW.md)
2. [MODULES.md](05-architecture/MODULES.md)
3. [DATABASE_SCHEMA.md](05-architecture/DATABASE_SCHEMA.md)

**👨‍💻 Pour contribuer :**
1. [SETUP.md](07-development/SETUP.md)
2. [TESTING.md](07-development/TESTING.md)
3. [CONTRIBUTING.md](07-development/CONTRIBUTING.md)

**🔧 Pour déployer :**
1. [DOCKER.md](02-installation/DOCKER.md)
2. [COMPOSE.md](06-docker/COMPOSE.md)
3. [CONFIG.md](03-configuration/CONFIG.md)

---

**Dernière mise à jour** : 25 janvier 2026  
**Documentation Version** : 1.0.0
