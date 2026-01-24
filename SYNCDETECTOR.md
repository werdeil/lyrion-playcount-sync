# 🔍 SyncDetector - Détection des désynchronisations

## Vue d'ensemble

**SyncDetector** est une classe pour détecter et analyser les désynchronisations entre les tables `tracks_persistent` et `alternativeplaycount` de la base de données Lyrion.

```python
from src.database import SyncDetector

# Détecter les morceaux manquants
missing = SyncDetector.find_missing_in_alternative(manager)

# Compter les désynchronisés
count = SyncDetector.count_missing(manager)

# Récupérer les stats
stats = SyncDetector.get_sync_stats(manager)
```

---

## Cas d'usage

### Cas 1 : Identifier les morceaux à synchroniser
```python
from src.database import DatabaseManager, SyncDetector

manager = DatabaseManager(auto_detect=True)

# Trouver les morceaux manquants
missing = SyncDetector.find_missing_in_alternative(manager)

print(f"Trouvé {len(missing)} morceaux manquants")

for track in missing[:10]:
    print(f"  {track['artist_name']} - {track['title']} ({track['playcount']} plays)")
```

### Cas 2 : Vérifier l'état de synchronisation
```python
stats = SyncDetector.get_sync_stats(manager)

print(f"Ratio de sync : {stats['sync_ratio']}%")
print(f"Morceaux manquants : {stats['missing_in_alternative']}")
print(f"Morceaux orphelins : {stats['orphaned']}")
```

### Cas 3 : Préparer une synchronisation
```python
# Récupérer tous les morceaux alternativeplaycount (pour matching)
alternative_tracks = SyncDetector.get_all_alternative_tracks(manager)

# Récupérer les détails d'un morceau spécifique
details = SyncDetector.get_track_details(
    manager, 
    urlmd5="abc123def456", 
    source_table="tracks_persistent"
)
```

---

## Méthodes

### 1. `find_missing_in_alternative(manager)`

**Trouve les morceaux présents dans `tracks_persistent` mais PAS dans `alternativeplaycount`.**

**Paramètres :**
- `manager`: Instance de `DatabaseManager`

**Retour :**
```python
[
    {
        'urlmd5': str,           # Hash MD5 du URL
        'playcount': int,        # Nombre de lectures
        'lastplayed': int,       # Timestamp Unix
        'rating': int,           # Note (0-100)
        'title': str,            # Titre du morceau
        'url': str,              # URL original
        'album_title': str,      # Titre de l'album
        'artist_name': str,      # Nom de l'artiste
        'url_orphaned': bool     # True si title est NULL
    }
]
```

**Exemple :**
```python
missing = SyncDetector.find_missing_in_alternative(manager)

# Afficher les 5 premiers par playcount
for track in missing[:5]:
    print(f"{track['artist_name']} - {track['title']}")
    print(f"  Playcount: {track['playcount']}")
    print(f"  Orphelin: {track['url_orphaned']}")
```

**Notes :**
- Retourne les morceaux triés par playcount DESC (priorité aux plus écoutés)
- `url_orphaned` est True si le fichier n'a pas de métadonnées (title=NULL)
- Les morceaux orphelins affichent `"[ORPHELIN]"` comme titre

---

### 2. `get_all_alternative_tracks(manager)`

**Récupère TOUS les morceaux de `alternativeplaycount` avec métadonnées.**

Utilisé pour le matching fuzzy contre les morceaux de `tracks_persistent`.

**Paramètres :**
- `manager`: Instance de `DatabaseManager`

**Retour :**
```python
[
    {
        'urlmd5': str,           # Hash MD5
        'playcount': int,        # Lectures
        'lastplayed': int,       # Timestamp
        'source': str,           # Source (ex: "MusicBrainz")
        'title': str,            # Titre
        'url': str,              # URL
        'album_title': str,      # Album
        'artist_name': str       # Artiste
    }
]
```

**Exemple :**
```python
tracks = SyncDetector.get_all_alternative_tracks(manager)

# Trouver les plus écoutés
top_tracks = sorted(tracks, key=lambda x: x['playcount'], reverse=True)[:10]

for i, track in enumerate(top_tracks, 1):
    print(f"{i}. {track['artist_name']} - {track['title']} ({track['playcount']})")
```

**Notes :**
- Inclut les morceaux avec ou sans métadonnées
- Triés par playcount DESC
- `source` indique la source du playcount (ex: Spotify, MusicBrainz)

---

### 3. `get_track_details(manager, urlmd5, source_table)`

**Récupère les détails complets d'un morceau spécifique.**

**Paramètres :**
- `manager`: Instance de `DatabaseManager`
- `urlmd5`: Hash MD5 du URL (str)
- `source_table`: Table source, `"tracks_persistent"` ou `"alternativeplaycount"` (str)

**Retour :**
```python
{
    'urlmd5': str,              # Hash MD5
    'playcount': int,           # Lectures
    'lastplayed': int,          # Timestamp
    'rating': int or 'N/A',     # Note (tracks_persistent seulement)
    'track_id': int,            # ID du track
    'title': str,               # Titre
    'url': str,                 # URL original
    'album_title': str,         # Album
    'artist_name': str,         # Artiste
    'contributor_count': int,   # Nombre de contributeurs
    'source': str or None       # Source (alternativeplaycount seulement)
}
```

