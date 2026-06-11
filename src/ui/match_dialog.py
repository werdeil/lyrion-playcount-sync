"""
Dialogue de sélection et correction du match.

Affiche :
- Morceau manquant avec ses métadonnées
- Suggestions de correspondance
- Choix de l'action (COPY/MERGE)
- Prévisualisation SQL
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List
from src.models import Track, MatchSuggestion, SyncOperation


class MatchDialog(tk.Toplevel):
    """Dialogue pour sélectionner et corriger une correspondance."""
    
    # Couleurs
    COLOR_GOOD = "#2ecc71"      # Vert - score >= 90%
    COLOR_WARNING = "#f39c12"   # Orange - score 60-90%
    COLOR_BAD = "#e74c3c"       # Rouge - score < 60%
    COLOR_NEUTRAL = "#95a5a6"   # Gris
    
    FONT_MAIN = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)
    FONT_MONO = ("Courier", 9)
    
    def __init__(
        self,
        parent: tk.Widget,
        missing_track: Track,
        suggested_matches: List[tuple[Track, float]],
        on_apply: Optional[Callable[[SyncOperation], bool]] = None,
        on_next: Optional[Callable] = None,
    ):
        """
        Initialiser le dialogue.
        
        Args:
            parent: Widget parent
            missing_track: Morceau manquant
            suggested_matches: Liste de (Track, score) triée par score
            on_apply: Callback lors de l'application
            on_next: Callback pour passer au suivant (batch)
        """
        super().__init__(parent)
        
        self.title("Trouver une correspondance")
        self.geometry("700x900")
        self.minsize(600, 700)
        
        self.missing_track = missing_track
        self.suggested_matches = suggested_matches
        self.on_apply = on_apply
        self.on_next = on_next
        
        # Variables de contrôle
        self.selected_match: Optional[Track] = None
        self.selected_action = tk.StringVar(value="COPY")
        self.new_playcount = tk.IntVar(value=missing_track.playcount)
        self.delete_missing = tk.BooleanVar(value=True)
        
        # Créer l'interface
        self._create_widgets()
        self._update_sql_preview()
        
        # Modal
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self) -> None:
        """Créer tous les widgets."""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Section morceau manquant
        self._create_missing_track_section(main_frame)
        
        # Section suggestions
        self._create_suggestions_section(main_frame)
        
        # Section action
        self._create_action_section(main_frame)
        
        # Section SQL
        self._create_sql_preview_section(main_frame)
        
        # Barre d'actions
        self._create_button_bar(main_frame)
    
    def _create_missing_track_section(self, parent: ttk.Frame) -> None:
        """Créer la section du morceau manquant."""
        frame = ttk.LabelFrame(parent, text="🎵 Morceau manquant (tracks_persistent)", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Infos du morceau
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X)
        
        # Artiste
        self._create_info_row(info_frame, "Artiste :", self.missing_track.artist or "N/A")
        
        # Titre
        self._create_info_row(info_frame, "Titre :", self.missing_track.title or "N/A")
        
        # Album
        self._create_info_row(info_frame, "Album :", self.missing_track.album or "N/A")
        
        # Playcount
        self._create_info_row(info_frame, "Playcount :", f"{self.missing_track.playcount} lectures")
        
        # Last played
        last_played = self.missing_track.lastplayed_formatted() if self.missing_track.lastplayed else "N/A"
        self._create_info_row(info_frame, "Dernière écoute :", last_played)
        
        # URL
        url_display = self.missing_track.url[:50] + "..." if self.missing_track.url and len(self.missing_track.url) > 50 else (self.missing_track.url or "N/A")
        self._create_info_row(info_frame, "URL :", url_display)
    
    def _create_info_row(self, parent: ttk.Frame, label: str, value: str) -> None:
        """Créer une ligne d'info (label + valeur)."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        
        label_widget = ttk.Label(row, text=label, font=("Segoe UI", 9, "bold"), width=15)
        label_widget.pack(side=tk.LEFT)
        
        value_widget = ttk.Label(row, text=value, font=self.FONT_SMALL, foreground="#bdc3c7")
        value_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_suggestions_section(self, parent: ttk.Frame) -> None:
        """Créer la section des suggestions."""
        frame = ttk.LabelFrame(parent, text="🔍 Suggestions (alternativeplaycount)", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Canvas avec scrollbar pour les suggestions
        canvas_frame = ttk.Frame(frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        self.suggestions_frame = ttk.Frame(canvas, relief=tk.FLAT)
        self.suggestions_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.suggestions_frame, anchor="nw")
        canvas.configure(yscroll=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Ajouter les suggestions
        self._populate_suggestions()
    
    def _populate_suggestions(self) -> None:
        """Remplir les suggestions."""
        if not self.suggested_matches:
            label = ttk.Label(
                self.suggestions_frame,
                text="❌ Aucune suggestion trouvée",
                foreground="#e74c3c"
            )
            label.pack(pady=20)
            return
        
        self.suggestion_buttons = []
        suggestion_var = tk.StringVar()
        
        for i, (track, score) in enumerate(self.suggested_matches):
            button, label_widget = self._create_suggestion_button(
                self.suggestions_frame,
                track,
                score,
                suggestion_var,
                i
            )
            self.suggestion_buttons.append((button, track, score))
        
        # Stocker la variable de suggestion
        self._suggestion_var = suggestion_var
    
    def _create_suggestion_button(
        self,
        parent: ttk.Frame,
        track: Track,
        score: float,
        var: tk.StringVar,
        index: int
    ) -> tuple:
        """Créer un bouton de suggestion."""
        card_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        card_frame.pack(fill=tk.X, pady=3)
        
        # Couleur selon score
        if score >= 90:
            color = self.COLOR_GOOD
            icon = "✓"
        elif score >= 60:
            color = self.COLOR_WARNING
            icon = "⚠"
        else:
            color = self.COLOR_BAD
            icon = "✗"
        
        # Radio button + score
        rb = ttk.Radiobutton(
            card_frame,
            text=f"{icon} {score:.0f}% - {track.artist or 'N/A'} - {track.title or 'N/A'}",
            variable=var,
            value=str(index),
            command=lambda: self._on_suggestion_selected(track)
        )
        rb.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        # Infos du track
        info = f"Album: {track.album or 'N/A'} | Plays: {track.playcount}"
        info_label = ttk.Label(card_frame, text=info, foreground="#95a5a6", font=self.FONT_SMALL)
        info_label.pack(anchor=tk.W, padx=20, pady=(0, 5))
        
        return rb, info_label
    
    def _create_action_section(self, parent: ttk.Frame) -> None:
        """Créer la section action."""
        frame = ttk.LabelFrame(parent, text="⚡ Action à effectuer", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Option COPY
        copy_frame = ttk.Frame(frame)
        copy_frame.pack(fill=tk.X, pady=5)
        
        rb_copy = ttk.Radiobutton(
            copy_frame,
            text="Copier le playcount (remplacer dans alternativeplaycount)",
            variable=self.selected_action,
            value="COPY",
            command=self._on_action_changed
        )
        rb_copy.pack(anchor=tk.W)
        
        spinbox_frame = ttk.Frame(copy_frame)
        spinbox_frame.pack(anchor=tk.W, padx=20, pady=(3, 0))
        
        ttk.Label(spinbox_frame, text="Playcount :", font=self.FONT_SMALL).pack(side=tk.LEFT)
        ttk.Spinbox(
            spinbox_frame,
            from_=0,
            to=999999,
            textvariable=self.new_playcount,
            width=10,
            font=self.FONT_SMALL
        ).pack(side=tk.LEFT, padx=5)
        
        # Option MERGE
        merge_frame = ttk.Frame(frame)
        merge_frame.pack(fill=tk.X, pady=5)
        
        rb_merge = ttk.Radiobutton(
            merge_frame,
            text="Fusionner (additionner les playcounts)",
            variable=self.selected_action,
            value="MERGE",
            command=self._on_action_changed
        )
        rb_merge.pack(anchor=tk.W)
        
        # Calcul fusion
        if self.suggested_matches:
            _, best_score = self.suggested_matches[0]
            merged = self.missing_track.playcount + best_score
            merge_label = ttk.Label(
                merge_frame,
                text=f"{self.missing_track.playcount} + {best_score:.0f} = {merged:.0f}",
                foreground="#95a5a6",
                font=self.FONT_SMALL
            )
            merge_label.pack(anchor=tk.W, padx=20, pady=(0, 3))
        
        # Checkbox DELETE
        delete_frame = ttk.Frame(frame)
        delete_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(
            delete_frame,
            text="Supprimer de tracks_persistent après sync",
            variable=self.delete_missing,
            onvalue=True,
            offvalue=False
        ).pack(anchor=tk.W)
    
    def _create_sql_preview_section(self, parent: ttk.Frame) -> None:
        """Créer la section de prévisualisation SQL."""
        frame = ttk.LabelFrame(parent, text="⚠️  Prévisualisation SQL", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.sql_text = tk.Text(
            frame,
            height=5,
            font=self.FONT_MONO,
            bg="#2c3e50",
            fg="#2ecc71",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.sql_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_button_bar(self, parent: ttk.Frame) -> None:
        """Créer la barre de boutons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="✓ Appliquer",
            command=self._on_apply_click
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="⏭️ Ignorer",
            command=self._on_ignore_click
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="✕ Annuler",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=2)
    
    def _on_suggestion_selected(self, track: Track) -> None:
        """Appeler quand une suggestion est sélectionnée."""
        self.selected_match = track
        self._update_sql_preview()
    
    def _on_action_changed(self) -> None:
        """Appeler quand l'action change."""
        self._update_sql_preview()
    
    def _update_sql_preview(self) -> None:
        """Mettre à jour la prévisualisation SQL."""
        if not self.selected_match:
            self.sql_text.config(state=tk.NORMAL)
            self.sql_text.delete(1.0, tk.END)
            self.sql_text.insert(tk.END, "Sélectionnez un match pour voir la prévisualisation")
            self.sql_text.config(state=tk.DISABLED)
            return
        
        # Créer l'opération
        action = self.selected_action.get()
        new_playcount = self.new_playcount.get()
        
        if action == "MERGE" and self.suggested_matches:
            _, match_score = self.suggested_matches[0]
            new_playcount = int(self.missing_track.playcount + match_score)
        
        op = SyncOperation(
            missing_urlmd5=self.missing_track.urlmd5,
            selected_alternative_urlmd5=self.selected_match.urlmd5,
            action=action,
            new_playcount=new_playcount
        )
        
        update_sql, delete_sql = op.to_sql()
        
        # Afficher
        self.sql_text.config(state=tk.NORMAL)
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(tk.END, f"-- {action}\n")
        self.sql_text.insert(tk.END, f"{update_sql}\n")
        self.sql_text.insert(tk.END, f"{delete_sql}\n")
        self.sql_text.config(state=tk.DISABLED)
        
        self._current_operation = op
    
    def _on_apply_click(self) -> None:
        """Appeler quand le bouton Appliquer est cliqué."""
        if not self.selected_match:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un match")
            return
        
        # Vérifier la validité
        if self.new_playcount.get() < 0:
            messagebox.showerror("Valeur invalide", "Playcount doit être >= 0")
            return
        
        # Confirmation si score faible
        if self.suggested_matches:
            _, score = self.suggested_matches[0]
            if score < 60:
                result = messagebox.askyesno(
                    "Confirmation",
                    f"Le score est faible ({score:.0f}%). Voulez-vous continuer?"
                )
                if not result:
                    return
        
        # Appliquer
        if self.on_apply:
            try:
                success = self.on_apply(self._current_operation)
                if success:
                    messagebox.showinfo("Succès", "L'opération a été appliquée")
                    self.destroy()
                else:
                    messagebox.showerror("Erreur", "L'opération a échoué")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'application:\n{e}")
    
    def _on_ignore_click(self) -> None:
        """Appeler quand le bouton Ignorer est cliqué."""
        if self.on_next:
            self.on_next()
        self.destroy()
