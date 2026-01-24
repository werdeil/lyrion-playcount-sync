"""
Exemples d'utilisation de DatabaseManager pour Lyrion Playcount Sync.

Ce fichier montre comment utiliser la classe DatabaseManager pour :
- Se connecter à la BD Lyrion
- Vérifier le schéma
- Créer des backups
- Lire et modifier les playcounts
- Synchroniser entre deux tables
"""

from pathlib import Path
from src.database import DatabaseManager, DatabaseConnectionError, PlaycountQueries
from src.utils import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# EXEMPLE 1 : Connexion simple avec détection automatique
# ============================================================================

def exemple_connexion_simple():
    """Connexion simple avec détection automatique du chemin."""
    
    try:
        # Créer un manager et détecter automatiquement le chemin
        manager = DatabaseManager()
        print(f"✓ BD trouvée : {manager.db_path}")
        
        # Établir la connexion en lecture seule
        manager.connect(readonly=True)
        print(f"✓ Connexion établie")
        
        # Fermer la connexion
        manager.close()
        
    except DatabaseConnectionError as e:
        print(f"✗ Erreur : {e}")


# ============================================================================
# EXEMPLE 2 : Utiliser DatabaseManager en context manager
# ============================================================================

def exemple_context_manager():
    """Utiliser DatabaseManager avec un context manager (recommandé)."""
    
    try:
        # Automatiquement connecté et fermé
        with DatabaseManager() as manager:
            manager.connect(readonly=True)
            
            # Vérifier le schéma
            manager.verify_schema()
            print("✓ Schéma valide")
            
            # Récupérer les stats
            stats = manager.get_table_stats()
            for table_name, table_stats in stats.items():
                print(f"  {table_name}: {table_stats['rows']} lignes")
    
    except DatabaseConnectionError as e:
        print(f"✗ Erreur : {e}")


# ============================================================================
# EXEMPLE 3 : Créer une sauvegarde avant modification
# ============================================================================

def exemple_backup_avant_modification():
    """Créer une sauvegarde avant de modifier les données."""
    
    try:
        with DatabaseManager() as manager:
            # Créer une sauvegarde
            backup_path = manager.backup_database()
            print(f"✓ Backup créé : {backup_path}")
            
            # Établir la connexion en lecture/écriture
            manager.connect(readonly=False)
            
            # Maintenant vous pouvez modifier les données
            # (voir exemple suivant)
            
    except DatabaseConnectionError as e:
        print(f"✗ Erreur : {e}")


# ============================================================================
# EXEMPLE 4 : Lire les playcounts
# ============================================================================

def exemple_lire_playcounts():
    """Lire les playcounts des deux tables."""
    
    try:
        with DatabaseManager() as manager:
            manager.connect(readonly=True)
            
            # Lire les statistiques
            stats = PlaycountQueries.get_urlmd5_stats(manager)
            
            print("\nStatistiques - tracks_persistent:")
            persistent = stats['tracks_persistent']
            print(f"  Total : {persistent['total']}")
            print(f"  Avec plays : {persistent['with_plays']}")
            print(f"  Moyenne : {persistent['avg_playcount']}")
            print(f"  Maximum : {persistent['max_playcount']}")
            
            print("\nStatistiques - alternativeplaycount:")
            alternative = stats['alternativeplaycount']
            print(f"  Total : {alternative['total']}")
            print(f"  Avec plays : {alternative['with_plays']}")
            print(f"  Moyenne : {alternative['avg_playcount']}")
            print(f"  Maximum : {alternative['max_playcount']}")
            
    except Exception as e:
        print(f"✗ Erreur : {e}")


# ============================================================================
# EXEMPLE 5 : Utiliser un curseur pour des requêtes personnalisées
# ============================================================================

def exemple_requete_personnalisee():
    """Exécuter des requêtes personnalisées."""
    
    try:
        with DatabaseManager() as manager:
            manager.connect(readonly=True)
            
            # Utiliser le cursor context manager
            with manager.cursor(commit=False) as cursor:
                # Récupérer les sources alternatives
                cursor.execute("""
                    SELECT DISTINCT source, COUNT(*) as count
                    FROM alternativeplaycount
                    GROUP BY source
                    ORDER BY count DESC
                """)
                
                print("\nSources alternatives :")
                for row in cursor.fetchall():
                    print(f"  {row[0]}: {row[1]} entries")
                
                # Récupérer les top 10 tracks les plus joués
                cursor.execute("""
                    SELECT 
                        t.artist,
                        t.title,
                        tp.playcount
                    FROM tracks_persistent tp
                    JOIN tracks t ON tp.urlmd5 = t.urlmd5
                    ORDER BY tp.playcount DESC
                    LIMIT 10
                """)
                
                print("\nTop 10 tracks les plus joués :")
                for row in cursor.fetchall():
                    print(f"  {row[0]} - {row[1]}: {row[2]} plays")
                
    except Exception as e:
        print(f"✗ Erreur : {e}")


# ============================================================================
# EXEMPLE 6 : Utiliser une transaction pour une synchronisation
# ============================================================================

