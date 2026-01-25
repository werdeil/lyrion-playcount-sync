#!/usr/bin/env python3
"""
Exemples d'utilisation de SyncOperations.

Démonstrations pratiques des opérations de synchronisation.
"""

from src.models import SyncOperation


def example_1_basic_update():
    """Exemple 1 : Mise à jour basique du playcount."""
    print("\n" + "="*60)
    print("EXEMPLE 1 : Mise à jour basique du playcount")
    print("="*60)
    
    print("""
# Importer SyncOperations
from src.database.operations import SyncOperations

# Initialiser
ops = SyncOperations('/path/to/database.db')

# Mettre à jour (UPDATE)
affected = ops.update_alternative_playcount(
    urlmd5='abc123',
    new_playcount=150
)
print(f'Rows affected: {affected}')  # 1

# Insérer si absent (INSERT)
affected = ops.update_alternative_playcount(
    urlmd5='xyz789',
    new_playcount=50
)
print(f'Rows affected: {affected}')  # 1
""")
    
    print("""
Comportement :
  - Si la ligne existe → UPDATE playcount
  - Si la ligne n'existe pas → INSERT avec source='manual_sync'
  - Toujours met à jour lastplayed si fourni
""")


def example_2_delete():
    """Exemple 2 : Supprimer un morceau."""
    print("\n" + "="*60)
    print("EXEMPLE 2 : Supprimer un morceau de tracks_persistent")
    print("="*60)
    
    print("""
# Supprimer
affected = ops.delete_from_tracks_persistent(
    urlmd5='missing_123'
)
print(f'Deleted: {affected}')  # 1

Log automatique :
  INFO: Deleting track from persistent: missing_123 (Queen - Bohemian Rhapsody)
  INFO: Deleted track from tracks_persistent
""")


def example_3_sync_copy():
    """Exemple 3 : Synchronisation COPY."""
    print("\n" + "="*60)
    print("EXEMPLE 3 : Synchronisation COPY")
    print("="*60)
    
    print("""
# Créer l'opération
operation = SyncOperation(
    missing_urlmd5='missing_001',
    selected_alternative_urlmd5='alt_001',
    action='COPY',
    new_playcount=42
)

# Exécuter
success = ops.sync_track(operation)

if success:
    print("✅ Synchronization successful")
else:
    print("❌ Synchronization failed")

Workflow :
  1. BEGIN TRANSACTION
  2. GET old value from alternativeplaycount
  3. UPDATE alternativeplaycount SET playcount=42
  4. DELETE FROM tracks_persistent WHERE urlmd5='missing_001'
  5. COMMIT (ou ROLLBACK si erreur)
  6. LOG dans sync_log

Result :
  - alternativeplaycount.playcount = 42
  - tracks_persistent.missing_001 = DELETED
""")


def example_4_sync_merge():
    """Exemple 4 : Synchronisation MERGE."""
    print("\n" + "="*60)
    print("EXEMPLE 4 : Synchronisation MERGE (fusion)")
    print("="*60)
    
    print("""
# Situation
alternativeplaycount[alt_001].playcount = 30
tracks_persistent[missing_001].playcount = 50

# Créer l'opération MERGE
operation = SyncOperation(
    missing_urlmd5='missing_001',
    selected_alternative_urlmd5='alt_001',
    action='MERGE',
    new_playcount=50  # playcount du morceau manquant
)

# Exécuter
success = ops.sync_track(operation)

Result :
  - alternativeplaycount[alt_001].playcount = 30 + 50 = 80
  - tracks_persistent[missing_001] = DELETED
  - Log : "MERGE: alt_001 → 30 + 50 = 80"
""")


def example_5_bulk_sync():
    """Exemple 5 : Synchronisation en masse (batch)."""
    print("\n" + "="*60)
    print("EXEMPLE 5 : Synchronisation en masse (batch)")
    print("="*60)
    
    print("""
# Créer une liste d'opérations
operations = [
    SyncOperation(
        missing_urlmd5='missing_001',
        selected_alternative_urlmd5='alt_001',
        action='COPY',
        new_playcount=42
    ),
    SyncOperation(
        missing_urlmd5='missing_002',
        selected_alternative_urlmd5='alt_002',
        action='MERGE',
        new_playcount=60
    ),
    SyncOperation(
        missing_urlmd5='missing_003',
        selected_alternative_urlmd5='alt_003',
        action='COPY',
        new_playcount=30
    ),
]

# Callback de progression
def progress_callback(current, total):
    print(f"Progress: {current}/{total} ({100*current//total}%)")

# Exécuter le batch
result = ops.bulk_sync(
    operations,
    progress_callback=progress_callback,
    stop_on_failure=False  # continuer même en cas d'erreur
)

# Résultats
print(f"Success: {result['success']}")      # 3
print(f"Failed: {result['failed']}")        # 0
print(f"Total: {result['total']}")          # 3
print(f"Errors: {result['errors']}")        # []

Output :
  Progress: 1/3 (33%)
  Progress: 2/3 (66%)
  Progress: 3/3 (100%)
  Success: 3
  Failed: 0
  Total: 3
""")


