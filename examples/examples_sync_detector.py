"""Exemples pratiques d'utilisation de SyncDetector."""

from src.database import DatabaseManager, SyncDetector, PlaycountQueries
from src.utils import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# EXEMPLE 1 : Diagnostic rapide de l'état de synchronisation
# ============================================================================

def exemple_diagnostic_rapide():
    """Voir rapidement l'état de synchronisation."""
    print("\n" + "="*70)
    print("EXEMPLE 1 : Diagnostic rapide")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    # Récupérer les stats
    stats = SyncDetector.get_sync_stats(manager)
    
    print(f"\n📊 État de synchronisation :")
    print(f"  Morceaux persistent: {stats['total_persistent']}")
    print(f"  Morceaux alternative: {stats['total_alternative']}")
    print(f"  Manquants: {stats['missing_in_alternative']}")
    print(f"  Orphelins: {stats['orphaned']}")
    print(f"  Ratio sync: {stats['sync_ratio']}%")


# ============================================================================
# EXEMPLE 2 : Identifier les morceaux à synchroniser (top 10)
# ============================================================================

def exemple_top_morceaux_manquants():
    """Afficher les 10 morceaux manquants les plus écoutés."""
    print("\n" + "="*70)
    print("EXEMPLE 2 : Top morceaux manquants")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    # Trouver les manquants
    missing = SyncDetector.find_missing_in_alternative(manager)
    
    print(f"\n🎵 Top 10 des {len(missing)} morceaux manquants :")
    print(f"{'#':2} {'Artiste':20} {'Titre':30} {'Plays':6} {'Orphelin':9}")
    print("-" * 70)
    
    for i, track in enumerate(missing[:10], 1):
        orphaned_flag = "✓ OUI" if track['url_orphaned'] else "✗ NON"
        print(f"{i:2} {track['artist_name'][:19]:20} {track['title'][:29]:30} "
              f"{track['playcount']:6} {orphaned_flag:9}")


# ============================================================================
# EXEMPLE 3 : Analyser la qualité des métadonnées
# ============================================================================

def exemple_analyse_metadonnees():
    """Analyser la qualité des métadonnées."""
    print("\n" + "="*70)
    print("EXEMPLE 3 : Analyse des métadonnées")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    missing = SyncDetector.find_missing_in_alternative(manager)
    
    # Compter les orphelins
    orphaned = [t for t in missing if t['url_orphaned']]
    with_metadata = [t for t in missing if not t['url_orphaned']]
    
    print(f"\n📝 Qualité des métadonnées :")
    print(f"  Total manquants: {len(missing)}")
    print(f"  Avec métadonnées: {len(with_metadata)} ({len(with_metadata)/len(missing)*100:.1f}%)")
    print(f"  Orphelins: {len(orphaned)} ({len(orphaned)/len(missing)*100:.1f}%)")
    
    if with_metadata:
        # Avec album ?
        with_album = [t for t in with_metadata if t['album_title']]
        print(f"  Avec album: {len(with_album)} ({len(with_album)/len(with_metadata)*100:.1f}%)")


# ============================================================================
# EXEMPLE 4 : Comparer les sources alternativeplaycount
# ============================================================================

def exemple_sources_alternative():
    """Analyser les sources alternativeplaycount."""
    print("\n" + "="*70)
    print("EXEMPLE 4 : Sources alternativeplaycount")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    tracks = SyncDetector.get_all_alternative_tracks(manager)
    
    # Compter par source
    sources = {}
    for track in tracks:
        source = track['source'] or "[SANS SOURCE]"
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\n📊 Distribution par source :")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(tracks)) * 100
        print(f"  {source:30}: {count:6} ({pct:5.1f}%)")


# ============================================================================
# EXEMPLE 5 : Filtrer les morceaux avant synchronisation
# ============================================================================

