"""
Interface desktop principale pour la synchronisation des playcounts.

Workflow en 3 étapes :
  1. Analyse DB → liste des pistes désynchronisées
  2. Clic sur une piste → suggestions dans le panneau droit
  3. Choix d'une suggestion → assignation en mémoire → bouton Sync
"""

import os
import sqlite3
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from src.utils.config import Config
from src.utils.remote_sync import RemoteSync, RemoteBusyError
from src.database.queries import SyncDetector


class MainWindow(tk.Tk):
    """Fenêtre principale de l'application Lyrion Playcount Sync."""

    TITLE = "Lyrion Playcount Sync"
    WINDOW_WIDTH = 1250
    WINDOW_HEIGHT = 760
    FONT_MAIN = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)

    COLOR_GOOD = "#2ecc71"
    COLOR_WARNING = "#f39c12"
    COLOR_BAD = "#e74c3c"
    COLOR_NEUTRAL = "#95a5a6"
    COLOR_ASSIGNED = "#3498db"

    def __init__(
        self,
        db_path: str = "",
        db_manager=None,
        matcher=None,
        on_sync_callback: Optional[Callable] = None,
    ):
        super().__init__()

        self.db_path = db_path
        self.db_manager = db_manager
        self.matcher = matcher
        self.on_sync_callback = on_sync_callback

        # Données chargées depuis la DB
        self.missing_tracks: dict = {}       # urlmd5 → track_data dict
        self.alternative_tracks: list = []   # liste pour le matching pool

        # État des assignations (en mémoire, pas encore écrit en DB)
        self.pending_assignments: dict = {}  # persist_urlmd5 → alt_match_dict

        # Mapping treeview item ↔ urlmd5
        self.item_to_urlmd5: dict = {}
        self.urlmd5_to_item: dict = {}

        # Mapping item suggestions → match dict
        self.suggestion_items: dict = {}

        # Pistes ignorées (urlmd5)
        self.ignored_tracks: set = set()

        self.title(self.TITLE)
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(950, 620)

        self._setup_styles()
        self._create_widgets()

        if self.db_manager:
            self._load_tracks_from_db()

        self._update_statusbar()

    # ─── Styles ──────────────────────────────────────────────────────────────

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.configure(
            "StatsTitle.TLabel",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#3498db",
        )
        style.configure(
            "StatsNumber.TLabel",
            font=("Segoe UI", 18, "bold"),
            background="#2c3e50",
            foreground="#2ecc71",
        )
        style.configure("Status.TLabel", font=self.FONT_SMALL, foreground="#95a5a6")
        style.configure("Action.TButton", font=("Segoe UI", 9), padding=(8, 4))
        style.configure("Remote.TButton", font=("Segoe UI", 9), padding=(8, 4), foreground="#1a6fa8")

    # ─── Construction UI ─────────────────────────────────────────────────────

    def _create_widgets(self) -> None:
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._create_stats_section(main_frame)
        self._create_main_section(main_frame)
        self._create_actions_section(main_frame)
        self._create_statusbar()

    def _create_stats_section(self, parent: ttk.Frame) -> None:
        stats_frame = ttk.LabelFrame(parent, text="Statistiques", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 8))

        col_frame = ttk.Frame(stats_frame)
        col_frame.pack(fill=tk.X)

        total_persistent = total_alternative = desynchronized = 0
        if self.db_manager:
            try:
                with self.db_manager.cursor(commit=False) as cursor:
                    cursor.execute("SELECT COUNT(*) FROM tracks_persistent")
                    total_persistent = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM alternativeplaycount")
                    total_alternative = cursor.fetchone()[0]
                    cursor.execute("""
                        SELECT COUNT(*) FROM tracks_persistent
                        WHERE urlmd5 NOT IN (SELECT urlmd5 FROM alternativeplaycount)
                    """)
                    desynchronized = cursor.fetchone()[0]
            except Exception:
                pass

        self._create_stat_card(col_frame, "tracks_persistent", f"{total_persistent:,}")
        self._create_stat_card(col_frame, "alternativeplaycount", f"{total_alternative:,}")
        self._create_stat_card(col_frame, "Désynchronisés", f"{desynchronized:,}")

    def _create_stat_card(self, parent: ttk.Frame, title: str, value: str) -> None:
        card = tk.Frame(parent, bg="#2c3e50", relief=tk.FLAT)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(
            card, text=title,
            font=("Segoe UI", 11, "bold"), bg="#2c3e50", fg="#3498db",
        ).pack(pady=(8, 2))
        tk.Label(
            card, text=value,
            font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="#2ecc71",
        ).pack(pady=(0, 8))

    def _create_main_section(self, parent: ttk.Frame) -> None:
        """Panneau séparé horizontalement : pistes à gauche, suggestions à droite."""
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        left_frame = ttk.LabelFrame(paned, text="Pistes désynchronisées", padding=5)
        right_frame = ttk.LabelFrame(paned, text="Suggestions", padding=5)

        paned.add(left_frame, weight=3)
        paned.add(right_frame, weight=2)

        self._create_tracks_panel(left_frame)
        self._create_suggestions_panel(right_frame)

    def _create_tracks_panel(self, parent: ttk.Frame) -> None:
        columns = ("Artiste", "Titre", "Écoutes", "Statut")
        self.tracks_tree = ttk.Treeview(
            parent, columns=columns, show="headings", selectmode="browse"
        )

        widths = [150, 260, 70, 110]
        for col, width in zip(columns, widths):
            self.tracks_tree.heading(
                col, text=col, command=lambda c=col: self._sort_tracks(c)
            )
            self.tracks_tree.column(col, width=width, anchor=tk.W)

        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tracks_tree.yview)
        self.tracks_tree.configure(yscroll=vsb.set)

        self.tracks_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.tracks_tree.tag_configure("assigned", foreground=self.COLOR_ASSIGNED)
        self.tracks_tree.tag_configure("ignored", foreground=self.COLOR_NEUTRAL)

        self.tracks_tree.bind("<<TreeviewSelect>>", self._on_track_selected)
        self.tracks_tree.bind("<Button-3>", self._on_track_right_click)

    def _create_suggestions_panel(self, parent: ttk.Frame) -> None:
        self.track_info_label = ttk.Label(
            parent,
            text="Cliquer sur une piste pour voir les suggestions",
            font=self.FONT_SMALL,
            wraplength=400,
        )
        self.track_info_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        columns = ("Score", "Artiste", "Titre", "Écoutes")
        self.suggestions_tree = ttk.Treeview(
            parent, columns=columns, show="headings", selectmode="browse"
        )

        widths = [75, 130, 200, 60]
        anchors = [tk.CENTER, tk.W, tk.W, tk.W]
        for col, width, anchor in zip(columns, widths, anchors):
            self.suggestions_tree.heading(col, text=col)
            self.suggestions_tree.column(col, width=width, anchor=anchor)

        vsb2 = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.suggestions_tree.yview)
        self.suggestions_tree.configure(yscroll=vsb2.set)

        self.suggestions_tree.grid(row=1, column=0, sticky="nsew")
        vsb2.grid(row=1, column=1, sticky="ns")
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.suggestions_tree.tag_configure("likely", foreground=self.COLOR_GOOD)
        self.suggestions_tree.tag_configure("possible", foreground=self.COLOR_WARNING)
        self.suggestions_tree.tag_configure("unlikely", foreground=self.COLOR_BAD)
        self.suggestions_tree.tag_configure("current", background="#1a5276")

        self.suggestions_tree.bind("<<TreeviewSelect>>", self._on_suggestion_selected)

    def _create_actions_section(self, parent: ttk.Frame) -> None:
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 6))

        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(0, 8))

        # Groupe 1 — action principale (tk.Button pour l'accent couleur)
        self.sync_btn = tk.Button(
            actions_frame,
            text="Sync assignées (0)",
            command=self._sync_assigned_tracks,
            state=tk.DISABLED,
            font=("Segoe UI", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            activebackground="#27ae60",
            activeforeground="white",
            relief=tk.RAISED,
            padx=10,
            pady=5,
            cursor="arrow",
        )
        self.sync_btn.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Separator(actions_frame, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=6
        )

        # Groupe 2 — actions secondaires (ttk natif, toujours lisible)
        ttk.Button(
            actions_frame, text="Ignorer",
            command=self._ignore_selected_track, style="Action.TButton"
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            actions_frame, text="Recharger",
            command=self._reload_data, style="Action.TButton"
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            actions_frame, text="Configuration",
            command=self._on_config_click, style="Action.TButton"
        ).pack(side=tk.LEFT, padx=2)

        # Groupe 3 — actions distantes (droite, texte bleu distinctif)
        cfg = Config.instance()
        if cfg.remote.is_configured():
            self.push_btn = ttk.Button(
                actions_frame, text="↑ Envoyer",
                command=self._push_remote_db, style="Remote.TButton"
            )
            self.push_btn.pack(side=tk.RIGHT, padx=(2, 0))
            self.fetch_btn = ttk.Button(
                actions_frame, text="↓ Récupérer",
                command=self._fetch_remote_db, style="Remote.TButton"
            )
            self.fetch_btn.pack(side=tk.RIGHT, padx=2)
            ttk.Separator(actions_frame, orient=tk.VERTICAL).pack(
                side=tk.RIGHT, fill=tk.Y, padx=6
            )

    def _create_statusbar(self) -> None:
        statusbar = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)

        self.db_label = ttk.Label(statusbar, text="", style="Status.TLabel")
        self.db_label.pack(side=tk.LEFT, padx=5, pady=2)

        self.status_label = ttk.Label(statusbar, text="", style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT, padx=20, pady=2)

        self.counter_label = ttk.Label(statusbar, text="", style="Status.TLabel")
        self.counter_label.pack(side=tk.RIGHT, padx=10, pady=2)

        self.progress_bar = ttk.Progressbar(statusbar, mode="indeterminate", length=120)
        # Non empaqueté par défaut — affiché à la demande


    # ─── Barre de progression ─────────────────────────────────────────────────

    def _show_progressbar(self, mode: str = "indeterminate", maximum: int = 100) -> None:
        self.progress_bar.config(mode=mode, maximum=maximum, value=0)
        self.progress_bar.pack(side=tk.RIGHT, padx=(0, 8), pady=2)
        if mode == "indeterminate":
            self.progress_bar.start(10)

    def _hide_progressbar(self) -> None:
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    def _update_progress_counter(self) -> None:
        total = len(self.missing_tracks)
        assigned = len(self.pending_assignments)
        ignored = sum(1 for uid in self.ignored_tracks if uid in self.missing_tracks)
        remaining = total - assigned - ignored
        if total == 0:
            self.counter_label.config(text="")
        else:
            self.counter_label.config(
                text=f"{remaining} restante(s)  ·  {assigned} assignée(s)  ·  {ignored} ignorée(s)"
            )

    # ─── Chargement données ───────────────────────────────────────────────────

    def _load_tracks_from_db(self) -> None:
        """Charge les pistes désynchronisées depuis la DB (Étape 1)."""
        if not self.db_manager:
            return

        try:
            self.tracks_tree.delete(*self.tracks_tree.get_children())
            self.missing_tracks.clear()
            self.item_to_urlmd5.clear()
            self.urlmd5_to_item.clear()
            self.pending_assignments.clear()
            self.suggestion_items.clear()
            self.ignored_tracks.clear()

            self._show_progressbar()
            loading_id = self.tracks_tree.insert("", tk.END, values=("Chargement…", "", "", ""))
            self.update()

            missing = SyncDetector.find_missing_in_alternative(self.db_manager)
            self.alternative_tracks = SyncDetector.get_all_alternative_tracks(self.db_manager)

            self.tracks_tree.delete(loading_id)
            self._hide_progressbar()

            seen: set = set()
            for track in missing:
                urlmd5 = track["urlmd5"]
                if urlmd5 in seen:
                    continue
                seen.add(urlmd5)
                self.missing_tracks[urlmd5] = track

                artist = track.get("artist_name") or ""
                title = track.get("title") or "[ORPHELIN]"
                playcount = track.get("playcount", 0)

                item_id = self.tracks_tree.insert(
                    "", tk.END, values=(artist, title, playcount, "—")
                )
                self.item_to_urlmd5[item_id] = urlmd5
                self.urlmd5_to_item[urlmd5] = item_id

            self._update_sync_button()
            self._update_statusbar()
            self._update_progress_counter()
            count = len(self.missing_tracks)
            self.update_status(f"{count} piste(s) désynchronisée(s) chargée(s)")

        except Exception as e:
            self._hide_progressbar()
            messagebox.showerror("Erreur chargement", f"Impossible de charger les pistes : {e}")

    def _reload_data(self) -> None:
        if self.pending_assignments:
            if not messagebox.askyesno(
                "Recharger",
                f"{len(self.pending_assignments)} assignation(s) en attente.\nRecharger quand même ?",
            ):
                return
        self._load_tracks_from_db()

    # ─── Étape 2 : sélection piste → affichage suggestions ───────────────────

    def _on_track_selected(self, event) -> None:
        selection = self.tracks_tree.selection()
        if not selection:
            return
        urlmd5 = self.item_to_urlmd5.get(selection[0])
        if urlmd5:
            track_data = self.missing_tracks.get(urlmd5)
            if track_data:
                self._show_suggestions(track_data)

    def _show_suggestions(self, track_data: dict) -> None:
        """Calcule et affiche les suggestions pour la piste sélectionnée (Étape 2)."""
        artist = track_data.get("artist_name") or ""
        title = track_data.get("title") or "[ORPHELIN]"
        playcount = track_data.get("playcount", 0)
        urlmd5 = track_data["urlmd5"]

        self.track_info_label.config(text=f"{artist} — {title}  ({playcount} écoutes)")

        self.suggestions_tree.delete(*self.suggestions_tree.get_children())
        self.suggestion_items.clear()

        current_assignment = self.pending_assignments.get(urlmd5)

        if not self.matcher or not self.alternative_tracks:
            self.suggestions_tree.insert(
                "", tk.END, values=("—", "Pas de données de matching", "", "")
            )
            return

        try:
            matches = self.matcher.find_best_matches(
                track_data, self.alternative_tracks, top_n=10
            )
        except Exception as e:
            self.suggestions_tree.insert(
                "", tk.END, values=("—", f"Erreur matching : {e}", "", "")
            )
            return

        for match in matches:
            score = match["match_score"]
            alt_urlmd5 = match.get("urlmd5") or ""
            alt_artist = match.get("artist") or ""
            alt_title = match.get("title") or ""
            alt_playcount = match.get("playcount", 0)

            tag = "likely" if score >= 80 else "possible" if score >= 60 else "unlikely"
            tags = [tag]
            is_current = current_assignment and current_assignment.get("urlmd5") == alt_urlmd5
            if is_current:
                tags.append("current")

            indicator = "●" if score >= 80 else "◐" if score >= 60 else "○"
            score_text = f"{indicator} {score:.0f}%"

            item_id = self.suggestions_tree.insert(
                "",
                tk.END,
                values=(score_text, alt_artist, alt_title, alt_playcount),
                tags=tuple(tags),
            )
            self.suggestion_items[item_id] = match

            if is_current:
                self.suggestions_tree.selection_set(item_id)

    # ─── Étape 2 : clic sur suggestion → assignation ─────────────────────────

    def _on_suggestion_selected(self, event) -> None:
        track_sel = self.tracks_tree.selection()
        if not track_sel:
            return
        persist_urlmd5 = self.item_to_urlmd5.get(track_sel[0])
        if not persist_urlmd5:
            return

        sugg_sel = self.suggestions_tree.selection()
        if not sugg_sel:
            return
        alt_match = self.suggestion_items.get(sugg_sel[0])
        if alt_match:
            self._assign_track(persist_urlmd5, alt_match)

    def _assign_track(self, persist_urlmd5: str, alt_match: dict) -> None:
        """Mémorise le choix sans écrire en DB."""
        self.pending_assignments[persist_urlmd5] = alt_match
        self.ignored_tracks.discard(persist_urlmd5)

        item_id = self.urlmd5_to_item.get(persist_urlmd5)
        if item_id:
            values = list(self.tracks_tree.item(item_id, "values"))
            values[3] = "Assignée"
            self.tracks_tree.item(item_id, values=values, tags=("assigned",))

        self._update_sync_button()
        self._update_progress_counter()
        alt_title = alt_match.get("title") or ""
        score = alt_match.get("match_score", 0)
        self.update_status(f"Assigné : {alt_title} ({score:.0f}%)")

    def _deassign_track(self, urlmd5: str) -> None:
        self.pending_assignments.pop(urlmd5, None)
        item_id = self.urlmd5_to_item.get(urlmd5)
        if item_id:
            values = list(self.tracks_tree.item(item_id, "values"))
            values[3] = "—"
            self.tracks_tree.item(item_id, values=values, tags=())
        self._update_sync_button()
        self._update_progress_counter()

    def _update_sync_button(self) -> None:
        count = len(self.pending_assignments)
        if count > 0:
            self.sync_btn.config(
                text=f"Sync assignées ({count})",
                state=tk.NORMAL,
                bg="#27ae60",
                fg="white",
                cursor="hand2",
            )
        else:
            self.sync_btn.config(
                text="Sync assignées (0)",
                state=tk.DISABLED,
                bg="#95a5a6",
                fg="white",
                cursor="arrow",
            )

    # ─── Étape 3 : synchronisation ────────────────────────────────────────────

    def _sync_assigned_tracks(self) -> None:
        """Applique toutes les assignations en attente (Étape 3)."""
        if not self.pending_assignments:
            return

        count = len(self.pending_assignments)
        if not messagebox.askyesno(
            "Confirmer la synchronisation",
            f"Synchroniser {count} piste(s) assignée(s) ?\n\n"
            "Cette opération va :\n"
            "  • Copier les playcounts vers alternativeplaycount\n"
            "  • Supprimer les entrées de tracks_persistent",
        ):
            return

        success_count = 0
        errors = []
        items_to_remove = []

        self._show_progressbar(mode="determinate", maximum=count)

        for persist_urlmd5, alt_match in list(self.pending_assignments.items()):
            track_data = self.missing_tracks.get(persist_urlmd5, {})
            persist_playcount = track_data.get("playcount", 0)
            persist_lastplayed = track_data.get("lastplayed")
            alt_urlmd5 = alt_match.get("urlmd5") or ""

            if not alt_urlmd5:
                errors.append(f"{persist_urlmd5[:8]}… : urlmd5 alt manquant")
                self.progress_bar["value"] += 1
                self.update()
                continue

            try:
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "UPDATE alternativeplaycount SET playCount=?, lastPlayed=? WHERE urlmd5=?",
                        (persist_playcount, persist_lastplayed, alt_urlmd5),
                    )
                    cursor.execute(
                        "DELETE FROM tracks_persistent WHERE urlmd5=?",
                        (persist_urlmd5,),
                    )
                success_count += 1
                items_to_remove.append(persist_urlmd5)
            except Exception as e:
                errors.append(f"{persist_urlmd5[:8]}… : {e}")

            self.progress_bar["value"] += 1
            self.update()

        self._hide_progressbar()

        for urlmd5 in items_to_remove:
            item_id = self.urlmd5_to_item.pop(urlmd5, None)
            if item_id:
                self.tracks_tree.delete(item_id)
                self.item_to_urlmd5.pop(item_id, None)
            self.missing_tracks.pop(urlmd5, None)
            self.pending_assignments.pop(urlmd5, None)

        self.suggestions_tree.delete(*self.suggestions_tree.get_children())
        self.suggestion_items.clear()
        self.track_info_label.config(
            text="Cliquer sur une piste pour voir les suggestions"
        )
        self._update_sync_button()
        self._update_progress_counter()

        if errors:
            messagebox.showwarning(
                "Synchronisation partielle",
                f"{success_count} piste(s) synchronisée(s).\n\nErreurs :\n"
                + "\n".join(errors),
            )
        else:
            messagebox.showinfo("Succès", f"{success_count} piste(s) synchronisée(s) avec succès.")

        self.update_status(f"{success_count} piste(s) synchronisée(s)")

    # ─── Ignorer ─────────────────────────────────────────────────────────────

    def _ignore_selected_track(self) -> None:
        selection = self.tracks_tree.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Sélectionnez une piste à ignorer.")
            return

        item_id = selection[0]
        urlmd5 = self.item_to_urlmd5.get(item_id)

        values = list(self.tracks_tree.item(item_id, "values"))
        values[3] = "Ignorée"
        self.tracks_tree.item(item_id, values=values, tags=("ignored",))

        if urlmd5:
            self.ignored_tracks.add(urlmd5)
            if urlmd5 in self.pending_assignments:
                del self.pending_assignments[urlmd5]
                self._update_sync_button()

        self._update_progress_counter()
        self.suggestions_tree.delete(*self.suggestions_tree.get_children())
        self.suggestion_items.clear()
        self.track_info_label.config(
            text="Cliquer sur une piste pour voir les suggestions"
        )

    # ─── Clic droit ──────────────────────────────────────────────────────────

    def _on_track_right_click(self, event) -> None:
        item = self.tracks_tree.identify("item", event.x, event.y)
        if not item:
            return
        self.tracks_tree.selection_set(item)
        urlmd5 = self.item_to_urlmd5.get(item)

        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Ignorer cette piste", command=self._ignore_selected_track)
        if urlmd5 and urlmd5 in self.pending_assignments:
            menu.add_command(
                label="Désassigner", command=lambda: self._deassign_track(urlmd5)
            )
        menu.post(event.x_root, event.y_root)

    # ─── Tri colonnes ────────────────────────────────────────────────────────

    def _sort_tracks(self, column: str) -> None:
        items = [
            (self.tracks_tree.set(k, column), k)
            for k in self.tracks_tree.get_children("")
        ]
        if column == "Écoutes":
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=True)
        else:
            items.sort()
        for index, (_, k) in enumerate(items):
            self.tracks_tree.move(k, "", index)

    # ─── Configuration ────────────────────────────────────────────────────────

    def _on_config_click(self) -> None:
        cfg = Config.instance()
        win = tk.Toplevel(self)
        win.title("Configuration")
        win.resizable(False, False)
        win.grab_set()

        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_general = ttk.Frame(notebook, padding=15)
        notebook.add(tab_general, text="Général")

        ttk.Label(tab_general, text="Seuil de correspondance automatique (%) :").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 4)
        )
        threshold_var = tk.IntVar(value=cfg.matching.auto_match_threshold)
        threshold_label = ttk.Label(tab_general, text=f"{threshold_var.get()}%", width=5)

        def _on_threshold(val):
            threshold_label.config(text=f"{int(float(val))}%")

        ttk.Scale(
            tab_general, from_=0, to=100, orient=tk.HORIZONTAL,
            variable=threshold_var, command=_on_threshold
        ).grid(row=1, column=0, sticky=tk.EW, pady=(0, 15))
        threshold_label.grid(row=1, column=1, padx=(8, 0))
        tab_general.columnconfigure(0, weight=1)

        ttk.Label(tab_general, text="Base de données :").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 4)
        )
        ttk.Label(tab_general, text=str(self.db_path), foreground="gray").grid(
            row=3, column=0, columnspan=2, sticky=tk.W
        )

        tab_remote = ttk.Frame(notebook, padding=15)
        notebook.add(tab_remote, text="Serveur distant")

        remote = cfg.remote
        host_var = tk.StringVar(value=remote.host)
        user_var = tk.StringVar(value=remote.user)
        dbpath_var = tk.StringVar(value=remote.db_path)
        port_var = tk.StringVar(value=str(remote.ssh_port))
        timeout_var = tk.StringVar(value=str(remote.timeout))
        sudo_var = tk.BooleanVar(value=remote.use_sudo)

        for i, (label, var) in enumerate([
            ("Hôte :", host_var),
            ("Utilisateur :", user_var),
            ("Chemin distant :", dbpath_var),
            ("Port SSH :", port_var),
            ("Délai (s) :", timeout_var),
        ]):
            ttk.Label(tab_remote, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            ttk.Entry(tab_remote, textvariable=var, width=35).grid(
                row=i, column=1, sticky=tk.EW, padx=(10, 0), pady=3
            )

        ttk.Checkbutton(
            tab_remote,
            text="Utiliser sudo pour l'envoi (si l'utilisateur SSH n'a pas les droits sur db_path)",
            variable=sudo_var,
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        tab_remote.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(win, padding=(10, 0, 10, 10))
        btn_frame.pack(fill=tk.X)

        def _apply():
            cfg.matching.auto_match_threshold = threshold_var.get()
            cfg.remote.host = host_var.get().strip()
            cfg.remote.user = user_var.get().strip()
            cfg.remote.db_path = dbpath_var.get().strip()
            cfg.remote.use_sudo = sudo_var.get()
            try:
                cfg.remote.ssh_port = int(port_var.get())
            except ValueError:
                pass
            try:
                cfg.remote.timeout = int(timeout_var.get())
            except ValueError:
                pass
            cfg.save_to_file("config.yaml")
            if hasattr(self, "fetch_btn"):
                state = tk.NORMAL if cfg.remote.is_configured() else tk.DISABLED
                self.fetch_btn.config(state=state)
                self.push_btn.config(state=state)
            messagebox.showinfo("Succès", "Configuration sauvegardée.")
            win.destroy()

        ttk.Button(btn_frame, text="Appliquer", command=_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Fermer", command=win.destroy).pack(side=tk.LEFT, padx=5)

        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - win.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    # ─── Sync distant ────────────────────────────────────────────────────────

    def _ask_yes_no(self, title: str, message: str) -> bool:
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

        ttk.Button(btn_frame, text="Oui", width=10, command=on_oui).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(btn_frame, text="Non", width=10, command=dlg.destroy).pack(
            side=tk.LEFT, padx=10
        )
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dlg.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.wait_window(dlg)
        return result.get()

    def _ask_sudo_password(self, host: str, user: str) -> Optional[str]:
        """
        Demande le mot de passe sudo de l'utilisateur SSH distant.

        Le mot de passe n'est jamais écrit dans config.yaml ni dans les logs.
        S'il est mémorisé, il ne l'est qu'en mémoire pour la durée de la session.

        Returns:
            Le mot de passe, ou None si l'utilisateur annule.
        """
        cached = getattr(self, "_sudo_pw_cache", None)
        if cached:
            return cached

        result: dict[str, Optional[str]] = {"pw": None}
        dlg = tk.Toplevel(self)
        dlg.title("Mot de passe sudo")
        dlg.resizable(False, False)
        dlg.grab_set()
        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame,
            text=f"Mot de passe sudo pour {user}@{host} :",
            justify=tk.LEFT,
        ).pack(anchor=tk.W)
        pw_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=pw_var, show="•", width=32)
        entry.pack(fill=tk.X, pady=(8, 6))
        entry.focus_set()
        remember_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Retenir pour cette session", variable=remember_var
        ).pack(anchor=tk.W)

        def on_ok(_event=None):
            result["pw"] = pw_var.get()
            if remember_var.get():
                self._sudo_pw_cache = pw_var.get()
            dlg.destroy()

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="OK", width=10, command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Annuler", width=10, command=dlg.destroy).pack(
            side=tk.LEFT, padx=5
        )
        entry.bind("<Return>", on_ok)

        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dlg.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.wait_window(dlg)
        return result["pw"]

    def _confirm_lms_stopped(self) -> bool:
        return self._ask_yes_no(
            "LMS doit être arrêté",
            "Avant tout transfert, Lyrion Media Server (LMS) doit être\n"
            "arrêté sur la machine distante pour éviter la corruption\n"
            "de la base de données.\n\n"
            "Avez-vous bien arrêté LMS avant de continuer ?",
        )

    def _push_remote_db(self) -> None:
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

        # En mode sudo, l'utilisateur SSH n'a pas les droits d'écriture directs
        # sur db_path : on demande son mot de passe sudo (jamais persisté).
        sudo_pw: Optional[str] = None
        if remote.use_sudo:
            sudo_pw = self._ask_sudo_password(remote.host, remote.user)
            if sudo_pw is None:
                return

        self.push_btn.config(state=tk.DISABLED, text="Envoi…")
        self.update_status(f"Envoi vers {remote.user}@{remote.host}…")
        self.update()

        # Exporter une copie consolidée (WAL fusionné) avant le transfert SCP.
        # Envoyer le .db brut laisserait les données du fichier -wal derrière.
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
        os.close(tmp_fd)
        try:
            self.db_manager.export_consolidated(tmp_path)
            success = RemoteSync(remote).upload(tmp_path, sudo_password=sudo_pw)
        except Exception as e:
            messagebox.showerror("Erreur", f"Envoi impossible : {e}")
            self.push_btn.config(state=tk.NORMAL, text="↑ Envoyer")
            return
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        if not success:
            # Purge un éventuel mot de passe mémorisé : il peut être la cause
            # de l'échec (mot de passe sudo erroné) → reprompt au prochain essai.
            self._sudo_pw_cache = None
            messagebox.showerror(
                "Échec",
                f"Impossible d'envoyer vers {remote.host}.\n"
                "Voir logs/sync.log pour le détail de l'erreur.",
            )
        else:
            messagebox.showinfo("Succès", f"Base de données envoyée vers {remote.host}.")
            self._update_statusbar()
        self.push_btn.config(state=tk.NORMAL, text="↑ Envoyer")

    def _fetch_remote_db(self) -> None:
        if not self._confirm_lms_stopped():
            return
        cfg = Config.instance()
        remote = cfg.remote
        self.fetch_btn.config(state=tk.DISABLED, text="Récupération…")
        self.update_status(f"Connexion à {remote.user}@{remote.host}…")
        self.update()
        try:
            success = RemoteSync(remote).fetch(cfg.database.path)
        except RemoteBusyError as e:
            messagebox.showwarning("Base distante occupée", str(e))
            self.fetch_btn.config(state=tk.NORMAL, text="↓ Récupérer")
            return
        except Exception as e:
            messagebox.showerror("Erreur", f"Récupération impossible : {e}")
            self.fetch_btn.config(state=tk.NORMAL, text="↓ Récupérer")
            return
        if not success:
            messagebox.showerror("Échec", f"Impossible de récupérer depuis {remote.host}.")
            self.fetch_btn.config(state=tk.NORMAL, text="↓ Récupérer")
            return
        try:
            if self.db_manager:
                self.db_manager.close()
                self.db_manager.connect()
        except Exception as e:
            messagebox.showerror("Erreur BD", f"Reconnexion impossible : {e}")
            self.fetch_btn.config(state=tk.NORMAL, text="↓ Récupérer")
            return
        self._load_tracks_from_db()
        self._update_statusbar()
        self.fetch_btn.config(state=tk.NORMAL, text="↓ Récupérer")
        messagebox.showinfo("Succès", "Base de données récupérée et rechargée.")

    # ─── Barre de statut ──────────────────────────────────────────────────────

    def _update_statusbar(self) -> None:
        if self.db_path:
            self.db_label.config(text=f"Connecté à {self.db_path}")
        else:
            self.db_label.config(text="Pas de connexion DB")


    # ─── API publique ─────────────────────────────────────────────────────────

    def update_status(self, message: str) -> None:
        self.status_label.config(text=message)

    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        if message_type == "warning":
            messagebox.showwarning(title, message)
        elif message_type == "error":
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
