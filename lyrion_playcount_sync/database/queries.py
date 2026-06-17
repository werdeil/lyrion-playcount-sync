"""Requêtes de base de données pour les playcounts."""

import re
from urllib.parse import unquote
from pathlib import PurePosixPath
from typing import List, Dict
from lyrion_playcount_sync.utils import setup_logger

logger = setup_logger(__name__)


def _parse_url_metadata(url: str) -> Dict[str, str]:
    """Extrait title/album/artist depuis une URL de fichier Lyrion.

    Exemple : file:///media/.../Artist/Album/01 Track.m4a
    → title="01 Track", album="Album", artist="Artist"
    """
    if not url:
        return {"title": "", "album_title": "", "artist_name": ""}
    decoded = unquote(url.replace("file://", ""))
    p = PurePosixPath(decoded)
    title = re.sub(r"^\d+\s*[-–—.]?\s*", "", p.stem).strip() or p.stem
    album = p.parent.name if p.parent != p.parent.parent else ""
    artist = p.parent.parent.name if p.parent.parent != p.parent.parent.parent else ""
    return {"title": title, "album_title": album, "artist_name": artist}


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
                        tp.playCount,
                        tp.lastPlayed,
                        tp.rating,
                        tp.url
                    FROM tracks_persistent tp
                    LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
                    WHERE ap.urlmd5 IS NULL
                    ORDER BY tp.playCount DESC
                """)

                for row in cursor.fetchall():
                    url = row[4] or ""
                    meta = _parse_url_metadata(url)
                    missing.append({
                        'urlmd5': row[0],
                        'playcount': row[1] or 0,
                        'lastplayed': row[2] or 0,
                        'rating': row[3] or 0,
                        'title': meta['title'] or "[ORPHELIN]",
                        'url': url,
                        'album_title': meta['album_title'],
                        'artist_name': meta['artist_name'],
                        'url_orphaned': not url,
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
                        ap.playCount,
                        ap.lastPlayed,
                        ap.remote,
                        ap.url
                    FROM alternativeplaycount ap
                    ORDER BY ap.playCount DESC
                """)

                for row in cursor.fetchall():
                    url = row[4] or ""
                    meta = _parse_url_metadata(url)
                    source = "remote" if row[3] else "local"
                    tracks.append({
                        'urlmd5': row[0],
                        'playcount': row[1] or 0,
                        'lastplayed': row[2] or 0,
                        'source': source,
                        'title': meta['title'],
                        'url': url,
                        'album_title': meta['album_title'],
                        'artist_name': meta['artist_name'],
                    })
            
            logger.info(f"Récupéré {len(tracks)} morceaux de alternativeplaycount")
            return tracks
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des tracks alternative : {e}")
            raise

    @staticmethod
    def count_zeroed_persistent(db_manager) -> int:
        """
        Compte les pistes présentes dans les deux tables dont
        tracks_persistent.playCount vaut 0 alors que alternativeplaycount > 0.

        Ce sont des pistes dont le compteur interne Lyrion a été laissé à zéro
        alors qu'un playcount existe côté alternativeplaycount (typiquement
        laissées incohérentes par une synchro qui n'a pas répercuté la valeur).

        Args:
            db_manager: Instance de DatabaseManager

        Returns:
            Nombre de pistes concernées

        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            with db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM tracks_persistent tp
                    JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
                    WHERE IFNULL(tp.playCount, 0) = 0
                      AND IFNULL(ap.playCount, 0) > 0
                """)
                count = cursor.fetchone()[0] or 0
                logger.debug(f"Pistes à playCount=0 à rattraper : {count}")
                return count

        except Exception as e:
            logger.error(f"Erreur lors du comptage des playcounts à zéro : {e}")
            raise

    @staticmethod
    def backfill_zeroed_persistent(db_manager) -> int:
        """
        Recopie playCount/lastPlayed depuis alternativeplaycount vers
        tracks_persistent pour les pistes dont tracks_persistent.playCount = 0
        et alternativeplaycount.playCount > 0.

        Ne touche qu'à ces lignes : les écarts dans l'autre sens et la dérive
        normale (deux compteurs non nuls) sont laissés intacts. lastPlayed est
        converti en entier car alternativeplaycount le stocke en flottant.

        Args:
            db_manager: Instance de DatabaseManager

        Returns:
            Nombre de lignes mises à jour

        Raises:
            Exception: En cas d'erreur de requête
        """
        try:
            with db_manager.transaction() as cursor:
                cursor.execute("""
                    UPDATE tracks_persistent
                    SET playCount = (
                            SELECT ap.playCount FROM alternativeplaycount ap
                            WHERE ap.urlmd5 = tracks_persistent.urlmd5
                        ),
                        lastPlayed = (
                            SELECT CAST(ap.lastPlayed AS INTEGER) FROM alternativeplaycount ap
                            WHERE ap.urlmd5 = tracks_persistent.urlmd5
                        )
                    WHERE IFNULL(playCount, 0) = 0
                      AND urlmd5 IN (
                            SELECT urlmd5 FROM alternativeplaycount
                            WHERE IFNULL(playCount, 0) > 0
                        )
                """)
                updated = cursor.rowcount

            logger.info(f"Backfill tracks_persistent : {updated} ligne(s) mise(s) à jour")
            return updated

        except Exception as e:
            logger.error(f"Erreur lors du backfill des playcounts à zéro : {e}")
            raise
