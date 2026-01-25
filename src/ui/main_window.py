"""
Interface desktop principale pour la synchronisation des playcounts.

Affiche les morceaux manquants et permet de:
- Visualiser les statistiques
- Filtrer les morceaux
- Visualiser les suggestions de match
- Corriger les sélections
- Exécuter la synchronisation
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Callable


class MainWindow(tk.Tk):
    """Fenêtre principale de l'application Lyrion Playcount Sync."""
    
    # Constantes de style
    TITLE = "Lyrion Playcount Sync"
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    THEME = "darkly"
    FONT_MAIN = ("Segoe UI", 10)
    FONT_TITLE = ("Segoe UI", 14, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    
    # Couleurs
    COLOR_GOOD = "#2ecc71"      # Vert - match > 90%
    COLOR_WARNING = "#f39c12"   # Orange - match 60-90%
    COLOR_BAD = "#e74c3c"       # Rouge - match < 60%
    COLOR_NEUTRAL = "#95a5a6"   # Gris - pas de match
    
    def __init__(self, db_path: str = "", db_manager = None, on_sync_callback: Optional[Callable] = None):
        """
        Initialiser la fenêtre principale.
        
        Args:
            db_path: Chemin vers la base de données persistante
            db_manager: Instance de DatabaseManager (optionnel)
            on_sync_callback: Callback appelé lors du sync (optionnel)
        """
        super().__init__()
        
        self.db_path = db_path
        self.db_manager = db_manager
        self.on_sync_callback = on_sync_callback
        self.selected_tracks = set()
        self.all_tracks = []
        self.filtered_tracks = []
        
        # Configuration de la fenêtre
        self.title(self.TITLE)
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(800, 600)
        
        # Configuration du style
        self._setup_styles()
        
        # Créer l'interface
        self._create_widgets()
        self._bind_events()
        
        # Charger les données depuis la BD si disponible
        if self.db_manager:
            self._load_tracks_from_db()
        
        # Mise à jour initiale du statusbar
        self._update_statusbar()
    
    def _setup_styles(self) -> None:
        """Configurer les styles personnalisés."""
        style = ttk.Style()
        
        # Styles pour les cartes de statistiques
        style.configure(
            "Stats.TLabel",
            font=self.FONT_SMALL,
            background="#2c3e50",
            foreground="#ecf0f1"
        )
        
        style.configure(
            "StatsTitle.TLabel",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#3498db"
        )
        
        style.configure(
            "StatsNumber.TLabel",
            font=("Segoe UI", 18, "bold"),
            background="#2c3e50",
            foreground="#2ecc71"
        )
        
        style.configure(
            "Title.TLabel",
            font=self.FONT_TITLE,
            foreground="#3498db"
        )
        
        style.configure(
            "Status.TLabel",
            font=self.FONT_SMALL,
            foreground="#95a5a6"
        )
    
    def _create_widgets(self) -> None:
        """Créer tous les widgets de l'interface."""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._create_stats_section(main_frame)
        self._create_search_section(main_frame)
        self._create_treeview_section(main_frame)
        self._create_selection_info_section(main_frame)
        self._create_actions_section(main_frame)
        self._create_statusbar()
    
    def _create_stats_section(self, parent: ttk.Frame) -> None:
        """Créer la zone de statistiques avec 3 cartes."""
        stats_frame = ttk.LabelFrame(parent, text="📊 Statistiques", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        col_frame = ttk.Frame(stats_frame)
        col_frame.pack(fill=tk.X, expand=True)
        
        # Calculer les statistiques
        self.total_persistent = 0
        self.total_alternative = 0
        self.desynchronized = 0
        
        if self.db_manager:
            try:
                with self.db_manager.cursor(commit=False) as cursor:
                    # Count total in tracks_persistent
                    cursor.execute("SELECT COUNT(*) FROM tracks_persistent")
                    self.total_persistent = cursor.fetchone()[0]
                    
                    # Count total in alternativeplaycount
                    cursor.execute("SELECT COUNT(*) FROM alternativeplaycount")
                    self.total_alternative = cursor.fetchone()[0]
                    
                    # Count desynchronized (in persistent but not in alternative)
                    cursor.execute("""
                        SELECT COUNT(*) FROM tracks_persistent tp 
                        WHERE tp.urlmd5 NOT IN (SELECT urlmd5 FROM alternativeplaycount)
                    """)
                    self.desynchronized = cursor.fetchone()[0]
            except Exception as e:
                print(f"Erreur lors du calcul des stats: {e}")
        
        self._create_stat_card(col_frame, "tracks_persistent", f"{self.total_persistent:,}", tk.LEFT)
        self._create_stat_card(col_frame, "alternativeplaycount", f"{self.total_alternative:,}", tk.LEFT)
        self._create_stat_card(col_frame, "Désynchronisés", f"{self.desynchronized:,}", tk.LEFT)
    
    def _create_stat_card(self, parent: ttk.Frame, title: str, value: str, side: str = tk.LEFT) -> None:
        """Créer une carte de statistique."""
        card_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        card_frame.pack(side=side, fill=tk.BOTH, expand=True, padx=5)
        
        title_label = ttk.Label(card_frame, text=title, style="StatsTitle.TLabel")
        title_label.pack(pady=(5, 2))
        
        value_label = ttk.Label(card_frame, text=value, style="StatsNumber.TLabel")
        value_label.pack(pady=(0, 5))
    
    def _create_search_section(self, parent: ttk.Frame) -> None:
        """Créer la barre de recherche et le bouton Scanner."""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        search_label = ttk.Label(search_frame, text="🔍 Recherche :")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=self.FONT_MAIN)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        scanner_btn = ttk.Button(search_frame, text="🔄 Scanner", command=self._on_scanner_click)
        scanner_btn.pack(side=tk.LEFT)
    
    def _create_treeview_section(self, parent: ttk.Frame) -> None:
        """Créer la Treeview pour afficher les morceaux."""
        treeview_frame = ttk.LabelFrame(
            parent,
            text="Morceaux manquants dans alternativeplaycount",
            padding=5
        )
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("Artiste", "Titre", "Album", "Plays", "Match?")
        self.treeview = ttk.Treeview(
            treeview_frame,
            columns=columns,
            height=12,
            show="headings"
        )
        
        self.treeview.heading("#0", text="")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        
        widths = [120, 200, 150, 60, 80]
        for col, width in zip(columns, widths):
            self.treeview.heading(col, text=col)
            self.treeview.column(col, width=width, anchor=tk.W)
        
        vsb = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.treeview.yview)
        hsb = ttk.Scrollbar(treeview_frame, orient=tk.HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        self.treeview.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        treeview_frame.grid_rowconfigure(0, weight=1)
        treeview_frame.grid_columnconfigure(0, weight=1)
        
        self._populate_treeview_example()
        
        self.treeview.bind("<Double-1>", self._on_treeview_double_click)
        self.treeview.bind("<Button-3>", self._on_treeview_right_click)
        self.treeview.bind("<Control-Button-1>", self._on_treeview_ctrl_click)
        self.treeview.bind("<Button-1>", self._on_treeview_click)
    
    def _populate_treeview_example(self) -> None:
        """Remplir la Treeview avec des données d'exemple."""
        example_data = [
            ("Queen", "Bohemian Rhapsody", "A Night at the Opera", "42", "✓ 95%"),
            ("The Beatles", "Hey Jude", "Past Masters", "38", "⚠ 68%"),
            ("Pink Floyd", "Comfortably Numb", "The Wall", "55", "✗ 45%"),
            ("Led Zeppelin", "Stairway to Heaven", "Led Zeppelin IV", "71", "✓ 92%"),
            ("David Bowie", "Space Oddity", "Space Oddity", "28", "⚠ 75%"),
            ("The Rolling Stones", "Sympathy for the Devil", "Beggars Banquet", "33", "✗ 38%"),
        ]
        
        for data in example_data:
            tags = self._get_match_tags(data[4])
            self.treeview.insert("", tk.END, values=data, tags=tags)
            self.all_tracks.append(data)
        
        self.filtered_tracks = self.all_tracks.copy()
        
        self.treeview.tag_configure("good", foreground=self.COLOR_GOOD)
        self.treeview.tag_configure("warning", foreground=self.COLOR_WARNING)
        self.treeview.tag_configure("bad", foreground=self.COLOR_BAD)
        self.treeview.tag_configure("neutral", foreground=self.COLOR_NEUTRAL)
    
    def _get_match_tags(self, match_str: str) -> tuple:
        """Obtenir les tags de couleur basés sur le score de match."""
        if "✓" in match_str:
            return ("good",)
        elif "⚠" in match_str:
            return ("warning",)
        elif "✗" in match_str:
            return ("bad",)
        else:
            return ("neutral",)
    
    def _create_selection_info_section(self, parent: ttk.Frame) -> None:
        """Créer l'info du compteur de sélection."""
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.selection_label = ttk.Label(
            info_frame,
            text="Sélectionnés : 0/58",
            font=self.FONT_SMALL
        )
        self.selection_label.pack(side=tk.LEFT)
    
    def _create_actions_section(self, parent: ttk.Frame) -> None:
        """Créer la barre d'actions."""
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(actions_frame, text="🔍 Voir détails", command=self._on_details_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="✏️ Corriger sélection", command=self._on_correct_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="⚙️ Config", command=self._on_config_click).pack(side=tk.LEFT, padx=2)
    
    def _create_statusbar(self) -> None:
        """Créer la barre de statut en bas."""
        statusbar = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.db_label = ttk.Label(statusbar, text="", style="Status.TLabel")
        self.db_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        sep_label = ttk.Label(statusbar, text="|", style="Status.TLabel")
        sep_label.pack(side=tk.LEFT, padx=2)
        
        self.clock_label = ttk.Label(statusbar, text="", style="Status.TLabel")
        self.clock_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        self._update_clock()
    
    def _bind_events(self) -> None:
        """Lier les événements."""
        pass
    
    def _on_search_change(self, *args) -> None:
        """Appeler quand le texte de recherche change."""
        search_text = self.search_var.get().lower()
        
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        
        self.filtered_tracks = [
            track for track in self.all_tracks
            if any(search_text in str(field).lower() for field in track[:3])
        ]
        
        for track in self.filtered_tracks:
            tags = self._get_match_tags(track[4])
            self.treeview.insert("", tk.END, values=track, tags=tags)
    
    def _on_scanner_click(self) -> None:
        """Appeler quand le bouton Scanner est cliqué."""
        messagebox.showinfo("Scanner", "Rafraîchissement des données...")
    
    def _on_treeview_double_click(self, event) -> None:
        """Appeler au double-clic sur un morceau."""
        selection = self.treeview.selection()
        if selection:
            values = self.treeview.item(selection[0], "values")
            messagebox.showinfo(
                "Détails du morceau",
                f"Artiste: {values[0]}\nTitre: {values[1]}\nAlbum: {values[2]}\nPlays: {values[3]}\nMatch: {values[4]}"
            )
    
    def _on_treeview_right_click(self, event) -> None:
        """Afficher le menu contextuel au clic-droit."""
        item = self.treeview.identify("item", event.x, event.y)
        if item:
            self.treeview.selection_set(item)
            menu = tk.Menu(self, tearoff=False)
            menu.add_command(label="Voir suggestions de match", command=self._on_suggestions_click)
            menu.add_separator()
            menu.add_command(label="Ignorer ce morceau", command=self._on_ignore_click)
            menu.add_command(label="Marquer comme résolu", command=self._on_mark_resolved_click)
            menu.post(event.x_root, event.y_root)
    
    def _on_treeview_click(self, event) -> None:
        """Appeler au clic simple sur un morceau."""
        item = self.treeview.identify("item", event.x, event.y)
        if item and item not in self.selected_tracks:
            self.selected_tracks.add(item)
            self._update_selection_label()
    
    def _on_treeview_ctrl_click(self, event) -> None:
        """Appeler au Ctrl+clic pour sélection multiple."""
        item = self.treeview.identify("item", event.x, event.y)
        if item:
            if item in self.selected_tracks:
                self.selected_tracks.remove(item)
            else:
                self.selected_tracks.add(item)
            self._update_selection_label()
    
    def _on_details_click(self) -> None:
        """Appeler quand le bouton Voir détails est cliqué."""
        if self.selected_tracks:
            messagebox.showinfo("Détails", f"Détails de {len(self.selected_tracks)} morceau(x)")
        else:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner au moins un morceau")
    
    def _on_correct_click(self) -> None:
        """Appeler quand le bouton Corriger sélection est cliqué."""
        if self.selected_tracks:
            messagebox.showinfo("Correction", "Ouverture du dialogue de correction...")
        else:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner au moins un morceau")
    
    def _on_config_click(self) -> None:
        """Appeler quand le bouton Config est cliqué."""
        messagebox.showinfo("Configuration", "Paramètres:\n- Seuil de match\n- Chemins DB\n- Préférences UI")
    
    def _on_suggestions_click(self) -> None:
        """Appeler pour voir les suggestions de match."""
        messagebox.showinfo("Suggestions", "Affichage des meilleures correspondances...")
    
    def _on_ignore_click(self) -> None:
        """Ignorer un morceau."""
        messagebox.showinfo("Ignorer", "Ce morceau a été ignoré.")
    
    def _on_mark_resolved_click(self) -> None:
        """Marquer comme résolu."""
        messagebox.showinfo("Résolu", "Ce morceau a été marqué comme résolu.")
    
    def _update_selection_label(self) -> None:
        """Mettre à jour le label du compteur de sélection."""
        total = len(self.filtered_tracks)
        selected = len(self.selected_tracks)
        self.selection_label.config(text=f"Sélectionnés : {selected}/{total}")
    
    def _update_statusbar(self) -> None:
        """Mettre à jour la barre de statut."""
        if self.db_path:
            self.db_label.config(text=f"Connecté à {self.db_path}")
        else:
            self.db_label.config(text="Pas de connexion DB")
    
    def _load_tracks_from_db(self) -> None:
        """Charger tous les tracks depuis la base de données."""
        if not self.db_manager:
            return
        
        try:
            # Afficher un message de chargement
            self.treeview.delete(*self.treeview.get_children())
            self.treeview.insert('', 'end', values=('Chargement...', 'Veuillez patienter', '(En cours)', '...', '...'))
            self.update()
            
            # Récupérer TOUS les tracks d'abord (sans les afficher)
            tracks_to_display = []
            
            with self.db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        tp.urlmd5,
                        tp.url,
                        tp.playCount,
                        tp.lastPlayed,
                        tp.rating,
                        CASE WHEN ap.urlmd5 IS NULL THEN 0 ELSE 1 END as has_alternative
                    FROM tracks_persistent tp
                    LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
                    ORDER BY tp.url
                """)
                
                for row in cursor.fetchall():
                    has_alternative = row[5] == 1
                    
                    # N'afficher que les tracks SANS alternative (désynchronisés)
                    if has_alternative:
                        continue
                    
                    # Extraire le titre et l'artiste de l'URL (format: artiste/album/titre)
                    url = row[1] or 'Unknown'
                    parts = url.split('/')
                    
                    if len(parts) >= 3:
                        artist = parts[-3]
                        album = parts[-2]
                        title = parts[-1].replace('.mp3', '').replace('.flac', '')
                    elif len(parts) >= 2:
                        artist = parts[-2]
                        title = parts[-1].replace('.mp3', '').replace('.flac', '')
                        album = 'Unknown Album'
                    else:
                        artist = 'Unknown Artist'
                        title = url.replace('.mp3', '').replace('.flac', '')
                        album = 'Unknown Album'
                    
                    track_data = {
                        'urlmd5': row[0],
                        'title': title,
                        'artist': artist,
                        'album': album,
                        'url': url,
                        'playcount': row[2] or 0,
                        'lastplayed': row[3],
                        'rating': row[4],
                        'has_alternative': has_alternative
                    }
                    self.all_tracks.append(track_data)
                    
                    # Afficher comme manquant
                    match_str = "✗ Manquant"
                    
                    tracks_to_display.append((
                        track_data['artist'],
                        track_data['title'],
                        track_data['album'],
                        track_data['playcount'],
                        match_str
                    ))
            
            # Maintenant afficher tous les tracks en batch
            self.treeview.delete(*self.treeview.get_children())
            for i, track_values in enumerate(tracks_to_display):
                self.treeview.insert('', 'end', values=track_values)
                # Mettre à jour l'interface tous les 100 items
                if (i + 1) % 100 == 0:
                    self.update()
            
            self.filtered_tracks = self.all_tracks.copy()
            self._update_statusbar()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des tracks: {e}")
    
    def _update_clock(self) -> None:
        """Mettre à jour l'horloge."""
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.after(1000, self._update_clock)
    
    def add_track(self, artist: str, title: str, album: str, playcount: int, match_score: float) -> None:
        """Ajouter un morceau à la liste."""
        if match_score >= 90:
            match_str = f"✓ {match_score:.0f}%"
        elif match_score >= 60:
            match_str = f"⚠ {match_score:.0f}%"
        else:
            match_str = f"✗ {match_score:.0f}%"
        
        track_data = (artist, title, album, str(playcount), match_str)
        tags = self._get_match_tags(match_str)
        
        self.treeview.insert("", tk.END, values=track_data, tags=tags)
        self.all_tracks.append(track_data)
    
    def clear_tracks(self) -> None:
        """Effacer tous les morceaux."""
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        self.all_tracks.clear()
        self.filtered_tracks.clear()
        self.selected_tracks.clear()
    
    def get_selected_tracks(self) -> list:
        """Obtenir les morceaux sélectionnés."""
        selected = []
        for item in self.selected_tracks:
            values = self.treeview.item(item, "values")
            selected.append(values)
        return selected
    
    def update_status(self, message: str) -> None:
        """Mettre à jour le message de statut."""
        self.db_label.config(text=message)
    
    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        """Afficher un message à l'utilisateur."""
        if message_type == "warning":
            messagebox.showwarning(title, message)
        elif message_type == "error":
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