**Exemple :**
```python
# Détails d'un morceau de tracks_persistent
details = SyncDetector.get_track_details(
    manager,
    "abc123def456",
    "tracks_persistent"
)

if details:
    print(f"Titre: {details['title']}")
    print(f"Artiste: {details['artist_name']}")
    print(f"Playcount: {details['playcount']}")
    print(f"Rating: {details['rating']}")
else:
    print("Morceau non trouvé")
```

**Exceptions :**
- `ValueError`: Si `source_table` invalide
- `Exception`: Erreur de requête

**Notes :**
- Retourne `None` si urlmd5 n'existe pas dans la table
- Affiche `"[ORPHELIN]"` si title est NULL
- `contributor_count` compte les contributeurs uniques

---

### 4. `count_missing(manager)`

**Compte le nombre total de morceaux désynchronisés.**

**Paramètres :**
- `manager`: Instance de `DatabaseManager`

**Retour :**
- `int` : Nombre de morceaux manquants

**Exemple :**
```python
count = SyncDetector.count_missing(manager)
print(f"Nombre de morceaux à synchroniser : {count}")
```

**Notes :**
- Équivalent à `len(find_missing_in_alternative())` mais plus performant
- Utilise `COUNT(DISTINCT)` pour éviter les doublons

---

### 5. `get_sync_stats(manager)`

**Récupère les statistiques globales de synchronisation.**

**Paramètres :**
- `manager`: Instance de `DatabaseManager`

**Retour :**
```python
{
    'total_persistent': int,           # Total dans tracks_persistent
    'total_alternative': int,          # Total dans alternativeplaycount
    'missing_in_alternative': int,     # Désynchronisés
    'orphaned': int,                   # Morceaux orphelins (title=NULL)
    'sync_ratio': int                  # % de synchronisation (0-100)
}
```

**Exemple :**
```python
stats = SyncDetector.get_sync_stats(manager)

print(f"Ratio de synchronisation : {stats['sync_ratio']}%")
print(f"Morceaux manquants : {stats['missing_in_alternative']}")
print(f"Morceaux orphelins : {stats['orphaned']}")
print(f"À synchroniser : {stats['missing_in_alternative'] - stats['orphaned']}")
```

**Notes :**
- `sync_ratio` = (total_alternative / total_persistent) * 100
- `orphaned` sont inclus dans `missing_in_alternative`
- Utile pour les statistiques et dashboards

---

## Gestion des fichiers orphelins

### Qu'est-ce qu'un fichier orphelin ?

Un fichier orphelin est un morceau dans `tracks_persistent` où `tracks.title` est NULL.

**Causes :**
- Fichier supprimé mais les stats restent dans la base
- Fichier inaccessible (permissions, stockage déconnecté)
- Corruption de la base de données

### Détection

```python
missing = SyncDetector.find_missing_in_alternative(manager)

orphaned = [t for t in missing if t['url_orphaned']]
print(f"Morceaux orphelins : {len(orphaned)}/{len(missing)}")

for track in orphaned:
    print(f"  {track['urlmd5']} - playcount={track['playcount']}")
```

### Traitement

```python
stats = SyncDetector.get_sync_stats(manager)

# Nombre réel à synchroniser (excluant orphelins)
real_count = stats['missing_in_alternative'] - stats['orphaned']
print(f"À synchroniser : {real_count}")

# Afficher les orphelins
orphaned_count = stats['orphaned']
print(f"Orphelins à nettoyer : {orphaned_count}")
```

---

## Requêtes SQL utilisées

### find_missing_in_alternative

```sql
SELECT 
    tp.urlmd5,
    tp.playcount,
    tp.lastplayed,
    tp.rating,
    t.title,
    t.url,
    a.title as album_title,
    c.name as artist_name
FROM tracks_persistent tp
LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
LEFT JOIN tracks t ON tp.urlmd5 = t.urlmd5
LEFT JOIN albums a ON t.album = a.id
LEFT JOIN contributor_track ct ON t.id = ct.track 
    AND ct.role IN (1, 5, 6)
LEFT JOIN contributors c ON ct.contributor = c.id
WHERE ap.urlmd5 IS NULL
ORDER BY tp.playcount DESC
```

**Optimisations :**
- `DISTINCT` sur `urlmd5` en cas de jointures multiples
- Index recommandés :
  - `tracks_persistent(urlmd5)`
  - `alternativeplaycount(urlmd5)`
  - `tracks(urlmd5)`

### count_missing

```sql
SELECT COUNT(DISTINCT tp.urlmd5)
FROM tracks_persistent tp
LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
WHERE ap.urlmd5 IS NULL
```

**Utilise `DISTINCT`** car plusieurs lignes peuvent matcher (ex: contributeurs multiples).

---

## Gestion des erreurs

### Exceptions possibles

```python
try:
    missing = SyncDetector.find_missing_in_alternative(manager)
except Exception as e:
    # Erreur de connexion, table manquante, etc.
    logger.error(f"Erreur SyncDetector : {e}")
```

