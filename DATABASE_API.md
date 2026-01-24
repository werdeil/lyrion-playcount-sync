# 📚 Documentation - DatabaseManager

Documentation complète de la classe `DatabaseManager` pour gérer la connexion à Lyrion Playcount.

## 🎯 Vue d'ensemble

`DatabaseManager` est une classe complète pour gérer la connexion SQLite à la base de données Lyrion avec :

- ✅ Détection automatique du chemin
- ✅ Mode lecture/écriture ou lecture seule
- ✅ Backups automatiques avec timestamps
- ✅ Vérification du schéma Lyrion
- ✅ Statistiques des tables
- ✅ Transactions sécurisées
- ✅ Context managers
- ✅ Gestion complète des erreurs

## 📋 Tables supportées

### tracks_persistent
Table principale de Lyrion pour les playcounts.

**Colonnes** :
- `urlmd5` (PRIMARY KEY) : Hash MD5 de l'URL du fichier
- `playcount` : Nombre de lectures
- `lastplayed` : Timestamp dernière lecture
- `rating` : Note (0-100)

### alternativeplaycount
Table pour les playcounts provenant de sources externes (Last.fm, etc.)

**Colonnes** :
- `urlmd5` (PRIMARY KEY) : Hash MD5 de l'URL
- `playcount` : Nombre de lectures
- `lastplayed` : Timestamp dernière lecture
- `source` : Origine des données (ex: 'lastfm', 'listenbrainz')

### tracks
Table avec les métadonnées des pistes.

**Colonnes** :
- `id` : ID interne
- `url` : Chemin du fichier
- `urlmd5` : Hash (FK vers tracks_persistent)
- `title` : Titre du morceau
- `tracknum` : Numéro de piste
- `album` : ID de l'album
- `timestamp` : Date d'ajout

## 🚀 Utilisation

### Installation simple

```python
from src.database import DatabaseManager

# Créer un manager avec détection automatique
manager = DatabaseManager()

# Ou avec chemin personnalisé
manager = DatabaseManager(db_path="/path/to/persist.db")
```

### Connexion

```python
# Connexion en lecture/écriture
manager.connect(readonly=False)

# Connexion en lecture seule (recommandée pour les opérations simples)
manager.connect(readonly=True)

# Fermer la connexion
manager.close()
```

### Utiliser en context manager (recommandé)

```python
with DatabaseManager() as manager:
    manager.connect(readonly=True)
    # Opérations...
    # Connexion fermée automatiquement
```

## 📖 Méthodes

### `__init__(db_path=None, auto_detect=True)`

Initialise le manager.

**Paramètres** :
- `db_path` (str, optionnel) : Chemin vers persist.db
- `auto_detect` (bool) : Détecter automatiquement le chemin

**Raises** :
- `DatabaseConnectionError` : Si le fichier n'est pas trouvé

**Exemple** :
```python
manager = DatabaseManager()  # Auto-détection
manager = DatabaseManager(db_path="/path/to/persist.db")  # Chemin spécifié
```

---

### `connect(readonly=False)`

Établit la connexion à la base de données.

**Paramètres** :
- `readonly` (bool) : Mode lecture seule

**Raises** :
- `DatabaseConnectionError` : En cas d'erreur de connexion

**Exemple** :
```python
manager.connect(readonly=True)  # Lecture seule
manager.connect(readonly=False)  # Lecture/écriture
```

---

### `backup_database() -> str`

Crée une sauvegarde de la BD avec timestamp.

**Returns** :
- str : Chemin du fichier de sauvegarde

**Raises** :
- `DatabaseConnectionError` : Si la sauvegarde échoue

**Exemple** :
```python
backup_path = manager.backup_database()
print(f"Backup : {backup_path}")
# Output: Backup : backups/persist.backup_20260124_153045.db
```

---

### `verify_schema() -> bool`

Vérifie que le schéma est valide pour Lyrion.

**Returns** :
- bool : True si valide

**Raises** :
- `DatabaseConnectionError` : Si le schéma est invalide

**Exemple** :
```python
manager.connect()
if manager.verify_schema():
    print("Schéma valide!")
```

---

### `get_table_stats() -> Dict[str, Dict[str, any]]`

Récupère les statistiques des tables Lyrion.

**Returns** :
- Dict : Statistiques par table

**Structure de retour** :
```python
{
    'tracks_persistent': {
        'rows': 5000,
        'db_size_bytes': 2097152,
        'with_plays': 3500  # Tracks avec playcount > 0
    },
    'alternativeplaycount': {
        'rows': 2000,
        'db_size_bytes': 1048576,
        'sources': ['lastfm', 'listenbrainz']
    },
    'tracks': {
        'rows': 5000,
        'db_size_bytes': 3145728
    }
}
```

**Raises** :
- `DatabaseConnectionError` : Si l'opération échoue

**Exemple** :
```python
stats = manager.get_table_stats()
for table_name, table_stats in stats.items():
    print(f"{table_name}: {table_stats['rows']} lignes")
```

---

### `get_connection() -> sqlite3.Connection`

Récupère la connexion SQLite.

**Returns** :
- sqlite3.Connection : Connexion active

**Raises** :
- `DatabaseConnectionError` : Si pas de connexion

**Exemple** :
```python
conn = manager.get_connection()
cursor = conn.cursor()
```

---

### `cursor(commit=True)` (Context Manager)

Context manager pour obtenir un curseur.

