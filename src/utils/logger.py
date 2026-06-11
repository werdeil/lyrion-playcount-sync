"""Module de configuration du logging."""

import logging
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

# Niveaux de logging disponibles
LEVEL_NAMES = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Cache des loggers
_loggers = {}


def setup_logger(
    name: str,
    log_level: str | int = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure et retourne un logger avec support fichier rotatif.
    
    Args:
        name: Nom du logger
        log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Fichier de log optionnel
        max_bytes: Taille max du fichier en bytes (défaut 10MB)
        backup_count: Nombre de fichiers backup (défaut 5)
        
    Returns:
        Logger configuré
    """
    # Retourner le logger en cache si déjà configuré
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    
    # Convertir le niveau - accepte str ou int
    if isinstance(log_level, str):
        level_str = log_level.upper()
        level = LEVEL_NAMES.get(level_str, logging.INFO)
    else:
        # Assume c'est un int de logging
        level = log_level
    logger.setLevel(level)
    
    # Éviter les handlers en doublons
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Format console: [LEVEL] message
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler fichier rotatif si spécifié
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format fichier: [TIMESTAMP] [LEVEL] [name] message
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Cacher le logger
    _loggers[name] = logger

    return logger
