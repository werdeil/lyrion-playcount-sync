# 📦 Modèles de données

**Fichier:** `src/models/track.py`  
**Status:** ✅ Production-Ready  
**Tests:** ✅ Tous réussis

---

## 📋 Overview

Trois classes dataclass pour représenter les données du système de synchronisation des playcounts :

| Classe | Rôle | Attributs |
|--------|------|-----------|
| **Track** | Représente un morceau | 9 attributs |
| **MatchSuggestion** | Suggestion de correspondance | 3 attributs + 4 méthodes |
| **SyncOperation** | Opération de sync à effectuer | 6 attributs + 2 méthodes |

---

## 🎵 Class: Track

Représente un morceau de musique avec ses métadonnées.

### Attributs

```python
@dataclass
class Track:
    urlmd5: str                    # MD5 unique de l'URL
    title: Optional[str]           # Titre du morceau
    artist: Optional[str]          # Artiste
    album: Optional[str]           # Album
    url: Optional[str]             # URL complète
    playcount: int                 # Nombre de lectures
    lastplayed: Optional[int] = None       # Timestamp UNIX (optionnel)
    rating: Optional[int] = None           # Note 0-5 (optionnel)
    source: str = 'tracks_persistent'      # Source du morceau
```

### Sources autorisées

```python
source in ('tracks_persistent', 'alternativeplaycount')
```

### Méthodes

#### `display_name() -> str`

Retourne un nom lisible pour l'affichage.

**Stratégie de fallback :**
1. `"Artist - Title"` (préféré)
2. `"Title"` seul
3. `"Artist"` seul
4. `URL`
5. `"Track (urlmd5[:8])..."` (fallback final)

**Exemple :**
```python
track = Track("md5", "Imagine", "John Lennon", "Imagine", None, 42)
print(track.display_name())  # "John Lennon - Imagine"

track2 = Track("md5", None, None, None, "https://ex.com", 10)
print(track2.display_name())  # "https://ex.com"
```

#### `lastplayed_formatted() -> str`

Convertit le timestamp UNIX en format date-heure lisible.

**Format :** `"DD/MM/YYYY HH:MM"` (fuseau horaire local)

**Exemple :**
```python
track = Track("md5", "Song", "Artist", None, None, 10, lastplayed=1705795200)
print(track.lastplayed_formatted())  # "21/01/2024 01:00"

track2 = Track("md5", "Song", "Artist", None, None, 5)
print(track2.lastplayed_formatted())  # "N/A"
```

#### `to_dict() -> dict`

Convertit le Track en dictionnaire pour sérialisation.

**Exemple :**
```python
track = Track("md5", "Song", "Artist", "Album", None, 42, rating=5)
d = track.to_dict()
# {'urlmd5': 'md5', 'title': 'Song', 'artist': 'Artist', ...}
```

#### `to_json() -> str`

Convertit le Track en JSON string formaté.

**Exemple :**
```python
track = Track("md5", "Song", "Artist", "Album", None, 42)
json_str = track.to_json()
# {"urlmd5": "md5", "title": "Song", ...}
```

### Validations

✅ `urlmd5` : Non vide  
✅ `playcount` : ≥ 0  
✅ `rating` : 0-5 si défini  
✅ `source` : Doit être 'tracks_persistent' ou 'alternativeplaycount'

---

## 🎯 Class: MatchSuggestion

Représente une suggestion de correspondance entre un morceau manquant et des alternatives.

### Attributs

```python
@dataclass
class MatchSuggestion:
    missing_track: Track                      # Morceau manquant
    suggested_matches: list[tuple[Track, float]] = []  # (track, score)
    auto_match_possible: bool = False         # score > 90
```

### Méthodes

#### `get_best_match() -> tuple[Track, float] | None`

Retourne le meilleur match si score > 60.

**Retour :**
- `(Track, score)` si existe et score > 60
- `None` sinon

**Exemple :**
```python
suggestion = MatchSuggestion(missing_track)
suggestion.add_match(alt1, 95.0)
suggestion.add_match(alt2, 55.0)

best = suggestion.get_best_match()
# (alt1, 95.0) - alt2 rejeté (55 < 60)
```

