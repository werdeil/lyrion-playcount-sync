"""
Application Configuration Module

Gère la configuration globale de l'application avec:
- Pattern singleton
- Chargement YAML
- Validation
- Persistance
"""

import yaml
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, fields as dc_fields
import logging

from src.utils.remote_sync import RemoteConfig  # noqa: F401 — réexporté

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuration de la base de données."""
    path: str = None  # Will be set from env or default
    auto_backup: bool = True
    backup_on_startup: bool = True
    backup_retention_days: int = 7
    
    def __post_init__(self):
        """Initialize path from environment or use default."""
        if self.path is None:
            # Try to read from environment variable first
            env_path = os.getenv('LYRION_DATA_PATH')
            if env_path:
                self.path = str(Path(env_path) / 'persist.db')
            else:
                self.path = "/config/prefs/persist.db"


@dataclass
class MatchingConfig:
    """Configuration du matching."""
    auto_match_threshold: int = 90
    suggestion_min_score: int = 50
    max_suggestions: int = 5
    weights: Dict[str, int] = None
    
    def __post_init__(self):
        """Initialiser les poids par défaut."""
        if self.weights is None:
            self.weights = {
                'title': 70,
                'artist': 20,
                'album': 10
            }
    
    def validate(self) -> bool:
        """Valider que les poids somment à 100."""
        total = sum(self.weights.values())
        if total != 100:
            logger.warning(
                f"Weights sum to {total}, should be 100. "
                f"Normalizing..."
            )
            # Normaliser les poids - garder le premier entier, ajuster les autres
            keys = list(self.weights.keys())
            if keys:
                # Calculer la différence et l'ajouter au dernier poids
                scale = 100 / total
                normalized = {k: int(self.weights[k] * scale) for k in keys}
                diff = 100 - sum(normalized.values())
                normalized[keys[-1]] += diff
                self.weights = normalized
            return False
        return True


@dataclass
class SyncConfig:
    """Configuration de la synchronisation."""
    default_action: str = "COPY"
    delete_after_sync: bool = True
    confirm_below_score: int = 70
    
    def validate(self) -> bool:
        """Valider les paramètres."""
        if self.default_action not in ["COPY", "MERGE", "SKIP"]:
            logger.error(f"Invalid default_action: {self.default_action}")
            self.default_action = "COPY"
            return False
        return True


@dataclass
class UIConfig:
    """Configuration de l'interface."""
    theme: str = "darkly"
    window_size: str = "1200x800"
    auto_refresh_seconds: int = 0
    show_tooltips: bool = True


