#!/usr/bin/env python3
"""Vérification de l'installation.

Alias historique : délègue à `run.py --check` pour ne maintenir qu'une seule
liste de dépendances / fichiers requis. Préférez désormais :

    python3 scripts/run.py --check
"""

import sys
from pathlib import Path

# Permettre l'import de run.py quel que soit le répertoire d'appel
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run import check_installation  # noqa: E402


if __name__ == '__main__':
    sys.exit(0 if check_installation() else 1)
