"""Tests pour la classe TrackMatcher."""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.matching.fuzzy_matcher import TrackMatcher
from src.utils import setup_logger

logger = setup_logger(__name__)
logging.basicConfig(level=logging.DEBUG)


# ============================================================================
# TEST 1 : Normalisation des strings
# ============================================================================

def test_normalize_string():
    """Test : Normalisation des chaînes."""
    print("\n" + "="*70)
    print("TEST 1 : normalize_string()")
    print("="*70)
    
    tests = [
        ("The Beatles", "beatles"),
        ("Hôtel California", "hotel california"),
        ("LA REINE DES NEIGES", "reine neiges"),
        ("L'Amour est bleu", "amour est bleu"),
        ("  Multiple   Spaces  ", "multiple spaces"),
        ("Song (Radio Edit)", "song radio edit"),
        ("Café au Lait", "cafe au lait"),
        ("François & Marie", "francois marie"),
    ]
    
    print("\nTests de normalisation:")
    all_passed = True
    for input_str, expected in tests:
        result = TrackMatcher.normalize_string(input_str)
        passed = result == expected
        all_passed = all_passed and passed
        status = "✅" if passed else "❌"
        print(f"  {status} '{input_str}' → '{result}' (attendu: '{expected}')")
    
    return all_passed


# ============================================================================
# TEST 2 : Match quality classification
# ============================================================================

def test_match_quality():
    """Test : Classification de la qualité du matching."""
    print("\n" + "="*70)
    print("TEST 2 : Match quality classification")
    print("="*70)
    
    tests = [
        (95, "LIKELY"),
        (85, "LIKELY"),
        (80, "LIKELY"),
        (79, "POSSIBLE"),
        (70, "POSSIBLE"),
        (60, "POSSIBLE"),
        (59, "UNLIKELY"),
        (30, "UNLIKELY"),
        (0, "UNLIKELY"),
    ]
    
    print("\nClassification des scores:")
    all_passed = True
    for score, expected_quality in tests:
        quality = TrackMatcher._get_match_quality(score)
        passed = quality == expected_quality
        all_passed = all_passed and passed
        status = "✅" if passed else "❌"
        is_likely = "✓" if TrackMatcher.is_likely_match(score) else "✗"
        is_possible = "✓" if TrackMatcher.is_possible_match(score) else "✗"
        print(f"  {status} Score {score:3} → {quality:8} (likely:{is_likely} possible:{is_possible})")
    
    return all_passed


# ============================================================================
# TEST 3 : Scoring simple
# ============================================================================

def test_scoring():
    """Test : Calcul du score de correspondance."""
    print("\n" + "="*70)
    print("TEST 3 : Score calculation")
    print("="*70)
    
    matcher = TrackMatcher()
    
    # Cas 1 : Match parfait
    missing1 = {
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 100
    }
    
    alternative1 = {
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 100
    }
    
    score1 = matcher._score_match(missing1, alternative1)
    print(f"\n1️⃣ Match parfait:")
    print(f"   Score: {score1['total_score']:.1f}/100")
    print(f"   Breakdown: {score1['breakdown']}")
    assert score1['total_score'] == 100.0, "Score devrait être 100"
    
    # Cas 2 : Match partiel (titre similaire)
    missing2 = {
        'title': 'Let It Be',
        'artist_name': 'The Beatles',
        'album_title': 'Let It Be',
        'playcount': 50
    }
    
    alternative2 = {
        'title': 'Let It Be',
        'artist_name': 'Beatles',
        'album_title': 'Let It Be',
        'playcount': 45
    }
    
    score2 = matcher._score_match(missing2, alternative2)
    print(f"\n2️⃣ Match partiel (artiste légèrement différent):")
    print(f"   Score: {score2['total_score']:.1f}/100")
    print(f"   Breakdown: {score2['breakdown']}")
    print(f"   Bonus playcount: {score2['playcount_bonus']:.1f}")
    
    # Cas 3 : Match différent (titre complètement différent)
    missing3 = {
        'title': 'Imagine',
        'artist_name': 'John Lennon',
        'album_title': 'Imagine',
        'playcount': 100
    }
    
    alternative3 = {
        'title': 'Yesterday',
        'artist_name': 'The Beatles',
        'album_title': 'Help!',
        'playcount': 50
    }
    
    score3 = matcher._score_match(missing3, alternative3)
    print(f"\n3️⃣ Match mauvais (complètement différent):")
    print(f"   Score: {score3['total_score']:.1f}/100")
    print(f"   Breakdown: {score3['breakdown']}")
    
    return True


# ============================================================================
# TEST 4 : Find best matches
# ============================================================================

