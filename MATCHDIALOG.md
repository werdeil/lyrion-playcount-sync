# MatchDialog - Dialogue de Sélection et Correction du Match

## 📋 Vue d'ensemble

Le `MatchDialog` est un dialogue modal Tkinter qui permet à l'utilisateur de :
1. **Examiner** le morceau manquant avec toutes ses métadonnées
2. **Sélectionner** parmi les suggestions de correspondance (triées par score)
3. **Choisir** la stratégie d'action (COPY/MERGE)
4. **Personnaliser** la valeur de playcount
5. **Valider** les changements avec prévisualisation SQL

## 🎨 Layout

```
┌─────────────────────────────────────────────────────┐
│ Trouver une correspondance                     [×]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌─ Morceau manquant (tracks_persistent) ─────────┐ │
│ │ Artiste : Queen                                 │ │
│ │ Titre   : Bohemian Rhapsody                     │ │
│ │ Album   : A Night at the Opera                  │ │
│ │ Playcount : 42 lectures                         │ │
│ │ Dernière écoute : 15/01/2024 14:32             │ │
│ │ URL     : /music/Queen/...                      │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ Suggestions (alternativeplaycount) ──────────┐  │
│ │ ┌─────────────────────────────────────────────┐ │ │
│ │ │ ✓ 95% - Queen - Bohemian Rhapsody          │ │ │
│ │ │   Album : A Night at the Opera              │ │ │
│ │ │   Playcount : 38                             │ │ │
│ │ ├─────────────────────────────────────────────┤ │ │
│ │ │ ○ 68% - Queen - Bohemian Rhap...           │ │ │
│ │ │   Album : Greatest Hits                     │ │ │
│ │ │   Playcount : 40                             │ │ │
│ │ ├─────────────────────────────────────────────┤ │ │
│ │ │ ○ 45% - Queen - The Show Must Go On       │ │ │
│ │ │   Album : Innuendo                          │ │ │
│ │ │   Playcount : 5                              │ │ │
│ │ └─────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ Action à effectuer ───────────────────────────┐  │
│ │ ● Copier le playcount                           │ │
│ │   Playcount : [42___]                           │ │
│ │                                                 │ │
│ │ ○ Fusionner (additionner)                       │ │
│ │   42 + 38 = 80                                  │ │
│ │                                                 │ │
│ │ ☑ Supprimer de tracks_persistent après sync    │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ⚠️  Prévisualisation SQL :                           │
│ -- COPY                                             │
│ UPDATE alternativeplaycount SET playcount=42...     │
│ DELETE FROM tracks_persistent WHERE urlmd5=...     │
│                                                     │
│       [✓ Appliquer] [⏭️ Ignorer] [✕ Annuler]        │
└─────────────────────────────────────────────────────┘
```

## 🎯 Sections Détaillées

### 1. **Morceau Manquant** (Read-Only)
Affiche toutes les métadonnées du morceau à synchroniser :
- **Artiste** : Nom de l'artiste
- **Titre** : Titre du morceau
- **Album** : Nom de l'album
- **Playcount** : Nombre de lectures
- **Dernière écoute** : Formatée en DD/MM/YYYY HH:MM
- **URL** : Chemin du fichier audio

Texte en gris pour bien signaler qu'il est en lecture seule.

### 2. **Suggestions** (Radio Buttons)
Liste défilable de suggestions triées par score décroissant :

#### Code Couleur
- **🟢 95%+** : Correspondance excellente (vert `#2ecc71`)
- **🟠 60-95%** : Correspondance acceptable (orange `#f39c12`)
- **🔴 <60%** : Correspondance faible (rouge `#e74c3c`)

#### Icônes
- **✓** : Score >= 90%
- **⚠** : Score 60-90%
- **✗** : Score < 60%

#### Chaque Suggestion Affiche
```
[●|○] 95% - Queen - Bohemian Rhapsody
      Album : A Night at the Opera | Playcount : 38
```

#### Interaction
- **Single Click** : Sélectionner (radio button)
- **Scrollbar** : Défiler si plusieurs suggestions

### 3. **Action à Effectuer**

#### Option COPY
Remplace le playcount dans `alternativeplaycount` :
```
● Copier le playcount (remplacer dans alternativeplaycount)
  Playcount : [42___]
```
- Permet d'éditer la valeur via **Spinbox**
- Valeur par défaut = playcount du morceau manquant

