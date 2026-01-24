# 🔗 TrackMatcher - Algorithme de Matching Fuzzy

## Vue d'ensemble

**TrackMatcher** est un algorithme de matching sophistiqué qui trouve les correspondances probabilistes entre les morceaux manquants de `tracks_persistent` et ceux disponibles dans `alternativeplaycount`.

```python
from src.matching.fuzzy_matcher import TrackMatcher

matcher = TrackMatcher()
matches = matcher.find_best_matches(missing_track, alternatives)
```

---

## Caractéristiques principales

### 🎯 Scoring pondéré

| Critère | Poids | Impact |
|---------|-------|--------|
| **Titre** | 70% | Priorité maximale |
| **Artiste** | 20% | Important |
| **Album** | 10% | Contexte |
| **Playcount** | +5 bonus | Si similaire (±20%) |

### 🧹 Normalisation robuste

- **Lowercase** automatique
- **Suppression des accents** (é → e)
- **Suppression des articles** (The, La, Les...)
- **Trim des espaces multiples**

### ⚡ Optimisations

- **Cache des strings normalisées**
- **Parallélisation** pour > 1000 tracks
- **Rapidfuzz** pour calculs rapides

### 🎓 Classification de qualité

| Score | Qualité | Action |
|-------|---------|--------|
| ≥ 80% | **LIKELY** | ✅ Accepter automatiquement |
| 60-80% | **POSSIBLE** | ⚠️ Vérification manuelle |
| < 60% | **UNLIKELY** | ❌ Rejeter |

---

## API Complète

### TrackMatcher()

```python
matcher = TrackMatcher(
    use_cache=True,      # Cache les strings normalisées
    use_parallel=True    # Parallélise si > 1000 tracks
)
```

### find_best_matches()

**Trouve les meilleures correspondances pour un morceau.**

```python
matches = matcher.find_best_matches(
    missing_track,      # dict: {title, artist_name, album_title, playcount}
    alternative_tracks, # list[dict]: tous les alternatives
    top_n=5            # Nombre de résultats à retourner
)
```

**Retour :**

```python
[
    {
        'urlmd5': 'abc123...',
        'title': 'Song Title',
        'artist': 'Artist Name',
        'album': 'Album Name',
        'playcount': 42,
        'source': 'Spotify',  # Source du morceau
        'match_score': 85.5,  # Score 0-100
        'score_breakdown': {
            'title': 90,      # Score titre
            'artist': 85,     # Score artiste
            'album': 80       # Score album
        },
        'match_quality': 'LIKELY'  # LIKELY, POSSIBLE, UNLIKELY
    }
]
```

### normalize_string()

**Normalise une chaîne pour le matching.**

```python
normalized = TrackMatcher.normalize_string("The Beatles")
# "beatles"

normalized = TrackMatcher.normalize_string("L'Amour est Bleu")
# "amour est bleu"
```

**Opérations :**
1. Lowercase
2. Supprimer accents
3. Supprimer articles
4. Supprimer caractères spéciaux
5. Trim espaces

### is_likely_match()

**Vérifie si c'est une correspondance certaine (≥80%).**

```python
if TrackMatcher.is_likely_match(score):
    print("Match probable ✅")
```

### is_possible_match()

**Vérifie si c'est une correspondance possible (≥60%).**

```python
if TrackMatcher.is_possible_match(score):
    print("Match possible ⚠️")
```

### clear_cache()

**Vide le cache des strings normalisées.**

```python
matcher.clear_cache()
```

---

## Algorithme de Scoring

### Étape 1 : Normalisation

```python
missing_title = normalize("THE BEATLES")      # "beatles"
alternative_title = normalize("The Beatles")   # "beatles"
```

### Étape 2 : Calcul des scores partiels

```python
title_score = fuzz.ratio("beatles", "beatles") = 100.0
artist_score = fuzz.ratio(...) = 95.0
album_score = fuzz.ratio(...) = 90.0
```

### Étape 3 : Scoring pondéré

```python
weighted_score = (title_score * 0.70) + (artist_score * 0.20) + (album_score * 0.10)
                = (100 * 0.70) + (95 * 0.20) + (90 * 0.10)
                = 70 + 19 + 9
                = 98.0
```

### Étape 4 : Bonus playcount

```python
playcount_bonus = 5 if (95 <= alt_playcount <= 105) else 0
total_score = min(100, weighted_score + bonus)
            = min(100, 98 + 5)
            = 100.0
```

---

## Cas d'usage

### Cas 1 : Match parfait

```python
missing = {
    'title': 'Bohemian Rhapsody',
    'artist_name': 'Queen',
    'album_title': 'A Night at the Opera',
    'playcount': 100
}

alternative = {
    'title': 'Bohemian Rhapsody',
    'artist_name': 'Queen',
    'album_title': 'A Night at the Opera',
    'playcount': 100
}

score = matcher._score_match(missing, alternative)
# Score: 100.0% (LIKELY) ✅
```

### Cas 2 : Match partiel (titre similaire, artiste simplifié)

```python
missing = {
    'title': 'Yesterday',
    'artist_name': 'The Beatles',
    'album_title': 'Help!',
    'playcount': 200
}

alternative = {
    'title': 'Yesterday',
    'artist_name': 'Beatles',  # "The" supprimé
    'album_title': 'Help!',
    'playcount': 200
}

score = matcher._score_match(missing, alternative)
# Score: ~95-98% (LIKELY) ✅
```

### Cas 3 : Match douteux (titre similaire mais artiste différent)

```python
missing = {
    'title': 'Imagine',
    'artist_name': 'John Lennon',
    'album_title': 'Imagine',
    'playcount': 100
}

alternative = {
    'title': 'Imagine',
    'artist_name': 'Various Artists',
    'album_title': 'Tribute to Lennon',
    'playcount': 80
}

score = matcher._score_match(missing, alternative)
# Score: ~60-70% (POSSIBLE) ⚠️
```

