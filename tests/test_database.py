"""Tests et exemples pour DatabaseManager."""

import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import DatabaseManager, DatabaseConnectionError, PlaycountQueries
from src.utils import setup_logger

logger = setup_logger('test', log_level='DEBUG')


def test_database_detection():
    """Test la détection automatique de la BD Lyrion."""
    print("\n" + "="*60)
    print("TEST 1 : Détection de la BD Lyrion")
    print("="*60)
    
    try:
        # Essayer de détecter automatiquement
        manager = DatabaseManager(auto_detect=True)
        print(f"✅ BD trouvée : {manager.db_path}")
        return manager
    except DatabaseConnectionError as e:
        print(f"❌ BD non trouvée : {e}")
        return None


def test_connection(db_path=None):
    """Test la connexion à la BD."""
    print("\n" + "="*60)
    print("TEST 2 : Connexion à la BD")
    print("="*60)
    
    try:
        manager = DatabaseManager(db_path=db_path, auto_detect=True)
        print(f"✓ Manager créé : {manager}")
        
        # Connexion en lecture/écriture
        manager.connect(readonly=False)
        print("✅ Connexion établie (lecture/écriture)")
        
        manager.close()
        return manager
    except DatabaseConnectionError as e:
        print(f"❌ Erreur de connexion : {e}")
        return None


def test_schema_validation(manager):
    """Test la validation du schéma."""
    print("\n" + "="*60)
    print("TEST 3 : Validation du schéma Lyrion")
    print("="*60)
    
    try:
        manager.connect(readonly=True)
        is_valid = manager.verify_schema()
        print(f"✅ Schéma valide : {is_valid}")
        manager.close()
    except DatabaseConnectionError as e:
        print(f"❌ Erreur de validation : {e}")


def test_table_stats(manager):
    """Test les statistiques des tables."""
    print("\n" + "="*60)
    print("TEST 4 : Statistiques des tables")
    print("="*60)
    
    try:
        manager.connect(readonly=True)
        stats = manager.get_table_stats()
        
        print("\nStatistiques des tables Lyrion :")
        print("-" * 60)
        for table_name, table_stats in stats.items():
            print(f"\n{table_name}:")
            for key, value in table_stats.items():
                if key == 'db_size_bytes':
                    print(f"  • {key}: {value:,} bytes")
                elif key == 'sources':
                    print(f"  • {key}: {', '.join(value)}")
                else:
                    print(f"  • {key}: {value:,}")
        
        manager.close()
    except DatabaseConnectionError as e:
        print(f"❌ Erreur lors de la lecture des stats : {e}")


def test_backup(manager):
    """Test la création de backup."""
    print("\n" + "="*60)
    print("TEST 5 : Création de backup")
    print("="*60)
    
    try:
        backup_path = manager.backup_database()
        print(f"✅ Backup créé : {backup_path}")
        
        # Vérifier que le fichier existe
        if Path(backup_path).exists():
            size = Path(backup_path).stat().st_size
            print(f"   Taille : {size:,} bytes")
        else:
            print("⚠️  Fichier de backup non trouvé")
    except DatabaseConnectionError as e:
        print(f"❌ Erreur lors du backup : {e}")


def test_readonly_connection(manager):
    """Test la connexion en lecture seule."""
    print("\n" + "="*60)
    print("TEST 6 : Connexion en lecture seule")
    print("="*60)
    
    try:
        manager.connect(readonly=True)
        print(f"✅ Connexion établie en lecture seule")
        print(f"   Mode : {manager.readonly}")
        
        # Essayer de lire les données
        with manager.cursor(commit=False) as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM tracks_persistent")
            count = cursor.fetchone()['count']
            print(f"   Nombre de tracks persistent : {count}")
        
        manager.close()
    except DatabaseConnectionError as e:
        print(f"❌ Erreur : {e}")


def test_context_manager(db_path=None):
    """Test l'utilisation de DatabaseManager comme context manager."""
    print("\n" + "="*60)
    print("TEST 7 : Utilisation en context manager")
    print("="*60)
    
    try:
        with DatabaseManager(db_path=db_path, auto_detect=True) as manager:
            manager.connect(readonly=True)
            print("✅ Connexion établie via context manager")
            
            # Lire les stats
            stats = manager.get_table_stats()
            print(f"   Tables lues : {list(stats.keys())}")
        
        print("✅ Connexion fermée automatiquement")
    except DatabaseConnectionError as e:
        print(f"❌ Erreur : {e}")


def test_cursor_context(manager):
    """Test l'utilisation du cursor comme context manager."""
    print("\n" + "="*60)
    print("TEST 8 : Utilisation du cursor en context manager")
    print("="*60)
    
    try:
        manager.connect(readonly=True)
        
        with manager.cursor(commit=False) as cursor:
            # Récupérer les sources alternatives
            cursor.execute("""
                SELECT DISTINCT source, COUNT(*) as count
                FROM alternativeplaycount
                GROUP BY source
            """)
            
            print("Sources alternatives trouvées :")
            for row in cursor.fetchall():
                print(f"  • {row[0]}: {row[1]} entries")
        
        manager.close()
    except DatabaseConnectionError as e:
        print(f"❌ Erreur : {e}")


def test_queries(manager):
    """Test les requêtes via PlaycountQueries."""
    print("\n" + "="*60)
    print("TEST 9 : PlaycountQueries")
    print("="*60)
    
    try:
        manager.connect(readonly=True)
        
        # Récupérer les stats
        stats = PlaycountQueries.get_urlmd5_stats(manager)
        
        print("\nStatistiques des playcounts :")
        print("-" * 60)
        for table_name, table_stats in stats.items():
            print(f"\n{table_name}:")
            for key, value in table_stats.items():
                print(f"  • {key}: {value:,}")
        
        manager.close()
    except Exception as e:
        print(f"❌ Erreur : {e}")


def main():
    """Lance tous les tests."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║  Tests de DatabaseManager pour Lyrion Playcount Sync  ║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    # Test 1 : Détection
    manager = test_database_detection()
    if not manager:
        print("\n❌ Impossible de continuer sans la BD Lyrion")
        return
    
    # Test 2 : Connexion
    test_connection(db_path=str(manager.db_path))
    
    # Test 3 : Validation du schéma
    test_schema_validation(manager)
    
    # Test 4 : Stats des tables
    test_table_stats(manager)
    
    # Test 5 : Backup
    test_backup(manager)
    
    # Test 6 : Lecture seule
    test_readonly_connection(manager)
    
    # Test 7 : Context manager
    test_context_manager(db_path=str(manager.db_path))
    
    # Test 8 : Cursor context
    test_cursor_context(manager)
    
    # Test 9 : Queries
    test_queries(manager)
    
    print("\n" + "="*60)
    print("✅ Tous les tests complétés!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
