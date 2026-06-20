"""Calcul de la DPSV (Dynamic Played/Skipped Value) du plugin Alternative Play Count.

Reproduit fidèlement l'algorithme du plugin LMS `lms-alternativeplaycount`
(fonction `_setDynamicPlayedSkippedValue`) :

- la DPSV est une note bornée à [-100, +100], partant de 0 pour un morceau neuf ;
- à chaque LECTURE :  delta = (100 - |dpsv|) / 8  (min 1), dpsv += delta, plafond +100 ;
- à chaque SKIP    :  delta = (100 - |dpsv|) / 4  (min 1), dpsv -= delta, plancher -100 ;
- après chaque événement la valeur est arrondie par `round_float` (arrondi au plus
  proche, demi-tour à l'opposé de zéro), donc la DPSV reste entière entre deux événements.

⚠️ La DPSV dépend de l'ORDRE chronologique des événements, que la table
`alternativeplaycount` ne conserve pas (seuls les totaux playCount/skipCount et les
dates du dernier événement sont stockés). Le plugin tient bien un historique par
événement, mais ailleurs et insuffisant pour lever l'ambiguïté : table `play_history`
dans un fichier SÉPARÉ `apc_external.db` (absent de persist.db), uniquement si la
préférence `playhistory` est active, élaguée à `playhistory_maxdbentries`, et qui ne
loggue QUE les lectures (pas les skips) — or c'est l'entrelacement lectures/skips qui
détermine la DPSV.

On ne peut donc que l'APPROCHER : on rejoue tous les événements en plaçant en dernier
celui dont la date est la plus récente (`lastPlayed` vs `lastSkipped`), ce qui respecte
la sémantique « décisions récentes ». À noter : pour un morceau SANS skip, l'ordre est
sans effet et le résultat est exact.
"""

from typing import Optional


def round_float(value: float) -> int:
    """Arrondi au plus proche, demi-tour à l'opposé de zéro.

    Réplique le `roundFloat` du plugin : int($f + $f/abs($f*2 || 1)).
    Exemples : 12.5 -> 13, -12.5 -> -13, 12.4 -> 12.
    """
    if value >= 0:
        return int(value + 0.5)
    return int(value - 0.5)


def _apply_play(dpsv: float) -> float:
    if dpsv >= 100:
        return dpsv
    delta = (100 - abs(dpsv)) / 8
    if delta < 1:
        delta = 1
    return min(round_float(dpsv + delta), 100)


def _apply_skip(dpsv: float) -> float:
    if dpsv <= -100:
        return dpsv
    delta = (100 - abs(dpsv)) / 4
    if delta < 1:
        delta = 1
    return max(round_float(dpsv - delta), -100)


def compute_dpsv(
    play_count: Optional[int],
    skip_count: Optional[int],
    last_played: Optional[float] = 0,
    last_skipped: Optional[float] = 0,
) -> int:
    """Recalcule la DPSV à partir des totaux de lectures/skips.

    L'ordre des événements étant inconnu, on rejoue les ``play_count`` lectures et
    ``skip_count`` skips en terminant par le type d'événement le plus récent d'après
    ``last_played`` / ``last_skipped`` (le dernier événement « pèse » le plus, car le
    delta diminue à mesure qu'on approche des bornes).

    Args:
        play_count: nombre total de lectures (None/négatif traité comme 0).
        skip_count: nombre total de skips (None/négatif traité comme 0).
        last_played: timestamp de la dernière lecture (epoch), 0 si jamais.
        last_skipped: timestamp du dernier skip (epoch), 0 si jamais.

    Returns:
        La DPSV entière dans [-100, 100].
    """
    plays = max(int(play_count or 0), 0)
    skips = max(int(skip_count or 0), 0)

    if plays == 0 and skips == 0:
        return 0

    # Le dernier événement appliqué doit correspondre à la date la plus récente.
    ends_with_skip = (last_skipped or 0) > (last_played or 0)

    dpsv = 0.0
    if ends_with_skip:
        for _ in range(plays):
            dpsv = _apply_play(dpsv)
        for _ in range(skips):
            dpsv = _apply_skip(dpsv)
    else:
        for _ in range(skips):
            dpsv = _apply_skip(dpsv)
        for _ in range(plays):
            dpsv = _apply_play(dpsv)

    return int(dpsv)