def exemple_filtrer_avant_sync():
    """Préparer une liste de morceaux à synchroniser en filtrant."""
    print("\n" + "="*70)
    print("EXEMPLE 5 : Filtrer avant synchronisation")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    missing = SyncDetector.find_missing_in_alternative(manager)
    
    # Filtre 1 : Exclure orphelins
    no_orphans = [t for t in missing if not t['url_orphaned']]
    print(f"\n1️⃣ Exclure orphelins: {len(no_orphans)}/{len(missing)}")
    
    # Filtre 2 : Playcount minimum de 5
    min_5_plays = [t for t in no_orphans if t['playcount'] >= 5]
    print(f"2️⃣ Playcount >= 5: {len(min_5_plays)}/{len(no_orphans)}")
    
    # Filtre 3 : Avec album
    with_album = [t for t in min_5_plays if t['album_title']]
    print(f"3️⃣ Avec album: {len(with_album)}/{len(min_5_plays)}")
    
    # Filtre 4 : Avec artiste
    with_artist = [t for t in with_album if t['artist_name']]
    print(f"4️⃣ Avec artiste: {len(with_artist)}/{len(with_album)}")
    
    print(f"\n✅ Final: {len(with_artist)} morceaux prêts à synchroniser")


# ============================================================================
# EXEMPLE 6 : Synchronisation sélective
# ============================================================================

def exemple_sync_selective():
    """Synchroniser uniquement les morceaux avec métadonnées valides."""
    print("\n" + "="*70)
    print("EXEMPLE 6 : Synchronisation sélective")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    # Récupérer les manquants
    missing = SyncDetector.find_missing_in_alternative(manager)
    
    # Filtrer : pas d'orphelins, playcount > 0
    to_sync = [t for t in missing 
               if not t['url_orphaned'] and t['playcount'] > 0]
    
    print(f"\n📋 Synchronisation sélective :")
    print(f"  À synchroniser: {len(to_sync)} morceaux")
    
    # Simulation (ne pas vraiment synchroniser dans cet exemple)
    print(f"\n🔄 Morceaux à synchroniser (top 5):")
    for track in to_sync[:5]:
        print(f"  - {track['artist_name'][:20]} - {track['title'][:30]} "
              f"({track['playcount']} plays)")


# ============================================================================
# EXEMPLE 7 : Détails complets d'un morceau
# ============================================================================

def exemple_details_morceau():
    """Récupérer les détails complets d'un morceau."""
    print("\n" + "="*70)
    print("EXEMPLE 7 : Détails complets d'un morceau")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    # Trouver un morceau manquant
    missing = SyncDetector.find_missing_in_alternative(manager)
    
    if not missing:
        print("Pas de morceaux manquants")
        return
    
    # Prendre le premier
    track = missing[0]
    urlmd5 = track['urlmd5']
    
    # Récupérer détails complets
    details = SyncDetector.get_track_details(
        manager, 
        urlmd5, 
        "tracks_persistent"
    )
    
    print(f"\n📋 Détails du morceau :")
    print(f"  URL MD5: {details['urlmd5']}")
    print(f"  Titre: {details['title']}")
    print(f"  Artiste: {details['artist_name']}")
    print(f"  Album: {details['album_title']}")
    print(f"  URL: {details['url']}")
    print(f"  Track ID: {details['track_id']}")
    print(f"  Playcount: {details['playcount']}")
    print(f"  Lastplayed: {details['lastplayed']}")
    print(f"  Rating: {details.get('rating', 'N/A')}")
    print(f"  Contributeurs: {details['contributor_count']}")


# ============================================================================
# EXEMPLE 8 : Rapport de désynchronisation détaillé
# ============================================================================

