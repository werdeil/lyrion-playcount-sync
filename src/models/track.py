"""Modèle de données pour les tracks."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    """Représente un track avec ses informations."""
    
    track_id: int
    title: str
    artist: str
    album: str
    playcount: int
    
    def __str__(self) -> str:
        """Retourne une représentation lisible du track."""
        return f"{self.artist} - {self.title} ({self.playcount} plays)"
    
    def __eq__(self, other) -> bool:
        """Compare deux tracks par titre et artiste."""
        if not isinstance(other, Track):
            return False
        return (self.title.lower() == other.title.lower() and
                self.artist.lower() == other.artist.lower())
    
    def __hash__(self) -> int:
        """Hash basé sur titre et artiste."""
        return hash((self.title.lower(), self.artist.lower()))


@dataclass
class TrackMatch:
    """Représente une correspondance entre deux tracks."""
    
    source_track: Track
    target_track: Track
    similarity_score: float
    
    def __repr__(self) -> str:
        """Représentation de la correspondance."""
        return (f"TrackMatch('{self.source_track.title}' -> "
                f"'{self.target_track.title}', {self.similarity_score:.1f}%)")
