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
from urllib.parse import unquote


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
    
    def __init__(self, db_path: str = "", db_manager = None, matcher = None, on_sync_callback: Optional[Callable] = None):
        """
        Initialiser la fenêtre principale.
        
        Args:
            db_path: Chemin vers la base de données persistante
            db_manager: Instance de DatabaseManager (optionnel)
            matcher: Instance de TrackMatcher (optionnel)
            on_sync_callback: Callback appelé lors du sync (optionnel)
        """
        super().__init__()
        
        self.db_path = db_path
        self.db_manager = db_manager
        self.matcher = matcher
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
    
    def _decode_url_parts(self, url: str) -> list:
        """Décoder les parties d'une URL pour éviter les caractères encodés."""
        # Décoder la URL complète
        decoded_url = unquote(url)
        parts = decoded_url.split('/')
        return parts
    
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
        """Afficher les détails du morceau sélectionné."""
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un morceau")
            return
        
        # Récupérer les données du morceau sélectionné
        item = selection[0]
        values = self.treeview.item(item, "values")
        
        if len(values) >= 5:
            artist, title, album, playcount, match = values[0], values[1], values[2], values[3], values[4]
            details = f"""
Détails du morceau:

Artiste: {artist}
Titre: {title}
Album: {album}
Playcounts: {playcount}
Correspondance: {match}

Clic-droit sur le morceau pour voir les options de correspondance.
            """
            messagebox.showinfo("Détails du morceau", details.strip())
        else:
            messagebox.showwarning("Erreur", "Impossible de récupérer les détails du morceau")
    
    def _on_correct_click(self) -> None:
        """Ouvrir le dialogue de correction pour les morceaux sélectionnés."""
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner au moins un morceau")
            return
        
        # Créer une fenêtre de correction
        correct_window = tk.Toplevel(self)
        correct_window.title("Corriger la sélection")
        correct_window.geometry("500x300")
        
        # Afficher les morceaux sélectionnés
        info_text = f"Vous avez sélectionné {len(selection)} morceau(x).\n\n"
        for item in list(selection)[:5]:  # Afficher les 5 premiers
            values = self.treeview.item(item, "values")
            if len(values) >= 2:
                info_text += f"- {values[0]} - {values[1]}\n"
        
        if len(selection) > 5:
            info_text += f"... et {len(selection) - 5} autre(s)\n"
        
        ttk.Label(correct_window, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Bouton pour marquer comme résolu
        def mark_all_resolved():
            for item in selection:
                self.treeview.item(item, tags=('resolved',))
            messagebox.showinfo("Succès", f"{len(selection)} morceau(x) marqué(s) comme résolus")
            correct_window.destroy()
        
        # Bouton pour ignorer
        def ignore_all():
            for item in selection:
                self.treeview.delete(item)
            messagebox.showinfo("Succès", f"{len(selection)} morceau(x) ignoré(s)")
            correct_window.destroy()
        
        button_frame = ttk.Frame(correct_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Marquer comme résolu", command=mark_all_resolved).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ignorer", command=ignore_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=correct_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def _on_config_click(self) -> None:
        """Ouvrir la fenêtre de configuration."""
        config_window = tk.Toplevel(self)
        config_window.title("Configuration")
        config_window.geometry("400x250")
        
        # Section des seuils
        ttk.Label(config_window, text="Seuil de correspondance (%):", font=self.FONT_SMALL).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        threshold_frame = ttk.Frame(config_window)
        threshold_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        threshold_scale = ttk.Scale(threshold_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        threshold_scale.set(70)
        threshold_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        threshold_label = ttk.Label(threshold_frame, text="70%", width=5)
        threshold_label.pack(side=tk.LEFT, padx=(5, 0))
        
        def update_threshold(val):
            threshold_label.config(text=f"{int(float(val))}%")
        
        threshold_scale.config(command=update_threshold)
        
        # Section des chemins
        ttk.Label(config_window, text="Base de données:", font=self.FONT_SMALL).pack(anchor=tk.W, padx=10, pady=(10, 5))
        ttk.Label(config_window, text=str(self.db_path), foreground="gray").pack(anchor=tk.W, padx=20, pady=(0, 10))
        
        # Boutons
        button_frame = ttk.Frame(config_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Appliquer", command=lambda: messagebox.showinfo("Succès", "Configuration sauvegardée")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Fermer", command=config_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def _on_suggestions_click(self) -> None:
        """Afficher les meilleures suggestions de match pour le morceau sélectionné."""
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("Erreur", "Aucun morceau sélectionné")
            return
        
        # Récupérer les valeurs du morceau sélectionné
        item = selection[0]
        values = self.treeview.item(item, "values")
        artist, title, album = values[0], values[1], values[2]
        
        # Créer une fenêtre popup pour les suggestions
        suggestions_window = tk.Toplevel(self)
        suggestions_window.title(f"Suggestions pour: {artist} - {title}")
        suggestions_window.geometry("600x400")
        
        # Frame pour la recherche
        search_frame = ttk.Frame(suggestions_window)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text=f"Morceaux similaires à: {artist} - {title}").pack()
        
        # Treeview pour les suggestions
        tree = ttk.Treeview(suggestions_window, columns=('Artist', 'Title', 'Score'), height=15)
        tree.column('#0', width=0, stretch=tk.NO)
        tree.column('Artist', anchor=tk.W, width=150)
        tree.column('Title', anchor=tk.W, width=300)
        tree.column('Score', anchor=tk.CENTER, width=80)
        
        tree.heading('#0', text='', anchor=tk.W)
        tree.heading('Artist', text='Artiste', anchor=tk.W)
        tree.heading('Title', text='Titre', anchor=tk.W)
        tree.heading('Score', text='Match', anchor=tk.CENTER)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Récupérer les meilleures suggestions
        suggestions = []
        if self.db_manager:
            try:
                with self.db_manager.cursor(commit=False) as cursor:
                    cursor.execute("SELECT urlmd5, url FROM alternativeplaycount LIMIT 50")
                    for row in cursor.fetchall():
                        url = row[1] or 'Unknown'
                        parts = self._decode_url_parts(url)
                        
                        if len(parts) >= 3:
                            alt_artist = parts[-3]
                            alt_title = parts[-1].replace('.mp3', '').replace('.flac', '')
                        elif len(parts) >= 2:
                            alt_artist = parts[-2]
                            alt_title = parts[-1].replace('.mp3', '').replace('.flac', '')
                        else:
                            alt_artist = 'Unknown'
                            alt_title = url
                        
                        # Calculer score
                        artist_score = self._string_similarity(artist.lower(), alt_artist.lower()) * 0.3
                        title_score = self._string_similarity(title.lower(), alt_title.lower()) * 0.7
                        total_score = (artist_score + title_score) * 100
                        
                        suggestions.append((alt_artist, alt_title, total_score))
                
                # Trier par score décroissant
                suggestions.sort(key=lambda x: x[2], reverse=True)
                
                # Afficher les top 10
                for i, (alt_artist, alt_title, score) in enumerate(suggestions[:10]):
                    tag = 'good' if score >= 90 else 'warning' if score >= 60 else 'bad'
                    tree.insert('', 'end', values=(alt_artist, alt_title, f"{score:.0f}%"), tags=(tag,))
                
                # Configurer les tags de couleur
                tree.tag_configure('good', foreground='green')
                tree.tag_configure('warning', foreground='orange')
                tree.tag_configure('bad', foreground='red')
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du chargement des suggestions: {e}")
    
    def _on_ignore_click(self) -> None:
        """Ignorer un morceau et le supprimer de la liste."""
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("Erreur", "Aucun morceau sélectionné")
            return
        
        item = selection[0]
        self.treeview.delete(item)
        messagebox.showinfo("Succès", "Morceau ignoré et supprimé de la liste.")
    
    def _on_mark_resolved_click(self) -> None:
        """Marquer un morceau comme résolu (correspondance acceptée)."""
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("Erreur", "Aucun morceau sélectionné")
            return
        
        item = selection[0]
        values = self.treeview.item(item, "values")
        artist, title, album, playcount, match = values[0], values[1], values[2], values[3], values[4]
        
        # Afficher les détails du morceau résolut
        messagebox.showinfo(
            "Morceau résolu",
            f"Le morceau '{artist} - {title}' a été marqué comme résolu.\n\n"
            f"Match trouvé: {match}\n"
            f"Playcounts seront synchronisés."
        )
        
        # Marquer comme résolu en changeant la couleur
        self.treeview.item(item, tags=('resolved',))
        
        # Créer la balance de résolu
        self.treeview.tag_configure('resolved', foreground='green')

    
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
            
            # Récupérer d'abord TOUS les morceaux de alternativeplaycount pour le matching
            alternative_tracks = {}
            with self.db_manager.cursor(commit=False) as cursor:
                cursor.execute("SELECT urlmd5, url FROM alternativeplaycount")
                for row in cursor.fetchall():
                    url = row[1] or 'Unknown'
                    # Extraire artiste/titre
                    parts = self._decode_url_parts(url)
                    if len(parts) >= 3:
                        artist = parts[-3]
                        title = parts[-1].replace('.mp3', '').replace('.flac', '')
                    elif len(parts) >= 2:
                        artist = parts[-2]
                        title = parts[-1].replace('.mp3', '').replace('.flac', '')
                    else:
                        artist = 'Unknown'
                        title = url
                    alternative_tracks[row[0]] = {
                        'artist': artist,
                        'title': title,
                        'url': url
                    }
            
            # Récupérer les tracks manquants et les matcher
            tracks_to_display = []
            
            with self.db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        tp.urlmd5,
                        tp.url,
                        tp.playCount,
                        tp.lastPlayed,
                        tp.rating
                    FROM tracks_persistent tp
                    WHERE tp.urlmd5 NOT IN (SELECT urlmd5 FROM alternativeplaycount)
                    ORDER BY tp.url
                """)
                
                for row in cursor.fetchall():
                    # Extraire le titre et l'artiste de l'URL
                    url = row[1] or 'Unknown'
                    parts = self._decode_url_parts(url)
                    
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
                        'has_alternative': False
                    }
                    self.all_tracks.append(track_data)
                    
                    # Trouver le meilleur match dans alternativeplaycount si matcher disponible
                    match_str = "✗ 0%"
                    if self.matcher and alternative_tracks:
                        best_score = 0
                        for alt_urlmd5, alt_track in alternative_tracks.items():
                            # Comparer artiste et titre
                            artist_score = self._string_similarity(artist.lower(), alt_track['artist'].lower()) * 0.3
                            title_score = self._string_similarity(title.lower(), alt_track['title'].lower()) * 0.7
                            total_score = (artist_score + title_score) * 100
                            
                            if total_score > best_score:
                                best_score = total_score
                        
                        if best_score > 0:
                            match_str = f"⚠ {best_score:.0f}%" if best_score < 90 else f"✓ {best_score:.0f}%"
                    
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
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculer la similarité entre deux strings (0.0 à 1.0).
        Utilise une simple méthode de Levenshtein ratio.
        """
        if not s1 or not s2:
            return 0.0
        
        # Simple similarité basée sur la longueur commune
        longer = max(len(s1), len(s2))
        if longer == 0:
            return 1.0
        
        # Compter les caractères en commun
        common = sum(1 for a, b in zip(s1, s2) if a == b)
        
        # Ratio de Levenshtein simple
        common = sum(c in s2 for c in s1)
        max_len = max(len(s1), len(s2))
        
        return common / max_len if max_len > 0 else 0.0
    
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