### Cas 4 : Non-match (complètement différent)

```python
missing = {
    'title': 'Imagine',
    'artist_name': 'John Lennon',
    'album_title': 'Imagine',
    'playcount': 100
}

alternative = {
    'title': 'Yesterday',
    'artist_name': 'The Beatles',
    'album_title': 'Help!',
    'playcount': 150
}

score = matcher._score_match(missing, alternative)
# Score: ~5-10% (UNLIKELY) ❌
```

---

## Normalisation - Exemples

| Avant | Après | Notes |
|-------|-------|-------|
| "The Beatles" | "beatles" | Article supprimé |
| "L'Amour est bleu" | "amour est bleu" | Article + accent |
| "François & Marie" | "francois marie" | Accents + spéciaux |
| "SONG (RADIO EDIT)" | "song radio edit" | Majuscules + spéciaux |
| "  Multiple   Spaces  " | "multiple spaces" | Espaces normalisés |

---

## Performance

### Benchmarks

| Opération | Temps | Conditions |
|-----------|-------|-----------|
| normalize_string() | ~0.1ms | Simple string |
| find_best_matches() | ~5-10ms par track | Sequential, 100k alts |
| find_best_matches() | ~1-2ms par track | Parallel, 100k alts |

### Optimisations

#### Cache

```python
matcher = TrackMatcher(use_cache=True)

# Premier appel: normalisation + cache
result1 = matcher._get_normalized("The Beatles")  # ~0.1ms

# Deuxième appel: depuis le cache
result2 = matcher._get_normalized("The Beatles")  # <0.01ms (10x faster)
```

#### Parallélisation

```python
matcher = TrackMatcher(use_parallel=True)

# Si > 1000 tracks: utilise ThreadPoolExecutor (4 workers)
matches = matcher.find_best_matches(missing, 2000_alternatives)
```

---

## Intégration

### 1. Import

```python
from src.matching.fuzzy_matcher import TrackMatcher
```

### 2. Créer une instance

```python
matcher = TrackMatcher(use_cache=True)
```

### 3. Matcher un morceau

```python
from src.database import SyncDetector

# Récupérer les données
missing = SyncDetector.find_missing_in_alternative(manager)
alternatives = SyncDetector.get_all_alternative_tracks(manager)

# Matcher chaque morceau manquant
for track in missing:
    matches = matcher.find_best_matches(track, alternatives, top_n=5)
    
    # Utiliser les résultats
    for match in matches:
        if TrackMatcher.is_likely_match(match['match_score']):
            print(f"✅ Found: {match['title']} ({match['match_score']:.1f}%)")
```

### 4. Workflow complet

```python
# 1. Détecter les manquants
stats = SyncDetector.get_sync_stats(manager)
missing = SyncDetector.find_missing_in_alternative(manager)

# 2. Récupérer les alternatives
alternatives = SyncDetector.get_all_alternative_tracks(manager)

# 3. Matcher
matcher = TrackMatcher()
for track in missing:
    matches = matcher.find_best_matches(track, alternatives, top_n=3)
    
    # 4. Filtrer par qualité
    likely = [m for m in matches if TrackMatcher.is_likely_match(m['match_score'])]
    possible = [m for m in matches if TrackMatcher.is_possible_match(m['match_score'])]
    
    # 5. Afficher les résultats
    if likely:
        print(f"✅ {track['title']}: {likely[0]['title']} ({likely[0]['match_score']:.1f}%)")
    elif possible:
        print(f"⚠️ {track['title']}: {possible[0]['title']} ({possible[0]['match_score']:.1f}%)")
    else:
        print(f"❌ {track['title']}: no match")
```

---

## Paramètres de configuration

### TITLE_WEIGHT = 0.70

Poids du titre dans le score global. Ajuster si les titres sont souvent différents.

```python
TrackMatcher.TITLE_WEIGHT = 0.80  # Augmenter le poids du titre
```

### ARTIST_WEIGHT = 0.20

Poids de l'artiste. Important pour éviter les faux positifs.

### ALBUM_WEIGHT = 0.10

Poids de l'album. Moins important mais aide pour le contexte.

### PLAYCOUNT_BONUS = 5.0

Points bonus si playcounts similaires.

### PLAYCOUNT_TOLERANCE = 0.20

Tolérance pour le bonus (+/- 20%).

### LIKELY_MATCH_THRESHOLD = 80.0

Score minimum pour une correspondance "certaine".

### POSSIBLE_MATCH_THRESHOLD = 60.0

Score minimum pour une correspondance "possible".

---

## Dépannage

### Q: Scores trop bas?
**A:** Vérifier la normalisation :
```python
print(TrackMatcher.normalize_string(title))
```

### Q: Trop de faux positifs?
**A:** Augmenter les seuils :
```python
TrackMatcher.LIKELY_MATCH_THRESHOLD = 85  # 80 → 85
```

### Q: Performance lente?
**A:** Utiliser le cache et la parallélisation :
```python
matcher = TrackMatcher(use_cache=True, use_parallel=True)
```

### Q: Cache trop gros?
**A:** Vider régulièrement :
```python
matcher.clear_cache()
```

---

## Exemples complets

Voir [examples_track_matcher.py](examples_track_matcher.py) pour 8 exemples pratiques.

---

## Tests

```bash
python test_track_matcher.py
```

7 tests complets validant :
1. Normalisation
2. Classification de qualité
3. Calcul de score
4. Meilleures correspondances
5. Bonus playcount
6. Cache
7. Insensibilité à la casse

---

**Version:** 2.0.0  
**Dernière mise à jour:** 24 janvier 2026