def example_6_error_handling():
    """Exemple 6 : Gestion des erreurs."""
    print("\n" + "="*60)
    print("EXEMPLE 6 : Gestion des erreurs et rollback")
    print("="*60)
    
    print("""
# Situation d'erreur
operation = SyncOperation(
    missing_urlmd5='missing_999',  # N'existe pas
    selected_alternative_urlmd5='alt_nonexistent',
    action='COPY',
    new_playcount=100
)

# Exécuter
success = ops.sync_track(operation)

if not success:
    print("❌ Operation failed")
    
    # La transaction a été automatiquement ROLLBACK
    # Aucune modification n'a été faite à la base de données

Comportement :
  - Exception durant transaction
  - ROLLBACK automatique
  - LOG : "❌ Sync failed: operation_id - error_message"
  - LOG dans sync_log : status='failed', error_message=...
  - Retourne False
""")


def example_7_history_and_stats():
    """Exemple 7 : Historique et statistiques."""
    print("\n" + "="*60)
    print("EXEMPLE 7 : Consulter l'historique et les statistiques")
    print("="*60)
    
    print("""
# Récupérer l'historique
history = ops.get_sync_history(limit=50)

for entry in history:
    print(f"Operation: {entry['operation_id']}")
    print(f"  Status: {entry['status']}")  # 'success' ou 'failed'
    print(f"  Action: {entry['action']}")  # 'COPY' ou 'MERGE'
    print(f"  Old playcount: {entry['old_playcount']}")
    print(f"  New playcount: {entry['new_playcount']}")
    print(f"  Timestamp: {entry['timestamp_iso']}")
    if entry['error_message']:
        print(f"  Error: {entry['error_message']}")

Output :
  Operation: 12345678-1234-5678-1234-567812345678
    Status: success
    Action: COPY
    Old playcount: 30
    New playcount: 42
    Timestamp: 2026-01-24T12:34:56
  ...

# Récupérer les statistiques
stats = ops.get_sync_stats(hours=24)

for action, data in stats['actions'].items():
    print(f"{action}:")
    print(f"  Total: {data['total']}")
    print(f"  Success: {data['success']}")
    print(f"  Failed: {data['failed']}")
    print(f"  Success rate: {data['success_rate']}")

Output :
  COPY:
    Total: 150
    Success: 145
    Failed: 5
    Success rate: 96.7%
  MERGE:
    Total: 50
    Success: 50
    Failed: 0
    Success rate: 100.0%
""")


def example_8_cleanup():
    """Exemple 8 : Nettoyage et maintenance."""
    print("\n" + "="*60)
    print("EXEMPLE 8 : Nettoyage de l'historique et backup")
    print("="*60)
    
    print("""
# Supprimer les logs plus vieux que 30 jours
deleted = ops.clear_sync_log(older_than_days=30)
print(f"Deleted {deleted} old log entries")

# Créer une sauvegarde
success = ops.backup_database('/path/to/backup.db')

if success:
    print("✅ Backup created successfully")
    
# Exemple complet :
from datetime import datetime

# Backup
backup_name = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
ops.backup_database(f'/backups/{backup_name}')

# Nettoyer les logs anciens
ops.clear_sync_log(older_than_days=30)

# Afficher les stats
stats = ops.get_sync_stats(hours=24)
print(f"Last 24 hours: {sum(d['total'] for d in stats['actions'].values())} ops")
""")


def example_9_complete_workflow():
    """Exemple 9 : Workflow complet."""
    print("\n" + "="*60)
    print("EXEMPLE 9 : Workflow complet (détection → matching → sync)")
    print("="*60)
    
    print("""
from src.database.queries import SyncDetector
from src.matching.fuzzy_matcher import TrackMatcher
from src.database.operations import SyncOperations

# 1. Détection
detector = SyncDetector('/path/to/db')
missing_tracks = detector.find_missing_in_alternative()
print(f"Found {len(missing_tracks)} missing tracks")

# 2. Matching
matcher = TrackMatcher()
ops = SyncOperations('/path/to/db')

operations = []
for missing in missing_tracks:
    suggestions = matcher.find_best_matches(missing)
    
    if suggestions and suggestions[0][1] >= 80:  # Score >= 80%
        best_match, score = suggestions[0]
        op = SyncOperation(
            missing_urlmd5=missing.urlmd5,
            selected_alternative_urlmd5=best_match.urlmd5,
            action='COPY',
            new_playcount=missing.playcount
        )
        operations.append(op)

print(f"Created {len(operations)} sync operations")

# 3. Synchronisation (batch)
def show_progress(current, total):
    pct = 100 * current // total
    print(f"[{'='*(pct//5)}{' '*(20-pct//5)}] {pct}%")

result = ops.bulk_sync(
    operations,
    progress_callback=show_progress,
    stop_on_failure=False
)

print(f"Result: {result['success']} success, {result['failed']} failed")

# 4. Backup et cleanup
ops.backup_database(f'backups/db_{datetime.now().isoformat()}.db')
ops.clear_sync_log(older_than_days=7)
""")


if __name__ == "__main__":
    print("\n🎵 EXEMPLES - SyncOperations\n")
    
    example_1_basic_update()
    example_2_delete()
    example_3_sync_copy()
    example_4_sync_merge()
    example_5_bulk_sync()
    example_6_error_handling()
    example_7_history_and_stats()
    example_8_cleanup()
    example_9_complete_workflow()
    
    print("\n" + "="*60)
    print("✅ Tous les exemples présentés avec succès")
    print("="*60)
    print("\n💡 Pour tester :")
    print("   python3 test_sync_operations.py\n")