def exemple_transaction_sync():
    """Utiliser une transaction pour une synchronisation sécurisée."""
    
    try:
        with DatabaseManager() as manager:
            manager.connect(readonly=False)
            
            # Créer une sauvegarde d'abord
            backup = manager.backup_database()
            print(f"✓ Backup créé : {backup}")
            
            # Utiliser une transaction pour la synchronisation
            with manager.transaction() as cursor:
                # Exemple : synchroniser des playcounts
                # (ceci est un exemple simplifié)
                
                cursor.execute("""
                    UPDATE tracks_persistent
                    SET playcount = (
                        SELECT playcount 
                        FROM alternativeplaycount
                        WHERE alternativeplaycount.urlmd5 = tracks_persistent.urlmd5
                    )
                    WHERE urlmd5 IN (
                        SELECT DISTINCT urlmd5 FROM alternativeplaycount
                    )
                """)
                
                print(f"✓ {cursor.rowcount} tracks mises à jour")
                # Automatiquement commité à la sortie
            
            print("✓ Synchronisation complétée avec succès")
            
    except DatabaseConnectionError as e:
        print(f"✗ Erreur : {e}")


# ============================================================================
# EXEMPLE 7 : Configuration avec un chemin personnalisé
# ============================================================================

def exemple_chemin_personnalise(db_path: str):
    """Utiliser un chemin personnalisé pour la BD."""
    
    try:
        # Spécifier explicitement le chemin
        manager = DatabaseManager(db_path=db_path, auto_detect=False)
        print(f"✓ BD chargée : {manager.db_path}")
        
        manager.connect(readonly=True)
        manager.verify_schema()
        print("✓ Schéma valide")
        
        manager.close()
        
    except DatabaseConnectionError as e:
        print(f"✗ Erreur : {e}")


# ============================================================================
# EXEMPLE 8 : Gestion d'erreurs complète
# ============================================================================

def exemple_gestion_erreurs():
    """Exemple complet avec gestion d'erreurs."""
    
    try:
        # Créer le manager
        manager = DatabaseManager()
        
    except DatabaseConnectionError as e:
        print(f"✗ Erreur lors de la création du manager : {e}")
        return
    
    try:
        # Établir la connexion
        manager.connect(readonly=True)
        
    except DatabaseConnectionError as e:
        print(f"✗ Erreur lors de la connexion : {e}")
        return
    
    try:
        # Vérifier le schéma
        manager.verify_schema()
        print("✓ Schéma valide")
        
    except DatabaseConnectionError as e:
        print(f"✗ Erreur de schéma : {e}")
    
    try:
        # Récupérer les stats
        stats = manager.get_table_stats()
        print(f"✓ {len(stats)} tables trouvées")
        
    except DatabaseConnectionError as e:
        print(f"✗ Erreur lors de la lecture des stats : {e}")
    
    finally:
        # Toujours fermer la connexion
        manager.close()
        print("✓ Connexion fermée")


# ============================================================================
# EXEMPLE 9 : Script de synchronisation complet
# ============================================================================

def exemple_script_sync_complet():
    """Script complet de synchronisation de playcounts."""
    
    print("\n" + "="*60)
    print("Script de synchronisation - Lyrion Playcount Sync")
    print("="*60 + "\n")
    
    try:
        # 1. Initialiser
        print("1. Initialisation...")
        with DatabaseManager() as manager:
            print(f"   BD : {manager.db_path}")
            
            # 2. Créer un backup
            print("\n2. Création du backup...")
            backup = manager.backup_database()
            print(f"   ✓ Backup : {backup}")
            
            # 3. Connexion et validation
            print("\n3. Connexion et validation...")
            manager.connect(readonly=False)
            manager.verify_schema()
            print("   ✓ Schéma valide")
            
            # 4. Récupérer les stats
            print("\n4. Analyse des données...")
            stats = manager.get_table_stats()
            persistent_rows = stats['tracks_persistent']['rows']
            alternative_rows = stats['alternativeplaycount']['rows']
            print(f"   tracks_persistent : {persistent_rows} lignes")
            print(f"   alternativeplaycount : {alternative_rows} lignes")
            
            # 5. Récupérer les stats de playcounts
            print("\n5. Statistiques des playcounts...")
            pc_stats = PlaycountQueries.get_urlmd5_stats(manager)
            persistent = pc_stats['tracks_persistent']
            alternative = pc_stats['alternativeplaycount']
            
            print(f"   tracks_persistent : {persistent['with_plays']} avec plays")
            print(f"   alternativeplaycount : {alternative['with_plays']} avec plays")
            
            # 6. Synchronisation (exemple)
            print("\n6. Synchronisation...")
            with manager.transaction() as cursor:
                # Exemple simplifié
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM tracks_persistent
                    WHERE playcount > 0
                """)
                count = cursor.fetchone()['count']
                print(f"   ✓ {count} tracks à synchroniser")
            
            print("\n✓ Synchronisation complétée avec succès!")
        
    except DatabaseConnectionError as e:
        print(f"\n✗ Erreur : {e}")


# ============================================================================
# Point d'entrée
# ============================================================================

if __name__ == '__main__':
    print("Exemples d'utilisation de DatabaseManager")
    print("="*60)
    
    # Décommenter les exemples à exécuter :
    
    # exemple_connexion_simple()
    # exemple_context_manager()
    # exemple_lire_playcounts()
    # exemple_requete_personnalisee()
    exemple_script_sync_complet()
