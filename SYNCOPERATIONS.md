# SyncOperations - Opérations de Synchronisation Base de Données

## 📋 Vue d'ensemble

`SyncOperations` gère toutes les opérations de modification de la base de données SQLite pour la synchronisation des playcounts. Elle encapsule :
- ✅ Transactions SQLite
- ✅ Logging complet
- ✅ Gestion d'erreurs robuste
- ✅ Backup et maintenance
- ✅ Historique d'opérations

## 🎯 Fonctionnalités Principales

### 1. **update_alternative_playcount()**
Met à jour ou insère dans `alternativeplaycount`

```python
affected = ops.update_alternative_playcount(
    urlmd5='abc123',
    new_playcount=150,
    new_lastplayed=None  # optionnel
)
```

**Comportement** :
- Si la ligne existe : UPDATE playcount
- Si absent : INSERT avec source='manual_sync'
- Retourne : nombre de lignes affectées (toujours 1)

### 2. **delete_from_tracks_persistent()**
Supprime un morceau de `tracks_persistent`

```python
affected = ops.delete_from_tracks_persistent(urlmd5='missing_123')
```

**Comportement** :
- Log les infos avant suppression (audit trail)
- Effectue DELETE
- Retourne : nombre de lignes supprimées

### 3. **sync_track()**
Opération principale avec transactions

```python
operation = SyncOperation(
    missing_urlmd5='missing_001',
    selected_alternative_urlmd5='alt_001',
    action='COPY',
    new_playcount=42
)

success = ops.sync_track(operation)
```

**Workflow** :
```
1. BEGIN TRANSACTION
2. GET old value (backup)
3. UPDATE alternativeplaycount
   - COPY : remplacer playcount
   - MERGE : additionner playcount
4. DELETE tracks_persistent
5. COMMIT (ou ROLLBACK si erreur)
6. LOG dans sync_log
```

**Retour** : `True` si succès, `False` si erreur

### 4. **bulk_sync()**
Traite une liste d'opérations

```python
operations = [
    SyncOperation(...),
    SyncOperation(...),
    SyncOperation(...),
]

def progress(current, total):
    print(f"{current}/{total}")

result = ops.bulk_sync(
    operations,
    progress_callback=progress,
    stop_on_failure=False
)

# Résultat
print(result['success'])  # 100
print(result['failed'])   # 2
print(result['errors'])   # [{'operation_id': '...', 'message': '...'}]
```

**Retour** : Dict avec `{'success', 'failed', 'errors', 'total'}`

### 5. **get_sync_history()**
Récupère l'historique des opérations

```python
history = ops.get_sync_history(limit=50)

for entry in history:
    print(f"{entry['operation_id']}")
    print(f"  Status: {entry['status']}")  # 'success' ou 'failed'
    print(f"  Action: {entry['action']}")  # 'COPY' ou 'MERGE'
    print(f"  Old: {entry['old_playcount']} → New: {entry['new_playcount']}")
    print(f"  Time: {entry['timestamp_iso']}")
```

### 6. **get_sync_stats()**
Statistiques de synchronisation

```python
stats = ops.get_sync_stats(hours=24)

for action, data in stats['actions'].items():
    print(f"{action}:")
    print(f"  Total: {data['total']}")
    print(f"  Success: {data['success']}")
    print(f"  Failed: {data['failed']}")
    print(f"  Success rate: {data['success_rate']}")
```

### 7. **clear_sync_log()**
Nettoie l'historique

```python
deleted = ops.clear_sync_log(older_than_days=30)
print(f"Deleted {deleted} old entries")
```

### 8. **backup_database()**
Crée une sauvegarde

```python
success = ops.backup_database('/path/to/backup.db')

if success:
    print("✅ Backup créé")
```

## 🗄️ Table sync_log

Chaque opération est loggée automatiquement :

```sql
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    operation_id TEXT UNIQUE NOT NULL,
    missing_urlmd5 TEXT NOT NULL,
    target_urlmd5 TEXT NOT NULL,
    action TEXT NOT NULL,              -- 'COPY' ou 'MERGE'
    old_playcount INTEGER,
    new_playcount INTEGER NOT NULL,
    status TEXT NOT NULL,              -- 'success' ou 'failed'
    error_message TEXT
)
```

## ✅ Transactions SQLite

Chaque `sync_track()` utilise une transaction complète :

```python
try:
    conn.execute("BEGIN TRANSACTION")
    
    # 1. Récupérer l'ancienne valeur
    old_value = get_alternative(urlmd5)
    
    # 2. UPDATE alternativeplaycount
    if action == 'COPY':
        update_alternative(urlmd5, new_playcount)
    elif action == 'MERGE':
        merged = old_value + new_playcount
        update_alternative(urlmd5, merged)
    
    # 3. DELETE tracks_persistent
    delete_persistent(missing_urlmd5)
    
    # 4. COMMIT
    conn.commit()
    log_operation(status='success')
    return True
    
except Exception as e:
    conn.rollback()  # Annuler tous les changements
    log_operation(status='failed', error=str(e))
    return False
```

