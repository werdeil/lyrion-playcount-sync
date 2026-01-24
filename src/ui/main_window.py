"""Fenêtre principale de l'application."""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *

from src.utils import setup_logger

logger = setup_logger(__name__)


class MainWindow:
    """Fenêtre principale de l'application."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialise la fenêtre principale.
        
        Args:
            root: Racine tkinter
        """
        self.root = root
        self.root.title("Lyrion Playcount Sync")
        self.root.geometry("800x600")
        
        logger.info("Initialisation de la fenêtre principale")
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self._show_about)
        
        # Cadre principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Titre
        title_label = ttk.Label(
            main_frame,
            text="Synchronisation des Playcounts",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Cadre d'état
        status_frame = ttk.LabelFrame(main_frame, text="État", padding=10)
        status_frame.pack(fill=X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Prêt")
        self.status_label.pack()
        
        # Cadre de contrôle
        control_frame = ttk.LabelFrame(main_frame, text="Contrôle", padding=10)
        control_frame.pack(fill=X, pady=10)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=X, expand=True)
        
        self.load_btn = ttk.Button(
            button_frame,
            text="Charger les données",
            command=self._on_load_data
        )
        self.load_btn.pack(side=LEFT, padx=5)
        
        self.match_btn = ttk.Button(
            button_frame,
            text="Trouver correspondances",
            command=self._on_find_matches,
            state=DISABLED
        )
        self.match_btn.pack(side=LEFT, padx=5)
        
        self.sync_btn = ttk.Button(
            button_frame,
            text="Synchroniser",
            command=self._on_sync,
            state=DISABLED
        )
        self.sync_btn.pack(side=LEFT, padx=5)
        
        # Cadre de résultats
        results_frame = ttk.LabelFrame(main_frame, text="Résultats", padding=10)
        results_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Treeview pour les résultats
        self.tree = ttk.Treeview(
            results_frame,
            columns=("artist", "title", "playcount"),
            height=15
        )
        self.tree.column("#0", width=50, anchor=W)
        self.tree.column("artist", width=200, anchor=W)
        self.tree.column("title", width=400, anchor=W)
        self.tree.column("playcount", width=100, anchor=E)
        
        self.tree.heading("#0", text="ID")
        self.tree.heading("artist", text="Artiste")
        self.tree.heading("title", text="Titre")
        self.tree.heading("playcount", text="Plays")
        
        self.tree.pack(fill=BOTH, expand=True)
    
    def _on_load_data(self):
        """Callback pour le chargement des données."""
        messagebox.showinfo("Charger les données", "Fonctionnalité en cours de développement")
    
    def _on_find_matches(self):
        """Callback pour trouver les correspondances."""
        messagebox.showinfo("Correspondances", "Fonctionnalité en cours de développement")
    
    def _on_sync(self):
        """Callback pour la synchronisation."""
        messagebox.showinfo("Synchronisation", "Fonctionnalité en cours de développement")
    
    def _show_about(self):
        """Affiche la fenêtre À propos."""
        messagebox.showinfo(
            "À propos",
            "Lyrion Playcount Sync v1.0\n\n"
            "Synchronise les playcounts entre tracks_persistent "
            "et alternativeplaycount dans Lyrion."
        )
    
    def set_status(self, message: str):
        """Définit le message d'état."""
        self.status_label.config(text=message)
        self.root.update()
    
    def run(self):
        """Démarre la boucle principale."""
        self.root.mainloop()
