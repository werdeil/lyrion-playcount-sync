"""Tests pour les modèles Track, MatchSuggestion, SyncOperation."""

import pytest
from src.models import Track, MatchSuggestion, SyncOperation


# ── Track ────────────────────────────────────────────────────────────────────

class TestTrack:

    def test_basic_creation(self):
        t = Track(
            urlmd5="abc123",
            title="Imagine",
            artist="John Lennon",
            album="Imagine",
            url="file:///music/imagine.mp3",
            playcount=42,
            lastplayed=1705795200,
            rating=5,
            source="tracks_persistent",
        )
        assert t.urlmd5 == "abc123"
        assert t.playcount == 42
        assert t.rating == 5

    def test_display_name_artist_and_title(self):
        t = Track("md5", "Song", "Artist", "Album", None, 0)
        assert t.display_name() == "Artist - Song"

    def test_display_name_title_only(self):
        t = Track("md5", "Song", None, None, None, 0)
        assert t.display_name() == "Song"

    def test_display_name_url_fallback(self):
        t = Track("md5", None, None, None, "file:///music/track.mp3", 0)
        assert t.display_name() == "file:///music/track.mp3"

    def test_display_name_urlmd5_fallback(self):
        t = Track("abc123def456", None, None, None, None, 0)
        assert "abc123de" in t.display_name()

    def test_lastplayed_formatted_none(self):
        t = Track("md5", "Title", None, None, None, 0)
        assert t.lastplayed_formatted() == "N/A"

    def test_lastplayed_formatted_timestamp(self):
        t = Track("md5", "Title", None, None, None, 0, lastplayed=1705795200)
        result = t.lastplayed_formatted()
        assert "2024" in result

    def test_rejects_negative_playcount(self):
        with pytest.raises(ValueError):
            Track("md5", "Title", None, None, None, -1)

    def test_rejects_rating_above_five(self):
        with pytest.raises(ValueError):
            Track("md5", "Title", None, None, None, 0, rating=6)

    def test_rejects_rating_below_zero(self):
        with pytest.raises(ValueError):
            Track("md5", "Title", None, None, None, 0, rating=-1)

    def test_rejects_invalid_source(self):
        with pytest.raises(ValueError):
            Track("md5", "Title", None, None, None, 0, source="unknown")

    def test_to_dict_contains_key_fields(self):
        t = Track("abc123", "Song", "Artist", "Album", None, 10)
        d = t.to_dict()
        assert d["urlmd5"] == "abc123"
        assert d["playcount"] == 10

    def test_to_json_is_valid_string(self):
        t = Track("abc123", "Song", "Artist", None, None, 5)
        import json
        data = json.loads(t.to_json())
        assert data["urlmd5"] == "abc123"

    def test_zero_playcount_is_valid(self):
        t = Track("md5", "Title", None, None, None, 0)
        assert t.playcount == 0

    def test_zero_rating_is_valid(self):
        t = Track("md5", "Title", None, None, None, 0, rating=0)
        assert t.rating == 0


# ── MatchSuggestion ──────────────────────────────────────────────────────────

class TestMatchSuggestion:

    def _make_track(self, uid: str, playcount: int = 0) -> Track:
        return Track(uid, "Song", "Artist", "Album", None, playcount,
                     source="alternativeplaycount")

    def test_empty_suggestion_no_auto_match(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        s = MatchSuggestion(missing)
        assert s.auto_match_possible is False
        assert s.get_best_match() is None

    def test_add_match_sorts_by_score_descending(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        s = MatchSuggestion(missing)
        s.add_match(self._make_track("alt_low"), 60.0)
        s.add_match(self._make_track("alt_high"), 95.0)
        best = s.suggested_matches[0]
        assert best[1] == 95.0

    def test_auto_match_flag_set_above_90(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        s = MatchSuggestion(missing)
        s.add_match(self._make_track("alt"), 91.0)
        assert s.auto_match_possible is True

    def test_auto_match_flag_not_set_at_90(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        s = MatchSuggestion(missing)
        s.add_match(self._make_track("alt"), 90.0)
        assert s.auto_match_possible is False

    def test_get_best_match_above_threshold(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        alt = self._make_track("alt")
        s = MatchSuggestion(missing, [(alt, 85.0)])
        result = s.get_best_match()
        assert result is not None
        assert result[1] == 85.0

    def test_get_best_match_below_threshold_returns_none(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        alt = self._make_track("alt")
        s = MatchSuggestion(missing, [(alt, 55.0)])
        assert s.get_best_match() is None

    def test_get_top_n(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        s = MatchSuggestion(missing)
        for i in range(5):
            s.add_match(self._make_track(f"alt_{i}"), float(50 + i * 10))
        assert len(s.get_top_n(3)) == 3

    def test_rejects_invalid_score(self):
        missing = Track("missing", "Song", "Artist", None, None, 0)
        alt = self._make_track("alt")
        with pytest.raises(ValueError):
            MatchSuggestion(missing, [(alt, 150.0)])


# ── SyncOperation ────────────────────────────────────────────────────────────

class TestSyncOperation:

    def test_copy_operation_to_sql(self):
        op = SyncOperation("missing_1", "alt_1", "COPY", new_playcount=42)
        update_sql, delete_sql = op.to_sql()
        assert "UPDATE tracks_persistent" in update_sql
        assert "42" in update_sql
        assert "DELETE FROM alternativeplaycount" in delete_sql

    def test_merge_operation_to_sql(self):
        op = SyncOperation("missing_1", "alt_1", "MERGE", new_playcount=100)
        update_sql, _ = op.to_sql()
        assert "UPDATE tracks_persistent" in update_sql

    def test_delete_operation_to_sql(self):
        op = SyncOperation("missing_1", "alt_1", "DELETE")
        update_sql, delete_sql = op.to_sql()
        assert "DELETE FROM tracks_persistent" in update_sql

    def test_copy_requires_playcount(self):
        with pytest.raises(ValueError):
            op = SyncOperation("missing_1", "alt_1", "COPY", new_playcount=None)
            op.to_sql()

    def test_operation_id_unique_per_instance(self):
        op1 = SyncOperation("a", "b", "COPY", 1)
        op2 = SyncOperation("a", "b", "COPY", 1)
        assert op1.operation_id != op2.operation_id

    def test_rejects_empty_missing_urlmd5(self):
        with pytest.raises(ValueError):
            SyncOperation("", "alt", "COPY", 10)

    def test_rejects_empty_alternative_urlmd5(self):
        with pytest.raises(ValueError):
            SyncOperation("missing", "", "COPY", 10)

    def test_rejects_invalid_action(self):
        with pytest.raises(ValueError):
            SyncOperation("missing", "alt", "INVALID")

    def test_rejects_negative_playcount(self):
        with pytest.raises(ValueError):
            SyncOperation("missing", "alt", "COPY", new_playcount=-1)

    def test_to_dict_serializable(self):
        op = SyncOperation("missing_1", "alt_1", "COPY", new_playcount=50)
        d = op.to_dict()
        assert d["action"] == "COPY"
        assert d["new_playcount"] == 50

    def test_to_json_valid(self):
        import json
        op = SyncOperation("missing_1", "alt_1", "MERGE", new_playcount=75)
        data = json.loads(op.to_json())
        assert data["action"] == "MERGE"
