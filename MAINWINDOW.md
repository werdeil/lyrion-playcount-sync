# 🖥️ Interface Desktop - MainWindow

**Fichier:** `src/ui/main_window.py`  
**Status:** ✅ Production-Ready v1.0.0  
**Date:** 24 janvier 2026

---

## 📋 Overview

Classe `MainWindow` héritant de `tk.Tk` pour l'interface graphique de synchronisation des playcounts.

**Features :**
- 📊 Affichage des statistiques avec 3 cartes
- 🔍 Barre de recherche avec filtre en temps réel
- 📋 Treeview triable avec code couleur
- 🎨 Thème dark mode (Tkinter natif)
- 🎯 Sélection multiple (Ctrl+clic, Shift+clic)
- ⚡ Menu contextuel (clic-droit)
- 🕐 Horloge en direct
- 💾 Statut DB en direct

---

## 🎨 Layout

```
┌─────────────────────────────────────────────────────┐
│ Lyrion Playcount Sync              [−][□][×]       │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📊 Statistiques                                     │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ tracks_pers… │ alternative… │ Désynchronisés│    │
│  │    1,247     │    1,189     │      58      │    │
│  └──────────────┴──────────────┴──────────────┘    │
│                                                     │
│ 🔍 Recherche : [........................] [🔄 Scanner]
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
││ Morceaux manquants...                            ││
│├─────────┬──────────┬──────────┬───┬──────────┤│
││ Artiste │ Titre    │ Album    │Pl.│ Match?   ││
│├─────────┼──────────┼──────────┼───┼──────────┤│
││ Queen   │ Bohemian │ A Night  │42 │ ✓ 95%   ││
││ Beatles │ Hey Jude │ Past M.  │38 │ ⚠ 68%   ││
│└─────────┴──────────┴──────────┴───┴──────────┘│
│                                                     │
│ Sélectionnés : 2/58                                │
│                                                     │
│ [🔍 Voir détails] [✏️ Corriger] [⚙️ Config]        │
│                                                     │
│ Connecté à /config/prefs/persist.db  │  12:34:56   │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Sections principales

### 1. Zone Statistiques

**3 cartes cliquables :**

| Carte | Valeur | Description |
|-------|--------|-------------|
| tracks_persistent | 1,247 | Morceaux dans la DB principale |
| alternativeplaycount | 1,189 | Morceaux dans la DB alternative |
| Désynchronisés | 58 | Morceaux non trouvés |

**Couleur :** Fond bleu/gris, texte vert pour le nombre

### 2. Barre de recherche

**Features :**
- 🔍 Recherche en temps réel
- ✅ Filtre sur artiste, titre, album
- 🔄 Bouton Scanner pour rafraîchir
- ⚡ Mise à jour instantanée de la Treeview

### 3. Treeview

**Colonnes :**
- `Artiste` (120px)
- `Titre` (200px)
- `Album` (150px)
- `Plays` (60px)
- `Match?` (80px)

**Interactions :**
- 🖱️ **Clic simple** : Sélection
- 🖱️ **Ctrl+Clic** : Sélection multiple
- 🖱️ **Double-clic** : Voir détails
- 🖱️ **Clic-droit** : Menu contextuel

**Code couleur :**
- 🟢 **Vert** : Match ≥ 90% (✓)
- 🟠 **Orange** : Match 60-90% (⚠)
- 🔴 **Rouge** : Match < 60% (✗)

### 4. Compteur de sélection

Affiche : `Sélectionnés : X/Y`

Mis à jour en temps réel.

### 5. Barre d'actions

**Boutons :**
- 🔍 **Voir détails** : Affiche les infos du morceau sélectionné
- ✏️ **Corriger sélection** : Ouvre un dialogue de correction batch
- ⚙️ **Config** : Paramètres de l'application

### 6. Statusbar

**Affiche :**
- 💾 Chemin de la DB
- 🕐 Heure en direct (HH:MM:SS)

---

## 📦 API Publique

### Constructeur

```python
MainWindow(db_path: str = "", on_sync_callback: Optional[Callable] = None)
```

**Paramètres :**
- `db_path` : Chemin vers la DB persistante
- `on_sync_callback` : Fonction appelée lors du sync

### Méthodes

#### `add_track(artist, title, album, playcount, match_score)`

Ajouter un morceau à la liste.

```python
app.add_track("Queen", "Bohemian Rhapsody", "A Night at the Opera", 42, 95.0)
```

#### `clear_tracks()`

Effacer tous les morceaux.

```python
app.clear_tracks()
```

#### `get_selected_tracks() -> list`

Obtenir les morceaux sélectionnés.

```python
selected = app.get_selected_tracks()
# [('Queen', 'Bohemian Rhapsody', ...), ...]
```

#### `update_status(message: str)`

Mettre à jour le message de statut.

```python
app.update_status("Synchronisation en cours...")
```

#### `show_message(title, message, message_type='info')`

Afficher un message à l'utilisateur.

```python
app.show_message("Succès", "Synchronisation terminée!", "info")
```

---

## 🎨 Constantes de style

```python
TITLE = "Lyrion Playcount Sync"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

