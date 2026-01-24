# 📍 Guide de navigation - Module Database

## 🎯 Où commencer?

### Je suis débutant
1. Lire : [DATABASE.md](DATABASE.md) (10 min)
2. Voir : [EXAMPLES.md](EXAMPLES.md) (15 min)
3. Tester : `python test_database.py` (5 min)

### Je suis développeur
1. Lire : [DATABASE_API.md](DATABASE_API.md) (20 min)
2. Utiliser : [EXAMPLES.md](EXAMPLES.md) (15 min)
3. Intégrer dans mon code

### Je veux debuguer
1. Lancer : `python test_database.py` - voir si erreurs
2. Consulter : [DATABASE_API.md#troubleshooting](DATABASE_API.md)
3. Vérifier les logs : `playcount_sync.log`

---

## 📚 Documents par besoin

### Je veux...

#### Comprendre le module
- [DATABASE.md](DATABASE.md) - Vue d'ensemble
- [MODULE_DATABASE_SUMMARY.md](MODULE_DATABASE_SUMMARY.md) - Résumé détaillé
- [DEVELOPMENT_COMPLETE.md](DEVELOPMENT_COMPLETE.md) - Résumé final

#### Utiliser l'API
- [DATABASE_API.md](DATABASE_API.md) - Référence complète
- [EXAMPLES.md](EXAMPLES.md) - Exemples pratiques
- [test_database.py](test_database.py) - Tests comme exemples

#### Migrer depuis v1.0
- [CHANGELOG_DATABASE.md](CHANGELOG_DATABASE.md) - Notes de version
- [DATABASE_API.md#migration](DATABASE_API.md) - Guide migration

#### Intégrer dans mon app
- [EXAMPLES.md](EXAMPLES.md) - Cas d'usage pratiques
- [src/main.py](src/main.py) - Exemple d'utilisation
- [test_database.py](test_database.py) - Patterns à utiliser

#### Déployer en production
- [DATABASE_API.md#securite](DATABASE_API.md) - Sécurité
- [EXAMPLES.md](EXAMPLES.md#synchronisation-complète) - Script complet
- [DATABASE.md#sécurité](DATABASE.md#sécurité) - Bonnes pratiques

---

## 🔍 Fichiers du module

### Code source

**connection.py** (353 lignes)
```python
DatabaseManager          # Classe principale
├── Détection chemin    # Auto-find persist.db
├── Connexion           # Read/write mode
├── Backup              # Sauvegarde + timestamp
├── Schéma              # Validation
├── Stats               # Statistiques
└── Transactions        # Sécurisées
```

**queries.py** (324 lignes)
```python
PlaycountQueries         # Requêtes SQL
├── Lectures            # get_tracks_*
├── Écritures          # update_*
├── Statistiques       # get_*_stats
└── Synchronisation    # sync_playcount
```

**__init__.py** (6 lignes)
```python
Imports
├── DatabaseManager
├── DatabaseConnectionError
└── PlaycountQueries
```

### Documentation

| Document | Longueur | Contenu |
|----------|----------|---------|
| [DATABASE.md](DATABASE.md) | 250 lignes | Guide d'utilisation |
| [DATABASE_API.md](DATABASE_API.md) | 500 lignes | Référence API |
| [EXAMPLES.md](EXAMPLES.md) | 280 lignes | Exemples pratiques |
| [CHANGELOG_DATABASE.md](CHANGELOG_DATABASE.md) | 300 lignes | Notes de version |
| [MODULE_DATABASE_SUMMARY.md](MODULE_DATABASE_SUMMARY.md) | 200+ lignes | Résumé développement |
| [DEVELOPMENT_COMPLETE.md](DEVELOPMENT_COMPLETE.md) | 200+ lignes | Résumé final |

### Tests

**test_database.py** (350 lignes)
```python
Test 1-9  # Validation complète
├── Détection
├── Connexion
├── Validation schéma
├── Stats
├── Backups
├── Read-only
├── Context managers
├── Curseurs
└── Queries
```

---

## 🚀 Cas d'usage rapides

### Cas 1 : Lire les stats
```
Où ? → DATABASE.md ou EXAMPLES.md
Code → src/database/queries.py (get_urlmd5_stats)
Test → test_database.py (Test 4)
```

### Cas 2 : Créer un backup
```
Où ? → DATABASE_API.md ou EXAMPLES.md
Code → src/database/connection.py (backup_database)
Test → test_database.py (Test 5)
```

### Cas 3 : Synchroniser playcounts
```
Où ? → EXAMPLES.md (Exemple 9)
Code → src/database/queries.py (sync_playcount)
Test → test_database.py
```

### Cas 4 : Requête personnalisée
```
Où ? → DATABASE_API.md ou EXAMPLES.md
Code → src/database/connection.py (cursor)
Test → test_database.py (Test 8)
```

---

## 🎓 Apprentissage progressif

### Niveau 1 : Débutant (30 min)
1. Lire : [DATABASE.md](DATABASE.md)
2. Voir : Premiers exemples de [EXAMPLES.md](EXAMPLES.md)
3. Tester : `python test_database.py`

### Niveau 2 : Intermédiaire (1-2h)
1. Lire : [DATABASE_API.md](DATABASE_API.md)
2. Étudier : [EXAMPLES.md](EXAMPLES.md) en détail
3. Comprendre : [src/database/connection.py](src/database/connection.py)
4. Comprendre : [src/database/queries.py](src/database/queries.py)

### Niveau 3 : Avancé (2-4h)
1. Lire : [CHANGELOG_DATABASE.md](CHANGELOG_DATABASE.md)
2. Étudier : [MODULE_DATABASE_SUMMARY.md](MODULE_DATABASE_SUMMARY.md)
3. Intégrer : Dans votre application
4. Optimiser : Pour votre cas d'usage

### Niveau 4 : Expert (4h+)
1. Contribuer : Améliorations
2. Étendre : Nouvelles fonctionnalités
3. Tester : Cas limites
4. Déployer : En production

---

## 🔗 Relations entre fichiers

```
DATABASE.md (Guide)
    ↓
    ├→ EXAMPLES.md (Exemples)
    ├→ DATABASE_API.md (API détaillée)
    └→ test_database.py (Tests)
         ↓
         ├→ src/database/connection.py
         └→ src/database/queries.py
             ↓
             └→ src/main.py (Utilisation)

CHANGELOG_DATABASE.md (Migration)
    ↓
    └→ Comprendre changements v1.0 → v2.0

MODULE_DATABASE_SUMMARY.md (Résumé)
DEVELOPMENT_COMPLETE.md (Final)
```

---

## ❓ FAQ rapide

### Q: Par où commencer?
**A:** Lire [DATABASE.md](DATABASE.md) puis [EXAMPLES.md](EXAMPLES.md)

### Q: Comment utiliser l'API?
**A:** Consulter [DATABASE_API.md](DATABASE_API.md)

### Q: Où sont les exemples?
**A:** Dans [EXAMPLES.md](EXAMPLES.md) et [test_database.py](test_database.py)

### Q: Comment migrer depuis v1.0?
**A:** Voir [CHANGELOG_DATABASE.md](CHANGELOG_DATABASE.md)

### Q: Comment intégrer dans mon app?
**A:** Voir [EXAMPLES.md](EXAMPLES.md) ou [src/main.py](src/main.py)

### Q: Quels sont les chemins par défaut?
**A:** [DATABASE_API.md#chemins-par-os](DATABASE_API.md)

### Q: Comment faire un backup?
**A:** [EXAMPLES.md](EXAMPLES.md) ou [DATABASE_API.md](DATABASE_API.md)

### Q: Comment traiter les erreurs?
**A:** [DATABASE_API.md#gestion-derreurs](DATABASE_API.md)

---

## 🛠️ Outils disponibles

### Documentation
- 📖 [DATABASE.md](DATABASE.md) - Guide (10-15 min)
- 📚 [DATABASE_API.md](DATABASE_API.md) - Référence (20-30 min)
- 💡 [EXAMPLES.md](EXAMPLES.md) - Exemples (15-20 min)

### Tests et validation
- 🧪 [test_database.py](test_database.py) - Tests
- ✅ 9 tests validant toutes les fonctionnalités

### Code source
- 🔧 [connection.py](src/database/connection.py) - Gestion connexion
- 📝 [queries.py](src/database/queries.py) - Requêtes SQL
- 📦 [__init__.py](src/database/__init__.py) - Imports

### Migration
- 🔄 [CHANGELOG_DATABASE.md](CHANGELOG_DATABASE.md) - Notes v1.0→v2.0
- 📊 [MODULE_DATABASE_SUMMARY.md](MODULE_DATABASE_SUMMARY.md) - Résumé

---

## ⏱️ Temps de lecture estimé

| Document | Temps |
|----------|-------|
| DATABASE.md | 10-15 min |
| EXAMPLES.md | 15-20 min |
| DATABASE_API.md | 20-30 min |
| CHANGELOG_DATABASE.md | 10-15 min |
| Codebase complet | 1-2h |
| Tests (test_database.py) | 5 min |

---

## 🎯 Objectifs par document

### DATABASE.md
- Comprendre le module
- Utilisation rapide
- Cas d'usage principaux

### DATABASE_API.md
- Référence complète
- Tous les paramètres
- Tous les cas d'erreur

### EXAMPLES.md
- Exemples pratiques
- Patterns à suivre
- Code prêt à copier

### test_database.py
- Valider installation
- Voir code en action
- Tester intégration

### CHANGELOG_DATABASE.md
- Comprendre v2.0
- Migrer depuis v1.0
- Breaking changes

---

## 🔐 Sécurité

Tous les documents ont une section sur la sécurité :
- [DATABASE.md#sécurité](DATABASE.md#sécurité)
- [DATABASE_API.md#sécurité](DATABASE_API.md#sécurité)
- [EXAMPLES.md](EXAMPLES.md) - Exemples sécurisés

---

## 🚀 Prochaines étapes

### 1. Lecture (30 min)
```
1. DATABASE.md (10 min)
2. EXAMPLES.md premiers exemples (10 min)
3. Parcourir DATABASE_API.md (10 min)
```

### 2. Tests (5 min)
```bash
python test_database.py
```

### 3. Intégration (1-2h)
```python
# Importer et utiliser
from src.database import DatabaseManager
manager = DatabaseManager()
```

### 4. Utilisation (Continu)
- Consulter documentation au besoin
- Suivre les patterns des exemples
- Adapter à votre cas d'usage

---

## 📞 Support

### Je suis bloqué
1. Consulter [DATABASE_API.md#troubleshooting](DATABASE_API.md)
2. Lancer `python test_database.py`
3. Vérifier logs : `playcount_sync.log`

### Je veux en savoir plus
1. Lire [DEVELOPMENT_COMPLETE.md](DEVELOPMENT_COMPLETE.md)
2. Étudier [MODULE_DATABASE_SUMMARY.md](MODULE_DATABASE_SUMMARY.md)
3. Examiner le code source

### Je veux contribuer
1. Comprendre l'architecture (module_database_summary.md)
2. Suivre les patterns dans le code
3. Ajouter tests pour nouvelles features

---

**Navigation Guide v2.0**  
*Dernière mise à jour : 24 janvier 2026*

👉 **Commencez par** : [DATABASE.md](DATABASE.md)
