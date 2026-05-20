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

from src.utils.config import Config
from src.utils.remote_sync import RemoteSync


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
        self.alternative_tracks = {}  # Tous les tracks de alternativeplaycount
        
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
    
    def _create_treeview_section(self, parent: ttk.Frame) -> None:
        """Créer la Treeview pour afficher les morceaux."""
        treeview_frame = ttk.LabelFrame(
            parent,
            text="Morceaux manquants dans alternativeplaycount",
            padding=5
        )
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("Artiste", "Titre", "Album", "Écoutes (persist)", "Écoutes (alt)", "Dernier (persist)", "Dernier (alt)", "Correspondance")
        self.treeview = ttk.Treeview(
            treeview_frame,
            columns=columns,
            height=12,
            show="headings"
        )
        
        self.treeview.heading("#0", text="")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        
        widths = [120, 200, 150, 80, 80, 100, 100, 80]
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
            ("Queen", "Bohemian Rhapsody", "A Night at the Opera", "42", "", "2024-01-15", "", "✓ 95%"),
            ("The Beatles", "Hey Jude", "Past Masters", "38", "", "2023-12-20", "", "⚠ 68%"),
            ("Pink Floyd", "Comfortably Numb", "The Wall", "55", "", "2024-02-01", "", "✗ 45%"),
            ("Led Zeppelin", "Stairway to Heaven", "Led Zeppelin IV", "71", "", "2024-01-30", "", "✓ 92%"),
            ("David Bowie", "Space Oddity", "Space Oddity", "28", "", "2023-11-10", "", "⚠ 75%"),
            ("The Rolling Stones", "Sympathy for the Devil", "Beggars Banquet", "33", "", "2024-01-05", "", "✗ 38%"),
        ]
        
        for data in example_data:
            tags = self._get_match_tags(data[4])
            self.treeview.insert("", tk.END, values=data, tags=tags)
            
            # Créer dict pour all_tracks (compatible avec sync_with_best_match)
            track_data = {
                'urlmd5': None,
                'title': data[1],
                'artist': data[0],
                'album': data[2],
                'url': '',
                'persist_playcount': int(data[3]) if data[3].isdigit() else 0,
                'persist_lastplayed': None,
                'rating': None,
                'alt_playcount': None,
                'alt_lastplayed': None
            }
            self.all_tracks.append(track_data)
        
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
        
        ttk.Button(actions_frame, text="⚡ Sync sélection", command=self._sync_selected_tracks).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="🚫 Ignorer", command=self._ignore_selected_tracks).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="⚙️ Config", command=self._on_config_click).pack(side=tk.LEFT, padx=2)

        cfg = Config.instance()
        if cfg.remote.is_configured():
            self.push_btn = ttk.Button(
                actions_frame,
                text="⬆ Mettre à jour BD distante",
                command=self._push_remote_db,
            )
            self.push_btn.pack(side=tk.RIGHT, padx=2)

            self.fetch_btn = ttk.Button(
                actions_frame,
                text="⬇ Récupérer BD distante",
                command=self._fetch_remote_db,
            )
            self.fetch_btn.pack(side=tk.RIGHT, padx=2)
    
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
    
    def _on_treeview_double_click(self, event) -> None:
        """Appeler au double-clic sur un morceau."""
        selection = self.treeview.selection()
        if selection:
            values = self.treeview.item(selection[0], "values")
            messagebox.showinfo(
                "Détails du morceau",
                f"Artiste : {values[0]}\nTitre : {values[1]}\nAlbum : {values[2]}\nÉcoutes : {values[3]}\nCorrespondance : {values[7]}"
            )
    
    def _on_treeview_right_click(self, event) -> None:
        """Afficher le menu contextuel au clic-droit."""
        item = self.treeview.identify("item", event.x, event.y)
        if item:
            self.treeview.selection_set(item)
            menu = tk.Menu(self, tearoff=False)
            menu.add_command(label="Voir les suggestions", command=self._on_suggestions_click)
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
    
    def _sync_selected_tracks(self) -> None:
        """Synchroniser les morceaux sélectionnés avec le meilleur match."""
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner au moins un morceau")
            return
        
        synced_count = 0
        for item in selection:
            values = self.treeview.item(item, "values")
            if len(values) >= 6:
                artist = values[0]
                title = values[1]
                persist_play = values[3]
                print(f"[INFO] Traitement: {artist} - {title} (playcount={persist_play})")
                
                # Trouver le meilleur match dans alternative_tracks
                best_match = None
                best_score = 0
                for alt_urlmd5, alt_track in self.alternative_tracks.items():
                    artist_score = self._string_similarity(artist.lower(), alt_track['artist'].lower()) * 0.3
                    title_score = self._string_similarity(title.lower(), alt_track['title'].lower()) * 0.7
                    total_score = (artist_score + title_score) * 100
                    
                    if total_score > best_score:
                        best_score = total_score
                        best_match = alt_urlmd5
                
                print(f"[INFO] Meilleur match trouvé: score={best_score:.0f}%")
                # Si on a trouvé un match avec score >= 60, faire la synchro
                if best_match and best_score >= 60:
                    try:
                        alt_track = self.alternative_tracks[best_match]
                        # Récupérer l'urlmd5 et persist_lastplayed du morceau persist via all_tracks
                        persist_urlmd5 = None
                        persist_lastplayed = None
                        
                        for track in self.all_tracks:
                            if isinstance(track, dict) and track.get('artist') == artist and track.get('title') == title:
                                persist_urlmd5 = track['urlmd5']
                                persist_lastplayed = track['persist_lastplayed']
                                break
                        
                        print(f"[INFO] Track persist trouvé: urlmd5={persist_urlmd5}")
                        if persist_urlmd5:
                            # Mettre à jour alternativeplaycount avec playcount et lastplayed de persist
                            print(f"[INFO] Mise à jour alternativeplaycount: playCount={persist_play}, lastPlayed={persist_lastplayed}")
                            with self.db_manager.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE alternativeplaycount 
                                    SET playCount = ?, lastPlayed = ?
                                    WHERE urlmd5 = ?
                                """, (persist_play, persist_lastplayed, best_match))
                            print(f"[INFO] ✓ alternativeplaycount mis à jour")
                            
                            # Supprimer de tracks_persistent
                            print(f"[INFO] Suppression de tracks_persistent: {persist_urlmd5}")
                            with self.db_manager.cursor() as cursor:
                                cursor.execute("DELETE FROM tracks_persistent WHERE urlmd5 = ?", (persist_urlmd5,))
                            print(f"[INFO] ✓ tracks_persistent supprimé")
                            
                            # Supprimer de la vue
                            self.treeview.delete(item)
                            synced_count += 1
                            print(f"[INFO] ✓ Synchronisation complétée pour: {artist} - {title}")
                    except Exception as e:
                        print(f"[ERROR] Exception: {e}")
                        messagebox.showerror("Erreur sync", f"Erreur lors de la synchronisation: {e}")
                else:
                    if best_match:
                        print(f"[INFO] Score insuffisant ({best_score:.0f}% < 60%) pour sync")
                    else:
                        print(f"[INFO] Aucun match trouvé pour ce morceau")
        
        if synced_count > 0:
            messagebox.showinfo("Succès", f"{synced_count} morceau(x) synchronisé(s) avec alternativeplaycount")
            print(f"[INFO] Total synchronisé: {synced_count} morceau(x)")
        else:
            messagebox.showwarning("Pas de synchronisation", "Aucune correspondance avec un score ≥ 60% trouvée")
    
    def _ignore_selected_tracks(self) -> None:
        """Ignorer les morceaux sélectionnés (les supprimer de la table persist et de la vue)."""
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner au moins un morceau")
            return
        
        count = 0
        for item in selection:
            values = self.treeview.item(item, "values")
            if len(values) >= 2:
                artist = values[0]
                title = values[1]
                
                # Trouver l'urlmd5 du morceau dans all_tracks
                persist_urlmd5 = None
                for track in self.all_tracks:
                    if isinstance(track, dict) and track.get('artist') == artist and track.get('title') == title:
                        persist_urlmd5 = track['urlmd5']
                        break
                
                if persist_urlmd5:
                    try:
                        # Supprimer de la table tracks_persistent
                        print(f"[INFO] Suppression ignorée de persist: {persist_urlmd5}")
                        with self.db_manager.cursor() as cursor:
                            cursor.execute("DELETE FROM tracks_persistent WHERE urlmd5 = ?", (persist_urlmd5,))
                        print(f"[INFO] ✓ {artist} - {title} supprimé de persist")
                        count += 1
                    except Exception as e:
                        print(f"[ERROR] Exception: {e}")
                        messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
                        continue
            
            # Supprimer de la vue
            self.treeview.delete(item)
        
        if count > 0:
            messagebox.showinfo("Succès", f"{count} morceau(x) ignoré(s) et supprimé(s) de persist")
            print(f"[INFO] Total ignoré: {count} morceau(x)")
        else:
            messagebox.showwarning("Erreur", "Aucun morceau n'a pu être supprimé")
    
    def _on_config_click(self) -> None:
        """Ouvrir la fenêtre de configuration."""
        cfg = Config.instance()

        win = tk.Toplevel(self)
        win.title("Configuration")
        win.resizable(False, False)
        win.grab_set()

        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ── Onglet Général ──────────────────────────────────────────────
        tab_general = ttk.Frame(notebook, padding=15)
        notebook.add(tab_general, text="Général")

        ttk.Label(tab_general, text="Seuil de correspondance automatique (%) :").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))

        threshold_var = tk.IntVar(value=cfg.matching.auto_match_threshold)
        threshold_label = ttk.Label(tab_general, text=f"{threshold_var.get()}%", width=5)

        def _on_threshold(val):
            threshold_label.config(text=f"{int(float(val))}%")

        scale = ttk.Scale(tab_general, from_=0, to=100, orient=tk.HORIZONTAL,
                          variable=threshold_var, command=_on_threshold)
        scale.grid(row=1, column=0, sticky=tk.EW, pady=(0, 15))
        threshold_label.grid(row=1, column=1, padx=(8, 0))
        tab_general.columnconfigure(0, weight=1)

        ttk.Label(tab_general, text="Base de données :").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))
        ttk.Label(tab_general, text=str(self.db_path), foreground="gray").grid(
            row=3, column=0, columnspan=2, sticky=tk.W)

        # ── Onglet Serveur distant ───────────────────────────────────────
        tab_remote = ttk.Frame(notebook, padding=15)
        notebook.add(tab_remote, text="Serveur distant")

        remote = cfg.remote

        host_var     = tk.StringVar(value=remote.host)
        user_var     = tk.StringVar(value=remote.user)
        dbpath_var   = tk.StringVar(value=remote.db_path)
        port_var     = tk.StringVar(value=str(remote.ssh_port))
        timeout_var  = tk.StringVar(value=str(remote.timeout))

        fields = [
            ("Hôte :",           host_var),
            ("Utilisateur :",    user_var),
            ("Chemin distant :", dbpath_var),
            ("Port SSH :",       port_var),
            ("Délai (s) :",      timeout_var),
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(tab_remote, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            ttk.Entry(tab_remote, textvariable=var, width=35).grid(
                row=i, column=1, sticky=tk.EW, padx=(10, 0), pady=3)

        tab_remote.columnconfigure(1, weight=1)

        # ── Boutons ──────────────────────────────────────────────────────
        btn_frame = ttk.Frame(win, padding=(10, 0, 10, 10))
        btn_frame.pack(fill=tk.X)

        def _apply():
            # Général
            cfg.matching.auto_match_threshold = threshold_var.get()

            # Remote
            cfg.remote.host    = host_var.get().strip()
            cfg.remote.user    = user_var.get().strip()
            cfg.remote.db_path = dbpath_var.get().strip()
            try:
                cfg.remote.ssh_port = int(port_var.get())
            except ValueError:
                pass
            try:
                cfg.remote.timeout = int(timeout_var.get())
            except ValueError:
                pass

            cfg.save_to_file("config.yaml")

            # Activer/désactiver les boutons remote selon host+user
            if hasattr(self, "fetch_btn"):
                state = tk.NORMAL if cfg.remote.is_configured() else tk.DISABLED
                self.fetch_btn.config(state=state)
                self.push_btn.config(state=state)

            messagebox.showinfo("Succès", "Configuration sauvegardée.")
            win.destroy()

        ttk.Button(btn_frame, text="Appliquer", command=_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Fermer", command=win.destroy).pack(side=tk.LEFT, padx=5)

        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")
    
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
        suggestions_window.title(f"Suggestions pour : {artist} - {title}")
        suggestions_window.geometry("600x400")
        
        # Frame pour la recherche
        search_frame = ttk.Frame(suggestions_window)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text=f"Morceaux similaires à : {artist} - {title}").pack()
        
        # Treeview pour les suggestions
        tree = ttk.Treeview(suggestions_window, columns=('Artist', 'Title', 'Score'), height=15)
        tree.column('#0', width=0, stretch=tk.NO)
        tree.column('Artist', anchor=tk.W, width=150)
        tree.column('Title', anchor=tk.W, width=300)
        tree.column('Score', anchor=tk.CENTER, width=80)
        
        tree.heading('#0', text='', anchor=tk.W)
        tree.heading('Artist', text='Artiste', anchor=tk.W)
        tree.heading('Title', text='Titre', anchor=tk.W)
        tree.heading('Score', text='Score', anchor=tk.CENTER)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Récupérer les meilleures suggestions
        suggestions = []
        if self.db_manager:
            try:
                # Utiliser les tracks alternatifs déjà chargés en mémoire
                # (ils contiennent tous les 23k+ tracks)
                for alt_urlmd5, alt_track in self.alternative_tracks.items():
                    alt_artist = alt_track['artist']
                    alt_title = alt_track['title']
                    
                    # Calculer score
                    artist_score = self._string_similarity(artist.lower(), alt_artist.lower()) * 0.3
                    title_score = self._string_similarity(title.lower(), alt_title.lower()) * 0.7
                    total_score = (artist_score + title_score) * 100
                    
                    suggestions.append((alt_artist, alt_title, total_score))
                
                # Trier par score décroissant
                suggestions.sort(key=lambda x: x[2], reverse=True)
                
                # Afficher les top 20
                for i, (alt_artist, alt_title, score) in enumerate(suggestions[:20]):
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
        artist = values[0]
        title = values[1]
        album = values[2]
        persist_play = values[3]
        alt_play = values[4]
        match = values[5]

        # Afficher les détails du morceau résolut
        messagebox.showinfo(
            "Morceau résolu",
            f"Le morceau '{artist} - {title}' a été marqué comme résolu.\n\n"
            f"Correspondance : {match}\n"
            f"Écoutes (persist) : {persist_play}\n"
            f"Écoutes (alt) : {alt_play}\n"
            f"Les écoutes seront synchronisées."
        )
        
        # Marquer comme résolu en changeant la couleur
        self.treeview.item(item, tags=('resolved',))
        
        # Créer la balance de résolu
        self.treeview.tag_configure('resolved', foreground='green')

    
    def _ask_yes_no(self, title: str, message: str) -> bool:
        """Boîte de dialogue Oui/Non centrée sur la fenêtre principale."""
        result = tk.BooleanVar(value=False)

        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.grab_set()

        ttk.Label(dlg, text=message, justify=tk.CENTER, padding=20).pack()

        btn_frame = ttk.Frame(dlg, padding=(0, 0, 0, 15))
        btn_frame.pack()

        def on_oui():
            result.set(True)
            dlg.destroy()

        ttk.Button(btn_frame, text="Oui", width=10, command=on_oui).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Non", width=10, command=dlg.destroy).pack(side=tk.LEFT, padx=10)

        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dlg.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

        self.wait_window(dlg)
        return result.get()

    def _confirm_lms_stopped(self) -> bool:
        """Afficher l'alerte LMS et retourner True si l'utilisateur confirme."""
        return self._ask_yes_no(
            "⚠ LMS doit être arrêté",
            "Avant tout transfert, Lyrion Media Server (LMS) doit être\n"
            "arrêté sur la machine distante pour éviter la corruption\n"
            "de la base de données.\n\n"
            "Avez-vous bien arrêté LMS avant de continuer ?",
        )

    def _push_remote_db(self) -> None:
        """Envoyer la BD locale vers l'hôte distant."""
        if not self._confirm_lms_stopped():
            return

        cfg = Config.instance()
        remote = cfg.remote

        if not self._ask_yes_no(
            "Confirmer l'envoi",
            f"Écraser la base de données sur {remote.host} ?\n\n"
            f"Source : {cfg.database.path}\n"
            f"Destination : {remote.user}@{remote.host}:{remote.db_path}",
        ):
            return

        self.push_btn.config(state=tk.DISABLED, text="⬆ Envoi…")
        self.update_status(f"Envoi vers {remote.user}@{remote.host}…")
        self.update()

        try:
            syncer = RemoteSync(remote)
            success = syncer.upload(cfg.database.path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Envoi impossible : {e}")
            self.push_btn.config(state=tk.NORMAL, text="⬆ Mettre à jour BD distante")
            return

        if not success:
            messagebox.showerror(
                "Échec",
                f"Impossible d'envoyer la base de données vers {remote.host}.\n"
                "Vérifiez que l'hôte est accessible et que la clé SSH est configurée.",
            )
        else:
            messagebox.showinfo("Succès", f"Base de données envoyée vers {remote.host}.")
            self._update_statusbar()

        self.push_btn.config(state=tk.NORMAL, text="⬆ Mettre à jour BD distante")

    def _fetch_remote_db(self) -> None:
        """Récupérer persist.db depuis l'hôte distant puis recharger les données."""
        if not self._confirm_lms_stopped():
            return

        cfg = Config.instance()
        remote = cfg.remote

        self.fetch_btn.config(state=tk.DISABLED, text="⬇ Récupération…")
        self.update_status(f"Connexion à {remote.user}@{remote.host}…")
        self.update()

        try:
            syncer = RemoteSync(remote)
            success = syncer.fetch(cfg.database.path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Récupération distante impossible : {e}")
            self.fetch_btn.config(state=tk.NORMAL, text="⬇ Récupérer BD distante")
            return

        if not success:
            messagebox.showerror(
                "Échec",
                f"Impossible de récupérer la base de données depuis {remote.host}.\n"
                "Vérifiez que l'hôte est accessible et que la clé SSH est configurée.",
            )
            self.fetch_btn.config(state=tk.NORMAL, text="⬇ Récupérer BD distante")
            return

        # Reconnecter et recharger
        try:
            if self.db_manager:
                self.db_manager.close()
                self.db_manager.connect()
        except Exception as e:
            messagebox.showerror("Erreur BD", f"Reconnexion impossible : {e}")
            self.fetch_btn.config(state=tk.NORMAL, text="⬇ Récupérer BD distante")
            return

        self.all_tracks.clear()
        self.filtered_tracks.clear()
        self.selected_tracks.clear()
        self._load_tracks_from_db()
        self._update_statusbar()
        self.fetch_btn.config(state=tk.NORMAL, text="⬇ Récupérer BD distante")
        messagebox.showinfo("Succès", "Base de données récupérée et rechargée.")

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
            self.treeview.insert('', 'end', values=('Chargement...', 'Veuillez patienter', '(En cours)', '...', '...', '...'))
            self.update()
            
            # Récupérer d'abord TOUS les morceaux de alternativeplaycount pour le matching
            self.alternative_tracks = {}
            with self.db_manager.cursor(commit=False) as cursor:
                cursor.execute("SELECT urlmd5, url, playCount, lastPlayed FROM alternativeplaycount")
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
                    self.alternative_tracks[row[0]] = {
                        'artist': artist,
                        'title': title,
                        'url': url,
                        'playCount': row[2] or 0,
                        'lastPlayed': row[3]
                    }
            
            # Récupérer les tracks (avec données alternative si présentes)
            tracks_to_display = []
            with self.db_manager.cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        tp.urlmd5,
                        tp.url,
                        tp.playCount AS persist_playcount,
                        tp.lastPlayed AS persist_lastplayed,
                        tp.rating,
                        ap.playCount AS alt_playcount,
                        ap.lastPlayed AS alt_lastplayed,
                        ap.url AS alt_url
                    FROM tracks_persistent tp
                    LEFT JOIN alternativeplaycount ap ON tp.urlmd5 = ap.urlmd5
                    WHERE ap.urlmd5 IS NULL
                    ORDER BY tp.url
                """)

                for row in cursor.fetchall():
                    # Extraire le titre et l'artiste de l'URL (persist)
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

                    persist_playcount = row[2] or 0
                    persist_lastplayed = row[3]
                    rating = row[4]
                    alt_playcount = row[5]
                    alt_lastplayed = row[6]

                    track_data = {
                        'urlmd5': row[0],
                        'title': title,
                        'artist': artist,
                        'album': album,
                        'url': url,
                        'persist_playcount': persist_playcount,
                        'persist_lastplayed': persist_lastplayed,
                        'rating': rating,
                        'alt_playcount': alt_playcount,
                        'alt_lastplayed': alt_lastplayed
                    }
                    self.all_tracks.append(track_data)
                    
                    # Déterminer le statut : tous les éléments affichés sont manquants
                    match_str = "✗ 0%"
                    best_alt_playcount = None
                    best_alt_lastplayed = None
                    if self.matcher and self.alternative_tracks:
                        best_score = 0
                        best_match_urlmd5 = None
                        for alt_urlmd5, alt_track in self.alternative_tracks.items():
                            # Comparer artiste et titre
                            artist_score = self._string_similarity(artist.lower(), alt_track['artist'].lower()) * 0.3
                            title_score = self._string_similarity(title.lower(), alt_track['title'].lower()) * 0.7
                            total_score = (artist_score + title_score) * 100
                            
                            if total_score > best_score:
                                best_score = total_score
                                best_match_urlmd5 = alt_urlmd5
                        
                        if best_score > 0:
                            match_str = f"⚠ {best_score:.0f}%" if best_score < 90 else f"✓ {best_score:.0f}%"
                            # Récupérer le playcount et lastplayed du meilleur match trouvé
                            if best_match_urlmd5 and best_match_urlmd5 in self.alternative_tracks:
                                best_alt_playcount = self.alternative_tracks[best_match_urlmd5].get('playCount')
                                best_alt_lastplayed = self.alternative_tracks[best_match_urlmd5].get('lastPlayed')

                    # Formater les dates lastPlayed
                    persist_lastplayed_str = self._format_timestamp(persist_lastplayed) if persist_lastplayed else ''
                    alt_lastplayed_str = self._format_timestamp(best_alt_lastplayed) if best_alt_lastplayed else ''
                    
                    tracks_to_display.append(
                        (
                            track_data['artist'],
                            track_data['title'],
                            track_data['album'],
                            str(track_data.get('persist_playcount', 0)),
                            str(best_alt_playcount if best_alt_playcount is not None else ''),
                            persist_lastplayed_str,
                            alt_lastplayed_str,
                            match_str
                        )
                    )
            
            # Maintenant afficher tous les tracks en batch
            self.treeview.delete(*self.treeview.get_children())
            for i, track_values in enumerate(tracks_to_display):
                # Appliquer tags de couleur basés sur le champ match (dernier)
                match_field = track_values[-1]
                tags = self._get_match_tags(match_field)
                self.treeview.insert('', 'end', values=track_values, tags=tags)
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
    
    def _format_timestamp(self, timestamp) -> str:
        """Formater un timestamp Unix en date lisible (YYYY-MM-DD)."""
        if timestamp is None:
            return ''
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        except (ValueError, OSError, TypeError):
            return ''
    
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
        
        # Créer tuple pour la treeview
        track_tuple = (artist, title, album, str(playcount), "", match_str)
        tags = self._get_match_tags(match_str)
        
        self.treeview.insert("", tk.END, values=track_tuple, tags=tags)
        
        # Créer dict pour all_tracks (compatible avec sync_with_best_match)
        track_data = {
            'urlmd5': None,
            'title': title,
            'artist': artist,
            'album': album,
            'url': '',
            'persist_playcount': playcount,
            'persist_lastplayed': None,
            'rating': None,
            'alt_playcount': None,
            'alt_lastplayed': None
        }
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
