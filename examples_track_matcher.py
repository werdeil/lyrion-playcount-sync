"""Exemples pratiques d'utilisation de TrackMatcher."""

from src.matching.fuzzy_matcher import TrackMatcher
from src.utils import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# EXEMPLE 1 : Matching simple
# ============================================================================

def exemple_matching_simple():
    """Matcher un morceau contre une liste de candidats."""
    print("\n" + "="*70)
    print("EXEMPLE 1 : Matching simple")
    print("="*70)
    
    matcher = TrackMatcher()
    
    # Morceau à matcher
    missing = {
        'title': 'Stairway to Heaven',
        'artist_name': 'Led Zeppelin',
        'album_title': 'Led Zeppelin IV',
        'playcount': 150
    }
    
    # Candidats
    alternatives = [
        {
            'urlmd5': 'abc123',
            'title': 'Stairway to Heaven',
            'artist_name': 'Led Zeppelin',
            'album_title': 'Led Zeppelin IV',
            'playcount': 150,
            'source': 'DB'
        },
        {
            'urlmd5': 'def456',
            'title': 'Whole Lotta Love',
            'artist_name': 'Led Zeppelin',
            'album_title': 'Led Zeppelin II',
            'playcount': 120,
            'source': 'Spotify'
        },
    ]
    
    # Matcher
    matches = matcher.find_best_matches(missing, alternatives, top_n=2)
    
    print(f"\n🎵 Morceau recherché:")
    print(f"  {missing['title']} - {missing['artist_name']}")
    print(f"\n🔍 Correspondances trouvées:")
    for i, match in enumerate(matches, 1):
        print(f"\n  {i}. {match['title']}")
        print(f"     Artiste: {match['artist']}")
        print(f"     Score: {match['match_score']:.1f}% [{match['match_quality']}]")


# ============================================================================
# EXEMPLE 2 : Normalisation pour debugging
# ============================================================================

def exemple_normalisation():
    """Voir comment les strings sont normalisées."""
    print("\n" + "="*70)
    print("EXEMPLE 2 : Normalisation des strings")
    print("="*70)
    
    exemples = [
        "The Beatles",
        "L'Amour est bleu",
        "Café au Lait",
        "  Multiple   Spaces  ",
        "Song (Radio Edit) [Remaster]",
        "François & Marie",
    ]
    
    print("\n📝 Avant → Après:")
    for s in exemples:
        normalized = TrackMatcher.normalize_string(s)
        print(f"  '{s}' → '{normalized}'")


# ============================================================================
# EXEMPLE 3 : Classification de qualité
# ============================================================================

def exemple_classification_qualite():
    """Voir les classifications de qualité."""
    print("\n" + "="*70)
    print("EXEMPLE 3 : Classification de qualité de matching")
    print("="*70)
    
    scores = [95, 85, 75, 65, 55, 35, 15]
    
    print("\n📊 Scores et classifications:")
    for score in scores:
        quality = TrackMatcher._get_match_quality(score)
        is_likely = "✓" if TrackMatcher.is_likely_match(score) else "✗"
        is_possible = "✓" if TrackMatcher.is_possible_match(score) else "✗"
        
        print(f"  Score {score:3} → {quality:8} (likely:{is_likely} possible:{is_possible})")


# ============================================================================
# EXEMPLE 4 : Analyse de scoring détaillée
# ============================================================================

def exemple_analyse_scoring():
    """Voir en détail comment le score est calculé."""
    print("\n" + "="*70)
    print("EXEMPLE 4 : Analyse détaillée du scoring")
    print("="*70)
    
    matcher = TrackMatcher()
    
    # Cas 1 : Match excellent
    print("\n1️⃣ Match excellent:")
    missing1 = {
        'title': 'Hotel California',
        'artist_name': 'Eagles',
        'album_title': 'Hotel California',
        'playcount': 100
    }
    
    alternative1 = {
        'title': 'Hotel California',
        'artist_name': 'Eagles',
        'album_title': 'Hotel California',
        'playcount': 100
    }
    
    score1 = matcher._score_match(missing1, alternative1)
    print(f"  Title score: {score1['breakdown']['title']:.1f}% (weight: 70%)")
    print(f"  Artist score: {score1['breakdown']['artist']:.1f}% (weight: 20%)")
    print(f"  Album score: {score1['breakdown']['album']:.1f}% (weight: 10%)")
    print(f"  Playcount bonus: {score1['playcount_bonus']:.1f} points")
    print(f"  Total score: {score1['total_score']:.1f}%")
    
    # Cas 2 : Match partiel
    print("\n2️⃣ Match partiel (artiste différent):")
    missing2 = {
        'title': 'Imagine',
        'artist_name': 'John Lennon',
        'album_title': 'Imagine',
        'playcount': 80
    }
    
    alternative2 = {
        'title': 'Imagine',
        'artist_name': 'Lennon',  # Artiste simplifié
        'album_title': 'Imagine',
        'playcount': 85
    }
    
    score2 = matcher._score_match(missing2, alternative2)
    print(f"  Title score: {score2['breakdown']['title']:.1f}% (weight: 70%)")
    print(f"  Artist score: {score2['breakdown']['artist']:.1f}% (weight: 20%)")
    print(f"  Album score: {score2['breakdown']['album']:.1f}% (weight: 10%)")
    print(f"  Playcount bonus: {score2['playcount_bonus']:.1f} points")
    print(f"  Total score: {score2['total_score']:.1f}%")


