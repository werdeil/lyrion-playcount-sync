# 📂 Documentation Structure - Guide Visuel

## 🎯 Vue d'Ensemble

```
📦 lyrion-playcount-sync/
│
├── 📄 README.md ........................ Point d'entrée principal
│   └─→ Lien vers docs/INDEX.md
│
├── 📖 docs/ ........................... NOUVELLE DOCUMENTATION CENTRALISÉE
│   │
│   ├── 📄 INDEX.md ..................... 🎯 POINT D'ENTRÉE DOCS
│   │   ├─→ 01-getting-started/QUICKSTART.md
│   │   ├─→ 02-installation/DOCKER.md
│   │   ├─→ 03-configuration/CONFIG.md
│   │   ├─→ 04-usage/USER_GUIDE.md
│   │   ├─→ 05-architecture/OVERVIEW.md
│   │   ├─→ 06-docker/GUIDE.md
│   │   ├─→ 07-development/CONTRIBUTING.md
│   │   └─→ 08-reference/CHANGELOG.md
│   │
│   ├── 01-getting-started/ ............ ⚡ DÉMARRAGE RAPIDE
│   │   ├── QUICKSTART.md ............. 5 min pour démarrer
│   │   ├── OVERVIEW.md ............... Vue d'ensemble projet
│   │   ├── REQUIREMENTS.md ........... Prérequis système
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── 02-installation/ .............. 📥 INSTALLATION
│   │   ├── DOCKER.md ................. Installation Docker
│   │   ├── LOCAL.md .................. Installation locale (dev)
│   │   ├── TROUBLESHOOTING.md ........ Dépannage install
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── 03-configuration/ ............. ⚙️  CONFIGURATION
│   │   ├── CONFIG.md ................. config.yaml détaillé
│   │   ├── ENVIRONMENT.md ............ Variables d'environnement
│   │   ├── DATABASE.md ............... Configuration Lyrion
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── 04-usage/ ..................... 🎮 UTILISATION
│   │   ├── USER_GUIDE.md ............. Guide complet utilisateur
│   │   ├── WORKFLOWS.md .............. Cas d'usage et workflows
│   │   ├── TROUBLESHOOTING.md ........ Dépannage utilisation
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── 05-architecture/ .............. 🏗️  ARCHITECTURE
│   │   ├── OVERVIEW.md ............... Vue d'ensemble architecture
│   │   ├── MODULES.md ................ Description modules
│   │   ├── DATABASE_SCHEMA.md ........ Schéma base données
│   │   ├── API.md .................... API interne
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── 06-docker/ .................... 🐳 DOCKER
│   │   ├── GUIDE.md .................. Guide Docker complet
│   │   ├── COMPOSE.md ................ Configuration docker-compose
│   │   ├── VNC.md .................... Accès GUI via VNC
│   │   ├── TROUBLESHOOTING.md ........ Dépannage Docker
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── 07-development/ ............... 👨‍💻 DÉVELOPPEMENT
│   │   ├── CONTRIBUTING.md ........... Guide contribution
│   │   ├── SETUP.md .................. Dev environment
│   │   ├── TESTING.md ................ Tests et QA
│   │   ├── CODE_STYLE.md ............. Style Python/PEP8
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── 08-reference/ ................. 📚 RÉFÉRENCE
│   │   ├── CHANGELOG.md .............. Historique versions
│   │   ├── API_REFERENCE.md .......... Référence API complète
│   │   ├── DATABASE_REFERENCE.md .... Tables Lyrion détaillées
│   │   ├── GLOSSARY.md ............... Glossaire termes
│   │   └── README.md ................. (auto-généré)
│   │
│   ├── MIGRATION_PLAN.md ............. 📋 Plan migration docs
│   └── README.md ..................... Index README auto-généré
│
├── 📂 OLD_DOCS/ ....................... 🗃️  ARCHIVE ANCIENS FICHIERS
│   ├── ARCHITECTURE.md
│   └── ... (autres anciens MD)
│
├── 🔧 cleanup_docs.sh ................. Script nettoyage (bash)
├── 📋 DOCUMENTATION_SUMMARY.md ........ Résumé réorganisation
│
└── src/, tests/, config, docker... ... CODE ET CONFIG
```

## 🔍 Par Thème

### Pour un **Nouvel Utilisateur**
```
START HERE → README.md
     ↓
START → docs/01-getting-started/QUICKSTART.md (5 min)
     ↓
INSTALL → docs/02-installation/DOCKER.md ou LOCAL.md
     ↓
LEARN → docs/01-getting-started/OVERVIEW.md
     ↓
USE → docs/04-usage/USER_GUIDE.md
```

