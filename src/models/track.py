"""
Modèles de données pour la synchronisation des morceaux.

Contient les classes dataclass pour représenter les données du système:
- Track: Représentation d'un morceau
- MatchSuggestion: Suggestion de correspondance entre morceaux
- SyncOperation: Opération de synchronisation à effectuer
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import json


@dataclass
class Track:
    """
    Représente un morceau de musique.
    
    Attributes:
        urlmd5: Identifiant unique MD5 de l'URL
        title: Titre du morceau (optionnel)
        artist: Nom de l'artiste (optionnel)
        album: Nom de l'album (optionnel)
        url: URL du morceau (optionnel)
        playcount: Nombre de lectures
        lastplayed: Timestamp UNIX de la dernière lecture (optionnel)
        rating: Note du morceau (optionnel)
        source: Source du morceau ('tracks_persistent' ou 'alternativeplaycount')
    """
    
    urlmd5: str
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    url: Optional[str]
    playcount: int
    lastplayed: Optional[int] = None  # timestamp UNIX
    rating: Optional[int] = None
    source: str = 'tracks_persistent'
    
    def __post_init__(self) -> None:
        """Valider les données après initialisation."""
        if not self.urlmd5:
            raise ValueError("urlmd5 ne peut pas être vide")
        
        if self.playcount < 0:
            raise ValueError("playcount ne peut pas être négatif")
        
        if self.rating is not None:
            if not 0 <= self.rating <= 5:
                raise ValueError("rating doit être entre 0 et 5")
        
        if self.source not in ('tracks_persistent', 'alternativeplaycount'):
            raise ValueError(f"source invalide: {self.source}")
    
    def display_name(self) -> str:
        """
        Retourne le nom d'affichage du morceau.
        
        Format: "Artist - Title" ou fallback sur url ou urlmd5
        
        Returns:
            str: Nom formaté pour affichage
        """
        if self.artist and self.title:
            return f"{self.artist} - {self.title}"
        
        if self.title:
            return self.title
        
        if self.artist:
            return self.artist
        
        if self.url:
            return self.url
        
        return f"Track ({self.urlmd5[:8]}...)"
    
    def lastplayed_formatted(self) -> str:
        """
        Convertit le timestamp UNIX en format date-heure lisible.
        
        Format: "DD/MM/YYYY HH:MM" (fuseau horaire local)
        
        Returns:
            str: Date formatée ou "N/A" si lastplayed est None
        """
        if self.lastplayed is None:
            return "N/A"
        
        try:
            dt = datetime.fromtimestamp(self.lastplayed)
            return dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, OSError):
            return "Invalid date"
    
    def to_dict(self) -> dict:
        """
        Convertit le Track en dictionnaire pour sérialisation.
        
        Returns:
            dict: Représentation dictionnaire du Track
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convertit le Track en JSON string.
        
        Returns:
            str: Représentation JSON du Track
        """
        data = self.to_dict()
        # Convertir les None en null JSON
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        """Représentation string du Track."""
        return f"Track({self.display_name()} | {self.playcount} plays | {self.source})"
    
    def __repr__(self) -> str:
        """Représentation pour debugging."""
        return (f"Track(urlmd5={self.urlmd5!r}, title={self.title!r}, "
                f"artist={self.artist!r}, playcount={self.playcount}, "
                f"source={self.source!r})")


@dataclass
class MatchSuggestion:
    """
    Représente une suggestion de correspondance entre deux morceaux.
    
    Attributes:
        missing_track: Morceau manquant de la base principale
        suggested_matches: Liste de (Track, score) trié par score décroissant
        auto_match_possible: True si le meilleur score > 90
    """
    
    missing_track: Track
    suggested_matches: list[tuple[Track, float]] = field(default_factory=list)
    auto_match_possible: bool = False
    
    def __post_init__(self) -> None:
        """Valider et mettre à jour auto_match_possible."""
        # Valider que les scores sont valides (0-100)
        for track, score in self.suggested_matches:
            if not 0 <= score <= 100:
                raise ValueError(f"Score invalide: {score} (doit être 0-100)")
        
        # Calculer auto_match_possible
        if self.suggested_matches:
            best_score = self.suggested_matches[0][1]
            self.auto_match_possible = best_score > 90
    
    def get_best_match(self) -> Optional[tuple[Track, float]]:
        """
        Retourne le meilleur match si score > 60.
        
        Returns:
            tuple[Track, float] | None: (Track, score) ou None si aucun match > 60
        """
        if not self.suggested_matches:
            return None
        
        best_track, best_score = self.suggested_matches[0]
        
        if best_score > 60:
            return (best_track, best_score)
        
        return None
    
    def add_match(self, track: Track, score: float) -> None:
        """
        Ajoute une correspondance et maintient l'ordre par score.
        
        Args:
            track: Track à ajouter
            score: Score de correspondance (0-100)
        """
        if not 0 <= score <= 100:
            raise ValueError(f"Score invalide: {score}")
        
        self.suggested_matches.append((track, score))
        # Trier par score décroissant
        self.suggested_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Recalculer auto_match_possible
        if self.suggested_matches:
            best_score = self.suggested_matches[0][1]
            self.auto_match_possible = best_score > 90
    
    def get_top_n(self, n: int) -> list[tuple[Track, float]]:
        """
        Retourne les top N correspondances.
        
        Args:
            n: Nombre de correspondances à retourner
        
        Returns:
            list[tuple[Track, float]]: Top N matches
        """
        return self.suggested_matches[:n]
    
    def __str__(self) -> str:
        """Représentation string."""
        best = self.get_best_match()
        if best:
            track, score = best
            return (f"MatchSuggestion({self.missing_track.display_name()} -> "
                    f"{track.display_name()} @ {score:.1f}%)")
        return f"MatchSuggestion({self.missing_track.display_name()} -> No match)"


@dataclass
class SyncOperation:
    """
    Représente une opération de synchronisation à effectuer.
    
    Attributes:
        operation_id: Identifiant unique (UUID)
        missing_urlmd5: URL MD5 du morceau manquant
        selected_alternative_urlmd5: URL MD5 du morceau alternatif sélectionné
        action: Type d'action ('COPY', 'MERGE', 'DELETE')
        new_playcount: Nouveau playcount après opération (optionnel)
        timestamp: Timestamp de création de l'opération
    """
    
    missing_urlmd5: str
    selected_alternative_urlmd5: str
    action: str
    new_playcount: Optional[int] = None
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self) -> None:
        """Valider les données après initialisation."""
        if not self.missing_urlmd5:
            raise ValueError("missing_urlmd5 ne peut pas être vide")
        
        if not self.selected_alternative_urlmd5:
            raise ValueError("selected_alternative_urlmd5 ne peut pas être vide")
        
        if self.action not in ('COPY', 'MERGE', 'DELETE'):
            raise ValueError(f"action invalide: {self.action}")
        
        if self.new_playcount is not None and self.new_playcount < 0:
            raise ValueError("new_playcount ne peut pas être négatif")
    
    def to_sql(self) -> tuple[str, str]:
        """
        Génère les requêtes SQL pour effectuer l'opération.
        
        Retourne un tuple (update_query, delete_query):
        - update_query: UPDATE tracks_persistent pour mettre à jour le playcount
        - delete_query: DELETE d'alternativeplaycount pour nettoyer l'enregistrement
        
        Returns:
            tuple[str, str]: (UPDATE query, DELETE query)
        
        Raises:
            ValueError: Si l'action est invalide ou new_playcount manquant
        """
        if self.action == 'COPY':
            # Copier le playcount et les données de alternativeplaycount vers tracks_persistent
            if self.new_playcount is None:
                raise ValueError("new_playcount requis pour action COPY")
            
            update_query = (
                f"UPDATE tracks_persistent "
                f"SET playcount = {self.new_playcount} "
                f"WHERE urlmd5 = '{self.missing_urlmd5}';"
            )
            
            delete_query = (
                f"DELETE FROM alternativeplaycount "
                f"WHERE urlmd5 = '{self.selected_alternative_urlmd5}';"
            )
        
        elif self.action == 'MERGE':
            # Fusionner: additionner les playcounts
            if self.new_playcount is None:
                raise ValueError("new_playcount requis pour action MERGE")
            
            update_query = (
                f"UPDATE tracks_persistent "
                f"SET playcount = {self.new_playcount} "
                f"WHERE urlmd5 = '{self.missing_urlmd5}';"
            )
            
            delete_query = (
                f"DELETE FROM alternativeplaycount "
                f"WHERE urlmd5 = '{self.selected_alternative_urlmd5}';"
            )
        
        elif self.action == 'DELETE':
            # Supprimer le morceau manquant
            update_query = (
                f"DELETE FROM tracks_persistent "
                f"WHERE urlmd5 = '{self.missing_urlmd5}';"
            )
            
            delete_query = (
                f"DELETE FROM alternativeplaycount "
                f"WHERE urlmd5 = '{self.selected_alternative_urlmd5}';"
            )
        
        else:
            raise ValueError(f"Action invalide: {self.action}")
        
        return (update_query, delete_query)
    
    def to_dict(self) -> dict:
        """
        Convertit l'opération en dictionnaire.
        
        Returns:
            dict: Représentation dictionnaire
        """
        return {
            'operation_id': self.operation_id,
            'missing_urlmd5': self.missing_urlmd5,
            'selected_alternative_urlmd5': self.selected_alternative_urlmd5,
            'action': self.action,
            'new_playcount': self.new_playcount,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def to_json(self) -> str:
        """
        Convertit l'opération en JSON string.
        
        Returns:
            str: Représentation JSON
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        """Représentation string."""
        return (f"SyncOperation({self.action}: "
                f"{self.missing_urlmd5[:8]}... -> "
                f"{self.selected_alternative_urlmd5[:8]}...)")
    
    def __repr__(self) -> str:
        """Représentation pour debugging."""
        return (f"SyncOperation(operation_id={self.operation_id!r}, "
                f"action={self.action!r}, "
                f"missing_urlmd5={self.missing_urlmd5!r})")


@dataclass
class TrackMatch:
    """
    Représente une correspondance entre deux morceaux.
    
    Attributes:
        source_track: Morceau source
        target_track: Morceau cible correspondant
        similarity_score: Score de similarité (0-100)
    """
    source_track: Track
    target_track: Track
    similarity_score: float
    
    def __post_init__(self) -> None:
        """Valider le score."""
        if not 0 <= self.similarity_score <= 100:
            raise ValueError(f"Score invalide: {self.similarity_score} (doit être 0-100)")


# Type aliases pour faciliter les annotations
TrackList = list[Track]
MatchSuggestionList = list[MatchSuggestion]
SyncOperationList = list[SyncOperation]
