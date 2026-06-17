"""Tests d'intégration pour DatabaseManager.

Ces tests nécessitent une base de données Lyrion accessible.
Ils sont automatiquement sautés si aucune BD n'est détectée.
"""

import pytest
from pathlib import Path

from lyrion_playcount_sync.database import DatabaseManager, DatabaseConnectionError


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


class TestConnection:

    def test_db_path_is_set(self, db_manager):
        assert db_manager.db_path is not None
        assert db_manager.db_path.exists()

    def test_connection_is_open(self, db_manager):
        assert db_manager.connection is not None

    def test_readonly_flag(self, db_manager):
        assert db_manager.readonly is True

    def test_reconnect_raises_warning(self, db_manager):
        # Appeler connect() une seconde fois ne doit pas lever d'exception
        db_manager.connect(readonly=True)


class TestSchemaValidation:

    def test_schema_is_valid(self, db_manager):
        assert db_manager.verify_schema() is True

    def test_required_tables_exist(self, db_manager):
        with db_manager.cursor(commit=False) as cursor:
            for table in ("tracks_persistent", "alternativeplaycount"):
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                assert cursor.fetchone() is not None, f"Table manquante : {table}"


class TestCursorContextManager:

    def test_read_query_executes(self, db_manager):
        with db_manager.cursor(commit=False) as cursor:
            cursor.execute("SELECT COUNT(*) FROM tracks_persistent")
            count = cursor.fetchone()[0]
        assert count >= 0

    def test_alternative_sources_readable(self, db_manager):
        with db_manager.cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT DISTINCT source FROM alternativeplaycount LIMIT 10"
            )
            rows = cursor.fetchall()
        assert isinstance(rows, list)


class TestBackup:

    def test_backup_creates_file(self, db_manager, tmp_path):
        db_manager.backup_dir = tmp_path
        backup_path = db_manager.backup_database()
        assert Path(backup_path).exists()
        assert Path(backup_path).stat().st_size > 0
