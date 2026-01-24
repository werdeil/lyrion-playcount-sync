"""Requêtes de base de données pour les playcounts."""

from typing import List, Tuple, Dict, Optional
from src.models import Track
from src.utils import setup_logger

logger = setup_logger(__name__)


class PlaycountQueries:
    """Gère les requêtes de playcounts Lyrion."""
    
    @staticmethod
    def get_tracks_from_persistent(db_manager) -> List[Track]:
        """
        Récupère les tracks de la table tracks_persistent.
        
        Args:
            db_manager: Instance de DatabaseManager
            
        Returns:
            Liste des tracks
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            with db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT t.id, t.title, t.artist, t.album, tp.playcount
                    FROM tracks_persistent tp
                    JOIN tracks t ON tp.urlmd5 = t.urlmd5
                    WHERE tp.playcount > 0
                    ORDER BY t.artist, t.title
                """)
                
                tracks = []
                for row in cursor.fetchall():
                    tracks.append(Track(
                        track_id=row[0],
                        title=row[1] or "",
                        artist=row[2] or "",
                        album=row[3] or "",
                        playcount=row[4] or 0
                    ))
                
                logger.info(f"Récupéré {len(tracks)} tracks de tracks_persistent")
                return tracks
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des tracks persistent : {e}")
            raise
    
    @staticmethod
    def get_tracks_from_alternative(db_manager) -> List[Track]:
        """
        Récupère les tracks de la table alternativeplaycount.
        
        Args:
            db_manager: Instance de DatabaseManager
            
        Returns:
            Liste des tracks
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            with db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT t.id, t.title, t.artist, t.album, apc.playcount
                    FROM alternativeplaycount apc
                    JOIN tracks t ON apc.urlmd5 = t.urlmd5
                    WHERE apc.playcount > 0
                    ORDER BY t.artist, t.title
                """)
                
                tracks = []
                for row in cursor.fetchall():
                    tracks.append(Track(
                        track_id=row[0],
                        title=row[1] or "",
                        artist=row[2] or "",
                        album=row[3] or "",
                        playcount=row[4] or 0
                    ))
                
                logger.info(f"Récupéré {len(tracks)} tracks de alternativeplaycount")
                return tracks
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des tracks alternative : {e}")
            raise
    
    @staticmethod
    def get_track_by_urlmd5(
        db_manager,
        urlmd5: str,
        table: str = "tracks_persistent"
    ) -> Optional[Track]:
        """
        Récupère un track par son urlmd5.
        
        Args:
            db_manager: Instance de DatabaseManager
            urlmd5: Hash MD5 du URL
            table: Table source (tracks_persistent ou alternativeplaycount)
            
        Returns:
            Track ou None
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            with db_manager.cursor(commit=False) as cursor:
                if table == "tracks_persistent":
                    query = """
                        SELECT t.id, t.title, t.artist, t.album, tp.playcount
                        FROM tracks_persistent tp
                        JOIN tracks t ON tp.urlmd5 = t.urlmd5
                        WHERE tp.urlmd5 = ?
                    """
                else:
                    query = """
                        SELECT t.id, t.title, t.artist, t.album, apc.playcount
                        FROM alternativeplaycount apc
                        JOIN tracks t ON apc.urlmd5 = t.urlmd5
                        WHERE apc.urlmd5 = ?
                    """
                
                cursor.execute(query, (urlmd5,))
                row = cursor.fetchone()
                
                if row:
                    return Track(
                        track_id=row[0],
                        title=row[1] or "",
                        artist=row[2] or "",
                        album=row[3] or "",
                        playcount=row[4] or 0
                    )
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du track : {e}")
            raise
    
    @staticmethod
    def update_playcount(
        db_manager,
        table: str,
        urlmd5: str,
        playcount: int
    ) -> bool:
        """
        Met à jour le playcount d'un track.
        
        Args:
            db_manager: Instance de DatabaseManager
            table: Table destination (tracks_persistent ou alternativeplaycount)
            urlmd5: Hash MD5 du URL
            playcount: Nouveau playcount
            
        Returns:
            True si succès, False sinon
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        if table not in ["tracks_persistent", "alternativeplaycount"]:
            raise ValueError(f"Table invalide : {table}")
        
        try:
            with db_manager.cursor(commit=True) as cursor:
                cursor.execute(f"""
                    UPDATE {table}
                    SET playcount = ?
                    WHERE urlmd5 = ?
                """, (playcount, urlmd5))
                
                logger.debug(f"Playcount mis à jour : {table}.{urlmd5} = {playcount}")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour : {e}")
            raise
    
    @staticmethod
    def update_lastplayed(
        db_manager,
        table: str,
        urlmd5: str,
        timestamp: int
    ) -> bool:
        """
        Met à jour la date de dernière lecture.
        
        Args:
            db_manager: Instance de DatabaseManager
            table: Table destination
            urlmd5: Hash MD5 du URL
            timestamp: Timestamp Unix
            
        Returns:
            True si succès
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        if table not in ["tracks_persistent", "alternativeplaycount"]:
            raise ValueError(f"Table invalide : {table}")
        
        try:
            with db_manager.cursor(commit=True) as cursor:
                cursor.execute(f"""
                    UPDATE {table}
                    SET lastplayed = ?
                    WHERE urlmd5 = ?
                """, (timestamp, urlmd5))
                
                logger.debug(f"Lastplayed mis à jour : {table}.{urlmd5}")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour : {e}")
            raise
    
    @staticmethod
    def get_urlmd5_stats(db_manager) -> Dict[str, Dict[str, int]]:
        """
        Récupère les statistiques de playcounts par source.
        
        Args:
            db_manager: Instance de DatabaseManager
            
        Returns:
            Dictionnaire avec stats
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            stats = {}
            
            with db_manager.cursor(commit=False) as cursor:
                # Stats tracks_persistent
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN playcount > 0 THEN 1 ELSE 0 END) as with_plays,
                        AVG(playcount) as avg_playcount,
                        MAX(playcount) as max_playcount
                    FROM tracks_persistent
                """)
                row = cursor.fetchone()
                stats['tracks_persistent'] = {
                    'total': row[0] or 0,
                    'with_plays': row[1] or 0,
                    'avg_playcount': int(row[2]) if row[2] else 0,
                    'max_playcount': row[3] or 0
                }
                
                # Stats alternativeplaycount
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN playcount > 0 THEN 1 ELSE 0 END) as with_plays,
                        AVG(playcount) as avg_playcount,
                        MAX(playcount) as max_playcount
                    FROM alternativeplaycount
                """)
                row = cursor.fetchone()
                stats['alternativeplaycount'] = {
                    'total': row[0] or 0,
                    'with_plays': row[1] or 0,
                    'avg_playcount': int(row[2]) if row[2] else 0,
                    'max_playcount': row[3] or 0
                }
            
            logger.debug(f"Stats récupérées : {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des stats : {e}")
            raise
    
    @staticmethod
    def sync_playcount(
        db_manager,
        from_table: str,
        to_table: str,
        urlmd5: str,
        playcount: int
    ) -> bool:
        """
        Synchronise les playcounts entre deux tables.
        
        Args:
            db_manager: Instance de DatabaseManager
            from_table: Table source
            to_table: Table destination
            urlmd5: Hash MD5 du URL
            playcount: Playcount à synchroniser
            
        Returns:
            True si succès
            
        Raises:
            Exception: En cas d'erreur
        """
        try:
            # Vérifier que l'urlmd5 existe dans la table destination
            with db_manager.cursor(commit=False) as cursor:
                cursor.execute(f"SELECT playcount FROM {to_table} WHERE urlmd5 = ?", (urlmd5,))
                existing = cursor.fetchone()
                
                if not existing:
                    logger.warning(f"urlmd5 {urlmd5} non trouvé dans {to_table}")
                    return False
            
            # Mettre à jour le playcount
            return PlaycountQueries.update_playcount(
                db_manager, to_table, urlmd5, playcount
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation : {e}")
            raise


class SyncDetector:
    """Détecte les désynchronisations entre tracks_persistent et alternativeplaycount."""
    
    @staticmethod
    def find_missing_in_alternative(db_manager) -> List[Dict]:
        """
        Trouve les urlmd5 présents dans tracks_persistent mais PAS dans alternativeplaycount.
        
        Retourne tous les morceaux avec métadonnées complètes incluant:
        - Infos de playcount (playcount, lastplayed, rating)
        - Métadonnées du track (title, url)
        - Métadonnées de l'album
        - Artiste principal
        
        Args:
            db_manager: Instance de DatabaseManager
            
        Returns:
            Liste de dictionnaires avec structure:
            {
                'urlmd5': str,
                'playcount': int,
                'lastplayed': int,
                'rating': int,
                'title': str,
                'url': str,
                'album_title': str,
                'artist_name': str,
                'url_orphaned': bool  # True si track.title est NULL
            }
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            missing = []
            
            with db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        tp.urlmd5,
                        tp.playcount,
                        tp.lastplayed,
                        tp.rating,
                        t.title,
                        t.url,
                        a.title as album_title,
                        c.name as artist_name
                    FROM tracks_persistent tp
                    LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
                    LEFT JOIN tracks t ON tp.urlmd5 = t.urlmd5
                    LEFT JOIN albums a ON t.album = a.id
                    LEFT JOIN contributor_track ct ON t.id = ct.track 
                        AND ct.role IN (1, 5, 6)
                    LEFT JOIN contributors c ON ct.contributor = c.id
                    WHERE ap.urlmd5 IS NULL
                    ORDER BY tp.playcount DESC
                """)
                
                for row in cursor.fetchall():
                    missing.append({
                        'urlmd5': row[0],
                        'playcount': row[1] or 0,
                        'lastplayed': row[2] or 0,
                        'rating': row[3] or 0,
                        'title': row[4] or "[ORPHELIN]",
                        'url': row[5] or "",
                        'album_title': row[6] or "",
                        'artist_name': row[7] or "",
                        'url_orphaned': row[4] is None  # Flag si title est NULL
                    })
            
            logger.info(f"Trouvé {len(missing)} morceaux manquants dans alternativeplaycount")
            return missing
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des morceaux manquants : {e}")
            raise
    
    @staticmethod
    def get_all_alternative_tracks(db_manager) -> List[Dict]:
        """
        Récupère TOUS les morceaux de alternativeplaycount avec métadonnées.
        
        Utilisé pour le matching fuzzy contre les morceaux de tracks_persistent.
        
        Args:
            db_manager: Instance de DatabaseManager
            
        Returns:
            Liste de dictionnaires avec structure:
            {
                'urlmd5': str,
                'playcount': int,
                'lastplayed': int,
                'source': str,
                'title': str,
                'url': str,
                'album_title': str,
                'artist_name': str
            }
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            tracks = []
            
            with db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        ap.urlmd5,
                        ap.playcount,
                        ap.lastplayed,
                        ap.source,
                        t.title,
                        t.url,
                        a.title as album_title,
                        c.name as artist_name
                    FROM alternativeplaycount ap
                    LEFT JOIN tracks t ON ap.urlmd5 = t.urlmd5
                    LEFT JOIN albums a ON t.album = a.id
                    LEFT JOIN contributor_track ct ON t.id = ct.track 
                        AND ct.role IN (1, 5, 6)
                    LEFT JOIN contributors c ON ct.contributor = c.id
                    ORDER BY ap.playcount DESC
                """)
                
                for row in cursor.fetchall():
                    tracks.append({
                        'urlmd5': row[0],
                        'playcount': row[1] or 0,
                        'lastplayed': row[2] or 0,
                        'source': row[3] or "",
                        'title': row[4] or "",
                        'url': row[5] or "",
                        'album_title': row[6] or "",
                        'artist_name': row[7] or ""
                    })
            
            logger.info(f"Récupéré {len(tracks)} morceaux de alternativeplaycount")
            return tracks
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des tracks alternative : {e}")
            raise
    
    @staticmethod
    def get_track_details(
        db_manager,
        urlmd5: str,
        source_table: str = "tracks_persistent"
    ) -> Optional[Dict]:
        """
        Récupère les détails complets d'un morceau spécifique.
        
        Args:
            db_manager: Instance de DatabaseManager
            urlmd5: Hash MD5 du URL
            source_table: Table source (tracks_persistent ou alternativeplaycount)
            
        Returns:
            Dictionnaire avec tous les détails du morceau ou None
            
        Raises:
            ValueError: Si source_table invalide
            Exception: En cas d'erreur de requête
        """
        if source_table not in ["tracks_persistent", "alternativeplaycount"]:
            raise ValueError(f"Table invalide : {source_table}")
        
        try:
            with db_manager.cursor(commit=False) as cursor:
                if source_table == "tracks_persistent":
                    cursor.execute("""
                        SELECT 
                            tp.urlmd5,
                            tp.playcount,
                            tp.lastplayed,
                            tp.rating,
                            t.id,
                            t.title,
                            t.url,
                            a.title as album_title,
                            c.name as artist_name,
                            COUNT(ct.id) as contributor_count
                        FROM tracks_persistent tp
                        LEFT JOIN tracks t ON tp.urlmd5 = t.urlmd5
                        LEFT JOIN albums a ON t.album = a.id
                        LEFT JOIN contributor_track ct ON t.id = ct.track
                        LEFT JOIN contributors c ON ct.contributor = c.id
                        WHERE tp.urlmd5 = ?
                        GROUP BY tp.urlmd5
                    """, (urlmd5,))
                else:  # alternativeplaycount
                    cursor.execute("""
                        SELECT 
                            ap.urlmd5,
                            ap.playcount,
                            ap.lastplayed,
                            ap.source,
                            t.id,
                            t.title,
                            t.url,
                            a.title as album_title,
                            c.name as artist_name,
                            COUNT(ct.id) as contributor_count
                        FROM alternativeplaycount ap
                        LEFT JOIN tracks t ON ap.urlmd5 = t.urlmd5
                        LEFT JOIN albums a ON t.album = a.id
                        LEFT JOIN contributor_track ct ON t.id = ct.track
                        LEFT JOIN contributors c ON ct.contributor = c.id
                        WHERE ap.urlmd5 = ?
                        GROUP BY ap.urlmd5
                    """, (urlmd5,))
                
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                if source_table == "tracks_persistent":
                    return {
                        'urlmd5': row[0],
                        'playcount': row[1] or 0,
                        'lastplayed': row[2] or 0,
                        'rating': row[3] or 0,
                        'track_id': row[4],
                        'title': row[5] or "[ORPHELIN]",
                        'url': row[6] or "",
                        'album_title': row[7] or "",
                        'artist_name': row[8] or "",
                        'contributor_count': row[9] or 0,
                        'source': 'tracks_persistent'
                    }
                else:
                    return {
                        'urlmd5': row[0],
                        'playcount': row[1] or 0,
                        'lastplayed': row[2] or 0,
                        'source': row[3] or "",
                        'track_id': row[4],
                        'title': row[5] or "",
                        'url': row[6] or "",
                        'album_title': row[7] or "",
                        'artist_name': row[8] or "",
                        'contributor_count': row[9] or 0
                    }
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des détails du track : {e}")
            raise
    
    @staticmethod
    def count_missing(db_manager) -> int:
        """
        Compte le nombre de morceaux désynchronisés.
        
        Retourne le nombre de urlmd5 présents dans tracks_persistent
        mais absents de alternativeplaycount.
        
        Args:
            db_manager: Instance de DatabaseManager
            
        Returns:
            Nombre de morceaux manquants
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            with db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT COUNT(DISTINCT tp.urlmd5)
                    FROM tracks_persistent tp
                    LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
                    WHERE ap.urlmd5 IS NULL
                """)
                
                count = cursor.fetchone()[0] or 0
                logger.debug(f"Morceaux manquants détectés : {count}")
                return count
                
        except Exception as e:
            logger.error(f"Erreur lors du comptage des morceaux manquants : {e}")
            raise
    
    @staticmethod
    def get_sync_stats(db_manager) -> Dict[str, int]:
        """
        Récupère les statistiques de synchronisation.
        
        Args:
            db_manager: Instance de DatabaseManager
            
        Returns:
            Dictionnaire avec:
            - total_persistent: Total morceaux dans tracks_persistent
            - total_alternative: Total morceaux dans alternativeplaycount
            - missing_in_alternative: Désynchronisés
            - orphaned: Morceaux sans fichier (title NULL)
            - sync_ratio: Pourcentage synchronisé (0-100)
            
        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            with db_manager.cursor(commit=False) as cursor:
                # Total persistent
                cursor.execute("SELECT COUNT(*) FROM tracks_persistent")
                total_persistent = cursor.fetchone()[0] or 0
                
                # Total alternative
                cursor.execute("SELECT COUNT(*) FROM alternativeplaycount")
                total_alternative = cursor.fetchone()[0] or 0
                
                # Manquants
                cursor.execute("""
                    SELECT COUNT(DISTINCT tp.urlmd5)
                    FROM tracks_persistent tp
                    LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
                    WHERE ap.urlmd5 IS NULL
                """)
                missing = cursor.fetchone()[0] or 0
                
                # Orphelins (pas de track.title)
                cursor.execute("""
                    SELECT COUNT(DISTINCT tp.urlmd5)
                    FROM tracks_persistent tp
                    LEFT JOIN tracks t ON tp.urlmd5 = t.urlmd5
                    WHERE t.title IS NULL
                """)
                orphaned = cursor.fetchone()[0] or 0
                
                # Ratio de synchronisation
                sync_ratio = 0
                if total_persistent > 0:
                    sync_ratio = int((total_alternative / total_persistent) * 100)
                
                stats = {
                    'total_persistent': total_persistent,
                    'total_alternative': total_alternative,
                    'missing_in_alternative': missing,
                    'orphaned': orphaned,
                    'sync_ratio': sync_ratio
                }
                
                logger.debug(f"Stats sync : {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats de sync : {e}")
            raise