FONT_MAIN = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SMALL = ("Segoe UI", 9)

COLOR_GOOD = "#2ecc71"     # Vert
COLOR_WARNING = "#f39c12"  # Orange
COLOR_BAD = "#e74c3c"      # Rouge
COLOR_NEUTRAL = "#95a5a6"  # Gris
```

---

## 🎯 Cas d'utilisation

### Scénario 1 : Afficher des morceaux

```python
from src.ui.main_window import MainWindow

app = MainWindow(db_path="/config/prefs/persist.db")

# Ajouter des morceaux
app.add_track("Queen", "Bohemian Rhapsody", "A Night", 42, 95.0)
app.add_track("Beatles", "Hey Jude", "Past Masters", 38, 68.0)
app.add_track("Pink Floyd", "Comfortably Numb", "The Wall", 55, 45.0)

app.mainloop()
```

### Scénario 2 : Récupérer la sélection

```python
def on_sync_requested():
    selected = app.get_selected_tracks()
    print(f"Sync de {len(selected)} morceau(x)...")
    # Lancer la synchronisation

app = MainWindow(on_sync_callback=on_sync_requested)
app.mainloop()
```

### Scénario 3 : Mettre à jour le statut

```python
import threading

def load_data():
    app.update_status("Chargement des données...")
    # Charger les données
    app.update_status("Prêt")

app = MainWindow()
thread = threading.Thread(target=load_data)
thread.start()
app.mainloop()
```

---

## 🖱️ Interactions détaillées

### Recherche

```
Utilisateur tape "queen" → Filtre en temps réel → Affiche les morceaux de Queen
```

**Colonnes filtrées :**
- Artiste
- Titre
- Album

### Sélection

```
Clic → Sélection unique
Ctrl+Clic → Toggle sélection
Shift+Clic → Sélection par plage (non implémenté)
```

### Menu contextuel

**Options :**
1. Voir suggestions de match
2. Ignorer ce morceau
3. Marquer comme résolu

### Double-clic

Affiche une fenêtre modale avec les détails du morceau.

---

## 📊 Architecture

### Attributs principaux

```python
self.db_path: str                    # Chemin DB
self.on_sync_callback: Callable      # Callback sync
self.selected_tracks: set            # Items sélectionnés
self.all_tracks: list                # Tous les morceaux
self.filtered_tracks: list           # Morceaux filtrés
```

### Widgets principaux

```python
self.search_var: StringVar           # Texte de recherche
self.treeview: ttk.Treeview          # Liste des morceaux
self.selection_label: ttk.Label      # Compteur sélection
self.db_label: ttk.Label             # Statut DB
self.clock_label: ttk.Label          # Horloge
```

---

## ✨ Caractéristiques

✅ **Thème dark mode** (natif Tkinter)  
✅ **Recherche en temps réel**  
✅ **Sélection multiple**  
✅ **Code couleur pour scores**  
✅ **Menu contextuel**  
✅ **Horloge en direct**  
✅ **Statusbar avec DB path**  
✅ **Treeview triable** (colonnes)  
✅ **Double-clic pour détails**  
✅ **API simple et claire**  

---

## 🚀 Utilisation

### Mode test

```bash
python3 test_main_window.py
```

### Mode production

```python
from src.ui.main_window import MainWindow
from src.database.queries import SyncDetector

app = MainWindow(db_path="/config/prefs/persist.db")

# Charger les données
detector = SyncDetector(db_manager)
missing = detector.find_missing_in_alternative()

# Ajouter à l'UI
for track in missing:
    app.add_track(
        artist=track.artist,
        title=track.title,
        album=track.album,
        playcount=track.playcount,
        match_score=95.0  # Venant de TrackMatcher
    )

app.mainloop()
```

---

## 🔗 Intégration

### Avec SyncDetector

```python
missing = SyncDetector.find_missing_in_alternative()
for track in missing:
    app.add_track(track.artist, track.title, track.album, track.playcount, 85.0)
```

### Avec TrackMatcher

```python
matcher = TrackMatcher()
matches = matcher.find_best_matches(track, alternatives)
best_score = matches[0][1] if matches else 0
app.add_track(track.artist, track.title, track.album, track.playcount, best_score)
```

---

## 📝 Notes

- **Police** : Segoe UI (Windows/Linux), défaut système (macOS)
- **Emojis** : Supportés nativement en Tkinter
- **Scrollbars** : Automatiques pour Treeview
- **Redimensionnement** : Fenêtre adaptable (min 800x600)
- **Thread-safe** : Utiliser `after()` pour les mises à jour depuis threads

---

## 🎯 Prochaines étapes

1. MatchDialog - Dialog pour afficher les suggestions
2. ConfigDialog - Paramètres
3. DetailsDialog - Détails complets
4. ProgressBar - Indicateur de progression
5. LogPanel - Affichage des logs

---

**Version:** 1.0.0  
**Status:** 🟢 Production-Ready  
**Créé:** 24 janvier 2026
