# 📚 Module Database - Documentation

## 🎯 Objectif

Le module `src/database/` fournit une couche d'abstraction complète pour gérer la connexion à la base de données Lyrion et effectuer des opérations de synchronisation de playcounts.

## 📦 Contenu

### `connection.py`
Classe **DatabaseManager** pour gérer la connexion SQLite.

**Fonctionnalités** :
- ✅ Détection automatique du chemin persist.db
- ✅ Mode lecture/écriture ou lecture seule
- ✅ Backups automatiques avec timestamps
- ✅ Vérification du schéma Lyrion
- ✅ Statistiques des tables
- ✅ Transactions sécurisées
- ✅ Context managers pour sécurité

**Classes** :
- `DatabaseManager` - Gestionnaire principal
- `DatabaseConnectionError` - Exception personnalisée

### `queries.py`
Classe **PlaycountQueries** pour les requêtes de playcounts.

**Fonctionnalités** :
- ✅ Lire les tracks de tracks_persistent
- ✅ Lire les tracks de alternativeplaycount
- ✅ Mettre à jour les playcounts
- ✅ Mettre à jour les dates de lecture
- ✅ Récupérer les statistiques
- ✅ Synchroniser entre tables

## 🚀 Utilisation rapide

### Connexion simple

```python
from src.database import DatabaseManager

# Détection automatique
manager = DatabaseManager()
manager.connect(readonly=True)

# Vérifier le schéma
manager.verify_schema()

# Récupérer les stats
stats = manager.get_table_stats()
print(stats)

manager.close()
```

### Avec context manager (recommandé)

```python
with DatabaseManager() as manager:
    manager.connect(readonly=True)
    
    # Vérifier le schéma
    manager.verify_schema()
    
    # Créer un backup
    backup = manager.backup_database()
    
    # Récupérer les stats
    stats = manager.get_table_stats()
    for table, data in stats.items():
        print(f"{table}: {data['rows']} lignes")
    # Connexion fermée automatiquement
```

### Avec transactions

```python
with DatabaseManager() as manager:
    manager.connect(readonly=False)
    
    # Créer un backup d'abord
    backup = manager.backup_database()
    print(f"Backup: {backup}")
    
    # Utiliser une transaction sécurisée
    with manager.transaction() as cursor:
        cursor.execute("""
            UPDATE tracks_persistent
            SET playcount = ?
            WHERE urlmd5 = ?
        """, (100, 'hash123'))
        
        print(f"Mises à jour: {cursor.rowcount}")
        # Automatiquement commité
```

### Utiliser PlaycountQueries

```python
from src.database import DatabaseManager, PlaycountQueries

with DatabaseManager() as manager:
    manager.connect(readonly=True)
    
    # Récupérer les stats
    stats = PlaycountQueries.get_urlmd5_stats(manager)
    
    print(f"tracks_persistent: {stats['tracks_persistent']['total']} lignes")
    print(f"alternativeplaycount: {stats['alternativeplaycount']['total']} lignes")
    
    # Lire les tracks
    # tracks = PlaycountQueries.get_tracks_from_persistent(manager)
```

## 📊 Tables Lyrion

### tracks_persistent
**Playcounts principaux**
- `urlmd5` : Hash MD5 (clé primaire)
- `playcount` : Nombre de lectures
- `lastplayed` : Timestamp dernière lecture
- `rating` : Note (0-100)

### alternativeplaycount
**Playcounts externes (Last.fm, etc.)**
- `urlmd5` : Hash MD5 (clé primaire)
- `playcount` : Nombre de lectures
- `lastplayed` : Timestamp
- `source` : Source (lastfm, listenbrainz, etc.)

### tracks
**Métadonnées des pistes**
- `id` : ID interne
- `url` : Chemin fichier
- `urlmd5` : Hash (FK)
- `title` : Titre
- `artist` : Artiste
- `album` : Album
- `tracknum` : Numéro piste
- `timestamp` : Date d'ajout

## 🔍 Chemins automatiques

Le manager cherche automatiquement dans cet ordre :

**Linux/Docker** :
1. `/config/prefs/persist.db`
2. `/var/lib/squeezeboxserver/cache/persist.db`
3. `/var/lib/squeezeboxserver/prefs/persist.db`

**macOS** :
1. `~/Library/Application Support/Squeezebox/prefs/persist.db`
2. `~/Library/Application Support/Logitech/Squeezebox/prefs/persist.db`

**Windows** :
1. `C:\ProgramData\Squeezebox\cache\persist.db`
2. `C:\ProgramData\Squeezebox\prefs\persist.db`

## 🛡️ Sécurité

- **Backups automatiques** : Avant chaque modification
- **Mode lecture seule** : Par défaut recommandé
- **Transactions** : Rollback automatique en cas d'erreur
- **Vérification** : Schéma validé avant opérations
- **Context managers** : Ressources toujours fermées

## 📝 Méthodes principales

### DatabaseManager

| Méthode | Description | Paramètres | Retour |
|---------|-------------|-----------|--------|
| `__init__()` | Initialiser | db_path, auto_detect | - |
| `connect()` | Établir connexion | readonly | - |
| `backup_database()` | Créer backup | - | str (chemin) |
| `verify_schema()` | Vérifier schéma | - | bool |
| `get_table_stats()` | Stats tables | - | Dict |
| `cursor()` | Context manager curseur | commit | Cursor |
| `transaction()` | Context manager transaction | - | Cursor |
| `close()` | Fermer connexion | - | - |

### PlaycountQueries

| Méthode | Description |
|---------|-------------|
| `get_tracks_from_persistent()` | Lire tracks_persistent |
| `get_tracks_from_alternative()` | Lire alternativeplaycount |
| `get_track_by_urlmd5()` | Lire un track par hash |
| `update_playcount()` | Mettre à jour playcount |
| `update_lastplayed()` | Mettre à jour lastplayed |
| `get_urlmd5_stats()` | Récupérer statistiques |
| `sync_playcount()` | Synchroniser entre tables |

## 🧪 Tests

```bash
# Lancer les tests
python test_database.py

# Résultats attendus :
# ✅ Tous les tests devraient afficher ✓ ou ✅
```

## 📖 Documentation détaillée

Pour la documentation API complète : [DATABASE_API.md](DATABASE_API.md)

Pour les exemples : [EXAMPLES.md](EXAMPLES.md)

## 🐛 Troubleshooting

### "Base de données non trouvée"
```python
# Solution 1 : Spécifier le chemin
manager = DatabaseManager(db_path="/path/to/persist.db")

# Solution 2 : Vérifier le chemin
from src.database import DatabaseManager
print(DatabaseManager.DEFAULT_PATHS)
```

### "Base de données verrouillée"
```python
# Solution : Arrêter Lyrion avant modifications
# Utiliser mode lecture seule sinon
manager.connect(readonly=True)
```

### "Table manquante"
```python
# Vérifier que c'est un fichier Lyrion valide
# et que le chemin est correct
try:
    manager.verify_schema()
except DatabaseConnectionError as e:
    print(f"Schéma invalide: {e}")
```

## 🔗 Intégration

Le module est utilisé par :
- `src/main.py` - Initialisation de l'application
- `src/matching/fuzzy_matcher.py` - Matching des tracks
- `src/ui/main_window.py` - Interface utilisateur

## 📚 Ressources

- [SQLite3 Docs](https://docs.python.org/3/library/sqlite3.html)
- [Lyrion/LMS](https://www.lyrion.org/)
- [Last.fm API](https://www.last.fm/api)