#### Option MERGE
Additionne les playcounts :
```
○ Fusionner (additionner les playcounts)
  42 + 38 = 80
```
- Calcul automatique
- Non éditable (lecture seule)

#### Checkbox DELETE
```
☑ Supprimer de tracks_persistent après sync
```
- Coché par défaut
- Optionnel si on veut garder le doublon

### 4. **Prévisualisation SQL**
Zone texte read-only affichant les requêtes SQL qui seront exécutées :

```sql
-- COPY
UPDATE alternativeplaycount SET playcount=42, lastplayed=UNIX_TIMESTAMP() WHERE urlmd5='xyz789uvw456'
DELETE FROM tracks_persistent WHERE urlmd5='abc123def456'
```

Mise à jour en **temps réel** lors de changements :
- Changement de suggestion
- Changement d'action (COPY/MERGE)
- Modification du playcount

### 5. **Barre d'Actions**
Trois boutons :
- **✓ Appliquer** : Valider et exécuter
- **⏭️ Ignorer** : Passer au suivant (mode batch)
- **✕ Annuler** : Fermer sans action

## 🔌 API

### Classe `MatchDialog`

```python
class MatchDialog(tk.Toplevel):
    """Dialogue pour sélectionner et corriger une correspondance."""
    
    def __init__(
        self,
        parent: tk.Widget,
        missing_track: Track,
        suggested_matches: List[tuple[Track, float]],
        on_apply: Optional[Callable[[SyncOperation], bool]] = None,
        on_next: Optional[Callable] = None,
    )
```

#### Paramètres

| Param | Type | Description |
|-------|------|-------------|
| `parent` | `tk.Widget` | Widget parent (fenêtre principale) |
| `missing_track` | `Track` | Morceau manquant de `tracks_persistent` |
| `suggested_matches` | `List[tuple[Track, float]]` | Suggestions avec scores (0-100) |
| `on_apply` | `Callable[[SyncOperation], bool]` | Callback lors de l'application |
| `on_next` | `Callable` | Callback pour passer au suivant |

#### Callbacks

##### `on_apply(operation: SyncOperation) -> bool`
Appelé quand l'utilisateur clique sur "Appliquer".

**Paramètres** :
- `operation` : `SyncOperation` avec tous les détails

**Retour** :
- `True` si succès → dialogue se ferme
- `False` si erreur → message d'erreur, dialogue reste ouvert

**Exemple** :
```python
def handle_apply(operation: SyncOperation) -> bool:
    try:
        # Backup
        backup_tracks = db.backup()
        
        # Exécuter les requêtes SQL
        update_sql, delete_sql = operation.to_sql()
        db.execute(update_sql)
        if operation.action != "MERGE":
            db.execute(delete_sql)
        
        # Log
        logger.info(f"Sync OK: {operation.operation_id}")
        return True
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return False

dialog = MatchDialog(
    root,
    missing_track,
    suggestions,
    on_apply=handle_apply
)
```

##### `on_next()`
Appelé quand l'utilisateur clique sur "Ignorer" (mode batch).

Permet de traiter le morceau suivant.

### Fonction Helper `show_match_dialog`

```python
def show_match_dialog(
    parent: tk.Widget,
    missing_track: Track,
    suggested_matches: List[tuple[Track, float]],
    on_apply: Optional[Callable[[SyncOperation], bool]] = None,
    on_next: Optional[Callable] = None,
) -> None
```

Wrapper pour ouvrir le dialogue en mode blocking (attend la fermeture).

## ✅ Validation

### Avant Application

1. **Au moins un match sélectionné**
   ```
   ⚠️ Sélection requise
   Veuillez sélectionner un match
   ```

2. **Playcount >= 0**
   ```
   ❌ Valeur invalide
   Playcount doit être >= 0
   ```

3. **Confirmation si score < 60%**
   ```
   ⚠️ Confirmation
   Le score est faible (45%). Voulez-vous continuer?
   [Oui] [Non]
   ```

### Validation Lors de la Sélection

- **Radio button** : Valide automatiquement
- **Spinbox** : Min = 0, Max = 999999
- **Checkbox** : Valide toujours

