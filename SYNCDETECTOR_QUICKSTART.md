# 🔍 SyncDetector - Guide de démarrage rapide

## Résumé

**SyncDetector** est une classe pour détecter les morceaux présents dans `tracks_persistent` mais **absent** de `alternativeplaycount`.

## Installation

```bash
# Déjà intégrée dans le projet
# Aucune installation supplémentaire nécessaire
```

## Importation

```python
from src.database import DatabaseManager, SyncDetector
```

## Utilisation rapide

### 1️⃣ Voir l'état global

```python
manager = DatabaseManager(auto_detect=True)

# Obtenir les stats
stats = SyncDetector.get_sync_stats(manager)

print(f"Ratio sync: {stats['sync_ratio']}%")
print(f"Manquants: {stats['missing_in_alternative']}")
```

**Retour :**
```python
{
    'total_persistent': 50000,           # Total tracks_persistent
    'total_alternative': 45000,          # Total alternativeplaycount  
    'missing_in_alternative': 5000,      # À synchroniser
    'orphaned': 200,                     # Sans métadonnées
    'sync_ratio': 90                     # Pourcentage synchronisé
}
```

### 2️⃣ Trouver les morceaux à synchroniser

```python
# Récupérer tous les morceaux manquants
missing = SyncDetector.find_missing_in_alternative(manager)

# Afficher top 10
for track in missing[:10]:
    print(f"{track['artist_name']} - {track['title']} ({track['playcount']})")
```

**Retour :** Liste de dicts avec métadonnées complètes

### 3️⃣ Compter les désynchronisés

```python
count = SyncDetector.count_missing(manager)
print(f"Morceaux à synchroniser: {count}")
```

### 4️⃣ Détails d'un morceau

```python
details = SyncDetector.get_track_details(
    manager,
    "abc123def456",  # urlmd5
    "tracks_persistent"
)

print(f"Titre: {details['title']}")
print(f"Plays: {details['playcount']}")
```

## Méthodes principales

| Méthode | But | Temps |
|---------|-----|-------|
| `find_missing_in_alternative()` | Lister les morceaux manquants | 200-500ms |
| `get_all_alternative_tracks()` | Récupérer tous les alternativeplaycount | 1-2s |
| `get_track_details()` | Détails d'un morceau | 10-20ms |
| `count_missing()` | Compter les manquants | 50ms |
| `get_sync_stats()` | Stats globales | 500ms-1s |

## Cas d'usage

### Cas 1 : Je veux synchroniser tout

```python
missing = SyncDetector.find_missing_in_alternative(manager)

# Synchroniser
for track in missing:
    if not track['url_orphaned']:  # Exclure les orphelins
        PlaycountQueries.sync_playcount(
            manager,
            "tracks_persistent",
            "alternativeplaycount",
            track['urlmd5'],
            track['playcount']
        )
```

### Cas 2 : Je veux les stats

```python
stats = SyncDetector.get_sync_stats(manager)

print(f"📊 {stats['sync_ratio']}% synchronisé")
print(f"❌ {stats['missing_in_alternative']} manquants")
print(f"👻 {stats['orphaned']} orphelins")
```

### Cas 3 : Je veux les top 10 manquants

```python
missing = SyncDetector.find_missing_in_alternative(manager)

for i, track in enumerate(missing[:10], 1):
    print(f"{i}. {track['artist_name']} - {track['title']} "
          f"({track['playcount']} plays)")
```

## Gestion des orphelins

Les orphelins sont les morceaux **sans métadonnées** (title=NULL dans tracks).

```python
missing = SyncDetector.find_missing_in_alternative(manager)

# Identifier
orphaned = [t for t in missing if t['url_orphaned']]
print(f"Orphelins: {len(orphaned)}")

# Exclure de la synchronisation
valid = [t for t in missing if not t['url_orphaned']]
```

## Fichiers liés

- 📖 [SYNCDETECTOR.md](SYNCDETECTOR.md) - Documentation complète
- 🧪 [test_sync_detector.py](test_sync_detector.py) - Tests (9 tests)
- 💡 [examples_sync_detector.py](examples_sync_detector.py) - 9 exemples
- 📝 [src/database/queries.py](src/database/queries.py) - Code source

## Lancer les tests

```bash
python test_sync_detector.py
```

## Lancer les exemples

```bash
python examples_sync_detector.py
```

## Intégration UI

```python
# Dans src/ui/main_window.py
from src.database import DatabaseManager, SyncDetector

class MainWindow:
    def __init__(self):
        self.manager = DatabaseManager(auto_detect=True)
    
    def update_sync_status(self):
        stats = SyncDetector.get_sync_stats(self.manager)
        self.status_label.setText(
            f"Sync: {stats['sync_ratio']}% "
            f"({stats['missing_in_alternative']} manquants)"
        )
```

## Structure des données

### find_missing_in_alternative()

```python
{
    'urlmd5': 'abc123...',         # Identifiant unique
    'playcount': 42,               # Nombre de lectures
    'lastplayed': 1705940404,      # Timestamp Unix
    'rating': 80,                  # Note (0-100)
    'title': 'Song Title',         # Titre du morceau
    'url': 'file:///path/...',     # URL du fichier
    'album_title': 'Album Name',   # Album
    'artist_name': 'Artist',       # Artiste
    'url_orphaned': False          # Flag orphelin
}
```

### get_sync_stats()

```python
{
    'total_persistent': 50000,     # Total persistent
    'total_alternative': 45000,    # Total alternative
    'missing_in_alternative': 5000,# À synchroniser
    'orphaned': 200,               # Sans metadata
    'sync_ratio': 90               # % synchronized
}
```

## Performance

- **Base de 100k morceaux**
- `count_missing()` → ~50ms
- `find_missing_in_alternative()` → ~200-500ms
- `get_sync_stats()` → ~500ms-1s

## Dépannage

### Q: Aucun résultat?
**A:** Vérifier que tracks_persistent et alternativeplaycount existent.
```python
stats = SyncDetector.get_sync_stats(manager)
if stats['total_persistent'] == 0:
    print("Base vide!")
```

### Q: Trop d'orphelins?
**A:** Vérifier l'état du stockage/permissions.
```python
stats = SyncDetector.get_sync_stats(manager)
print(f"Orphelins: {stats['orphaned']}/{stats['total_persistent']}")
```

### Q: Sync_ratio faible?
**A:** Plus de synchronisation à faire.
```python
if stats['sync_ratio'] < 80:
    print(f"À synchroniser: {stats['missing_in_alternative']}")
```

## 📚 Documentation complète

Voir [SYNCDETECTOR.md](SYNCDETECTOR.md) pour:
- Tous les paramètres des méthodes
- Gestion détaillée des erreurs
- Requêtes SQL utilisées
- Optimisations possibles
- Exemples avancés

---

**Prêt à commencer?** → [Lire SYNCDETECTOR.md](SYNCDETECTOR.md)

**Veux des exemples?** → `python examples_sync_detector.py`

**Lancer les tests?** → `python test_sync_detector.py`