### Pour un **Admin/DevOps**
```
START → docs/INDEX.md
     ↓
INSTALL → docs/02-installation/DOCKER.md
     ↓
CONFIG → docs/03-configuration/CONFIG.md
     ↓
DEPLOY → docs/06-docker/GUIDE.md
     ↓
TROUBLESHOOT → docs/02-installation/TROUBLESHOOTING.md
```

### Pour un **Développeur**
```
START → docs/INDEX.md
     ↓
CONTRIBUTE → docs/07-development/CONTRIBUTING.md
     ↓
SETUP → docs/07-development/SETUP.md
     ↓
LEARN CODE → docs/05-architecture/OVERVIEW.md
     ↓
WRITE → docs/07-development/CODE_STYLE.md
     ↓
TEST → docs/07-development/TESTING.md
```

### Pour un **Architecte/DevOps Avancé**
```
START → docs/INDEX.md
     ↓
ARCHITECTURE → docs/05-architecture/OVERVIEW.md
     ↓
MODULES → docs/05-architecture/MODULES.md
     ↓
DATABASE → docs/05-architecture/DATABASE_SCHEMA.md
     ↓
API → docs/05-architecture/API.md
```

## 📊 Contenu par Section

| Section | Fichiers | Lignes | Focus |
|---------|----------|--------|-------|
| **01-getting-started** | 3 | 500+ | Démarrage, vue ensemble |
| **02-installation** | 3 | 400+ | Docker, local, dépannage |
| **03-configuration** | 3 | 350+ | Config app, env, BD |
| **04-usage** | 3 | 400+ | Guide, workflows, help |
| **05-architecture** | 4 | 600+ | Vue ensemble, modules, API |
| **06-docker** | 4 | 400+ | Docker, compose, VNC |
| **07-development** | 4 | 600+ | Contributing, setup, tests |
| **08-reference** | 4 | 400+ | Changelog, API, glossaire |
| **Total** | 28 | 3,650+ | Complet |

## 🔗 Flux de Liens

```
                    README.md
                        │
                        ↓
                  docs/INDEX.md ◄── POINT CENTRAL
                    /   |   \
                   /    |    \
                  ↓     ↓     ↓
            01-  02-   03-   04-   05-   06-   07-   08-
          getting install config usage arch  docker dev  ref
```

## 📌 Conventions

### Noms de Fichiers
- **Majuscules** : SECTIONS_PRINCIPALES.md
- **CamelCase** : SectionSpecifique.md
- **Minuscules** : section_courte.md
- **Autres** : README.md, INDEX.md, GLOSSARY.md

### Numérotation Sections
```
01-getting-started      Démarrage (pas pour production)
02-installation         Installation complète
03-configuration        Configuration détaillée
04-usage               Utilisation application
05-architecture        Comprendre le code
06-docker              Déploiement Docker
07-development         Contribution et dev
08-reference           Références et historique
```

### Hiérarchie Titre Markdown
```
# Section Principale (utilisé 1x par fichier)
## Sous-section
### Sous-sous-section
#### Détail
```

## 🎯 Avantages Structure

✅ **Logique** - Numérotation pour progression naturelle  
✅ **Clair** - Noms explicites de dossiers  
✅ **Centralisé** - docs/INDEX.md maître  
✅ **Maintenable** - Pas de doublons  
✅ **Scalable** - Facile ajouter sections  
✅ **Accessible** - Links depuis README.md  

## 🚀 Utilisation

### Lire docs/
```bash
# Voir structure
tree docs/

# Voir INDEX
cat docs/INDEX.md

# Chercher un doc
find docs/ -name "*pattern*" -type f

# Lire markdown dans terminal
less docs/01-getting-started/QUICKSTART.md
```

### Ajouter Document
```bash
# Ajouter dans docs/XX-theme/
touch docs/07-development/NEW_GUIDE.md

# Éditer
nano docs/07-development/NEW_GUIDE.md

# Ajouter lien dans INDEX.md
# ...
```

### Archiver Ancien Doc
```bash
# Déplacer vers OLD_DOCS/
mv OLD_DOCUMENT.md OLD_DOCS/

# Commiter
git add .
git commit -m "docs: Archive OLD_DOCUMENT.md"
```

## 📞 Questions ?

- **Vue d'ensemble** → [docs/INDEX.md](docs/INDEX.md)
- **Chercher doc** → Ctrl+F dans INDEX.md
- **Contribution** → [CONTRIBUTING.md](docs/07-development/CONTRIBUTING.md)

---

**Structure créée** : 25 janvier 2026  
**Version** : 1.0.0  
**Status** : ✅ Organisation complète