@dataclass
class LoggingConfig:
    """Configuration du logging."""
    level: str = "INFO"
    file: str = "./logs/sync.log"
    
    def validate(self) -> bool:
        """Valider le niveau de logging."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in valid_levels:
            logger.warning(f"Invalid log level: {self.level}, using INFO")
            self.level = "INFO"
            return False
        return True


class Config:
    """
    Configuration singleton de l'application.
    
    Charge et gère les configurations depuis fichier YAML.
    Valide les valeurs et fournit les defaults.
    
    Example:
        >>> config = Config.instance()
        >>> db_path = config.database.path
        >>> config.load_from_file('config.yaml')
    """
    
    _instance: Optional['Config'] = None
    
    def __init__(self):
        """Initialiser avec les valeurs par défaut."""
        self.remote = RemoteConfig()
        self.database = DatabaseConfig()
        self.matching = MatchingConfig()
        self.sync = SyncConfig()
        self.ui = UIConfig()
        self.logging = LoggingConfig()
        self._config_file: Optional[Path] = None
    
    @classmethod
    def instance(cls) -> 'Config':
        """
        Récupérer ou créer l'instance singleton.
        
        Returns:
            Config: Instance unique
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Charger la configuration depuis un fichier YAML.
        
        Args:
            file_path: Chemin du fichier YAML
        
        Returns:
            bool: True si succès
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            yaml.YAMLError: Si le fichier n'est pas valide
        """
        config_path = Path(file_path)
        
        if not config_path.exists():
            logger.error(f"Config file not found: {file_path}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning("Config file is empty, using defaults")
                return True
            
            # Charger chaque section
            if 'remote' in data:
                valid_keys = {f.name for f in dc_fields(RemoteConfig)}
                remote_data = {k: v for k, v in data['remote'].items() if k in valid_keys}
                self.remote = RemoteConfig(**remote_data)

            if 'database' in data:
                self.database = DatabaseConfig(**data['database'])
            
            if 'matching' in data:
                match_data = data['matching']
                self.matching = MatchingConfig(**match_data)
            
            if 'sync' in data:
                self.sync = SyncConfig(**data['sync'])
            
            if 'ui' in data:
                self.ui = UIConfig(**data['ui'])
            
            if 'logging' in data:
                self.logging = LoggingConfig(**data['logging'])
            
            self._config_file = config_path
            
            # Valider les configurations
            self.validate()
            
            logger.info(f"Config loaded from: {file_path}")
            return True
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def validate(self) -> bool:
        """
        Valider toutes les configurations.
        
        Returns:
            bool: True si toutes valides
        """
        all_valid = True
        
        all_valid &= self.matching.validate()
        all_valid &= self.sync.validate()
        all_valid &= self.logging.validate()
        
        if all_valid:
            logger.debug("All configurations are valid")
        
        return all_valid
    
    def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """
        Sauvegarder la configuration dans un fichier YAML.
        
        Args:
            file_path: Chemin du fichier (utilise le fichier chargé si None)
        
        Returns:
            bool: True si succès
        """
        if file_path:
            config_path = Path(file_path)
        elif self._config_file:
            config_path = self._config_file
        else:
            logger.error("No config file path specified")
            return False
        
        try:
            config_dict = {
                'remote': asdict(self.remote),
                'database': asdict(self.database),
                'matching': asdict(self.matching),
                'sync': asdict(self.sync),
                'ui': asdict(self.ui),
                'logging': asdict(self.logging),
            }
            
            # Créer le répertoire si nécessaire
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Config saved to: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupérer une valeur de configuration (dot notation).
        
        Args:
            key: Clé (ex: 'matching.auto_match_threshold')
            default: Valeur par défaut
        
        Returns:
            Any: Valeur ou default
        
        Example:
            >>> threshold = config.get('matching.auto_match_threshold', 90)
        """
        parts = key.split('.')
        
        try:
            obj = getattr(self, parts[0])
            for part in parts[1:]:
                obj = getattr(obj, part)
            return obj
        except (AttributeError, IndexError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Définir une valeur de configuration (dot notation).
        
        Args:
            key: Clé (ex: 'matching.auto_match_threshold')
            value: Nouvelle valeur
        
        Returns:
            bool: True si succès
        
        Example:
            >>> config.set('matching.auto_match_threshold', 85)
        """
        parts = key.split('.')
        
        if len(parts) < 2:
            logger.error(f"Invalid config key: {key}")
            return False
        
        try:
            # Naviguer jusqu'à l'avant-dernier niveau
            obj = getattr(self, parts[0])
            for part in parts[1:-1]:
                obj = getattr(obj, part)
            
            # Vérifier que l'attribut existe déjà
            if not hasattr(obj, parts[-1]):
                logger.error(f"Invalid config key: {key} (field does not exist)")
                return False
            
            # Définir la valeur au dernier niveau
            setattr(obj, parts[-1], value)
            logger.debug(f"Config updated: {key} = {value}")
            return True
        except (AttributeError, IndexError) as e:
            logger.error(f"Invalid config key: {key} ({e})")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir la configuration en dictionnaire.
        
        Returns:
            Dict: Configuration complète
        """
        return {
            'remote': asdict(self.remote),
            'database': asdict(self.database),
            'matching': asdict(self.matching),
            'sync': asdict(self.sync),
            'ui': asdict(self.ui),
            'logging': asdict(self.logging),
        }
    
    def __repr__(self) -> str:
        """Représentation textuelle."""
        config_dict = self.to_dict()
        return f"Config({json.dumps(config_dict, indent=2)})"
