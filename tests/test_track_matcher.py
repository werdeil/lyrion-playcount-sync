"""Tests pour la classe TrackMatcher."""

import pytest
from src.matching.fuzzy_matcher import TrackMatcher


@pytest.fixture
def matcher():
    return TrackMatcher(use_cache=True, use_parallel=False)


# ── Normalisation ─────────────────────────────────────────────────────────────

class TestNormalization:

    @pytest.mark.parametrize("input_str, expected", [
        ("The Beatles",         "beatles"),
        ("Hôtel California",    "hotel california"),
        ("LA REINE DES NEIGES", "reine neiges"),
        ("L'Amour est bleu",    "lamour est bleu"),
        ("  Multiple   Spaces  ", "multiple spaces"),
        ("Song (Radio Edit)",   "song radio edit"),
        ("Café au Lait",        "cafe au lait"),
        ("François & Marie",    "francois marie"),
    ])
    def test_normalize_string(self, input_str, expected):
        assert TrackMatcher.normalize_string(input_str) == expected

    def test_empty_string_returns_empty(self):
        assert TrackMatcher.normalize_string("") == ""

    def test_normalize_is_idempotent(self):
        s = "The Rolling Stones"
        once = TrackMatcher.normalize_string(s)
        twice = TrackMatcher.normalize_string(once)
        assert once == twice


# ── Qualité du matching ───────────────────────────────────────────────────────

class TestMatchQuality:

    @pytest.mark.parametrize("score, expected", [
        (100, "LIKELY"),
        (80,  "LIKELY"),
        (79,  "POSSIBLE"),
        (60,  "POSSIBLE"),
        (59,  "UNLIKELY"),
        (0,   "UNLIKELY"),
    ])
    def test_get_match_quality(self, score, expected):
        assert TrackMatcher._get_match_quality(score) == expected


# ── Calcul du score ───────────────────────────────────────────────────────────

class TestScoring:

    def test_perfect_match_scores_100(self, matcher):
        track = {"title": "Bohemian Rhapsody", "artist_name": "Queen",
                 "album_title": "A Night at the Opera", "playcount": 100}
        result = matcher._score_match(track, track)
        assert result["total_score"] == 100.0

    def test_case_insensitive_match(self, matcher):
        a = {"title": "IMAGINE", "artist_name": "JOHN LENNON",
             "album_title": "IMAGINE", "playcount": 50}
        b = {"title": "Imagine", "artist_name": "John Lennon",
             "album_title": "Imagine", "playcount": 50}
        result = matcher._score_match(a, b)
        assert result["total_score"] == 100.0

    def test_completely_different_tracks_score_low(self, matcher):
        a = {"title": "Imagine", "artist_name": "John Lennon",
             "album_title": "Imagine", "playcount": 100}
        b = {"title": "Yesterday", "artist_name": "The Beatles",
             "album_title": "Help!", "playcount": 50}
        result = matcher._score_match(a, b)
        assert result["total_score"] < 40

    def test_score_breakdown_has_expected_keys(self, matcher):
        track = {"title": "Song", "artist_name": "Artist",
                 "album_title": "Album", "playcount": 10}
        result = matcher._score_match(track, track)
        assert "title" in result["breakdown"]
        assert "artist" in result["breakdown"]
        assert "album" in result["breakdown"]

    def test_score_capped_at_100(self, matcher):
        track = {"title": "Song", "artist_name": "Artist",
                 "album_title": "Album", "playcount": 100}
        result = matcher._score_match(track, track)
        assert result["total_score"] <= 100.0


# ── Bonus playcount ───────────────────────────────────────────────────────────