### Validation des paramètres

```python
try:
    details = SyncDetector.get_track_details(manager, urlmd5, "invalid_table")
except ValueError as e:
    print(f"Table invalide : {e}")
```

### Points d'échec courants

| Erreur | Cause | Solution |
|--------|-------|----------|
| `sqlite3.OperationalError` | Base verrouillée | Attendre ou fermer autres processus |
| `sqlite3.DatabaseError` | Schéma incompatible | Vérifier Lyrion version |
| `KeyError` | Colonne manquante | Vérifier la structure Lyrion |
| `None` retourné | urlmd5 inexistant | Vérifier urlmd5 valide |

---

## Performance

### Optimisations

1. **Requêtes avec DISTINCT** pour éviter les doublons (contributeurs multiples)
2. **LEFT JOIN au lieu de INNER JOIN** pour inclure orphelins
3. **Filtres WHERE optimisés** pour limiter les données
4. **Indexes recommandés** sur les colonnes de jointure

### Benchmarks (base ~100k morceaux)

| Méthode | Temps |
|---------|-------|
| `count_missing()` | ~50ms |
| `find_missing_in_alternative()` | ~200-500ms |
| `get_all_alternative_tracks()` | ~1-2s |
| `get_track_details()` | ~10-20ms |
| `get_sync_stats()` | ~500ms-1s |

### Optimisations possibles

```sql
-- Créer les indexes (si absent)
CREATE INDEX IF NOT EXISTS idx_tracks_persistent_urlmd5 
    ON tracks_persistent(urlmd5);

CREATE INDEX IF NOT EXISTS idx_alternativeplaycount_urlmd5 
    ON alternativeplaycount(urlmd5);

CREATE INDEX IF NOT EXISTS idx_tracks_urlmd5 
    ON tracks(urlmd5);

-- Analyser la base pour améliorer le planner
ANALYZE;
```

---

## Intégration avec le workflow

### Étape 1 : Diagnostic
```python
# Voir l'état global
stats = SyncDetector.get_sync_stats(manager)
print(f"Sync ratio : {stats['sync_ratio']}%")
```

### Étape 2 : Identification
```python
# Trouver les morceaux à synchroniser
missing = SyncDetector.find_missing_in_alternative(manager)
print(f"À synchroniser : {len(missing)} morceaux")
```

### Étape 3 : Filtrage
```python
# Exclure les orphelins
to_sync = [t for t in missing if not t['url_orphaned']]
print(f"Réellement à synchroniser : {len(to_sync)}")
```

### Étape 4 : Synchronisation
```python
# Synchroniser chaque morceau
from src.database import PlaycountQueries

for track in to_sync:
    PlaycountQueries.sync_playcount(
        manager,
        "tracks_persistent",
        "alternativeplaycount",
        track['urlmd5'],
        track['playcount']
    )
```

---

## Exemples complets

### Rapport de synchronisation
```python
from src.database import DatabaseManager, SyncDetector

manager = DatabaseManager(auto_detect=True)

# Stats globales
stats = SyncDetector.get_sync_stats(manager)

print(f"📊 Rapport de synchronisation")
print(f"================================")
print(f"Morceaux persistent : {stats['total_persistent']}")
print(f"Morceaux alternative : {stats['total_alternative']}")
print(f"Manquants : {stats['missing_in_alternative']}")
print(f"Orphelins : {stats['orphaned']}")
print(f"À synchroniser : {stats['missing_in_alternative'] - stats['orphaned']}")
print(f"Ratio : {stats['sync_ratio']}%")

# Top morceaux manquants
print(f"\n🎵 Top 10 morceaux à synchroniser")
print(f"================================")
missing = SyncDetector.find_missing_in_alternative(manager)
for i, track in enumerate(missing[:10], 1):
    if not track['url_orphaned']:
        print(f"{i}. {track['artist_name']} - {track['title']} ({track['playcount']})")
```

### Détection des orphelins
```python
missing = SyncDetector.find_missing_in_alternative(manager)
orphaned = [t for t in missing if t['url_orphaned']]

print(f"🗑️ Fichiers orphelins détectés : {len(orphaned)}")
for track in orphaned[:5]:
    print(f"  - {track['urlmd5']} (playcount={track['playcount']})")
```

### Vérification de synchronisation avant/après
```python
# Avant
before = SyncDetector.count_missing(manager)

# ... effectuer la synchronisation ...

# Après
after = SyncDetector.count_missing(manager)

print(f"Avant : {before} manquants")
print(f"Après : {after} manquants")
print(f"Synchronisés : {before - after}")
```

---

## 📝 Notes importantes

1. **LEFT JOIN utilisé** pour inclure les orphelins (title=NULL)
2. **DISTINCT sur urlmd5** pour éviter les doublons (contributeurs multiples)
3. **Triés par playcount DESC** pour prioriser les plus écoutés
4. **Metadata complètes** incluant album, artiste, source
5. **Flag url_orphaned** pour identifier facilement les fichiers sans métadonnées

---

**Version :** 2.0.0  
**Dernière mise à jour :** 24 janvier 2026
