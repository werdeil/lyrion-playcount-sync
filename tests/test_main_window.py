"""Tests unitaires pour MainWindow — logique métier sans affichage UI."""

import tkinter as tk
import pytest
from unittest.mock import MagicMock

from src.ui.main_window import MainWindow


@pytest.fixture
def win():
    """Instance MainWindow avec état interne initialisé et widgets mockés."""
    w = object.__new__(MainWindow)

    w.pending_assignments = {}
    w.missing_tracks = {
        "md5_a": {
            "urlmd5": "md5_a",
            "artist_name": "Queen",
            "title": "Bohemian Rhapsody",
            "playcount": 42,
            "lastplayed": 0,
        },
        "md5_b": {
            "urlmd5": "md5_b",
            "artist_name": "Beatles",
            "title": "Hey Jude",
            "playcount": 10,
            "lastplayed": 0,
        },
    }
    w.item_to_urlmd5 = {"item1": "md5_a", "item2": "md5_b"}
    w.urlmd5_to_item = {"md5_a": "item1", "md5_b": "item2"}
    w.suggestion_items = {}
    w.alternative_tracks = []
    w.ignored_tracks = set()
    w.db_path = "test.db"
    w.db_manager = None
    w.matcher = None

    w.tracks_tree = MagicMock()
    w.tracks_tree.item.return_value = ("Artist", "Title", "10", "—")
    w.suggestions_tree = MagicMock()
    w.track_info_label = MagicMock()
    w.sync_btn = MagicMock()
    w.status_label = MagicMock()
    w.db_label = MagicMock()
    w.counter_label = MagicMock()

    return w


def _assert_sync_btn(win, text, state):
    """Vérifie le libellé et l'état du bouton Sync sans contraindre le style."""
    kwargs = win.sync_btn.config.call_args.kwargs
    assert kwargs["text"] == text
    assert kwargs["state"] == state


class TestAssignment:
    """Tests des assignations en attente."""

    def test_assign_stores_in_pending(self, win):
        alt = {"urlmd5": "alt_1", "title": "Bohemian Rhapsody", "match_score": 95.0}
        win._assign_track("md5_a", alt)
        assert win.pending_assignments["md5_a"] is alt

    def test_assign_enables_sync_button(self, win):
        alt = {"urlmd5": "alt_1", "title": "Song", "match_score": 85.0}
        win._assign_track("md5_a", alt)
        _assert_sync_btn(win, "Sync assignées (1)", tk.NORMAL)

    def test_reassign_replaces_previous(self, win):
        alt1 = {"urlmd5": "alt_1", "title": "Song A", "match_score": 85.0}
        alt2 = {"urlmd5": "alt_2", "title": "Song B", "match_score": 72.0}
        win._assign_track("md5_a", alt1)
        win._assign_track("md5_a", alt2)
        assert win.pending_assignments["md5_a"] is alt2
        # Toujours 1 assignation, pas 2
        assert len(win.pending_assignments) == 1

    def test_multiple_assignments_counted(self, win):
        win._assign_track("md5_a", {"urlmd5": "alt_1", "title": "A", "match_score": 90.0})
        win._assign_track("md5_b", {"urlmd5": "alt_2", "title": "B", "match_score": 80.0})
        assert len(win.pending_assignments) == 2
        _assert_sync_btn(win, "Sync assignées (2)", tk.NORMAL)

    def test_deassign_removes_from_pending(self, win):
        win.pending_assignments["md5_a"] = {"urlmd5": "alt_1"}
        win._deassign_track("md5_a")
        assert "md5_a" not in win.pending_assignments

    def test_deassign_disables_button_when_empty(self, win):
        win.pending_assignments["md5_a"] = {"urlmd5": "alt_1"}
        win._deassign_track("md5_a")
        _assert_sync_btn(win, "Sync assignées (0)", tk.DISABLED)

    def test_deassign_unknown_urlmd5_is_noop(self, win):
        win._deassign_track("nonexistent_md5")
        assert win.pending_assignments == {}

    def test_deassign_preserves_other_assignments(self, win):
        win.pending_assignments["md5_a"] = {"urlmd5": "alt_1"}
        win.pending_assignments["md5_b"] = {"urlmd5": "alt_2"}
        win._deassign_track("md5_a")
        assert "md5_b" in win.pending_assignments
        assert "md5_a" not in win.pending_assignments


class TestSyncButton:
    """Tests de l'état du bouton Sync."""

    def test_disabled_with_no_assignments(self, win):
        win._update_sync_button()
        _assert_sync_btn(win, "Sync assignées (0)", tk.DISABLED)

    def test_enabled_with_one_assignment(self, win):
        win.pending_assignments["md5_a"] = {"urlmd5": "alt_1"}
        win._update_sync_button()
        _assert_sync_btn(win, "Sync assignées (1)", tk.NORMAL)

    def test_label_reflects_count(self, win):
        for i in range(5):
            win.pending_assignments[f"md5_{i}"] = {"urlmd5": f"alt_{i}"}
        win._update_sync_button()
        _assert_sync_btn(win, "Sync assignées (5)", tk.NORMAL)


class TestIgnore:
    """Tests de l'ignorance d'une piste."""

    def test_ignore_clears_right_panel(self, win):
        win.tracks_tree.selection.return_value = ("item1",)
        win._ignore_selected_track()
        win.suggestions_tree.delete.assert_called()
        win.track_info_label.config.assert_called()

    def test_ignore_removes_pending_assignment(self, win):
        win.pending_assignments["md5_a"] = {"urlmd5": "alt_1"}
        win.tracks_tree.selection.return_value = ("item1",)
        win._ignore_selected_track()
        assert "md5_a" not in win.pending_assignments
        _assert_sync_btn(win, "Sync assignées (0)", tk.DISABLED)

    def test_ignore_with_no_selection_is_noop(self, win):
        win.tracks_tree.selection.return_value = ()
        win._ignore_selected_track()
        win.suggestions_tree.delete.assert_not_called()
