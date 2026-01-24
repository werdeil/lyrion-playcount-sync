#!/usr/bin/env python3
"""
Tests rapides pour valider les modèles.
"""

from datetime import datetime, timezone
from src.models import Track, MatchSuggestion, SyncOperation


def test_track_basic():
    """Tester la création d'un Track simple."""
    print("\n🧪 Test: Track basic creation")
    
    track = Track(
        urlmd5="abc123def456",
        title="Imagine",
        artist="John Lennon",
        album="Imagine",
        url="https://example.com/imagine",
        playcount=42,
        lastplayed=1705795200,  # 2024-01-20
        rating=5,
        source="tracks_persistent"
    )
    
    print(f"  ✅ Track created: {track}")
    print(f"  ✅ Display name: {track.display_name()}")
    print(f"  ✅ Last played: {track.lastplayed_formatted()}")
    print(f"  ✅ Dict: {track.to_dict()}")


def test_track_display_name():
    """Tester les fallbacks de display_name()."""
    print("\n🧪 Test: Track display_name fallbacks")
    
    # Cas 1: Artiste + Titre
    t1 = Track("md5_1", "Song", "Artist", "Album", None, 10)
    print(f"  ✅ Artist + Title: {t1.display_name()}")
    
    # Cas 2: Titre seul
    t2 = Track("md5_2", "Song", None, None, None, 5)
    print(f"  ✅ Title only: {t2.display_name()}")
    
    # Cas 3: URL seule
    t3 = Track("md5_3", None, None, None, "https://example.com", 2)
    print(f"  ✅ URL only: {t3.display_name()}")
    
    # Cas 4: Rien, fallback sur urlmd5
    t4 = Track("abc123def456", None, None, None, None, 1)
    print(f"  ✅ Fallback urlmd5: {t4.display_name()}")


def test_match_suggestion():
    """Tester MatchSuggestion."""
    print("\n🧪 Test: MatchSuggestion")
    
    missing_track = Track(
        "missing_1", "Imagine", "John Lennon", "Imagine", None, 0
    )
    
    suggestion = MatchSuggestion(missing_track)
    
    # Ajouter des matches
    alternative1 = Track(
        "alt_1", "Imagine", "John Lennon", "Imagine", None, 150
    )
    suggestion.add_match(alternative1, 95.0)
    
    alternative2 = Track(
        "alt_2", "Imagine", "Various Artists", "Best Of", None, 50
    )
    suggestion.add_match(alternative2, 65.0)
    
    print(f"  ✅ Suggestion created: {suggestion}")
    print(f"  ✅ Best match: {suggestion.get_best_match()}")
    print(f"  ✅ Auto-match possible: {suggestion.auto_match_possible}")
    print(f"  ✅ Top 1: {suggestion.get_top_n(1)}")


def test_sync_operation():
    """Tester SyncOperation et génération SQL."""
    print("\n🧪 Test: SyncOperation")
    
    # Opération COPY
    op_copy = SyncOperation(
        missing_urlmd5="missing_1",
        selected_alternative_urlmd5="alt_1",
        action="COPY",
        new_playcount=150
    )
    
    print(f"  ✅ COPY operation: {op_copy}")
    update_sql, delete_sql = op_copy.to_sql()
    print(f"  ✅ UPDATE query: {update_sql}")
    print(f"  ✅ DELETE query: {delete_sql}")
    
    # Opération MERGE
    op_merge = SyncOperation(
        missing_urlmd5="missing_1",
        selected_alternative_urlmd5="alt_1",
        action="MERGE",
        new_playcount=200
    )
    
    print(f"  ✅ MERGE operation: {op_merge}")
    
    # Opération DELETE
    op_delete = SyncOperation(
        missing_urlmd5="missing_1",
        selected_alternative_urlmd5="alt_1",
        action="DELETE"
    )
    
    print(f"  ✅ DELETE operation: {op_delete}")
    update_sql, delete_sql = op_delete.to_sql()
    print(f"  ✅ DELETE UPDATE: {update_sql}")


def test_validations():
    """Tester les validations."""
    print("\n🧪 Test: Validations")
    
    # Validation playcount négatif
    try:
        Track("md5", "Title", "Artist", None, None, -5)
        print("  ❌ Should have rejected negative playcount")
    except ValueError as e:
        print(f"  ✅ Rejected negative playcount: {e}")
    
    # Validation rating hors limites
    try:
        Track("md5", "Title", "Artist", None, None, 10, rating=10)
        print("  ❌ Should have rejected rating > 5")
    except ValueError as e:
        print(f"  ✅ Rejected invalid rating: {e}")
    
    # Validation source invalide
    try:
        Track("md5", "Title", "Artist", None, None, 10, source="invalid")
        print("  ❌ Should have rejected invalid source")
    except ValueError as e:
        print(f"  ✅ Rejected invalid source: {e}")
    
    # Validation action invalide
    try:
        SyncOperation("missing", "alt", "INVALID")
        print("  ❌ Should have rejected invalid action")
    except ValueError as e:
        print(f"  ✅ Rejected invalid action: {e}")


def test_json_export():
    """Tester l'export JSON."""
    print("\n🧪 Test: JSON export")
    
    track = Track(
        urlmd5="abc123",
        title="Imagine",
        artist="John Lennon",
        album="Imagine",
        url="https://example.com",
        playcount=42,
        rating=5
    )
    
    json_str = track.to_json()
    print(f"  ✅ Track JSON export successful ({len(json_str)} chars)")
    
    op = SyncOperation(
        missing_urlmd5="missing_1",
        selected_alternative_urlmd5="alt_1",
        action="COPY",
        new_playcount=100
    )
    
    json_str = op.to_json()
    print(f"  ✅ SyncOperation JSON export successful ({len(json_str)} chars)")


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("🧪 Tests des modèles Track, MatchSuggestion, SyncOperation")
    print("=" * 60)
    
    test_track_basic()
    test_track_display_name()
    test_match_suggestion()
    test_sync_operation()
    test_validations()
    test_json_export()
    
    print("\n" + "=" * 60)
    print("✅ Tous les tests réussis !")
    print("=" * 60)


if __name__ == "__main__":
    main()
