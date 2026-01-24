# 📝 Notes de version - Module Database

## Version 2.0.0 - DatabaseManager Complet

**Date** : 24 janvier 2026  
**Statut** : ✅ Production-Ready

### 🎯 Changements majeurs

#### Nouvelle classe : DatabaseManager
Remplace `DatabaseConnection` avec bien plus de fonctionnalités.

**Avant** :
```python
from src.database import DatabaseConnection

db = DatabaseConnection(db_path)
with db.get_connection() as conn:
    cursor = conn.cursor()
    # Opérations...
```

**Après** :
```python
from src.database import DatabaseManager

with DatabaseManager() as manager:
    manager.connect(readonly=True)
    stats = manager.get_table_stats()
    # Opérations sécurisées...
```

#### Nouvelles fonctionnalités

1. **Détection automatique du chemin**
   ```python
   manager = DatabaseManager()  # Détecte automatiquement
   ```

2. **Backups automatiques avec timestamps**
   ```python
   backup_path = manager.backup_database()
   # backups/persist.backup_20260124_153045.db
   ```

3. **Vérification du schéma Lyrion**
   ```python
   manager.verify_schema()  # Vérifie tables et colonnes
   ```

4. **Statistiques des tables**
   ```python
   stats = manager.get_table_stats()
   # {
   #   'tracks_persistent': {'rows': 5000, ...},
   #   'alternativeplaycount': {'rows': 2000, ...}
   # }
   ```

5. **Transactions sécurisées**
   ```python
   with manager.transaction() as cursor:
       cursor.execute("UPDATE ...")
       # Automatiquement commité ou rollback
   ```

6. **Mode lecture seule par défaut**
   ```python
   manager.connect(readonly=True)  # Sûr
   manager.connect(readonly=False)  # Modifications
   ```

### 📦 Fichiers modifiés

| Fichier | Changements |
|---------|------------|
| `src/database/connection.py` | Complètement rewritten |
| `src/database/queries.py` | Mis à jour pour utiliser DatabaseManager |
| `src/database/__init__.py` | Imports mis à jour |
| `src/main.py` | Imports mis à jour |

### ✨ Nouveaux fichiers

- `test_database.py` - Tests complets
- `EXAMPLES.md` - Exemples d'utilisation
- `DATABASE_API.md` - Documentation API
- `DATABASE.md` - Guide du module

### 🔄 Migration depuis v1.0

#### Étape 1 : Imports
```python
# Avant
from src.database import DatabaseConnection

# Après
from src.database import DatabaseManager
```

#### Étape 2 : Initialisation
```python
# Avant
db = DatabaseConnection(db_path="/path/to/persist.db")

# Après
db = DatabaseManager(db_path="/path/to/persist.db")
# ou avec auto-détection
db = DatabaseManager()
```

#### Étape 3 : Utilisation
```python
# Avant
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")

# Après - Option 1 (Recommandée)
with db as manager:
    manager.connect(readonly=True)
    with manager.cursor(commit=False) as cursor:
        cursor.execute("SELECT ...")

# Après - Option 2 (Context manager complet)
with DatabaseManager() as manager:
    manager.connect(readonly=True)
    # Connexion fermée automatiquement
```

### 🎁 Avantages de la migration

1. **Plus sûr** 
   - Transactions sécurisées
   - Mode lecture seule par défaut
   - Backups automatiques

2. **Plus robuste**
   - Détection automatique du chemin
   - Vérification du schéma
   - Gestion complète des erreurs

3. **Plus facile**
   - Context managers
   - API cohérente
   - Documentation complète

4. **Plus performant**
   - Statistiques de table
   - Connexion optimisée
   - Timeouts configurés

### 🔍 Détails techniques

#### Détection de chemin
Cherche dans cet ordre :
1. Linux: `/config/prefs/persist.db`
2. Linux: `/var/lib/squeezeboxserver/cache/persist.db`
3. macOS: `~/Library/Application Support/Squeezebox/prefs/persist.db`
4. Windows: `C:\ProgramData\Squeezebox\cache\persist.db`

