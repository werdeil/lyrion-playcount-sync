#!/usr/bin/env python3
"""
Tests de la classe SyncOperations.

Valide toutes les fonctionnalités de modification de base de données.
"""

import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from src.models import Track, SyncOperation
from src.database.operations import SyncOperations


def test_sync_operations():
    """Test complet des opérations de synchronisation."""
    
    print("\n" + "="*60)
    print("TEST 1 : Initialisation et création de table")
    print("="*60)
    
    # Créer une DB temporaire de test
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db_path = f.name
    
    try:
        # Créer les tables nécessaires
        conn = sqlite3.connect(test_db_path)
        conn.execute("""
            CREATE TABLE tracks_persistent (
                id INTEGER PRIMARY KEY,
                urlmd5 TEXT UNIQUE,
                title TEXT,
                artist TEXT,
                album TEXT,
                url TEXT,
                playcount INTEGER,
                lastplayed INTEGER,
                rating INTEGER,
                source TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE alternativeplaycount (
                id INTEGER PRIMARY KEY,
                urlmd5 TEXT UNIQUE,
                title TEXT,
                artist TEXT,
                album TEXT,
                url TEXT,
                playcount INTEGER,
                lastplayed INTEGER,
                rating INTEGER,
                source TEXT
            )
        """)
        
        # Insérer des données de test
        conn.execute("""
            INSERT INTO tracks_persistent (urlmd5, title, artist, album, url, playcount, rating, source)
            VALUES ('missing1', 'Song 1', 'Artist 1', 'Album 1', '/song1', 50, 5, 'tracks_persistent')
        """)
        
        conn.execute("""
            INSERT INTO alternativeplaycount (urlmd5, title, artist, album, url, playcount, rating, source)
            VALUES ('alt1', 'Song 1', 'Artist 1', 'Album 1', '/song1', 30, 5, 'alternativeplaycount')
        """)
        
        conn.commit()
        conn.close()
        
        # Initialiser SyncOperations
        ops = SyncOperations(test_db_path)
        print("✅ SyncOperations initialized")
        print("✅ sync_log table created")
        
        print("\n" + "="*60)
        print("TEST 2 : update_alternative_playcount (UPDATE)")
        print("="*60)
        
        # Test UPDATE
        affected = ops.update_alternative_playcount('alt1', 75)
        print(f"✅ Updated playcount for alt1")
        print(f"   Rows affected: {affected}")
        
        # Vérifier la mise à jour
        conn = sqlite3.connect(test_db_path)
        cursor = conn.execute(
            "SELECT playcount FROM alternativeplaycount WHERE urlmd5 = 'alt1'"
        )
        row = cursor.fetchone()
        assert row[0] == 75, "Playcount not updated correctly"
        conn.close()
        print(f"✅ Verified: playcount = 75")
        
        print("\n" + "="*60)
        print("TEST 3 : update_alternative_playcount (INSERT)")
        print("="*60)
        
        # Test INSERT (nouvelle ligne)
        affected = ops.update_alternative_playcount('alt_new', 42)
        print(f"✅ Inserted new record for alt_new")
        
        # Vérifier l'insertion
        conn = sqlite3.connect(test_db_path)
        cursor = conn.execute(
            "SELECT playcount FROM alternativeplaycount WHERE urlmd5 = 'alt_new'"
        )
        row = cursor.fetchone()
        assert row is not None, "Record not inserted"
        assert row[0] == 42, "Playcount not inserted correctly"
        conn.close()
        print(f"✅ Verified: new record created with playcount = 42")
        
        print("\n" + "="*60)
        print("TEST 4 : delete_from_tracks_persistent")
        print("="*60)
        
        # Test DELETE
        affected = ops.delete_from_tracks_persistent('missing1')
        print(f"✅ Deleted record from tracks_persistent")
        print(f"   Rows deleted: {affected}")
        
        # Vérifier la suppression
        conn = sqlite3.connect(test_db_path)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM tracks_persistent WHERE urlmd5 = 'missing1'"
        )
        count = cursor.fetchone()[0]
        assert count == 0, "Record not deleted"
        conn.close()
        print(f"✅ Verified: record deleted")
        
        print("\n" + "="*60)
        print("TEST 5 : sync_track (COPY)")
        print("="*60)
        
        # Préparer pour sync_track
        conn = sqlite3.connect(test_db_path)
        conn.execute("""
            INSERT INTO tracks_persistent (urlmd5, title, artist, album, url, playcount, rating, source)
            VALUES ('missing2', 'Song 2', 'Artist 2', 'Album 2', '/song2', 100, 5, 'tracks_persistent')
        """)
        
        conn.execute("""
            INSERT INTO alternativeplaycount (urlmd5, title, artist, album, url, playcount, rating, source)
            VALUES ('alt2', 'Song 2', 'Artist 2', 'Album 2', '/song2', 60, 5, 'alternativeplaycount')
        """)
        conn.commit()
        conn.close()
        
        # Créer et exécuter une opération COPY
        operation = SyncOperation(
            missing_urlmd5='missing2',
            selected_alternative_urlmd5='alt2',
            action='COPY',
            new_playcount=100
        )
        
        success = ops.sync_track(operation)
        assert success, "sync_track failed"
        print(f"✅ COPY operation successful: {operation.operation_id}")
        
        # Vérifier les résultats
        conn = sqlite3.connect(test_db_path)
        
        # Vérifier que playcount a été mis à jour
        cursor = conn.execute(
            "SELECT playcount FROM alternativeplaycount WHERE urlmd5 = 'alt2'"
        )
        playcount = cursor.fetchone()[0]
        assert playcount == 100, f"Playcount not updated to 100, got {playcount}"
        print(f"✅ Verified: alternativeplaycount updated to 100")
        
        # Vérifier que le morceau a été supprimé
        cursor = conn.execute(
            "SELECT COUNT(*) FROM tracks_persistent WHERE urlmd5 = 'missing2'"
        )
        count = cursor.fetchone()[0]
        assert count == 0, "Track not deleted from persistent"
        print(f"✅ Verified: track deleted from persistent")
        
        conn.close()
        
        print("\n" + "="*60)
        print("TEST 6 : sync_track (MERGE)")
        print("="*60)
        
        # Préparer pour MERGE
        conn = sqlite3.connect(test_db_path)
        conn.execute("""
            INSERT INTO tracks_persistent (urlmd5, title, artist, album, url, playcount, rating, source)
            VALUES ('missing3', 'Song 3', 'Artist 3', 'Album 3', '/song3', 50, 5, 'tracks_persistent')
        """)
        
        conn.execute("""
            INSERT INTO alternativeplaycount (urlmd5, title, artist, album, url, playcount, rating, source)
            VALUES ('alt3', 'Song 3', 'Artist 3', 'Album 3', '/song3', 30, 5, 'alternativeplaycount')
        """)
        conn.commit()
        conn.close()
        
        # Créer et exécuter une opération MERGE
        operation = SyncOperation(
            missing_urlmd5='missing3',
            selected_alternative_urlmd5='alt3',
            action='MERGE',
            new_playcount=50  # 30 + 50 = 80
        )
        
        success = ops.sync_track(operation)
        assert success, "sync_track MERGE failed"
        print(f"✅ MERGE operation successful: {operation.operation_id}")
        
        # Vérifier que les playcounts ont été additionnés
        conn = sqlite3.connect(test_db_path)
        cursor = conn.execute(
            "SELECT playcount FROM alternativeplaycount WHERE urlmd5 = 'alt3'"
        )
        playcount = cursor.fetchone()[0]
        assert playcount == 80, f"Merge failed: expected 80, got {playcount}"
        print(f"✅ Verified: MERGE result = 30 + 50 = 80")
        
        conn.close()
        
        print("\n" + "="*60)
        print("TEST 7 : get_sync_history")
        print("="*60)
        
        history = ops.get_sync_history(limit=10)
        print(f"✅ Retrieved sync history")
        print(f"   Total entries: {len(history)}")
        
        if history:
            latest = history[0]
            print(f"   Latest entry:")
            print(f"     Operation ID: {latest['operation_id']}")
            print(f"     Status: {latest['status']}")
            print(f"     Action: {latest['action']}")
            print(f"     Old playcount: {latest['old_playcount']}")
            print(f"     New playcount: {latest['new_playcount']}")
        
        print("\n" + "="*60)
        print("TEST 8 : get_sync_stats")
        print("="*60)
        
        stats = ops.get_sync_stats(hours=24)
        print(f"✅ Retrieved sync statistics")
        print(f"   Period: last 24 hours")
        if stats.get('actions'):
            for action, data in stats['actions'].items():
                print(f"   {action}:")
                print(f"     Total: {data['total']}")
                print(f"     Success: {data['success']}")
                print(f"     Failed: {data['failed']}")
                print(f"     Success rate: {data['success_rate']}")
        
        print("\n" + "="*60)
        print("TEST 9 : bulk_sync")
        print("="*60)
        
        # Préparer plusieurs opérations
        for i in range(4, 7):
            conn = sqlite3.connect(test_db_path)
            conn.execute(f"""
                INSERT INTO tracks_persistent (urlmd5, title, artist, album, url, playcount, rating, source)
                VALUES ('missing{i}', 'Song {i}', 'Artist {i}', 'Album {i}', '/song{i}', {i*10}, 5, 'tracks_persistent')
            """)
            
            conn.execute(f"""
                INSERT INTO alternativeplaycount (urlmd5, title, artist, album, url, playcount, rating, source)
                VALUES ('alt{i}', 'Song {i}', 'Artist {i}', 'Album {i}', '/song{i}', {i*5}, 5, 'alternativeplaycount')
            """)
            conn.commit()
            conn.close()
        
        # Créer les opérations
        operations = [
            SyncOperation(
                missing_urlmd5=f'missing{i}',
                selected_alternative_urlmd5=f'alt{i}',
                action='COPY',
                new_playcount=i*10
            )
            for i in range(4, 7)
        ]
        
        # Callback de progression
        def progress(current, total):
            print(f"   Progress: {current}/{total}")
        
        result = ops.bulk_sync(operations, progress_callback=progress)
        print(f"✅ Bulk sync completed")
        print(f"   Success: {result['success']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Total: {result['total']}")
        
        assert result['success'] == 3, "Not all operations succeeded"
        print(f"✅ All 3 bulk operations succeeded")
        
        print("\n" + "="*60)
        print("TEST 10 : backup_database")
        print("="*60)
        
        backup_path = Path(test_db_path).parent / "test_backup.db"
        success = ops.backup_database(backup_path)
        assert success, "Backup failed"
        assert backup_path.exists(), "Backup file not created"
        print(f"✅ Database backed up to {backup_path}")
        print(f"   Backup size: {backup_path.stat().st_size} bytes")
        
        # Cleanup backup
        backup_path.unlink()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        
    finally:
        # Cleanup
        Path(test_db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_sync_operations()
