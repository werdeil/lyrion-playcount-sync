"""Application Lyrion Playcount Sync."""

import os
from pathlib import Path
from importlib import resources

__version__ = "1.0.0"
__author__ = "werdeil"


def example_config_path() -> Path:
    """Chemin du fichier ``config.yaml.example`` embarqué dans le package.

    Fonctionne aussi bien en développement qu'une fois le package installé
    via pip, en localisant la ressource à l'intérieur du package plutôt que
    dans le répertoire courant.
    """
    return Path(resources.files("lyrion_playcount_sync") / "config.yaml.example")


def user_config_path() -> Path:
    """Emplacement persistant du ``config.yaml`` de l'utilisateur.

    Respecte ``XDG_CONFIG_HOME`` si défini, sinon ``~/.config``. Cet
    emplacement ne dépend pas du répertoire courant : l'app retrouve donc
    sa configuration quel que soit le mode de lancement (script GUI installé,
    Finder, terminal…).
    """
    base = os.environ.get('XDG_CONFIG_HOME')
    base_dir = Path(base) if base else Path.home() / '.config'
    return base_dir / 'lyrion-playcount-sync' / 'config.yaml'


def resolve_config_path(explicit: str | None = None) -> Path:
    """Détermine le ``config.yaml`` à utiliser, indépendamment du cwd.

    Ordre de recherche (premier existant gagne) :
    1. ``explicit`` (chemin passé en argument), s'il est fourni ;
    2. ``./config.yaml`` dans le répertoire courant (confort dev) ;
    3. le config utilisateur (``user_config_path``).

    Si aucun n'existe, renvoie le chemin du config utilisateur : c'est la
    cible par défaut où l'app pourra créer/sauvegarder la configuration.
    """
    if explicit:
        return Path(explicit)

    candidates = [Path.cwd() / 'config.yaml', user_config_path()]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return user_config_path()