#### `add_match(track: Track, score: float) -> None`

Ajoute une correspondance et maintient le tri par score.

**Comportement :**
- Valide le score (0-100)
- Ajoute à la liste
- Trie par score décroissant
- Recalcule `auto_match_possible`

**Exemple :**
```python
suggestion = MatchSuggestion(missing_track)
suggestion.add_match(alt1, 75.0)
suggestion.add_match(alt2, 85.0)
# suggested_matches = [(alt2, 85.0), (alt1, 75.0)]
```

#### `get_top_n(n: int) -> list[tuple[Track, float]]`

Retourne les top N correspondances.

**Exemple :**
```python
top_3 = suggestion.get_top_n(3)
# Retourne les 3 premiers matches
```

### Propriété: auto_match_possible

Booléen calculé automatiquement :
- `True` si meilleur score > 90 (suggestion automatique possible)
- `False` sinon (vérification manuelle requise)

**Cas d'utilisation :**
```python
if suggestion.auto_match_possible:
    # Appliquer automatiquement
    apply_match(suggestion)
else:
    # Demander confirmation utilisateur
    show_dialog(suggestion)
```

---

## 🔄 Class: SyncOperation

Représente une opération de synchronisation à effectuer sur la base de données.

### Attributs

```python
@dataclass
class SyncOperation:
    missing_urlmd5: str                 # MD5 du morceau manquant
    selected_alternative_urlmd5: str    # MD5 du morceau sélectionné
    action: str                         # 'COPY', 'MERGE', 'DELETE'
    new_playcount: Optional[int] = None # Nouveau playcount
    operation_id: str = "<UUID>"        # ID unique
    timestamp: datetime = "<NOW UTC>"   # Timestamp
```

### Actions supportées

| Action | Description | SQL |
|--------|-------------|-----|
| **COPY** | Copier les données de alt vers persistent | UPDATE + DELETE |
| **MERGE** | Fusionner les playcounts | UPDATE + DELETE |
| **DELETE** | Supprimer le morceau manquant | DELETE + DELETE |

### Méthodes

#### `to_sql() -> tuple[str, str]`

Génère les requêtes SQL pour effectuer l'opération.

**Retourne :** `(UPDATE query, DELETE query)`

**Action COPY :**
```python
op = SyncOperation("missing_1", "alt_1", "COPY", new_playcount=150)
update, delete = op.to_sql()
# update: UPDATE tracks_persistent SET playcount = 150 WHERE urlmd5 = 'missing_1';
# delete: DELETE FROM alternativeplaycount WHERE urlmd5 = 'alt_1';
```

**Action MERGE :**
```python
op = SyncOperation("missing_1", "alt_1", "MERGE", new_playcount=250)
# Même SQL que COPY (le calcul du playcount est fait ailleurs)
```

**Action DELETE :**
```python
op = SyncOperation("missing_1", "alt_1", "DELETE")
update, delete = op.to_sql()
# update: DELETE FROM tracks_persistent WHERE urlmd5 = 'missing_1';
# delete: DELETE FROM alternativeplaycount WHERE urlmd5 = 'alt_1';
```

#### `to_dict() -> dict`

Convertit l'opération en dictionnaire.

#### `to_json() -> str`

Convertit l'opération en JSON string formaté.

### Validations

✅ `missing_urlmd5` : Non vide  
✅ `selected_alternative_urlmd5` : Non vide  
✅ `action` : 'COPY', 'MERGE', ou 'DELETE'  
✅ `new_playcount` : ≥ 0 si défini  
✅ `new_playcount` : Requis pour COPY et MERGE

---

## 📊 Exemples d'utilisation

### Scénario 1: Afficher un morceau

```python
from src.models import Track

track = Track(
    urlmd5="abc123def456",
    title="Imagine",
    artist="John Lennon",
    album="Imagine",
    url="https://music.example.com/imagine",
    playcount=42,
    lastplayed=1705795200,
    rating=5,
    source="tracks_persistent"
)

print(track.display_name())      # "John Lennon - Imagine"
print(track.playcount)           # 42
print(track.lastplayed_formatted())  # "21/01/2024 01:00"
```