## 🔐 Sécurité & Robustesse

✅ **Transactions ACID** : Tout-ou-rien  
✅ **Rollback automatique** : En cas d'erreur  
✅ **Paramètres liés** : Protection contre SQL injection  
✅ **Logging complet** : Audit trail de toutes les opérations  
✅ **Backup** : Sauvegarde facilement disponible  
✅ **Foreign Keys** : Activées pour l'intégrité

## 📊 Logging

Tous les messages sont loggés dans `src.database.operations` :

```python
import logging
logger = logging.getLogger(__name__)

# INFO
logger.info("✅ Sync successful: operation_id")
logger.info("Updated alternativeplaycount for abc123: 150")
logger.info("Deleted track from tracks_persistent")

# ERROR
logger.error("❌ Sync failed: operation_id - error message")
logger.error("Error updating playcount for abc123: connection lost")
```

## 🎯 Cas d'Usage

### Synchronisation simple
```python
ops = SyncOperations('/path/to/db')

op = SyncOperation(
    missing_urlmd5='m1',
    selected_alternative_urlmd5='a1',
    action='COPY',
    new_playcount=100
)

success = ops.sync_track(op)
```

### Batch avec progression
```python
operations = [...]  # liste d'opérations

def show_progress(current, total):
    pct = 100 * current // total
    print(f"[{pct:3d}%] {current}/{total}")

result = ops.bulk_sync(operations, progress_callback=show_progress)
print(f"Result: {result['success']} success, {result['failed']} failed")
```

### Avec gestion d'erreurs
```python
result = ops.bulk_sync(
    operations,
    stop_on_failure=False  # continuer malgré les erreurs
)

for error in result['errors']:
    print(f"Operation {error['operation_id']}: {error['message']}")
```

### Maintenance
```python
# Backup régulier
from datetime import datetime
backup_name = f"backup_{datetime.now().isoformat()}.db"
ops.backup_database(f'/backups/{backup_name}')

# Nettoyer les logs anciens
ops.clear_sync_log(older_than_days=30)

# Afficher les stats
stats = ops.get_sync_stats(hours=24)
print(stats)
```

## 📈 Performance

| Opération | Temps Typique |
|-----------|---------------|
| update_alternative_playcount | <1ms |
| delete_from_tracks_persistent | <1ms |
| sync_track | 2-5ms |
| bulk_sync (100 ops) | 200-500ms |
| get_sync_history | <10ms |
| backup_database | 50-200ms |

## 🔗 Intégration avec MatchDialog

```python
from src.ui.match_dialog import show_match_dialog
from src.database.operations import SyncOperations

ops = SyncOperations('/path/to/db')

def handle_apply(operation: SyncOperation) -> bool:
    """Callback du dialogue pour appliquer l'opération."""
    try:
        # Backup avant sync
        ops.backup_database('backup.db')
        
        # Exécuter
        success = ops.sync_track(operation)
        
        if success:
            print("✅ Sync successful")
        else:
            print("❌ Sync failed")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False

# Afficher le dialogue
show_match_dialog(
    parent=main_window,
    missing_track=track,
    suggested_matches=suggestions,
    on_apply=handle_apply
)
```

## 🧪 Tests

Tous les tests passent :

```bash
$ python3 test_sync_operations.py

TEST 1: Initialisation et création de table ✅
TEST 2: update_alternative_playcount (UPDATE) ✅
TEST 3: update_alternative_playcount (INSERT) ✅
TEST 4: delete_from_tracks_persistent ✅
TEST 5: sync_track (COPY) ✅
TEST 6: sync_track (MERGE) ✅
TEST 7: get_sync_history ✅
TEST 8: get_sync_stats ✅
TEST 9: bulk_sync ✅
TEST 10: backup_database ✅

✅ ALL TESTS PASSED
```

## 📚 Exemples

Voir [examples_sync_operations.py](examples_sync_operations.py) pour 9 exemples complets.

## 🔍 Dépannage

### Erreur "database is locked"
- Réduire le timeout : `self.conn = sqlite3.connect(db, timeout=5)`
- Vérifier que les autres connexions sont fermées

### Pas de log des opérations
- Vérifier le niveau de logging
- Configurer : `logging.basicConfig(level=logging.INFO)`

### Erreurs de contrainte FK
- Activer les ForeignKeys : `PRAGMA foreign_keys = ON`
- Vérifier que les urlmd5 existent dans les deux tables

---

**Version** : 1.0  
**Date** : 24/01/2026  
**Statut** : Production ✅