# ============================================================================
# EXEMPLE 5 : Matching avec multiple candidats
# ============================================================================

def exemple_matching_multiple():
    """Matcher contre plusieurs candidats et voir le top 3."""
    print("\n" + "="*70)
    print("EXEMPLE 5 : Matching avec multiple candidats")
    print("="*70)
    
    matcher = TrackMatcher()
    
    missing = {
        'title': 'Yesterday',
        'artist_name': 'The Beatles',
        'album_title': 'Help!',
        'playcount': 200
    }
    
    alternatives = [
        {
            'urlmd5': '001',
            'title': 'Yesterday',
            'artist_name': 'Beatles',
            'album_title': 'Help!',
            'playcount': 200,
            'source': 'DB'
        },
        {
            'urlmd5': '002',
            'title': 'Let It Be',
            'artist_name': 'The Beatles',
            'album_title': 'Let It Be',
            'playcount': 180,
            'source': 'DB'
        },
        {
            'urlmd5': '003',
            'title': 'Yesterday (Remaster)',
            'artist_name': 'Beatles',
            'album_title': 'Help! (Deluxe)',
            'playcount': 190,
            'source': 'Spotify'
        },
        {
            'urlmd5': '004',
            'title': 'Here Comes The Sun',
            'artist_name': 'The Beatles',
            'album_title': 'Abbey Road',
            'playcount': 170,
            'source': 'DB'
        },
        {
            'urlmd5': '005',
            'title': 'Help!',
            'artist_name': 'The Beatles',
            'album_title': 'Help!',
            'playcount': 160,
            'source': 'DB'
        },
    ]
    
    matches = matcher.find_best_matches(missing, alternatives, top_n=3)
    
    print(f"\n🎵 Recherche: '{missing['title']}' - {missing['artist_name']}")
    print(f"\n🏆 Top 3 correspondances:")
    for i, match in enumerate(matches, 1):
        medal = ["🥇", "🥈", "🥉"][i-1]
        print(f"\n  {medal} #{i} : {match['title']}")
        print(f"        Artiste: {match['artist']}")
        print(f"        Album: {match['album']}")
        print(f"        Playcount: {match['playcount']}")
        print(f"        Score: {match['match_score']:.1f}% ({match['match_quality']})")


# ============================================================================
# EXEMPLE 6 : Bonus playcount
# ============================================================================

def exemple_playcount_bonus():
    """Voir l'impact du bonus playcount similaire."""
    print("\n" + "="*70)
    print("EXEMPLE 6 : Bonus playcount similaire")
    print("="*70)
    
    matcher = TrackMatcher()
    
    # Titre et artiste identiques, playcount différent
    missing = {
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 100
    }
    
    # Cas 1: Playcount similaire (100)
    alt1 = {
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 100
    }
    score1 = matcher._score_match(missing, alt1)
    
    # Cas 2: Playcount similaire (95) - toujours dans tolerance
    alt2 = {
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 95
    }
    score2 = matcher._score_match(missing, alt2)
    
    # Cas 3: Playcount différent (80) - hors tolerance
    alt3 = {
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 80
    }
    score3 = matcher._score_match(missing, alt3)
    
    print(f"\n🎵 Morceau: 100 plays")
    print(f"\n1️⃣ Playcount 100 (match exact):")
    print(f"   Score: {score1['total_score']:.1f}% (bonus: {score1['playcount_bonus']:.1f})")
    
    print(f"\n2️⃣ Playcount 95 (95% = dans tolerance ±20%):")
    print(f"   Score: {score2['total_score']:.1f}% (bonus: {score2['playcount_bonus']:.1f})")
    
    print(f"\n3️⃣ Playcount 80 (80% = hors tolerance):")
    print(f"   Score: {score3['total_score']:.1f}% (bonus: {score3['playcount_bonus']:.1f})")


