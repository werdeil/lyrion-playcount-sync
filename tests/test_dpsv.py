"""Tests du calcul de la DPSV (Alternative Play Count)."""

from lyrion_playcount_sync.database.dpsv import compute_dpsv, round_float


class TestRoundFloat:
    def test_half_rounds_away_from_zero(self):
        assert round_float(12.5) == 13
        assert round_float(-12.5) == -13

    def test_normal_rounding(self):
        assert round_float(12.4) == 12
        assert round_float(12.6) == 13
        assert round_float(-12.4) == -12
        assert round_float(0) == 0


class TestComputeDpsv:
    def test_no_events_is_zero(self):
        assert compute_dpsv(0, 0) == 0
        assert compute_dpsv(None, None) == 0

    def test_single_play(self):
        # (100-0)/8 = 12.5 -> 13  (valeur observée dans persist.db)
        assert compute_dpsv(1, 0, last_played=100, last_skipped=0) == 13

    def test_single_skip(self):
        # (100-0)/4 = 25 -> -25
        assert compute_dpsv(0, 1, last_played=0, last_skipped=100) == -25

    def test_capped_at_100(self):
        assert compute_dpsv(1000, 0) == 100

    def test_floored_at_minus_100(self):
        assert compute_dpsv(0, 1000) == -100

    def test_order_depends_on_dates(self):
        # Termine par une lecture (lastPlayed le plus récent) -> remonte.
        ends_play = compute_dpsv(2, 1, last_played=200, last_skipped=100)
        # Termine par un skip (lastSkipped le plus récent) -> redescend.
        ends_skip = compute_dpsv(2, 1, last_played=100, last_skipped=200)
        assert ends_skip > ends_play

    def test_skip_weighs_more_than_play(self):
        # Un skip (÷4) doit déplacer plus fort qu'une lecture (÷8).
        assert abs(compute_dpsv(0, 1)) > abs(compute_dpsv(1, 0))

    def test_negative_or_none_counts_treated_as_zero(self):
        assert compute_dpsv(-5, None) == 0