#### Vérification du schéma
Vérifie la présence de :
- `tracks_persistent` avec colonnes (urlmd5, playcount, lastplayed, rating)
- `alternativeplaycount` avec colonnes (urlmd5, playcount, lastplayed, source)
- `tracks` avec colonnes (id, url, urlmd5, title, tracknum, album, timestamp)

#### Backups
- Format : `persist.backup_YYYYMMDD_HHMMSS.db`
- Localisation : `./backups/`
- Automatique avant modification

### 📋 Checklist de migration

- [ ] Mettre à jour les imports dans tous les fichiers
- [ ] Remplacer `DatabaseConnection` par `DatabaseManager`
- [ ] Tester la détection automatique du chemin
- [ ] Vérifier la création des backups
- [ ] Tester en mode lecture/écriture
- [ ] Tester la vérification du schéma
- [ ] Lancer `test_database.py` pour validation complète
- [ ] Consulter [DATABASE_API.md](DATABASE_API.md) pour les détails

### 🐛 Changements de comportement

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| Détection chemin | ❌ | ✅ |
| Backups automatiques | ❌ | ✅ |
| Vérification schéma | ❌ | ✅ |
| Transactions | ❌ | ✅ |
| Mode lecture seule | ❌ | ✅ |
| Context managers | ⚠️ Partielle | ✅ Complète |
| Gestion erreurs | Basique | Complète |

### ⚠️ Breaking Changes

1. **Imports** : `DatabaseConnection` → `DatabaseManager`
2. **Méthodes** : 
   - `get_connection()` → `connect()` + `get_connection()`
   - `get_cursor()` → `cursor()`
3. **Exception** : `FileNotFoundError` → `DatabaseConnectionError`

### 🔗 Intégrations

#### src/main.py
```python
# Avant
db = DatabaseConnection(config['database']['path'])

# Après
db = DatabaseManager(
    db_path=config['database'].get('path'),
    auto_detect=True
)
```

#### src/database/queries.py
Toutes les méthodes acceptent `DatabaseManager` au lieu de curseur.

```python
# Avant
PlaycountQueries.get_tracks_from_persistent(cursor)

# Après
PlaycountQueries.get_tracks_from_persistent(manager)
```

### 📚 Documentation

Voir aussi :
- [DATABASE.md](DATABASE.md) - Guide du module
- [DATABASE_API.md](DATABASE_API.md) - Référence API complète
- [EXAMPLES.md](EXAMPLES.md) - Exemples d'utilisation
- [test_database.py](test_database.py) - Tests et exemples

### ✅ Validation

Tous les tests passent :
```
✅ Test 1 : Détection de la BD
✅ Test 2 : Connexion à la BD
✅ Test 3 : Validation du schéma
✅ Test 4 : Statistiques des tables
✅ Test 5 : Création de backup
✅ Test 6 : Connexion en lecture seule
✅ Test 7 : Utilisation en context manager
✅ Test 8 : Utilisation du cursor
✅ Test 9 : PlaycountQueries
```

### 🚀 Déploiement

1. **Mettre à jour le code** depuis cette version
2. **Exécuter les tests** : `python test_database.py`
3. **Vérifier les logs** pour erreurs de schéma
4. **Tester en read-only d'abord** : `manager.connect(readonly=True)`
5. **Créer un backup** : `manager.backup_database()` avant modifications

### 💬 Support

Pour les problèmes :
1. Consulter [DATABASE_API.md](DATABASE_API.md)
2. Voir [EXAMPLES.md](EXAMPLES.md)
3. Lancer `test_database.py`
4. Vérifier les logs pour détails

---

**Version** : 2.0.0  
**Date** : 24 janvier 2026  
**Status** : ✅ Production-Ready