def test_find_best_matches():
    """Test : Trouver les meilleures correspondances."""
    print("\n" + "="*70)
    print("TEST 4 : find_best_matches()")
    print("="*70)
    
    matcher = TrackMatcher()
    
    # Morceau à matcher
    missing = {
        'title': 'Bohemian Rhapsody',
        'artist_name': 'Queen',
        'album_title': 'A Night at the Opera',
        'playcount': 100
    }
    
    # Candidats (alternativeplaycount)
    alternatives = [
        {
            'urlmd5': '111',
            'title': 'Bohemian Rhapsody',
            'artist_name': 'Queen',
            'album_title': 'A Night at the Opera',
            'playcount': 100,
            'source': 'DB'
        },
        {
            'urlmd5': '222',
            'title': 'We Will Rock You',
            'artist_name': 'Queen',
            'album_title': 'Sheer Heart Attack',
            'playcount': 80,
            'source': 'DB'
        },
        {
            'urlmd5': '333',
            'title': 'Bohemian Rhapsody (Remaster)',
            'artist_name': 'Queen',
            'album_title': 'A Night at the Opera',
            'playcount': 95,
            'source': 'Spotify'
        },
        {
            'urlmd5': '444',
            'title': 'The Show Must Go On',
            'artist_name': 'Queen',
            'album_title': 'Innuendo',
            'playcount': 70,
            'source': 'DB'
        },
    ]
    
    # Trouver top 3
    matches = matcher.find_best_matches(missing, alternatives, top_n=3)
    
    print(f"\n🎵 Recherche: '{missing['title']}' - {missing['artist_name']}")
    print(f"\nTop 3 correspondances trouvées:")
    for i, match in enumerate(matches, 1):
        print(f"\n  {i}. {match['title']}")
        print(f"     Artiste: {match['artist']}")
        print(f"     Playcount: {match['playcount']}")
        print(f"     Score: {match['match_score']:.1f}% ({match['match_quality']})")
        print(f"     Breakdown: {match['score_breakdown']}")
    
    # Vérifications
    assert len(matches) == 3, f"Devrait avoir 3 correspondances, got {len(matches)}"
    assert matches[0]['match_score'] >= 95, "Top match devrait être très bon"
    assert matches[0]['match_quality'] == 'LIKELY', "Top match devrait être LIKELY"
    
    return True


# ============================================================================
# TEST 5 : Playcount bonus
# ============================================================================

def test_playcount_bonus():
    """Test : Bonus playcount similaire."""
    print("\n" + "="*70)
    print("TEST 5 : Playcount bonus")
    print("="*70)
    
    matcher = TrackMatcher()
    
    tests = [
        (100, 100, 5.0, "Exact match"),
        (100, 95, 5.0, "95% = within tolerance"),
        (100, 85, 0.0, "85% = outside tolerance"),
        (100, 50, 0.0, "50% = outside tolerance"),
        (0, 100, 0.0, "0 playcount"),
        (100, 0, 0.0, "0 playcount"),
    ]
    
    print("\nBonus playcount (±20% tolerance):")
    for pc1, pc2, expected_bonus, description in tests:
        bonus = matcher._calculate_playcount_bonus(pc1, pc2)
        status = "✅" if bonus == expected_bonus else "❌"
        print(f"  {status} {pc1:3} vs {pc2:3} → {bonus:.1f} (expected {expected_bonus:.1f}) - {description}")
    
    return True


# ============================================================================
# TEST 6 : Cache
# ============================================================================

def test_cache():
    """Test : Cache des strings normalisées."""
    print("\n" + "="*70)
    print("TEST 6 : Normalization cache")
    print("="*70)
    
    matcher = TrackMatcher(use_cache=True)
    
    # Première normalisation
    str1 = "The Beatles"
    result1 = matcher._get_normalized(str1)
    cache_size_1 = len(matcher._normalize_cache)
    
    # Deuxième normalisation (devrait être en cache)
    result2 = matcher._get_normalized(str1)
    cache_size_2 = len(matcher._normalize_cache)
    
    # Troisième string
    str3 = "Queen"
    result3 = matcher._get_normalized(str3)
    cache_size_3 = len(matcher._normalize_cache)
    
    print(f"\n📦 Cache test:")
    print(f"  Après 1ère normalisation: cache size = {cache_size_1}")
    print(f"  Après 2e normalisation (same): cache size = {cache_size_2}")
    print(f"  Après 3e normalisation (diff): cache size = {cache_size_3}")
    
    assert cache_size_1 == 1, "Cache devrait avoir 1 entry"
    assert cache_size_2 == 1, "Cache ne devrait pas augmenter"
    assert cache_size_3 == 2, "Cache devrait avoir 2 entries"
    
    # Tester clear_cache
    matcher.clear_cache()
    print(f"  Après clear_cache: cache size = {len(matcher._normalize_cache)}")
    assert len(matcher._normalize_cache) == 0, "Cache devrait être vide"
    
    return True


# ============================================================================
# TEST 7 : Case insensitive
# ============================================================================

def test_case_insensitive():
    """Test : Insensibilité à la casse."""
    print("\n" + "="*70)
    print("TEST 7 : Case insensitivity")
    print("="*70)
    
    matcher = TrackMatcher()
    
    missing = {
        'title': 'IMAGINE',
        'artist_name': 'JOHN LENNON',
        'album_title': 'IMAGINE',
        'playcount': 50
    }
    
    alternative = {
        'title': 'Imagine',
        'artist_name': 'John Lennon',
        'album_title': 'Imagine',
        'playcount': 50
    }
    
    score = matcher._score_match(missing, alternative)
    print(f"\n大文字小文字の無視:")
    print(f"  IMAGINE vs Imagine → {score['total_score']:.1f}% (should be 100)")
    
    assert score['total_score'] == 100.0, "Score should be 100 (case insensitive)"
    
    return True


# ============================================================================
# Main
# ============================================================================

def main():
    """Lance tous les tests."""
    print("\n" + "#"*70)
    print("# TESTS DE LA CLASSE TrackMatcher")
    print("#"*70)
    
    tests = [
        ("Normalisation des strings", test_normalize_string),
        ("Classification de qualité", test_match_quality),
        ("Calcul de score", test_scoring),
        ("Meilleures correspondances", test_find_best_matches),
        ("Bonus playcount", test_playcount_bonus),
        ("Cache", test_cache),
        ("Insensibilité à la casse", test_case_insensitive),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⏸️ Tests interrompus")
            break
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
            logger.exception(e)
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "#"*70)
    print("# RÉSUMÉ")
    print("#"*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests réussis : {passed}/{total}")
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\nTaux de réussite : {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n✅ TOUS LES TESTS RÉUSSIS !")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) échoué(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
