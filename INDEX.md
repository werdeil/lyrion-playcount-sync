# 📚 Index complet du projet Lyrion Playcount Sync

## 🎯 Points d'entrée selon votre besoin

### Je veux...

#### 📖 **Comprendre le projet**
- Lire [README.md](README.md) - Vue d'ensemble complète
- Consulter [SUMMARY.md](SUMMARY.md) - Résumé technique
- Vérifier [MANIFEST.md](MANIFEST.md) - Détails du projet

#### 🚀 **Installer et lancer**
- Guide rapide : [QUICKSTART.md](QUICKSTART.md)
- Guide détaillé : [INSTALLATION.md](INSTALLATION.md)
- Vérifier installation : `python check_install.py`

#### 💻 **Lancer l'application**
1. Installer : `pip install -r requirements.txt`
2. Configurer : `cp config.yaml.example config.yaml` (adapter le chemin)
3. Lancer : `python -m src/main.py`

#### 🐳 **Utiliser Docker**
```bash
docker-compose up -d
# Accès VNC : localhost:5901 (password: password)
```

#### 🔧 **Développer et contribuer**
- Consulter la structure : voir section Arborescence
- Comprendre l'architecture : [README.md#architecture](README.md#architecture)
- Implémenter features : voir Modules à compléter

#### 🆘 **Résoudre un problème**
1. Consulter [QUICKSTART.md#dépannage](QUICKSTART.md#dépannage)
2. Consulter [INSTALLATION.md#dépannage](INSTALLATION.md#dépannage)
3. Exécuter `python check_install.py`
4. Vérifier les logs : `cat playcount_sync.log`

---

## 📁 Arborescence complète

```
lyrion-playcount-sync/                  # Racine du projet
│
├── 📖 DOCUMENTATION
│   ├── README.md                       ← Lisez moi d'abord!
│   ├── INSTALLATION.md                 ← Guide d'installation
│   ├── QUICKSTART.md                   ← 5 minutes pour commencer
│   ├── SUMMARY.md                      ← Résumé technique
│   ├── MANIFEST.md                     ← Détails du projet
│   └── INDEX.md                        ← Ce fichier
│
├── ⚙️ CONFIGURATION
│   ├── requirements.txt                ← Dépendances Python
│   ├── config.yaml.example             ← Configuration exemple
│   ├── .env.example                    ← Variables d'environnement
│   └── .gitignore
│
├── 🐳 DOCKER
│   ├── Dockerfile                      ← Image conteneur
│   ├── docker-compose.yml              ← Orchestration
│   └── supervisord.conf                ← Gestion services
│
├── 🔧 INSTALLATION & VÉRIFICATION
│   ├── setup.sh                        ← Installation macOS/Linux
│   ├── setup.bat                       ← Installation Windows
│   └── check_install.py                ← Vérification installation
│
└── 💻 CODE SOURCE
    └── src/
        │
        ├── main.py                     ← Point d'entrée
        ├── __init__.py
        │
        ├── 📚 database/                ← Gestion base de données
        │   ├── __init__.py
        │   ├── connection.py           ✅ Connexion SQLite
        │   └── queries.py              ✅ Requêtes SQL
        │
        ├── 🔍 matching/                ← Algorithme matching
        │   ├── __init__.py
        │   └── fuzzy_matcher.py        ✅ Matching fuzzy
        │
        ├── 📊 models/                  ← Modèles de données
        │   ├── __init__.py
        │   └── track.py                ✅ Track, TrackMatch
        │
        ├── 🎨 ui/                      ← Interface utilisateur
        │   ├── __init__.py
        │   ├── main_window.py          ✅ Fenêtre principale
        │   └── match_dialog.py         ⏳ À implémenter
        │
        └── 🛠️ utils/                   ← Utilitaires
            ├── __init__.py
            └── logger.py               ✅ Logging
```

---

## 📚 Guide de lecture par rôle

### 👨‍💼 Pour le chef de projet
1. [SUMMARY.md](SUMMARY.md) - Aperçu du projet
2. [MANIFEST.md](MANIFEST.md) - Détails et ressources
3. [README.md](README.md) - Fonctionnalités et roadmap

### 👨‍💻 Pour le développeur
1. [QUICKSTART.md](QUICKSTART.md) - Installation rapide
2. [README.md#architecture](README.md#architecture) - Architecture
3. `src/` - Explorer le code source
4. [INSTALLATION.md](INSTALLATION.md) - Installation détaillée

### 🔧 Pour l'administrateur système
1. [INSTALLATION.md](INSTALLATION.md) - Installation sur serveur
2. [INSTALLATION.md#localiser-la-bd-lyrion](#localiser-la-bd-lyrion) - Trouver la BD
3. [README.md#docker](#docker) - Déploiement Docker
4. `docker-compose.yml` - Configuration Docker

### 🆘 Pour le dépannage
1. [QUICKSTART.md#dépannage](QUICKSTART.md#dépannage) - Problèmes courants
2. [INSTALLATION.md#dépannage](INSTALLATION.md#dépannage) - Problèmes installation
3. `python check_install.py` - Diagnostic
4. `cat playcount_sync.log` - Logs détaillés

---

## 🔑 Concepts clés

### Stack technique
- **Backend** : Python 3.11+
- **UI** : Tkinter + ttkbootstrap
- **BD** : SQLite (persist.db)
- **Matching** : rapidfuzz
- **Config** : YAML + .env

### Modules principaux
1. **database/** - Lecture/écriture BD
2. **matching/** - Algorithme de matching
3. **ui/** - Interface utilisateur
4. **models/** - Structures de données
5. **utils/** - Utilitaires (logging)

### Workflow principal
```
Utilisateur
   ↓ [Interface UI]
Charger données
   ↓ [database/queries.py]
FuzzyMatcher
   ↓ [matching/fuzzy_matcher.py]
Revue correspondances
   ↓ [ui/match_dialog.py]
Synchroniser
   ↓ [database/connection.py]
SQLite BD mise à jour
```

---

## 📋 Checklist d'installation

### ✅ Avant de commencer
- [ ] Python 3.11+ installé
- [ ] Accès à la BD Lyrion
- [ ] Git installé (optionnel)

### ✅ Installation
- [ ] `pip install -r requirements.txt`
- [ ] `cp config.yaml.example config.yaml`
- [ ] Adapter `database.path` dans config.yaml
- [ ] `python check_install.py` - Doit afficher ✓

### ✅ Premier lancement
- [ ] `python -m src.main`
- [ ] Fenêtre principale doit s'afficher
- [ ] Pas d'erreur dans les logs

### ✅ Configuration avancée (optionnel)
- [ ] Adapter `matching.similarity_threshold`
- [ ] Essayer différentes `matching.ratio_method`
- [ ] Configurer les logs dans `config.yaml`

---

## 🆘 FAQ rapide

### Q: Où est ma base de données Lyrion?
**R:** Voir [INSTALLATION.md#localiser-la-bd-lyrion](INSTALLATION.md#localiser-la-bd-lyrion)

### Q: Que faire si aucune correspondance n'est trouvée?
**R:** Voir [QUICKSTART.md#pas-de-correspondances](QUICKSTART.md#pas-de-correspondances)

### Q: Comment utiliser Docker?
**R:** Voir [README.md#docker](README.md#docker)

### Q: Quelles sont les dépendances?
**R:** Voir requirements.txt ou [README.md#requirements](README.md#requirements)

### Q: Comment déboguer?
**R:** Exécutez `python check_install.py` et consultez `playcount_sync.log`

---

## 📦 Fichiers importants

### À lire en priorité
- **requirements.txt** - Dépendances Python
- **config.yaml.example** - Configuration modèle
- **src/main.py** - Point d'entrée

### À configurer
- **config.yaml** - Créer à partir de config.yaml.example
- **.env** (optionnel) - Créer à partir de .env.example

### À comprendre
- **src/database/connection.py** - Comment accéder la BD
- **src/matching/fuzzy_matcher.py** - Comment fonctionne le matching
- **src/ui/main_window.py** - L'interface utilisateur

---

## 🚀 Commandes utiles

### Installation
```bash
# Installation complète
./setup.sh                    # macOS/Linux
setup.bat                     # Windows

# Installation manuelle
pip install -r requirements.txt
cp config.yaml.example config.yaml
```

### Vérification
```bash
# Vérifier l'installation
python check_install.py

# Vérifier les dépendances
pip list | grep -E "ttkbootstrap|rapidfuzz|pyyaml"
```

### Lancement
```bash
# Mode développement
python -m src.main

# Mode debug
export LOG_LEVEL=DEBUG
python -m src.main
```

### Docker
```bash
# Lancer les conteneurs
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

---

## 📊 Statistiques du projet

| Métrique | Valeur |
|----------|--------|
| Fichiers totaux | 25 |
| Fichiers Python | 13 |
| Fichiers config | 4 |
| Fichiers Docker | 3 |
| Fichiers doc | 6 |
| Lignes de code | ~1200 |
| Dépendances | 4 |
| Modules | 5 |
| Classes | 8 |

---

## 🎯 Prochaines étapes

1. **Lire** [QUICKSTART.md](QUICKSTART.md) - 5 minutes
2. **Installer** les dépendances - 3 minutes
3. **Configurer** config.yaml - 2 minutes
4. **Vérifier** `python check_install.py` - 1 minute
5. **Lancer** `python -m src.main` - 1 minute
6. **Explorer** le code source - 30 minutes

---

## 💬 Support

### Ressources
- [README.md](README.md) - Documentation
- [INSTALLATION.md](INSTALLATION.md) - Installation
- [QUICKSTART.md](QUICKSTART.md) - Démarrage
- [MANIFEST.md](MANIFEST.md) - Détails

### Diagnostic
- Exécuter `python check_install.py`
- Consulter `playcount_sync.log`
- Vérifier les permissions sur les fichiers

---

## 📄 Licence

MIT - Libre d'utilisation et de modification

---

*Dernière mise à jour : 24 janvier 2026*
*Pour naviguer ce projet, commencez par [README.md](README.md) ou [QUICKSTART.md](QUICKSTART.md)*
