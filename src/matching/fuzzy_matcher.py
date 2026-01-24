"""Module de matching basé sur la similarité de chaînes."""

import unicodedata
import re
from typing import List, Tuple, Optional, Dict, Any
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz

from src.models import Track, TrackMatch
from src.utils import setup_logger

logger = setup_logger(__name__)


class TrackMatcher:
    """Matcher sophistiqué basé sur scoring pondéré."""
    
    # Poids de chaque critère
    TITLE_WEIGHT = 0.70      # 70%
    ARTIST_WEIGHT = 0.20     # 20%
    ALBUM_WEIGHT = 0.10      # 10%
    
    # Bonus/pénalité
    PLAYCOUNT_BONUS = 5.0    # Points bonus si playcount similaire
    PLAYCOUNT_TOLERANCE = 0.20  # ±20% pour bonus
    
    # Seuils
    LIKELY_MATCH_THRESHOLD = 80.0   # Très probable
    POSSIBLE_MATCH_THRESHOLD = 60.0  # Possible
    
    # Articles à supprimer
    ARTICLES = {
        'en': ['the', 'a', 'an'],
        'fr': ['le', 'la', 'les', 'l', 'un', 'une', 'des', 'd'],
        'es': ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'],
        'de': ['der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine'],
    }
    
    def __init__(self, use_cache: bool = True, use_parallel: bool = True):
        """
        Initialise le matcher.
        
        Args:
            use_cache: Cache les strings normalisées
            use_parallel: Utilise la parallélisation pour > 1000 tracks
        """
        self.use_cache = use_cache
        self.use_parallel = use_parallel
        self._normalize_cache: Dict[str, str] = {}
        
        logger.info(f"TrackMatcher initialisé (cache={use_cache}, parallel={use_parallel})")
    
    @staticmethod
    def normalize_string(s: str) -> str:
        """
        Normalise une chaîne pour le matching.
        
        Opérations :
        - Lowercase
        - Supprime accents/diacritiques
        - Supprime articles
        - Trim espaces multiples
        
        Args:
            s: Chaîne à normaliser
            
        Returns:
            Chaîne normalisée
        """
        if not s:
            return ""
        
        # Lowercase
        s = s.lower().strip()
        
        # Supprimer accents
        s = ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Supprimer caractères spéciaux (garder lettres, chiffres, espaces)
        s = re.sub(r'[^a-z0-9\s]', '', s)
        
        # Supprimer articles
        words = s.split()
        articles = set()
        for lang_articles in TrackMatcher.ARTICLES.values():
            articles.update(lang_articles)
        
        words = [w for w in words if w not in articles]
        s = ' '.join(words)
        
        # Trim espaces multiples
        s = re.sub(r'\s+', ' ', s).strip()
        
        return s
    
    def _get_normalized(self, s: str) -> str:
        """
        Récupère la version normalisée (avec cache).
        
        Args:
            s: Chaîne
            
        Returns:
            Chaîne normalisée (cachée si possible)
        """
        if not self.use_cache:
            return self.normalize_string(s)
        
        if s not in self._normalize_cache:
            self._normalize_cache[s] = self.normalize_string(s)
        
        return self._normalize_cache[s]
    
    def _calculate_playcount_bonus(self, pc1: int, pc2: int) -> float:
        """
        Calcule le bonus si les playcounts sont similaires.
        
        Args:
            pc1: Playcount 1
            pc2: Playcount 2
            
        Returns:
            Bonus (0 ou PLAYCOUNT_BONUS)
        """
        if pc1 == 0 or pc2 == 0:
            return 0.0
        
        # Calculer la différence relative
        ratio = min(pc1, pc2) / max(pc1, pc2)
        
        # Si dans la tolérance, bonus
        if ratio >= (1.0 - self.PLAYCOUNT_TOLERANCE):
            return self.PLAYCOUNT_BONUS
        
        return 0.0
    
    def _score_match(
        self,
        missing: Dict[str, Any],
        alternative: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcule le score de correspondance entre deux morceaux.
        
        Args:
            missing: Morceau de tracks_persistent
            alternative: Morceau de alternativeplaycount
            
        Returns:
            Dict avec score total et breakdown
        """
        # Normaliser les strings
        missing_title = self._get_normalized(missing.get('title', ''))
        missing_artist = self._get_normalized(missing.get('artist_name', ''))
        missing_album = self._get_normalized(missing.get('album_title', ''))
        
        alternative_title = self._get_normalized(alternative.get('title', ''))
        alternative_artist = self._get_normalized(alternative.get('artist_name', ''))
        alternative_album = self._get_normalized(alternative.get('album_title', ''))
        
        # Calculer les scores partiels
        title_score = fuzz.ratio(missing_title, alternative_title) if missing_title and alternative_title else 0.0
        artist_score = fuzz.ratio(missing_artist, alternative_artist) if missing_artist and alternative_artist else 0.0
        album_score = fuzz.ratio(missing_album, alternative_album) if missing_album and alternative_album else 0.0
        
        # Calculer le score pondéré
        weighted_score = (
            (title_score * self.TITLE_WEIGHT) +
            (artist_score * self.ARTIST_WEIGHT) +
            (album_score * self.ALBUM_WEIGHT)
        )
        
        # Ajouter le bonus playcount
        playcount_bonus = self._calculate_playcount_bonus(
            missing.get('playcount', 0),
            alternative.get('playcount', 0)
        )
        
        total_score = min(100.0, weighted_score + playcount_bonus)
        
        return {
            'total_score': total_score,
            'title_score': title_score,
            'artist_score': artist_score,
            'album_score': album_score,
            'playcount_bonus': playcount_bonus,
            'breakdown': {
                'title': title_score,
                'artist': artist_score,
                'album': album_score
            }
        }
    
    def find_best_matches(
        self,
        missing_track: Dict[str, Any],
        alternative_tracks: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Trouve les meilleures correspondances pour un morceau.
        
        Args:
            missing_track: Morceau de tracks_persistent (dict)
            alternative_tracks: Liste des morceaux de alternativeplaycount
            top_n: Nombre de suggestions à retourner
            
        Returns:
            Liste des top_n correspondances triées par score décroissant
            [
                {
                    'urlmd5': 'abc123...',
                    'title': 'Song Title',
                    'artist': 'Artist Name',
                    'album': 'Album Name',
                    'playcount': 42,
                    'source': 'source',
                    'match_score': 85.5,
                    'score_breakdown': {'title': 90, 'artist': 85, 'album': 80},
                    'match_quality': 'LIKELY'  # LIKELY, POSSIBLE, UNLIKELY
                },
                ...
            ]
        """
        try:
            logger.debug(f"Recherche correspondances pour '{missing_track.get('title', '?')}' "
                        f"parmi {len(alternative_tracks)} alternatives")
            
            # Paralléliser si beaucoup de tracks
            if self.use_parallel and len(alternative_tracks) > 1000:
                matches = self._find_best_matches_parallel(
                    missing_track, alternative_tracks, top_n
                )
            else:
                matches = self._find_best_matches_sequential(
                    missing_track, alternative_tracks, top_n
                )
            
            logger.debug(f"Trouvé {len(matches)} correspondances "
                        f"(top: {matches[0]['match_score']:.1f}% si existe)")
            
            return matches
            
        except Exception as e:
            logger.error(f"Erreur lors du matching : {e}")
            raise
    
    def _find_best_matches_sequential(
        self,
        missing_track: Dict[str, Any],
        alternative_tracks: List[Dict[str, Any]],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """
        Calcule les correspondances en séquentiel.
        
        Args:
            missing_track: Morceau à matcher
            alternative_tracks: Candidates
            top_n: Nombre de résultats
            
        Returns:
            Top N correspondances
        """
        matches = []
        
        for alt_track in alternative_tracks:
            score_data = self._score_match(missing_track, alt_track)
            
            matches.append({
                'urlmd5': alt_track.get('urlmd5'),
                'title': alt_track.get('title', ''),
                'artist': alt_track.get('artist_name', ''),
                'album': alt_track.get('album_title', ''),
                'playcount': alt_track.get('playcount', 0),
                'source': alt_track.get('source', ''),
                'match_score': score_data['total_score'],
                'score_breakdown': score_data['breakdown'],
                'match_quality': self._get_match_quality(score_data['total_score'])
            })
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:top_n]
    
    def _find_best_matches_parallel(
        self,
        missing_track: Dict[str, Any],
        alternative_tracks: List[Dict[str, Any]],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """
        Calcule les correspondances en parallèle.
        
        Args:
            missing_track: Morceau à matcher
            alternative_tracks: Candidates
            top_n: Nombre de résultats
            
        Returns:
            Top N correspondances
        """
        matches = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._score_match, missing_track, alt): alt
                for alt in alternative_tracks
            }
            
            for future in as_completed(futures):
                alt_track = futures[future]
                try:
                    score_data = future.result()
                    matches.append({
                        'urlmd5': alt_track.get('urlmd5'),
                        'title': alt_track.get('title', ''),
                        'artist': alt_track.get('artist_name', ''),
                        'album': alt_track.get('album_title', ''),
                        'playcount': alt_track.get('playcount', 0),
                        'source': alt_track.get('source', ''),
                        'match_score': score_data['total_score'],
                        'score_breakdown': score_data['breakdown'],
                        'match_quality': self._get_match_quality(score_data['total_score'])
                    })
                except Exception as e:
                    logger.warning(f"Erreur lors du matching parallèle : {e}")
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:top_n]
    
    @staticmethod
    def is_likely_match(score: float) -> bool:
        """
        Vérifie si c'est une correspondance probable.
        
        score >= 80 : très probable
        score >= 60 : possible
        score < 60 : peu probable
        
        Args:
            score: Score de correspondance (0-100)
            
        Returns:
            True si score >= 80
        """
        return score >= TrackMatcher.LIKELY_MATCH_THRESHOLD
    
    @staticmethod
    def is_possible_match(score: float) -> bool:
        """
        Vérifie si c'est une correspondance possible.
        
        Args:
            score: Score de correspondance (0-100)
            
        Returns:
            True si score >= 60
        """
        return score >= TrackMatcher.POSSIBLE_MATCH_THRESHOLD
    
    @staticmethod
    def _get_match_quality(score: float) -> str:
        """
        Classe la qualité du matching.
        
        Args:
            score: Score de correspondance
            
        Returns:
            'LIKELY', 'POSSIBLE', ou 'UNLIKELY'
        """
        if score >= TrackMatcher.LIKELY_MATCH_THRESHOLD:
            return 'LIKELY'
        elif score >= TrackMatcher.POSSIBLE_MATCH_THRESHOLD:
            return 'POSSIBLE'
        else:
            return 'UNLIKELY'
    
    def clear_cache(self):
        """Vide le cache des strings normalisées."""
        self._normalize_cache.clear()
        logger.debug("Cache normalisé vidé")



    """Apparie les tracks basé sur la similarité de titre et artiste."""
    
    def __init__(self, threshold: int = 85, method: str = "token_sort_ratio"):
        """
        Initialise le matcher.
        
        Args:
            threshold: Seuil de similarité (0-100)
            method: Méthode de comparaison (ratio, partial_ratio, token_sort_ratio, token_set_ratio)
        """
        self.threshold = threshold
        self.method = method
        self.similarity_fn = getattr(fuzz, method)
        
        logger.info(f"FuzzyMatcher initialisé : threshold={threshold}, method={method}")
    
    def match_tracks(
        self,
        source_tracks: List[Track],
        target_tracks: List[Track]
    ) -> List[TrackMatch]:
        """
        Apparie les tracks entre deux listes.
        
        Args:
            source_tracks: Liste des tracks source
            target_tracks: Liste des tracks cible
            
        Returns:
            Liste des correspondances trouvées
        """
        matches = []
        
        for source in source_tracks:
            best_match = None
            best_score = 0
            
            for target in target_tracks:
                # Calcul de la similarité
                score = self._calculate_similarity(source, target)
                
                if score > best_score and score >= self.threshold:
                    best_score = score
                    best_match = target
            
            if best_match:
                matches.append(TrackMatch(
                    source_track=source,
                    target_track=best_match,
                    similarity_score=best_score
                ))
        
        logger.info(f"Trouvé {len(matches)} correspondances sur {len(source_tracks)} tracks")
        return matches
    
    def _calculate_similarity(self, source: Track, target: Track) -> float:
        """
        Calcule la similarité entre deux tracks.
        
        Args:
            source: Track source
            target: Track cible
            
        Returns:
            Score de similarité (0-100)
        """
        # Combine titre et artiste pour la comparaison
        source_str = f"{source.artist} {source.title}"
        target_str = f"{target.artist} {target.title}"
        
        score = self.similarity_fn(source_str, target_str)
        return float(score)
    
    def find_best_match(
        self,
        track: Track,
        candidates: List[Track]
    ) -> Optional[Tuple[Track, float]]:
        """
        Trouve la meilleure correspondance pour un track.
        
        Args:
            track: Track à matcher
            candidates: Liste des tracks candidats
            
        Returns:
            Tuple (track correspondant, score) ou None
        """
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            score = self._calculate_similarity(track, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        if best_match and best_score >= self.threshold:
            return (best_match, best_score)
        
        return None