# ============================================================================
# EXEMPLE 7 : Cache pour performance
# ============================================================================

def exemple_cache_performance():
    """Voir l'impact du cache sur les performances."""
    print("\n" + "="*70)
    print("EXEMPLE 7 : Impact du cache")
    print("="*70)
    
    import time
    
    # Sans cache
    matcher_no_cache = TrackMatcher(use_cache=False)
    
    test_strings = [
        "The Beatles",
        "Queen",
        "Led Zeppelin",
        "Pink Floyd",
    ] * 25  # Répéter 25x = 100 normalisations
    
    start = time.time()
    for s in test_strings:
        matcher_no_cache.normalize_string(s)
    time_no_cache = time.time() - start
    
    # Avec cache
    matcher_cache = TrackMatcher(use_cache=True)
    
    start = time.time()
    for s in test_strings:
        matcher_cache._get_normalized(s)
    time_cache = time.time() - start
    
    speedup = time_no_cache / time_cache if time_cache > 0 else 0
    
    print(f"\n📊 Performance (100 normalisations, 4 unique strings):")
    print(f"  Sans cache: {time_no_cache*1000:.2f}ms")
    print(f"  Avec cache: {time_cache*1000:.2f}ms")
    print(f"  Speedup: {speedup:.1f}x plus rapide")
    print(f"  Cache size: {len(matcher_cache._normalize_cache)} entries")


# ============================================================================
# EXEMPLE 8 : Workflow complet
# ============================================================================

def exemple_workflow_complet():
    """Workflow complet : détecter et matcher."""
    print("\n" + "="*70)
    print("EXEMPLE 8 : Workflow complet")
    print("="*70)
    
    matcher = TrackMatcher()
    
    # Morceau manquant détecté
    missing_track = {
        'title': 'Under the Bridge',
        'artist_name': 'Red Hot Chili Peppers',
        'album_title': 'Blood Sugar Sex Magik',
        'playcount': 75
    }
    
    # Alternatives potentielles
    alternatives = [
        {
            'urlmd5': 'rhcp001',
            'title': 'Under the Bridge',
            'artist_name': 'Red Hot Chili Peppers',
            'album_title': 'Blood Sugar Sex Magik',
            'playcount': 75,
            'source': 'DB'
        },
        {
            'urlmd5': 'rhcp002',
            'title': 'By the Way',
            'artist_name': 'Red Hot Chili Peppers',
            'album_title': 'By the Way',
            'playcount': 60,
            'source': 'Spotify'
        },
    ]
    
    # Étape 1: Trouver correspondances
    matches = matcher.find_best_matches(missing_track, alternatives, top_n=5)
    
    # Étape 2: Filtrer par qualité
    likely_matches = [m for m in matches if TrackMatcher.is_likely_match(m['match_score'])]
    possible_matches = [m for m in matches if TrackMatcher.is_possible_match(m['match_score']) 
                       and not TrackMatcher.is_likely_match(m['match_score'])]
    
    print(f"\n🎵 Morceau manquant: {missing_track['title']}")
    print(f"\n📊 Résultats:")
    print(f"  Total matches found: {len(matches)}")
    print(f"  Likely matches (≥80%): {len(likely_matches)}")
    print(f"  Possible matches (60-80%): {len(possible_matches)}")
    
    if likely_matches:
        print(f"\n✅ Correspondances certaines:")
        for m in likely_matches:
            print(f"   - {m['title']} ({m['match_score']:.1f}%)")
    
    if possible_matches:
        print(f"\n⚠️ Correspondances possibles:")
        for m in possible_matches:
            print(f"   - {m['title']} ({m['match_score']:.1f}%)")


# ============================================================================
# Main
# ============================================================================

def main():
    """Lancer tous les exemples."""
    print("\n" + "#"*70)
    print("# EXEMPLES - TrackMatcher")
    print("#"*70)
    
    exemples = [
        exemple_matching_simple,
        exemple_normalisation,
        exemple_classification_qualite,
        exemple_analyse_scoring,
        exemple_matching_multiple,
        exemple_playcount_bonus,
        exemple_cache_performance,
        exemple_workflow_complet,
    ]
    
    for exemple in exemples:
        try:
            exemple()
        except KeyboardInterrupt:
            print("\n\n⏸️ Exemples interrompus")
            break
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
            logger.exception(e)
    
    print("\n" + "#"*70)
    print("# Exemples terminés")
    print("#"*70)


if __name__ == "__main__":
    main()
