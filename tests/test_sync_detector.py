"""Tests d'intégration pour SyncDetector.

Ces tests nécessitent une base de données Lyrion accessible.
Ils sont automatiquement sautés si aucune BD n'est détectée.
"""

import pytest

from src.database import DatabaseManager, DatabaseConnectionError, SyncDetector


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
