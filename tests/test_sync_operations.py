"""Tests pour SyncOperations sur une base de données temporaire."""

import sqlite3
import tempfile
import pytest
from pathlib import Path

from src.models import SyncOperation
from src.database.operations import SyncOperations


@pytest.fixture
def test_db(tmp_path):
    """Base de données SQLite temporaire avec schema minimal."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE tracks_persistent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urlmd5 TEXT UNIQUE,
            playcount INTEGER,
            lastplayed INTEGER
        );
        CREATE TABLE alternativeplaycount (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urlmd5 TEXT UNIQUE,
            playcount INTEGER,
            lastplayed INTEGER,
            source TEXT
        );
    """)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def ops(test_db):
    return SyncOperations(test_db)


def _insert_persist(db_path, urlmd5, playcount, lastplayed=None):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT OR REPLACE INTO tracks_persistent (urlmd5, playcount, lastplayed) VALUES (?,?,?)",
        (urlmd5, playcount, lastplayed),
    )
    conn.commit()
    conn.close()


def _insert_alt(db_path, urlmd5, playcount, source="test"):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT OR REPLACE INTO alternativeplaycount (urlmd5, playcount, source) VALUES (?,?,?)",
        (urlmd5, playcount, source),
    )
    conn.commit()
    conn.close()


def _read_alt_playcount(db_path, urlmd5):
    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "SELECT playcount FROM alternativeplaycount WHERE urlmd5=?", (urlmd5,)
    ).fetchone()
    conn.close()
    return row[0] if row else None


def _persist_exists(db_path, urlmd5):
    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "SELECT 1 FROM tracks_persistent WHERE urlmd5=?", (urlmd5,)
    ).fetchone()
    conn.close()
    return row is not None


# ── update_alternative_playcount ──────────────────────────────────────────────

class TestUpdateAlternativePlaycount:

    def test_update_existing_row(self, ops, test_db):
        _insert_alt(test_db, "alt1", 30)
        ops.update_alternative_playcount("alt1", 75)
        assert _read_alt_playcount(test_db, "alt1") == 75

    def test_insert_new_row_when_absent(self, ops, test_db):
        ops.update_alternative_playcount("alt_new", 42)
        assert _read_alt_playcount(test_db, "alt_new") == 42

    def test_returns_one_on_success(self, ops, test_db):
        _insert_alt(test_db, "alt1", 10)
        result = ops.update_alternative_playcount("alt1", 20)
        assert result == 1


# ── delete_from_tracks_persistent ─────────────────────────────────────────────

class TestDeleteFromPersistent:

    def test_deletes_existing_row(self, ops, test_db):
        _insert_persist(test_db, "miss1", 50)
        ops.delete_from_tracks_persistent("miss1")
        assert not _persist_exists(test_db, "miss1")

    def test_delete_nonexistent_does_not_raise(self, ops):
        ops.delete_from_tracks_persistent("nonexistent_urlmd5")


# ── sync_track COPY ───────────────────────────────────────────────────────────

class TestSyncTrackCopy:

    def test_copy_updates_alt_playcount(self, ops, test_db):
        _insert_persist(test_db, "miss2", 100)
        _insert_alt(test_db, "alt2", 60)

        op = SyncOperation("miss2", "alt2", "COPY", new_playcount=100)
        assert ops.sync_track(op) is True
        assert _read_alt_playcount(test_db, "alt2") == 100

    def test_copy_deletes_from_persistent(self, ops, test_db):
        _insert_persist(test_db, "miss2", 100)
        _insert_alt(test_db, "alt2", 60)

        op = SyncOperation("miss2", "alt2", "COPY", new_playcount=100)
        ops.sync_track(op)
        assert not _persist_exists(test_db, "miss2")

    def test_copy_is_atomic_on_success(self, ops, test_db):
        _insert_persist(test_db, "miss2", 100)
        _insert_alt(test_db, "alt2", 60)

        result = ops.sync_track(SyncOperation("miss2", "alt2", "COPY", new_playcount=100))
        assert result is True
        assert _read_alt_playcount(test_db, "alt2") == 100
        assert not _persist_exists(test_db, "miss2")


# ── sync_track MERGE ──────────────────────────────────────────────────────────

class TestSyncTrackMerge:

    def test_merge_adds_playcounts(self, ops, test_db):
        _insert_persist(test_db, "miss3", 50)
        _insert_alt(test_db, "alt3", 30)

        op = SyncOperation("miss3", "alt3", "MERGE", new_playcount=50)
        ops.sync_track(op)
        assert _read_alt_playcount(test_db, "alt3") == 80  # 30 + 50

    def test_merge_deletes_from_persistent(self, ops, test_db):
        _insert_persist(test_db, "miss3", 50)
        _insert_alt(test_db, "alt3", 30)

        ops.sync_track(SyncOperation("miss3", "alt3", "MERGE", new_playcount=50))
        assert not _persist_exists(test_db, "miss3")


# ── bulk_sync ─────────────────────────────────────────────────────────────────

class TestBulkSync:

    def test_all_succeed(self, ops, test_db):
        for i in range(1, 4):
            _insert_persist(test_db, f"miss{i}", i * 10)
            _insert_alt(test_db, f"alt{i}", i * 5)

        operations = [
            SyncOperation(f"miss{i}", f"alt{i}", "COPY", new_playcount=i * 10)
            for i in range(1, 4)
        ]
        result = ops.bulk_sync(operations)
        assert result["success"] == 3
        assert result["failed"] == 0

    def test_progress_callback_called(self, ops, test_db):
        _insert_persist(test_db, "miss1", 10)
        _insert_alt(test_db, "alt1", 5)

        calls = []
        ops.bulk_sync(
            [SyncOperation("miss1", "alt1", "COPY", new_playcount=10)],
            progress_callback=lambda cur, tot: calls.append((cur, tot)),
        )
        assert calls == [(1, 1)]

    def test_result_structure(self, ops, test_db):
        _insert_persist(test_db, "miss1", 10)
        _insert_alt(test_db, "alt1", 5)

        result = ops.bulk_sync(
            [SyncOperation("miss1", "alt1", "COPY", new_playcount=10)]
        )
        assert "success" in result
        assert "failed" in result
        assert "total" in result
        assert "errors" in result