### Scénario 2: Traiter une suggestion de match

```python
from src.models import Track, MatchSuggestion

missing = Track("md5_missing", "Imagine", "John Lennon", None, None, 0)
suggestion = MatchSuggestion(missing)

# Ajouter des candidats
alt1 = Track("md5_alt1", "Imagine", "John Lennon", "Imagine", None, 150)
suggestion.add_match(alt1, 95.0)

alt2 = Track("md5_alt2", "Imagine", "Various", "Best Of", None, 50)
suggestion.add_match(alt2, 65.0)

# Vérifier la possibilité d'auto-match
if suggestion.auto_match_possible:
    print("✅ Auto-match recommandé")
else:
    print("⚠️ Vérification manuelle requise")

# Obtenir le meilleur match
best = suggestion.get_best_match()
if best:
    track, score = best
    print(f"Meilleur match: {track.display_name()} ({score:.1f}%)")
```

### Scénario 3: Créer et exécuter une opération de sync

```python
from src.models import SyncOperation

# Créer l'opération
op = SyncOperation(
    missing_urlmd5="missing_1",
    selected_alternative_urlmd5="alt_1",
    action="COPY",
    new_playcount=150
)

print(f"Opération: {op}")
print(f"ID: {op.operation_id}")

# Générer les SQL
update_sql, delete_sql = op.to_sql()

print("SQL à exécuter:")
print(f"  1. {update_sql}")
print(f"  2. {delete_sql}")

# Exporter en JSON pour logging
json_log = op.to_json()
print(f"Log JSON: {json_log}")
```

---

## 🔧 Intégration avec d'autres modules

### Avec TrackMatcher

```python
from src.models import Track, MatchSuggestion
from src.matching.fuzzy_matcher import TrackMatcher

# Récupérer un morceau manquant
missing_track = Track(...)

# Matcher avec alternatives
matcher = TrackMatcher()
matches = matcher.find_best_matches(missing_track, alternatives, top_n=5)

# Créer une MatchSuggestion
suggestion = MatchSuggestion(missing_track)
for alt_track, score in matches:
    suggestion.add_match(alt_track, score)

# Vérifier possibilité auto-match
if suggestion.auto_match_possible:
    apply_automatically(suggestion)
else:
    show_to_user(suggestion)
```

### Avec SyncDetector

```python
from src.models import Track, SyncOperation
from src.database.queries import SyncDetector

# Trouver les morceaux manquants
detector = SyncDetector(db_manager)
missing_tracks = detector.find_missing_in_alternative()

# Pour chaque match accepté, créer une opération
for match in accepted_matches:
    op = SyncOperation(
        missing_urlmd5=match.missing_track.urlmd5,
        selected_alternative_urlmd5=match.selected.urlmd5,
        action="COPY",
        new_playcount=match.selected.playcount
    )
    
    # Exécuter
    update_sql, delete_sql = op.to_sql()
    db_manager.execute(update_sql)
    db_manager.execute(delete_sql)
```

---

## 🧪 Tests

Exécuter les tests :

```bash
python3 test_models.py
```

**Tests inclus :**
✅ Track creation et display_name  
✅ MatchSuggestion scoring et best_match  
✅ SyncOperation SQL generation  
✅ Validations (playcount, rating, source, action)  
✅ JSON export

---

## 📈 Statistiques

| Métrique | Valeur |
|----------|--------|
| Lignes de code | 450+ |
| Classes | 3 |
| Méthodes | 11 |
| Attributs | 18 |
| Type hints | ✅ 100% |
| Documentation | ✅ Complète |
| Validation | ✅ Stricte |

---

## 🚀 Prochaines étapes

1. Intégrer avec UI pour afficher Tracks
2. Créer dialogs pour MatchSuggestions
3. Implémenter persistence de SyncOperations
4. Logger les opérations exécutées

---

**Version:** 1.0.0  
**Status:** 🟢 Production-Ready  
**Dernière mise à jour:** 24 janvier 2026