## 🔄 Flux d'Utilisation

### Cas 1 : Accepter la Meilleure Suggestion

```
1. Utilisateur ouvre le dialogue
2. Première suggestion (95%) pré-sélectionnée
3. Action "COPY" sélectionnée
4. Playcount = 42 (valeur par défaut)
5. SQL généré automatiquement
6. Clique sur "Appliquer"
7. Callback `on_apply` exécuté
8. Dialogue se ferme si succès
```

### Cas 2 : Personnaliser le Playcount

```
1. Sélectionner une suggestion
2. Changer l'action à "MERGE"
3. Voir calcul automatique : 42 + 38 = 80
4. Ou choisir "COPY" et éditer manuellement : [80___]
5. SQL mis à jour
6. Appliquer
```

### Cas 3 : Suggestion Faible

```
1. Sélectionner suggestion 45%
2. Cliquer sur "Appliquer"
3. Dialogue de confirmation affiche : "Le score est faible (45%)"
4. Utilisateur peut accepter ou annuler
```

### Cas 4 : Mode Batch

```
1. Traiter premier morceau
2. Cliquer "Ignorer"
3. Callback `on_next` appelé
4. Passer au morceau suivant
```

## 🎨 Thème et Couleurs

```python
COLOR_GOOD = "#2ecc71"      # Vert - score >= 90%
COLOR_WARNING = "#f39c12"   # Orange - score 60-90%
COLOR_BAD = "#e74c3c"       # Rouge - score < 60%
COLOR_NEUTRAL = "#95a5a6"   # Gris
```

## 📊 Données Utilisées

### Track (Modèle)
```python
@dataclass
class Track:
    urlmd5: str              # Identifiant unique
    title: str               # Titre
    artist: str              # Artiste
    album: str               # Album
    url: str                 # Chemin fichier
    playcount: int           # Nombre lectures
    lastplayed: int | None   # Timestamp Unix
    rating: int              # Note 0-5
    source: str              # 'tracks_persistent' ou 'alternativeplaycount'
```

### SyncOperation (Résultat)
```python
@dataclass
class SyncOperation:
    missing_urlmd5: str      # MD5 du morceau manquant
    selected_alternative_urlmd5: str  # MD5 du match
    action: str              # 'COPY' ou 'MERGE'
    new_playcount: int       # Playcount après opération
    operation_id: uuid.UUID  # UUID unique
    timestamp: datetime      # Date/heure
    
    def to_sql(self) -> tuple[str, str]:
        """Retourne (UPDATE, DELETE) SQL"""
```

## 🚀 Intégration avec MainWindow

```python
from src.ui.main_window import MainWindow
from src.ui.match_dialog import show_match_dialog

class MainWindow(tk.Tk):
    def show_match_dialog_for_selection(self):
        """Ouvrir le dialogue pour le morceau sélectionné."""
        
        track = self.selected_tracks[0]  # Récupérer le morceau
        suggestions = self.track_matcher.find_best_matches(track)
        
        def handle_apply(operation):
            try:
                # Exécuter l'opération
                db.execute_sync(operation)
                self.refresh_view()
                return True
            except:
                return False
        
        show_match_dialog(
            self,
            track,
            suggestions,
            on_apply=handle_apply
        )
```

## 📝 Exemple Complet

Voir : [examples_match_dialog.py](examples_match_dialog.py)

## 🧪 Tests

Voir : [test_match_dialog.py](test_match_dialog.py)

Pour lancer :
```bash
python3 test_match_dialog.py
```

Une fenêtre s'ouvre avec un bouton "Ouvrir MatchDialog".

## 📦 Dépendances

- `tkinter` : GUI native (inclus avec Python)
- `src.models.Track` : Modèle du morceau
- `src.models.SyncOperation` : Modèle de l'opération
- Type hints standard

**Aucune dépendance externe.**

## 🔗 Liens

- [MainWindow](MAINWINDOW.md) - Interface principale
- [Models](MODELS.md) - Modèles de données
- [TrackMatcher](../matching/fuzzy_matcher.py) - Matching
- [SyncDetector](../database/queries.py) - Détection

---

**Version** : 1.0  
**Date** : 24/01/2026  
**Statut** : Production ✅