**Paramètres** :
- `commit` (bool) : Commiter à la sortie

**Yields** :
- sqlite3.Cursor : Curseur SQLite

**Raises** :
- `DatabaseConnectionError` : Si erreur

**Exemple** :
```python
with manager.cursor(commit=False) as cursor:
    cursor.execute("SELECT COUNT(*) FROM tracks_persistent")
    count = cursor.fetchone()[0]
    print(f"Total : {count}")
```

---

### `transaction()` (Context Manager)

Context manager pour une transaction complète.

**Yields** :
- sqlite3.Cursor : Curseur de transaction

**Raises** :
- `DatabaseConnectionError` : Si erreur ou mode lecture seule

**Exemple** :
```python
with manager.transaction() as cursor:
    cursor.execute("UPDATE tracks_persistent SET playcount = ? WHERE urlmd5 = ?", (100, 'hash'))
    # Automatiquement commité
```

---

### `close()`

Ferme la connexion à la BD.

**Exemple** :
```python
manager.close()
```

---

## 🛡️ Gestion d'erreurs

### DatabaseConnectionError

Exception personnalisée pour les erreurs de BD.

**Cas d'usage** :
```python
try:
    manager = DatabaseManager()
except DatabaseConnectionError as e:
    print(f"Erreur : {e}")
```

### Erreurs courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| "Base de données non trouvée" | Chemin invalide | Vérifier le chemin avec `DatabaseManager.DEFAULT_PATHS` |
| "Base de données verrouillée" | Lyrion en cours d'exécution | Arrêter Lyrion avant modifications |
| "Table manquante" | Schéma invalide | Vérifier que c'est un vrai fichier Lyrion |
| "Pas de connexion établie" | `connect()` non appelé | Appeler `connect()` avant toute opération |

## 📍 Chemins par OS

### Linux/Docker
```
/config/prefs/persist.db
/var/lib/squeezeboxserver/cache/persist.db
/var/lib/squeezeboxserver/prefs/persist.db
```

### macOS
```
~/Library/Application Support/Squeezebox/prefs/persist.db
~/Library/Application Support/Logitech/Squeezebox/prefs/persist.db
```

### Windows
```
C:\ProgramData\Squeezebox\cache\persist.db
C:\ProgramData\Squeezebox\prefs\persist.db
```

## 📝 Exemples

### Exemple 1 : Lire les stats

```python
from src.database import DatabaseManager

with DatabaseManager() as manager:
    manager.connect(readonly=True)
    stats = manager.get_table_stats()
    
    for table_name, table_stats in stats.items():
        print(f"{table_name}: {table_stats['rows']} lignes")
```

### Exemple 2 : Backup avant modification

```python
with DatabaseManager() as manager:
    # Créer une sauvegarde
    backup = manager.backup_database()
    print(f"Sauvegarde créée : {backup}")
    
    # Connexion en lecture/écriture
    manager.connect(readonly=False)
    
    # Vérifier le schéma
    manager.verify_schema()
    
    # Modifications sécurisées
    with manager.transaction() as cursor:
        cursor.execute("UPDATE ...")
```

### Exemple 3 : Requête personnalisée

```python
with DatabaseManager() as manager:
    manager.connect(readonly=True)
    
    with manager.cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT artist, title, playcount
            FROM tracks_persistent
            JOIN tracks ON tracks_persistent.urlmd5 = tracks.urlmd5
            ORDER BY playcount DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"{row[0]} - {row[1]}: {row[2]} plays")
```

## 🔧 Configuration

Les chemins par défaut sont consultés dans cet ordre :

```python
DEFAULT_PATHS = [
    Path('/config/prefs/persist.db'),  # Docker
    Path('/var/lib/squeezeboxserver/cache/persist.db'),  # Linux
    Path('/var/lib/squeezeboxserver/prefs/persist.db'),  # Linux
    Path('~/Library/.../Squeezebox/prefs/persist.db'),  # macOS
    # ...
]
```

Pour ajouter un chemin personnalisé :

```python
manager = DatabaseManager(db_path="/custom/path/persist.db", auto_detect=False)
```

## 🚨 Sécurité

- ✅ Backups automatiques avant modification
- ✅ Mode lecture seule par défaut
- ✅ Transactions sécurisées
- ✅ Rollback automatique en cas d'erreur
- ✅ Vérification du schéma
- ✅ Gestion des fichiers verrouillés

## 📊 Performance

- Connexion pool : Non (simple pour cette utilisation)
- Timeout : 10 secondes
- Row factory : `sqlite3.Row` pour accès par nom

## 🔗 Integration avec PlaycountQueries

La classe `PlaycountQueries` utilise `DatabaseManager` :

```python
from src.database import PlaycountQueries

# Lire les stats
stats = PlaycountQueries.get_urlmd5_stats(manager)

# Synchroniser des playcounts
PlaycountQueries.sync_playcount(
    manager,
    from_table="alternativeplaycount",
    to_table="tracks_persistent",
    urlmd5="abc123",
    playcount=100
)
```

## 🧪 Tests

Voir `test_database.py` pour les tests complets.

```bash
python test_database.py
```

## 📚 Ressources

- [SQLite3 Python Docs](https://docs.python.org/3/library/sqlite3.html)
- [Lyrion Documentation](https://www.lyrion.org/)
- [Context Managers Python](https://docs.python.org/3/library/stdtypes.html#context-manager-types)
