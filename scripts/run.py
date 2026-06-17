#!/usr/bin/env python3
"""Lanceur de développement du GUI Lyrion Playcount Sync.

Équivalent à la commande installée ``lyrion-playcount-sync``, mais utilisable
sans installation pip : rend le package importable depuis l'arborescence locale
puis lance l'interface graphique.

    python3 scripts/run.py            # lancer le GUI
    python3 scripts/run.py config.yaml  # avec un fichier de config explicite
"""

import sys
from pathlib import Path

# Rendre le package importable lorsqu'on lance ce script sans installation pip.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from lyrion_playcount_sync.main import main  # noqa: E402

if __name__ == '__main__':
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(config_file))
