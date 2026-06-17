"""Tests d'intégration pour SyncDetector.

Ces tests nécessitent une base de données Lyrion accessible.
Ils sont automatiquement sautés si aucune BD n'est détectée.
"""

import pytest

from lyrion_playcount_sync.database import DatabaseManager, DatabaseConnectionError, SyncDetector


@pytest.fixture(scope="module")
def db_manager():
    """Connexion à la BD Lyrion locale. Skip si indisponible."""
    try:
        manager = DatabaseManager(auto_detect=True)
        manager.connect(readonly=True)
        yield manager
        manager.close()
    except (DatabaseConnectionError, Exception) as e:
        pytest.skip(f"BD Lyrion non accessible : {e}")


class TestFindMissingInAlternative:

    def test_returns_list(self, db_manager):
        result = SyncDetector.find_missing_in_alternative(db_manager)
        assert isinstance(result, list)

    def test_each_item_has_required_keys(self, db_manager):
        result = SyncDetector.find_missing_in_alternative(db_manager)
        for item in result[:10]:
            for key in ("urlmd5", "playcount", "lastplayed", "title",
                        "url", "album_title", "artist_name", "url_orphaned"):
                assert key in item, f"Clé manquante : {key}"

    def test_playcount_non_negative(self, db_manager):
        result = SyncDetector.find_missing_in_alternative(db_manager)
        for item in result:
            assert item["playcount"] >= 0

    def test_no_item_in_alternativeplaycount(self, db_manager):
        missing = SyncDetector.find_missing_in_alternative(db_manager)
        if not missing:
            pytest.skip("Aucune désynchronisation dans cette BD")
        urlmd5_set = {item["urlmd5"] for item in missing}
        with db_manager.cursor(commit=False) as cursor:
            cursor.execute("SELECT urlmd5 FROM alternativeplaycount")
            alt_set = {row[0] for row in cursor.fetchall()}
        overlap = urlmd5_set & alt_set
        assert len(overlap) == 0, f"Des urlmd5 se retrouvent dans les deux tables : {overlap}"


class TestGetAllAlternativeTracks:

    def test_returns_list(self, db_manager):
        result = SyncDetector.get_all_alternative_tracks(db_manager)
        assert isinstance(result, list)

    def test_each_item_has_required_keys(self, db_manager):
        result = SyncDetector.get_all_alternative_tracks(db_manager)
        for item in result[:10]:
            for key in ("urlmd5", "playcount", "lastplayed", "source",
                        "title", "url", "album_title", "artist_name"):
                assert key in item, f"Clé manquante : {key}"

    def test_playcount_non_negative(self, db_manager):
        result = SyncDetector.get_all_alternative_tracks(db_manager)
        for item in result:
            assert item["playcount"] >= 0


class TestCountZeroedPersistent:

    def test_returns_non_negative_int(self, db_manager):
        count = SyncDetector.count_zeroed_persistent(db_manager)
        assert isinstance(count, int)
        assert count >= 0


@pytest.fixture
def writable_db(tmp_path):
    """Petite BD inscriptible avec le schéma minimal des deux tables."""
    import sqlite3
    db_path = tmp_path / "backfill.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE tracks_persistent (
            urlmd5 TEXT PRIMARY KEY, playCount INTEGER, lastPlayed INTEGER
        );
        CREATE TABLE alternativeplaycount (
            urlmd5 TEXT PRIMARY KEY, playCount INTEGER, lastPlayed REAL
        );
        -- a : tp à 0, ap>0  → doit être rattrapé
        INSERT INTO tracks_persistent VALUES ('a', 0, 0);
        INSERT INTO alternativeplaycount VALUES ('a', 3, 1700000000.5);
        -- b : tp>ap (dérive normale) → intact
        INSERT INTO tracks_persistent VALUES ('b', 5, 111);
        INSERT INTO alternativeplaycount VALUES ('b', 2, 222.0);
        -- c : tp à 0 mais ap=0 aussi → intact
        INSERT INTO tracks_persistent VALUES ('c', 0, 0);
        INSERT INTO alternativeplaycount VALUES ('c', 0, 0.0);
        -- d : présent seulement dans persistent → intact
        INSERT INTO tracks_persistent VALUES ('d', 0, 0);
    """)
    conn.commit()
    conn.close()

    manager = DatabaseManager(str(db_path))
    manager.connect()
    yield manager
    manager.close()


class TestBackfillZeroedPersistent:

    def test_count_before(self, writable_db):
        assert SyncDetector.count_zeroed_persistent(writable_db) == 1

    def test_backfill_copies_value_and_date(self, writable_db):
        updated = SyncDetector.backfill_zeroed_persistent(writable_db)
        assert updated == 1
        with writable_db.cursor(commit=False) as c:
            c.execute("SELECT playCount, lastPlayed FROM tracks_persistent WHERE urlmd5='a'")
            pc, last = c.fetchone()
        assert pc == 3
        assert last == 1700000000  # flottant tronqué en entier

    def test_other_rows_untouched(self, writable_db):
        SyncDetector.backfill_zeroed_persistent(writable_db)
        with writable_db.cursor(commit=False) as c:
            c.execute("SELECT playCount FROM tracks_persistent WHERE urlmd5='b'")
            assert c.fetchone()[0] == 5  # dérive normale conservée
            c.execute("SELECT playCount FROM tracks_persistent WHERE urlmd5='c'")
            assert c.fetchone()[0] == 0  # ap=0 → pas touché
            c.execute("SELECT playCount FROM tracks_persistent WHERE urlmd5='d'")
            assert c.fetchone()[0] == 0  # absent de alternativeplaycount

    def test_idempotent(self, writable_db):
        assert SyncDetector.backfill_zeroed_persistent(writable_db) == 1
        assert SyncDetector.backfill_zeroed_persistent(writable_db) == 0
        assert SyncDetector.count_zeroed_persistent(writable_db) == 0
