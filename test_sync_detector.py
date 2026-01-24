"""Tests pour la classe SyncDetector."""

import sys
import logging
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import DatabaseManager, SyncDetector
from src.utils import setup_logger

logger = setup_logger(__name__)
logging.basicConfig(level=logging.DEBUG)


def test_find_missing_in_alternative():
    """Test : Trouver les morceaux manquants dans alternativeplaycount."""
    print("\n" + "="*70)
    print("TEST 1 : find_missing_in_alternative()")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        missing = SyncDetector.find_missing_in_alternative(manager)
        
        print(f"\n✅ Trouvé {len(missing)} morceaux manquants")
        
        # Afficher les 5 premiers
        if missing:
            print("\nPremiers morceaux manquants (top 5 par playcount) :")
            for i, track in enumerate(missing[:5], 1):
                orphaned_flag = " [ORPHELIN]" if track['url_orphaned'] else ""
                print(f"  {i}. {track['artist_name'][:20]:20} - {track['title'][:30]:30} "
                      f"({track['playcount']} plays){orphaned_flag}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def test_get_all_alternative_tracks():
    """Test : Récupérer tous les morceaux alternativeplaycount."""
    print("\n" + "="*70)
    print("TEST 2 : get_all_alternative_tracks()")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        tracks = SyncDetector.get_all_alternative_tracks(manager)
        
        print(f"\n✅ Récupéré {len(tracks)} morceaux de alternativeplaycount")
        
        # Stats
        total_playcount = sum(t['playcount'] for t in tracks)
        avg_playcount = total_playcount / len(tracks) if tracks else 0
        
        print(f"\nStatistiques :")
        print(f"  Total : {len(tracks)} morceaux")
        print(f"  Playcount total : {total_playcount}")
        print(f"  Playcount moyen : {avg_playcount:.2f}")
        
        # Afficher les 5 premiers
        if tracks:
            print("\nTop 5 morceaux (par playcount) :")
            for i, track in enumerate(tracks[:5], 1):
                source = f" [{track['source']}]" if track['source'] else ""
                print(f"  {i}. {track['artist_name'][:20]:20} - {track['title'][:30]:30} "
                      f"({track['playcount']} plays){source}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def test_get_track_details():
    """Test : Récupérer les détails d'un morceau spécifique."""
    print("\n" + "="*70)
    print("TEST 3 : get_track_details()")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        # Trouver un morceau manquant
        missing = SyncDetector.find_missing_in_alternative(manager)
        
        if not missing:
            print("\n⚠️  Pas de morceaux manquants pour tester")
            return True
        
        # Prendre le premier
        urlmd5 = missing[0]['urlmd5']
        
        # Récupérer détails
        details = SyncDetector.get_track_details(manager, urlmd5, "tracks_persistent")
        
        print(f"\n✅ Détails récupérés pour {urlmd5}")
        print(f"\nInformations :")
        print(f"  Artiste : {details['artist_name']}")
        print(f"  Titre : {details['title']}")
        print(f"  Album : {details['album_title']}")
        print(f"  URL : {details['url']}")
        print(f"  Playcount : {details['playcount']}")
        print(f"  Lastplayed : {details['lastplayed']}")
        print(f"  Rating : {details.get('rating', 'N/A')}")
        print(f"  Contributeurs : {details['contributor_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def test_count_missing():
    """Test : Compter les morceaux manquants."""
    print("\n" + "="*70)
    print("TEST 4 : count_missing()")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        count = SyncDetector.count_missing(manager)
        
        print(f"\n✅ Nombre de morceaux manquants : {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def test_get_sync_stats():
    """Test : Récupérer les stats de synchronisation."""
    print("\n" + "="*70)
    print("TEST 5 : get_sync_stats()")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        stats = SyncDetector.get_sync_stats(manager)
        
        print(f"\n✅ Stats de synchronisation :")
        print(f"  Total tracks_persistent : {stats['total_persistent']}")
        print(f"  Total alternativeplaycount : {stats['total_alternative']}")
        print(f"  Morceaux manquants : {stats['missing_in_alternative']}")
        print(f"  Morceaux orphelins : {stats['orphaned']}")
        print(f"  Ratio synchronisation : {stats['sync_ratio']}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def test_missing_with_orphaned_files():
    """Test : Vérifier la gestion des fichiers orphelins."""
    print("\n" + "="*70)
    print("TEST 6 : Gestion des fichiers orphelins")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        missing = SyncDetector.find_missing_in_alternative(manager)
        
        orphaned = [t for t in missing if t['url_orphaned']]
        with_metadata = [t for t in missing if not t['url_orphaned']]
        
        print(f"\n✅ Analyse des fichiers orphelins :")
        print(f"  Total manquants : {len(missing)}")
        print(f"  Orphelins (title=NULL) : {len(orphaned)}")
        print(f"  Avec métadonnées : {len(with_metadata)}")
        print(f"  Pourcentage orphelins : {(len(orphaned)/len(missing)*100):.1f}%" if missing else "N/A")
        
        if orphaned:
            print("\nExemples de fichiers orphelins :")
            for track in orphaned[:3]:
                print(f"  - {track['urlmd5']} (playcount={track['playcount']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def test_alternative_track_with_null_title():
    """Test : Morceaux alternativeplaycount avec title NULL."""
    print("\n" + "="*70)
    print("TEST 7 : Morceaux alternativeplaycount sans title")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        tracks = SyncDetector.get_all_alternative_tracks(manager)
        
        null_titles = [t for t in tracks if not t['title']]
        
        print(f"\n✅ Analyse des morceaux sans title :")
        print(f"  Total : {len(tracks)}")
        print(f"  Sans title : {len(null_titles)}")
        print(f"  Pourcentage : {(len(null_titles)/len(tracks)*100):.1f}%" if tracks else "N/A")
        
        if null_titles:
            print(f"\nPremiers morceaux sans title :")
            for track in null_titles[:5]:
                print(f"  - urlmd5={track['urlmd5']} source={track['source']} "
                      f"playcount={track['playcount']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def test_invalid_parameters():
    """Test : Gestion des paramètres invalides."""
    print("\n" + "="*70)
    print("TEST 8 : Gestion des paramètres invalides")
    print("="*70)
    
    try:
        manager = DatabaseManager(auto_detect=True)
        
        # Tester table invalide
        try:
            SyncDetector.get_track_details(manager, "abc123", "invalid_table")
            print("❌ Devrait avoir levé ValueError")
            return False
        except ValueError as e:
            print(f"✅ ValueError correctement levée : {e}")
        
        # Tester urlmd5 non existant
        result = SyncDetector.get_track_details(manager, "nonexistent" * 4, "tracks_persistent")
        if result is None:
            print("✅ Retour None pour urlmd5 inexistant")
        else:
            print(f"❌ Devrait retourner None, got {result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        logger.exception(e)
        return False


def main():
    """Lance tous les tests."""
    print("\n" + "#"*70)
    print("# TESTS DE LA CLASSE SyncDetector")
    print("#"*70)
    
    tests = [
        test_find_missing_in_alternative,
        test_get_all_alternative_tracks,
        test_get_track_details,
        test_count_missing,
        test_get_sync_stats,
        test_missing_with_orphaned_files,
        test_alternative_track_with_null_title,
        test_invalid_parameters,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except KeyboardInterrupt:
            print("\n\n⏸️  Tests interrompus")
            break
        except Exception as e:
            print(f"\n❌ Erreur non gérée : {e}")
            logger.exception(e)
            results.append(False)
    
    # Résumé
    print("\n" + "#"*70)
    print("# RÉSUMÉ")
    print("#"*70)
    passed = sum(results)
    total = len(results)
    print(f"\nTests réussis : {passed}/{total}")
    print(f"Taux de réussite : {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n✅ TOUS LES TESTS RÉUSSIS !")
    else:
        print(f"\n⚠️  {total - passed} test(s) échoué(s)")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
