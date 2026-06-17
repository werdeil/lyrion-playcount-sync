"""Tests unitaires pour MatchDialog."""

import pytest
from lyrion_playcount_sync.models import Track, SyncOperation


class TestMatchDialogImport:
    """Vérifie que le module s'importe sans erreur."""

    def test_module_importable(self):
        from lyrion_playcount_sync.ui import match_dialog  # noqa: F401

    def test_class_exists(self):
        from lyrion_playcount_sync.ui.match_dialog import MatchDialog
        assert callable(MatchDialog)


class TestSyncOperationBuilding:
    """Tests de construction de SyncOperation (logique partagée avec le dialog)."""

    def test_copy_operation_carries_persist_playcount(self):
        op = SyncOperation(
            missing_urlmd5="missing_abc",
            selected_alternative_urlmd5="alt_xyz",
            action="COPY",
            new_playcount=42,
        )
        assert op.action == "COPY"
        assert op.new_playcount == 42
        assert op.missing_urlmd5 == "missing_abc"
        assert op.selected_alternative_urlmd5 == "alt_xyz"

    def test_merge_operation_valid(self):
        op = SyncOperation(
            missing_urlmd5="missing_abc",
            selected_alternative_urlmd5="alt_xyz",
            action="MERGE",
            new_playcount=100,
        )
        assert op.action == "MERGE"

    def test_operation_rejects_empty_urlmd5(self):
        with pytest.raises(ValueError):
            SyncOperation(
                missing_urlmd5="",
                selected_alternative_urlmd5="alt_xyz",
                action="COPY",
                new_playcount=10,
            )

    def test_operation_rejects_invalid_action(self):
        with pytest.raises(ValueError):
            SyncOperation(
                missing_urlmd5="missing_abc",
                selected_alternative_urlmd5="alt_xyz",
                action="UNKNOWN",
                new_playcount=10,
            )

    def test_operation_id_is_unique(self):
        op1 = SyncOperation("a", "b", "COPY", 1)
        op2 = SyncOperation("a", "b", "COPY", 1)
        assert op1.operation_id != op2.operation_id
