# 🚀 TrackMatcher - Quick Start

## Installation

```bash
# Déjà intégré dans le projet
# Aucune installation supplémentaire nécessaire
```

## Utilisation rapide (5 min)

### 1. Import

```python
from src.matching.fuzzy_matcher import TrackMatcher
```

### 2. Créer une instance

```python
matcher = TrackMatcher()
```

### 3. Matcher un morceau

```python
missing_track = {
    'title': 'Bohemian Rhapsody',
    'artist_name': 'Queen',
    'album_title': 'A Night at the Opera',
    'playcount': 100
}

alternatives = [
    {
        'urlmd5': 'abc123',
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 100,
        'source': 'DB'
    },
    # ... plus de morceaux
]

matches = matcher.find_best_matches(missing_track, alternatives, top_n=5)
```

### 4. Utiliser les résultats

```python
for match in matches:
    print(f"{match['title']} - {match['artist']}")
    print(f"  Score: {match['match_score']:.1f}% ({match['match_quality']})")
```

---

## Cas d'usage courants

### Cas 1 : Vérifier si c'est une correspondance certaine

```python
if TrackMatcher.is_likely_match(match['match_score']):
    print("✅ Match probable")
else:
    print("⚠️ Match douteux")
```

### Cas 2 : Filtrer par qualité

```python
matches = matcher.find_best_matches(missing, alternatives)

# Filtrer
likely = [m for m in matches if TrackMatcher.is_likely_match(m['match_score'])]
possible = [m for m in matches if TrackMatcher.is_possible_match(m['match_score'])]

print(f"Certaines: {len(likely)}, Possibles: {len(possible)}")
```

### Cas 3 : Voir le breakdown du score

```python
match = matches[0]
print(f"Titre: {match['score_breakdown']['title']:.1f}%")
print(f"Artiste: {match['score_breakdown']['artist']:.1f}%")
print(f"Album: {match['score_breakdown']['album']:.1f}%")
```

### Cas 4 : Normaliser une chaîne

```python
normalized = TrackMatcher.normalize_string("THE BEATLES")
# "beatles"
```

---

## Workflow complet

```python
from src.database import DatabaseManager, SyncDetector
from src.matching.fuzzy_matcher import TrackMatcher

# 1. Connexion
manager = DatabaseManager(auto_detect=True)

# 2. Détecter les manquants
missing = SyncDetector.find_missing_in_alternative(manager)
alternatives = SyncDetector.get_all_alternative_tracks(manager)

# 3. Matcher
matcher = TrackMatcher()
for track in missing[:10]:  # Top 10
    matches = matcher.find_best_matches(track, alternatives, top_n=3)
    
    if matches and TrackMatcher.is_likely_match(matches[0]['match_score']):
        print(f"✅ {track['title']} → {matches[0]['title']} ({matches[0]['match_score']:.1f}%)")
```

---

## Configuration rapide

### Avec cache (recommandé)

```python
matcher = TrackMatcher(use_cache=True, use_parallel=True)
```

### Sans cache (si mémoire limitée)

```python
matcher = TrackMatcher(use_cache=False)
```

### Vider le cache

```python
matcher.clear_cache()
```

---

## Seuils de qualité

| Score | Qualité | Action |
|-------|---------|--------|
| ≥ 80% | **LIKELY** | ✅ Accepter |
| 60-80% | **POSSIBLE** | ⚠️ Vérifier |
| < 60% | **UNLIKELY** | ❌ Rejeter |

---

## Performance

| Base | Temps |
|------|-------|
| 100 tracks | ~1-2s |
| 1,000 tracks | ~10-20s |
| 10,000 tracks | ~100-200s |

Utilisez `use_parallel=True` pour > 1000 tracks.

---

## Lancer les tests

```bash
python test_track_matcher.py
```

## Voir les exemples

```bash
python examples_track_matcher.py
```

## Documentation complète

→ [TRACKMATCHER.md](TRACKMATCHER.md)

---

**Prêt à commencer ?** Voir [TRACKMATCHER.md](TRACKMATCHER.md) pour plus de détails !