def exemple_rapport_detail():
    """Générer un rapport détaillé de désynchronisation."""
    print("\n" + "="*70)
    print("EXEMPLE 8 : Rapport de désynchronisation")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    # Stats globales
    stats = SyncDetector.get_sync_stats(manager)
    missing = SyncDetector.find_missing_in_alternative(manager)
    
    # Analyser
    orphaned = [t for t in missing if t['url_orphaned']]
    valid = [t for t in missing if not t['url_orphaned']]
    
    total_plays = sum(t['playcount'] for t in valid)
    avg_plays = total_plays / len(valid) if valid else 0
    
    print(f"\n📊 RAPPORT DE DÉSYNCHRONISATION")
    print(f"\n1. RÉSUMÉ GLOBAL")
    print(f"  ├─ Total tracks_persistent: {stats['total_persistent']}")
    print(f"  ├─ Total alternativeplaycount: {stats['total_alternative']}")
    print(f"  ├─ Ratio sync: {stats['sync_ratio']}%")
    print(f"  └─ Écart: {stats['total_persistent'] - stats['total_alternative']}")
    
    print(f"\n2. DÉSYNCHRONISÉS")
    print(f"  ├─ Total manquants: {len(missing)}")
    print(f"  ├─ Avec métadonnées: {len(valid)}")
    print(f"  └─ Orphelins: {len(orphaned)}")
    
    print(f"\n3. STATISTICS (Morceaux valides)")
    print(f"  ├─ Total plays: {total_plays}")
    print(f"  ├─ Plays moyen: {avg_plays:.1f}")
    print(f"  └─ Max plays: {max((t['playcount'] for t in valid), default=0)}")
    
    print(f"\n4. DISTRIBUTIONE")
    top_10_plays = sum(t['playcount'] for t in valid[:10])
    print(f"  ├─ Top 10 = {top_10_plays} plays ({(top_10_plays/total_plays*100):.1f}%)")
    print(f"  └─ Autres = {total_plays - top_10_plays} plays")


# ============================================================================
# EXEMPLE 9 : Vérification avant/après synchronisation
# ============================================================================

def exemple_verification_sync():
    """Vérifier l'état avant et après synchronisation."""
    print("\n" + "="*70)
    print("EXEMPLE 9 : Vérification sync avant/après")
    print("="*70)
    
    manager = DatabaseManager(auto_detect=True)
    
    # État AVANT
    before = SyncDetector.get_sync_stats(manager)
    print(f"\n📊 AVANT synchronisation :")
    print(f"  Morceaux manquants: {before['missing_in_alternative']}")
    print(f"  Ratio sync: {before['sync_ratio']}%")
    
    # Simulation : compter les à synchroniser
    missing = SyncDetector.find_missing_in_alternative(manager)
    valid = [t for t in missing if not t['url_orphaned']]
    
    print(f"\n🔄 SYNCHRONISATION")
    print(f"  À synchroniser: {len(valid)} morceaux")
    print(f"  (Dans un vrai script, on ferait le PlaycountQueries.sync_playcount)")
    
    # État APRÈS (simulation)
    print(f"\n📊 APRÈS synchronisation (prédiction) :")
    after_missing = before['missing_in_alternative'] - len(valid)
    after_ratio = ((before['total_alternative'] + len(valid)) / before['total_persistent']) * 100
    print(f"  Morceaux manquants: {after_missing}")
    print(f"  Ratio sync: {int(after_ratio)}%")
    print(f"  Améliorations: {len(valid)} morceaux")


# ============================================================================
# Main - Lancer tous les exemples
# ============================================================================

def main():
    """Lancer tous les exemples."""
    print("\n" + "#"*70)
    print("# EXEMPLES D'UTILISATION - SyncDetector")
    print("#"*70)
    
    exemples = [
        exemple_diagnostic_rapide,
        exemple_top_morceaux_manquants,
        exemple_analyse_metadonnees,
        exemple_sources_alternative,
        exemple_filtrer_avant_sync,
        exemple_sync_selective,
        exemple_details_morceau,
        exemple_rapport_detail,
        exemple_verification_sync,
    ]
    
    for exemple in exemples:
        try:
            exemple()
        except KeyboardInterrupt:
            print("\n\n⏸️ Exemples interrompus")
            break
        except Exception as e:
            print(f"\n❌ Erreur dans {exemple.__name__}: {e}")
            logger.exception(e)
    
    print("\n" + "#"*70)
    print("# Exemples terminés")
    print("#"*70)


if __name__ == "__main__":
    main()