class TestPlaycountBonus:

    @pytest.mark.parametrize("pc1, pc2, expected_bonus", [
        (100, 100, 5.0),   # identiques
        (100, 95,  5.0),   # 95% → dans la tolérance ±20%
        (100, 80,  5.0),   # 80% → limite tolérance
        (100, 79,  0.0),   # 79% → hors tolérance
        (100, 50,  0.0),   # 50% → hors tolérance
        (0,   100, 0.0),   # zéro → pas de bonus
        (100, 0,   0.0),   # zéro → pas de bonus
    ])
    def test_playcount_bonus(self, matcher, pc1, pc2, expected_bonus):
        assert matcher._calculate_playcount_bonus(pc1, pc2) == expected_bonus


# ── find_best_matches ────────────────────────────────────────────────────────

class TestFindBestMatches:

    @pytest.fixture
    def alternatives(self):
        return [
            {"urlmd5": "111", "title": "Bohemian Rhapsody",
             "artist_name": "Queen", "album_title": "A Night at the Opera",
             "playcount": 100, "source": "DB"},
            {"urlmd5": "222", "title": "We Will Rock You",
             "artist_name": "Queen", "album_title": "News of the World",
             "playcount": 80, "source": "DB"},
            {"urlmd5": "333", "title": "Bohemian Rhapsody (Remaster)",
             "artist_name": "Queen", "album_title": "A Night at the Opera",
             "playcount": 95, "source": "Spotify"},
            {"urlmd5": "444", "title": "The Show Must Go On",
             "artist_name": "Queen", "album_title": "Innuendo",
             "playcount": 70, "source": "DB"},
        ]

    def test_returns_requested_count(self, matcher, alternatives):
        missing = {"title": "Bohemian Rhapsody", "artist_name": "Queen",
                   "album_title": "A Night at the Opera", "playcount": 100}
        matches = matcher.find_best_matches(missing, alternatives, top_n=3)
        assert len(matches) == 3

    def test_results_sorted_descending(self, matcher, alternatives):
        missing = {"title": "Bohemian Rhapsody", "artist_name": "Queen",
                   "album_title": "A Night at the Opera", "playcount": 100}
        matches = matcher.find_best_matches(missing, alternatives, top_n=4)
        scores = [m["match_score"] for m in matches]
        assert scores == sorted(scores, reverse=True)

    def test_best_match_is_exact(self, matcher, alternatives):
        missing = {"title": "Bohemian Rhapsody", "artist_name": "Queen",
                   "album_title": "A Night at the Opera", "playcount": 100}
        matches = matcher.find_best_matches(missing, alternatives, top_n=1)
        assert matches[0]["match_score"] >= 95
        assert matches[0]["match_quality"] == "LIKELY"

    def test_match_dict_has_expected_keys(self, matcher, alternatives):
        missing = {"title": "Bohemian Rhapsody", "artist_name": "Queen",
                   "album_title": "A Night at the Opera", "playcount": 100}
        match = matcher.find_best_matches(missing, alternatives, top_n=1)[0]
        for key in ("urlmd5", "title", "artist", "album", "playcount",
                    "match_score", "match_quality", "score_breakdown"):
            assert key in match

    def test_empty_alternatives_returns_empty(self, matcher):
        missing = {"title": "Song", "artist_name": "Artist",
                   "album_title": "Album", "playcount": 10}
        matches = matcher.find_best_matches(missing, [], top_n=5)
        assert matches == []


# ── Cache ────────────────────────────────────────────────────────────────────

class TestCache:

    def test_cache_hit_does_not_grow(self):
        m = TrackMatcher(use_cache=True)
        m._get_normalized("The Beatles")
        size_before = len(m._normalize_cache)
        m._get_normalized("The Beatles")
        assert len(m._normalize_cache) == size_before

    def test_new_string_grows_cache(self):
        m = TrackMatcher(use_cache=True)
        m._get_normalized("The Beatles")
        m._get_normalized("Queen")
        assert len(m._normalize_cache) == 2

    def test_no_cache_mode_does_not_store(self):
        m = TrackMatcher(use_cache=False)
        m._get_normalized("The Beatles")
        assert len(m._normalize_cache) == 0
