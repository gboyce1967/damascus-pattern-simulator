#!/usr/bin/env python3
"""
Damascus 3D Pattern Simulator - GUI Application
================================================

Full Tkinter-based GUI for the 3D Damascus simulator.

FEATURES:
---------
- Interactive 3D viewport (embedded matplotlib)
- Real-time parameter controls with sliders
- Pattern selection (Feather, Twist, Raindrop)
- Cross-section preview with Z-position slider
- Operation timeline with undo/redo
- Export controls (3D models, images, operation logs)
- Extensive debugging with visual feedback

UI LAYOUT:
----------
┌─────────────────────────────────────────────────────┐
│ Menu Bar (File, View, Help)                         │
├──────────────────┬──────────────────────────────────┤
│                  │                                  │
│  Pattern Select  │      3D Viewport                 │
│  ┌────────────┐  │    (Interactive 3D View)         │
│  │ Feather    │  │                                  │
│  │ Twist      │  │                                  │
│  │ Raindrop   │  │                                  │
│  └────────────┘  │                                  │
│                  │                                  │
│  Parameters      ├──────────────────────────────────┤
│  ┌────────────┐  │   Cross-Section Preview          │
│  │ Sliders    │  │   (2D Pattern View)              │
│  │ & Controls │  │   [Z-Position Slider]            │
│  └────────────┘  │                                  │
│                  │                                  │
│  Operations      │                                  │
│  [Apply][Undo]   │                                  │
│                  │                                  │
│  Export          │                                  │
│  [3D][Image]     │                                  │
│  [Log]           │                                  │
├──────────────────┴──────────────────────────────────┤
│ Status Bar: Ready | Layers: 30 | Operations: 2     │
└─────────────────────────────────────────────────────┘

Author: Damascus Pattern Simulator Team
Date: 2026-02-02
Version: 2.0 (3D GUI)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import numpy as np
import zipfile
import os
import logging

# Matplotlib is optional - only needed for cross-section export
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
from datetime import datetime
import json
from pathlib import Path

# Import from lib modules
from lib.logging_config import logger, LOGS_DIR as SIM_LOGS_DIR
from lib.damascus_billet import Damascus3DBillet
from lib.damascus_layer import DamascusLayer  # noqa: F401 (backward compat)
from lib.vispy_viewer import DamascusVispyViewer
from lib.tk_log_handler import TkTextLogHandler
from lib.gui_dialogs import (
    show_debug_console, show_billet_stats, show_about, show_quick_start,
    show_build_plate_warning,
)
from lib.gui_references import (
    show_heat_treatment_guide, show_steel_properties, show_add_custom_steel_dialog,
    show_forging_losses, show_plasticity_guide,
)
from lib.gui_export import export_3d_model, export_cross_section, export_operation_log
from lib.gui_forging import forge_to_square, forge_to_octagon

import open3d as o3d  # noqa: F401 (used by caller code)


class Damascus3DGUI:
    """
    Main GUI application for 3D Damascus Pattern Simulator.
    
    ARCHITECTURE:
    ------------
    - Left panel: Pattern selection and parameter controls
    - Right panel: 3D viewport (top) and cross-section preview (bottom)
    - Bottom: Status bar with real-time information
    - Menu bar: File operations, view options, help
    
    DEBUGGING:
    ---------
    - All UI actions logged
    - Parameter changes tracked
    - Operation history displayed in timeline
    - Debug console available via View menu
    """
    
    def __init__(self, root):
        """
        Initialize the GUI application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Damascus 3D Pattern Simulator")
        self.root.geometry("1600x1000")
        
        # Color scheme
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#e0e0e0',
            'panel_bg': '#252525',
            'accent': '#0d7377',
            'border': '#404040'
        }
        
        # 3D Engine
        self.billet = None
        self.current_pattern_type = None  # 'feather', 'twist', or 'raindrop'
        
        # Visualization state
        self.vispy_viewer = None  # VisPy 3D viewer (replaces matplotlib 3D)
        self.cross_section_image = None
        self.cross_section_display = None
        
        # View orientation controls
        self.view_elevation = tk.DoubleVar(value=30.0)
        self.view_azimuth = tk.DoubleVar(value=45.0)
        self.view_roll = tk.DoubleVar(value=0.0)  # For rotating billet
        
        # UI state
        self.operation_history = []  # List of operation descriptions for timeline
        self.is_forged = False  # Track if billet has been forged to square/octagon
        
        # Build plate configuration (static workspace dimensions)
        self.build_plate_width = tk.DoubleVar(value=400.0)  # mm (X-axis)
        self.build_plate_length = tk.DoubleVar(value=400.0)  # mm (Y-axis)
        self.build_plate_height = tk.DoubleVar(value=200.0)  # mm (Z-axis - max viewing height)

        # Live debug console state
        self.debug_console_window = None
        self.debug_console_text = None
        self.debug_console_handler = None
        
        logger.info("="*70)
        logger.info("Damascus 3D GUI Application Starting")
        logger.info("="*70)
        
        # Setup UI components
        self.setup_style()
        self.setup_menu_bar()
        self.setup_ui()
        
        # Create initial billet
        self.create_new_billet()
        
        logger.info("GUI initialization complete")
    
    def setup_style(self):
        """Configure ttk styles for modern dark theme."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('.', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton', background=self.colors['accent'], foreground='white')
        style.map('TButton', background=[('active', self.colors['accent'])])
        style.configure('TLabelframe', background=self.colors['panel_bg'], 
                       foreground=self.colors['fg'], bordercolor=self.colors['border'])
        style.configure('TLabelframe.Label', background=self.colors['panel_bg'], 
                       foreground=self.colors['fg'])
        
        # Configure Entry widgets to have black text on white background
        style.configure('TEntry', fieldbackground='white', foreground='black')
        style.configure('TCombobox', fieldbackground='white', foreground='black')
        style.map('TCombobox', fieldbackground=[('readonly', 'white')])
        
        logger.debug("TTK style configured")
    
    def setup_menu_bar(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Billet", command=self.create_new_billet)
        file_menu.add_separator()
        file_menu.add_command(label="Export 3D Model (.obj)...", command=lambda: self.export_3d_model('obj'))
        file_menu.add_command(label="Export 3D Model (.stl)...", command=lambda: self.export_3d_model('stl'))
        file_menu.add_command(label="Export Cross-Section (PNG)...", command=self.export_cross_section)
        file_menu.add_command(label="Export Operation Log (JSON)...", command=self.export_operation_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh 3D View", command=self.update_3d_view)
        view_menu.add_command(label="Refresh Cross-Section", command=self.update_cross_section)
        view_menu.add_separator()
        view_menu.add_command(label="Show Debug Console", command=self.show_debug_console)
        view_menu.add_command(label="Show Billet Statistics", command=self.show_billet_stats)
        
        # Reference menu
        reference_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reference", menu=reference_menu)
        reference_menu.add_command(label="📚 Hardening & Tempering Guide", command=self.show_heat_treatment_guide)
        reference_menu.add_command(label="🔬 Steel Properties Database", command=self.show_steel_properties)
        reference_menu.add_separator()
        reference_menu.add_command(label="📖 Forging Losses Reference", command=self.show_forging_losses)
        reference_menu.add_command(label="⚒️ Steel Plasticity Guide", command=self.show_plasticity_guide)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Quick Start Guide", command=self.show_quick_start)
        
        logger.debug("Menu bar created")
    
    def setup_ui(self):
        """Create the main UI layout."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel container with scrollbar - 25% width
        left_container = ttk.Frame(main_container, width=400)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_container.pack_propagate(False)
        
        # Create canvas and scrollbar for left panel
        left_canvas = tk.Canvas(left_container, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_container, orient=tk.VERTICAL, command=left_canvas.yview)
        self.scrollable_left_panel = ttk.Frame(left_canvas)
        
        self.scrollable_left_panel.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        
        left_canvas.create_window((0, 0), window=self.scrollable_left_panel, anchor=tk.NW)
        left_canvas.configure(yscrollcommand=scrollbar.set)
        
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Right panel (viewports) - 75% width
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Setup each section
        self.setup_left_panel(self.scrollable_left_panel)
        self.setup_right_panel(right_panel)
        self.setup_status_bar()
        
        logger.debug("Main UI layout created")
    
    def setup_left_panel(self, parent):
        """
        Create left control panel.
        
        Contains:
        - Pattern selection buttons
        - Layer configuration
        - Parameter controls
        - Operation buttons
        - Export buttons
        """
        # Pattern Selection
        pattern_frame = ttk.LabelFrame(parent, text="Pattern Type", padding=10)
        pattern_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(pattern_frame, text="🪶 Feather Damascus", 
                  command=self.select_feather_pattern).pack(fill=tk.X, pady=2)
        ttk.Button(pattern_frame, text="🔄 Twist/Ladder Damascus", 
                  command=self.select_twist_pattern).pack(fill=tk.X, pady=2)
        ttk.Button(pattern_frame, text="💧 Raindrop Damascus", 
                  command=self.select_raindrop_pattern).pack(fill=tk.X, pady=2)
        
        # Forging Operations
        forge_frame = ttk.LabelFrame(parent, text="Forging Operations", padding=10)
        forge_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(forge_frame, text="🔨 Forge to Square Bar",
                  command=self.forge_to_square).pack(fill=tk.X, pady=2)
        ttk.Button(forge_frame, text="⬡ Forge to Octagon Bar",
                  command=self.forge_to_octagon).pack(fill=tk.X, pady=2)
        
        ttk.Label(forge_frame, text="(Required before twisting)",
                 font=('Arial', 8, 'italic')).pack(pady=(5, 0))
        
        # Layer Configuration
        layer_frame = ttk.LabelFrame(parent, text="Layer Configuration", padding=10)
        layer_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.num_layers = tk.IntVar(value=30)
        self.white_thickness = tk.DoubleVar(value=0.8)
        self.black_thickness = tk.DoubleVar(value=0.8)
        self.billet_width = tk.DoubleVar(value=50.0)
        self.billet_length = tk.DoubleVar(value=100.0)
        
        ttk.Label(layer_frame, text="Number of Layers:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(layer_frame, from_=10, to=100, textvariable=self.num_layers, 
                   width=10).grid(row=0, column=1, pady=2)
        
        ttk.Label(layer_frame, text="White Thickness (mm):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(layer_frame, from_=0.1, to=5.0, increment=0.1, 
                   textvariable=self.white_thickness, width=10).grid(row=1, column=1, pady=2)
        
        ttk.Label(layer_frame, text="Black Thickness (mm):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(layer_frame, from_=0.1, to=5.0, increment=0.1, 
                   textvariable=self.black_thickness, width=10).grid(row=2, column=1, pady=2)
        
        ttk.Label(layer_frame, text="Width (mm):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(layer_frame, from_=20, to=200, textvariable=self.billet_width, 
                   width=10).grid(row=3, column=1, pady=2)
        
        ttk.Label(layer_frame, text="Length (mm):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(layer_frame, from_=50, to=300, textvariable=self.billet_length, 
                   width=10).grid(row=4, column=1, pady=2)
        
        ttk.Button(layer_frame, text="Create New Billet", 
                  command=self.create_new_billet).grid(row=5, column=0, columnspan=2, pady=(10, 0), sticky=tk.EW)
        
        # Parameters (dynamically populated based on pattern type)
        self.params_frame = ttk.LabelFrame(parent, text="Pattern Parameters", padding=10)
        self.params_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.param_label = ttk.Label(self.params_frame, text="Select a pattern type above")
        self.param_label.pack()
        
        # Operations
        ops_frame = ttk.LabelFrame(parent, text="Operations", padding=10)
        ops_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(ops_frame, text="▶ Apply Operation", 
                  command=self.apply_current_operation).pack(fill=tk.X, pady=2)
        ttk.Button(ops_frame, text="↶ Undo Last Operation", 
                  command=self.undo_operation).pack(fill=tk.X, pady=2)
        ttk.Button(ops_frame, text="🔄 Reset Billet", 
                  command=self.reset_billet).pack(fill=tk.X, pady=2)
        
        # Build Plate Configuration
        buildplate_frame = ttk.LabelFrame(parent, text="Build Plate (Workspace)", padding=10)
        buildplate_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(buildplate_frame, text="Width (mm):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(buildplate_frame, from_=100, to=2000, increment=50, 
                   textvariable=self.build_plate_width, width=10,
                   command=lambda: self.update_3d_view()).grid(row=0, column=1, pady=2)
        
        ttk.Label(buildplate_frame, text="Length (mm):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(buildplate_frame, from_=100, to=2000, increment=50, 
                   textvariable=self.build_plate_length, width=10,
                   command=lambda: self.update_3d_view()).grid(row=1, column=1, pady=2)
        
        ttk.Label(buildplate_frame, text="Height (mm):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(buildplate_frame, from_=100, to=2000, increment=50, 
                   textvariable=self.build_plate_height, width=10,
                   command=lambda: self.update_3d_view()).grid(row=2, column=1, pady=2)
        
        ttk.Label(buildplate_frame, text="(Viewport shows static build area)",
                 font=('Arial', 8, 'italic')).grid(row=3, column=0, columnspan=2, pady=(5, 0))
        
        # View Orientation
        view_frame = ttk.LabelFrame(parent, text="View Orientation", padding=10)
        view_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(view_frame, text="Elevation (°):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Scale(view_frame, from_=-90, to=90, variable=self.view_elevation,
                 orient=tk.HORIZONTAL, command=lambda v: self.update_3d_view()).grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Label(view_frame, textvariable=self.view_elevation).grid(row=0, column=2, pady=2)
        
        ttk.Label(view_frame, text="Azimuth (°):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Scale(view_frame, from_=0, to=360, variable=self.view_azimuth,
                 orient=tk.HORIZONTAL, command=lambda v: self.update_3d_view()).grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Label(view_frame, textvariable=self.view_azimuth).grid(row=1, column=2, pady=2)
        
        ttk.Button(view_frame, text="Top View (Build Plate)", 
                  command=self.set_top_view).grid(row=2, column=0, sticky=tk.EW, pady=2)
        ttk.Button(view_frame, text="Front View", 
                  command=self.set_front_view).grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Button(view_frame, text="Isometric", 
                  command=self.set_isometric_view).grid(row=2, column=2, sticky=tk.EW, pady=2)
        
        ttk.Button(view_frame, text="🔍 Zoom to Fit", 
                  command=self.zoom_to_fit).grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(5, 0))
        
        view_frame.columnconfigure(1, weight=1)
        
        # Export
        export_frame = ttk.LabelFrame(parent, text="Export", padding=10)
        export_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(export_frame, text="💾 Save 3D Model (.obj)", 
                  command=lambda: self.export_3d_model('obj')).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="🖼️ Save Cross-Section (PNG)", 
                  command=self.export_cross_section).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="📋 Save Operation Log (JSON)", 
                  command=self.export_operation_log).pack(fill=tk.X, pady=2)
        
        logger.debug("Left panel created")
    
    def setup_right_panel(self, parent):
        """
        Create right viewport panel.
        
        Contains:
        - 3D viewport (full height) - VisPy OpenGL viewer
        """
        # 3D Viewport - VisPy (full panel)
        viewport_frame = ttk.LabelFrame(parent, text="3D Billet View (VisPy OpenGL)", padding=5)
        viewport_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create VisPy 3D viewer
        # Note: VisPy will create its own native widget that embeds in Tkinter
        self.vispy_viewer = DamascusVispyViewer(parent=viewport_frame)
        
        # Get the native widget and pack it
        vispy_widget = self.vispy_viewer.get_native_widget()
        vispy_widget.pack(fill=tk.BOTH, expand=True)
        
        logger.info("VisPy 3D viewer created and embedded in Tkinter")
        logger.info("  - Left drag: Rotate")
        logger.info("  - Right drag: Pan")
        logger.info("  - Mouse wheel: Zoom (proper zoom behavior!)")
        
        # Note: Cross-section preview removed to maximize 3D viewport space
        # Z-position variables kept for potential future use
        self.z_position = tk.DoubleVar(value=0.0)
        self.z_slider = None
        self.z_label = None
        self.xsection_canvas = None
        
        logger.debug("Right panel created with full-height 3D viewport")
    
    def setup_status_bar(self):
        """Create status bar at bottom."""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_text = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_text, 
                 relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.stats_text = tk.StringVar(value="Layers: 0 | Operations: 0")
        ttk.Label(status_frame, textvariable=self.stats_text, 
                 relief=tk.SUNKEN).pack(side=tk.RIGHT)
        
        logger.debug("Status bar created")
    
    # ========================================================================
    # PATTERN SELECTION
    # ========================================================================
    
    def select_feather_pattern(self):
        """Select Feather Damascus pattern type."""
        logger.info("User selected: Feather Damascus")
        self.current_pattern_type = 'feather'
        self.status_text.set("Pattern: Feather Damascus (Wedge Split)")
        self.setup_feather_parameters()
    
    def select_twist_pattern(self):
        """Select Twist/Ladder Damascus pattern type."""
        logger.info("User selected: Twist Damascus")
        self.current_pattern_type = 'twist'
        self.status_text.set("Pattern: Twist/Ladder Damascus")
        self.setup_twist_parameters()
    
    def select_raindrop_pattern(self):
        """Select Raindrop Damascus pattern type."""
        logger.info("User selected: Raindrop Damascus")
        self.current_pattern_type = 'raindrop'
        self.status_text.set("Pattern: Raindrop Damascus (Drilling)")
        self.setup_raindrop_parameters()
    
    # ========================================================================
    # PARAMETER CONTROLS
    # ========================================================================
    
    def setup_feather_parameters(self):
        """Setup parameter controls for Feather Damascus."""
        # Clear existing parameters
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(self.params_frame, text="Feather Damascus Parameters", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Wedge depth
        ttk.Label(self.params_frame, text="Wedge Depth (mm):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.wedge_depth = tk.DoubleVar(value=18.0)
        ttk.Scale(self.params_frame, from_=5.0, to=30.0, variable=self.wedge_depth, 
                 orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.wedge_depth).grid(row=1, column=2, pady=2)
        
        # Wedge angle
        ttk.Label(self.params_frame, text="Wedge Angle (°):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.wedge_angle = tk.DoubleVar(value=35.0)
        ttk.Scale(self.params_frame, from_=20.0, to=50.0, variable=self.wedge_angle, 
                 orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.wedge_angle).grid(row=2, column=2, pady=2)
        
        # Split gap
        ttk.Label(self.params_frame, text="Split Gap (mm):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.split_gap = tk.DoubleVar(value=6.0)
        ttk.Scale(self.params_frame, from_=2.0, to=15.0, variable=self.split_gap, 
                 orient=tk.HORIZONTAL).grid(row=3, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.split_gap).grid(row=3, column=2, pady=2)
        
        self.params_frame.columnconfigure(1, weight=1)
        logger.debug("Feather parameters configured")
    
    def setup_twist_parameters(self):
        """Setup parameter controls for Twist Damascus."""
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(self.params_frame, text="Twist Damascus Parameters", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Twist angle
        ttk.Label(self.params_frame, text="Twist Angle (°):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.twist_angle = tk.DoubleVar(value=180.0)
        ttk.Scale(self.params_frame, from_=45.0, to=360.0, variable=self.twist_angle, 
                 orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.twist_angle).grid(row=1, column=2, pady=2)
        
        # Compression factor
        ttk.Label(self.params_frame, text="Compression:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.compression_factor = tk.DoubleVar(value=0.7)
        ttk.Scale(self.params_frame, from_=0.3, to=0.95, variable=self.compression_factor, 
                 orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.compression_factor).grid(row=2, column=2, pady=2)
        
        self.params_frame.columnconfigure(1, weight=1)
        logger.debug("Twist parameters configured")
    
    def setup_raindrop_parameters(self):
        """Setup parameter controls for Raindrop Damascus."""
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(self.params_frame, text="Raindrop Damascus Parameters", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Hole radius
        ttk.Label(self.params_frame, text="Hole Radius (mm):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.hole_radius = tk.DoubleVar(value=6.0)
        ttk.Scale(self.params_frame, from_=3.0, to=15.0, variable=self.hole_radius, 
                 orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.hole_radius).grid(row=1, column=2, pady=2)
        
        # Hole spacing
        ttk.Label(self.params_frame, text="Hole Spacing (mm):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.hole_spacing = tk.DoubleVar(value=20.0)
        ttk.Scale(self.params_frame, from_=10.0, to=40.0, variable=self.hole_spacing, 
                 orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.hole_spacing).grid(row=2, column=2, pady=2)
        
        # Grid size
        ttk.Label(self.params_frame, text="Grid Size:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.grid_size = tk.IntVar(value=3)
        ttk.Spinbox(self.params_frame, from_=2, to=5, textvariable=self.grid_size, 
                   width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Compression
        ttk.Label(self.params_frame, text="Compression:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.raindrop_compression = tk.DoubleVar(value=0.5)
        ttk.Scale(self.params_frame, from_=0.3, to=0.8, variable=self.raindrop_compression, 
                 orient=tk.HORIZONTAL).grid(row=4, column=1, sticky=tk.EW, pady=2)
        ttk.Label(self.params_frame, textvariable=self.raindrop_compression).grid(row=4, column=2, pady=2)
        
        self.params_frame.columnconfigure(1, weight=1)
        logger.debug("Raindrop parameters configured")
    
    # ========================================================================
    # BILLET OPERATIONS
    # ========================================================================
    
    def create_new_billet(self):
        """Create a new Damascus billet with current layer configuration."""
        try:
            logger.info("Creating new billet...")
            self.status_text.set("Creating new billet...")
            
            # Check if billet fits on build plate
            billet_w = self.billet_width.get()
            billet_l = self.billet_length.get()
            plate_w = self.build_plate_width.get()
            plate_l = self.build_plate_length.get()
            
            if billet_w > plate_w or billet_l > plate_l:
                logger.warning(f"Billet ({billet_w}×{billet_l}mm) exceeds build plate ({plate_w}×{plate_l}mm)")
                
                # Create custom dialog with three options
                dialog = tk.Toplevel(self.root)
                dialog.title("Build Plate Size Warning")
                dialog.transient(self.root)
                dialog.grab_set()
                
                # Warning message
                msg_frame = ttk.Frame(dialog, padding=20)
                msg_frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(msg_frame, text="⚠️ Billet Exceeds Build Plate!", 
                         font=('Arial', 12, 'bold')).pack(pady=(0, 10))
                ttk.Label(msg_frame, text=f"Billet: {billet_w:.0f}mm × {billet_l:.0f}mm").pack()
                ttk.Label(msg_frame, text=f"Build Plate: {plate_w:.0f}mm × {plate_l:.0f}mm").pack(pady=(0, 15))
                
                ttk.Label(msg_frame, text="The billet will extend beyond the workspace.",
                         font=('Arial', 9, 'italic')).pack(pady=(0, 10))
                
                # Store user choice
                user_choice = {'action': None}
                
                def auto_resize():
                    user_choice['action'] = 'resize'
                    dialog.destroy()
                
                def continue_anyway():
                    user_choice['action'] = 'continue'
                    dialog.destroy()
                
                def cancel_operation():
                    user_choice['action'] = 'cancel'
                    dialog.destroy()
                
                # Buttons
                button_frame = ttk.Frame(dialog, padding=(20, 0, 20, 20))
                button_frame.pack(fill=tk.X)
                
                # Calculate what the new size would be
                new_plate_w = max(plate_w, billet_w * 1.1)
                new_plate_l = max(plate_l, billet_l * 1.1)
                
                ttk.Button(button_frame, text=f"📐 Auto-Resize Build Plate\n({new_plate_w:.0f} × {new_plate_l:.0f} mm)",
                          command=auto_resize).pack(fill=tk.X, pady=2)
                ttk.Button(button_frame, text="✓ Continue Anyway",
                          command=continue_anyway).pack(fill=tk.X, pady=2)
                ttk.Button(button_frame, text="✗ Cancel",
                          command=cancel_operation).pack(fill=tk.X, pady=2)
                
                # Center dialog
                dialog.update_idletasks()
                dialog_width = dialog.winfo_reqwidth() + 40
                dialog_height = dialog.winfo_reqheight() + 20
                screen_width = dialog.winfo_screenwidth()
                screen_height = dialog.winfo_screenheight()
                x = (screen_width - dialog_width) // 2
                y = (screen_height - dialog_height) // 2
                dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
                
                dialog.wait_window()
                
                # Handle user choice
                if user_choice['action'] == 'cancel':
                    logger.info("Billet creation cancelled by user")
                    self.status_text.set("Billet creation cancelled")
                    return
                elif user_choice['action'] == 'resize':
                    # Auto-resize build plate to fit billet with 10% margin
                    self.build_plate_width.set(new_plate_w)
                    self.build_plate_length.set(new_plate_l)
                    logger.info(f"Auto-resized build plate to {new_plate_w:.0f}×{new_plate_l:.0f}mm")
                    self.status_text.set(f"Build plate resized to {new_plate_w:.0f}×{new_plate_l:.0f}mm")
                # If 'continue', just proceed without changes
            
            # Create billet
            self.billet = Damascus3DBillet(
                width=billet_w,
                length=billet_l
            )
            
            # Add layers
            self.billet.create_simple_layers(
                num_layers=self.num_layers.get(),
                white_thickness=self.white_thickness.get(),
                black_thickness=self.black_thickness.get()
            )
            
            # Clear operation history
            self.operation_history = []
            
            # Update displays
            self.update_3d_view()
            self.update_cross_section()
            self.update_status()
            
            self.status_text.set(f"Created new billet: {self.num_layers.get()} layers")
            logger.info(f"New billet created: {self.num_layers.get()} layers")
            
        except Exception as e:
            logger.error(f"Failed to create billet: {e}")
            messagebox.showerror("Error", f"Failed to create billet: {e}")
    
    def apply_current_operation(self):
        """Apply the currently selected pattern operation."""
        if self.billet is None:
            messagebox.showwarning("No Billet", "Please create a billet first")
            return
        
        if self.current_pattern_type is None:
            messagebox.showwarning("No Pattern", "Please select a pattern type")
            return
        
        try:
            logger.info(f"Applying operation: {self.current_pattern_type}")
            self.status_text.set(f"Applying {self.current_pattern_type} operation...")
            self.root.update()
            
            if self.current_pattern_type == 'feather':
                self.billet.apply_wedge_deformation(
                    wedge_depth=self.wedge_depth.get(),
                    wedge_angle=self.wedge_angle.get(),
                    split_gap=self.split_gap.get(),
                    debug=True
                )
                op_desc = f"Wedge: depth={self.wedge_depth.get():.1f}mm, angle={self.wedge_angle.get():.1f}°"
                
            elif self.current_pattern_type == 'twist':
                # Check if billet has been forged first
                if not self.is_forged:
                    messagebox.showwarning(
                        "Forging Required",
                        "Before twisting, the billet must be forged into a square or octagonal bar.\n\n"
                        "Click 'Forge to Square Bar' or 'Forge to Octagon Bar' first."
                    )
                    logger.warning("Twist attempted without forging - operation blocked")
                    return
                
                self.billet.apply_twist(
                    angle_degrees=self.twist_angle.get(),
                    axis='y',  # Twist around length axis (Y)
                    debug=True
                )
                op_desc = f"Twist: {self.twist_angle.get():.1f}°"
                
            elif self.current_pattern_type == 'raindrop':
                # Calculate hole positions
                grid_size = self.grid_size.get()
                spacing = self.hole_spacing.get()
                radius = self.hole_radius.get()
                
                # Create grid
                start = -(grid_size - 1) * spacing / 2
                for i in range(grid_size):
                    for j in range(grid_size):
                        x_pos = start + i * spacing
                        z_pos = start + j * spacing
                        self.billet.drill_hole(x_pos, z_pos, radius, debug=(i==0 and j==0))
                
                op_desc = f"Drilled {grid_size}×{grid_size} holes, radius={radius:.1f}mm"
            
            # Add to operation history
            self.operation_history.append(op_desc)
            
            # Update displays
            self.update_3d_view()
            self.update_cross_section()
            self.update_status()
            
            self.status_text.set(f"Operation complete: {op_desc}")
            logger.info(f"Operation applied successfully: {op_desc}")
            
        except Exception as e:
            logger.error(f"Failed to apply operation: {e}")
            messagebox.showerror("Error", f"Failed to apply operation: {e}")
            self.status_text.set("Error applying operation")
    
    def undo_operation(self):
        """Undo the last operation (recreate billet and replay operations)."""
        if not self.operation_history:
            messagebox.showinfo("Nothing to Undo", "No operations to undo")
            return
        
        logger.info("Undoing last operation")
        # TODO: Implement proper undo by replaying operation history
        messagebox.showinfo("Not Implemented", "Undo functionality coming soon!\n\n"
                           "For now, use 'Reset Billet' and reapply operations manually.")
    
    def reset_billet(self):
        """Reset billet to original state."""
        logger.info("Resetting billet")
        self.operation_history = []
        self.is_forged = False
        self.create_new_billet()
        self.status_text.set("Billet reset to original state")
    
    def forge_to_square(self):
        """Forge the billet into a square cross-section bar (delegates to lib)."""
        op_desc, forged = forge_to_square(
            self.root, self.billet, self.build_plate_width, self.build_plate_length
        )
        if forged:
            self.is_forged = True
            self.operation_history.append(op_desc)
            self.update_3d_view()
            self.update_cross_section()
            self.update_status()
            self.root.update_idletasks()
            self.status_text.set(f"Forged to square: {self.billet.width:.1f}mm × {self.billet.length:.1f}mm")
        return
    
    def forge_to_octagon(self):
        """Forge the billet into an octagonal bar (delegates to lib)."""
        op_desc, forged = forge_to_octagon(
            self.root, self.billet, self.build_plate_width, self.build_plate_length
        )
        if forged:
            self.is_forged = True
            self.operation_history.append(op_desc)
            self.update_3d_view()
            self.update_cross_section()
            self.update_status()
            self.root.update_idletasks()
            self.status_text.set(f"Forged to octagon: ~{self.billet.width:.1f}mm × {self.billet.length:.1f}mm")
    
        # ========================================================================
    # VISUALIZATION UPDATES
    # ========================================================================
    
    def update_3d_view(self):
        """Update the 3D viewport with current billet state using VisPy."""
        if self.billet is None:
            return
        
        if self.vispy_viewer is None:
            logger.warning("VisPy viewer not initialized")
            return
        
        logger.debug(f"Updating VisPy 3D viewport - Billet: {self.billet.width:.1f}W x {self.billet.length:.1f}L, {len(self.billet.layers)} layers")
        self.status_text.set("Rendering 3D view with VisPy...")
        self.root.update()
        
        # Render billet using VisPy viewer
        plate_w = self.build_plate_width.get()
        plate_l = self.build_plate_length.get()
        
        self.vispy_viewer.render_billet(
            self.billet,
            build_plate_width=plate_w,
            build_plate_length=plate_l
        )
        
        # Apply view angles if needed
        elevation = self.view_elevation.get()
        azimuth = self.view_azimuth.get()
        self.vispy_viewer.set_view_angles(elevation, azimuth)
        
        self.status_text.set("3D view updated (VisPy)")
        logger.debug(f"VisPy viewport rendered with {len(self.billet.layers)} layers")
    
    def update_cross_section(self):
        """Update the cross-section preview."""
        # Cross-section preview was removed from UI - this function is now a no-op
        # but kept for compatibility with existing code that calls it
        if self.billet is None or self.xsection_canvas is None:
            return
        
        logger.debug(f"Updating cross-section at Z={self.z_position.get():.1f}mm")
        self.status_text.set("Extracting cross-section...")
        self.root.update()
        
        # Extract cross-section
        z_pos = self.z_position.get()
        cross_section_array = self.billet.extract_cross_section(
            z_slice=z_pos,
            resolution=600,
            debug=False
        )
        
        # Convert to PIL Image
        self.cross_section_image = Image.fromarray(cross_section_array)
        
        # Display on canvas
        canvas_width = self.xsection_canvas.winfo_width()
        canvas_height = self.xsection_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Resize to fit canvas
            display_img = self.cross_section_image.resize(
                (canvas_width, canvas_height),
                Image.Resampling.LANCZOS
            )
            
            self.cross_section_display = ImageTk.PhotoImage(display_img)
            
            # Clear and redraw
            self.xsection_canvas.delete("all")
            self.xsection_canvas.create_image(
                canvas_width//2, canvas_height//2,
                image=self.cross_section_display
            )
        
        self.status_text.set(f"Cross-section at Z={z_pos:.1f}mm")
        logger.debug("Cross-section updated")
    
    def on_z_position_change(self, value):
        """Called when Z-position slider changes."""
        if self.z_label is not None:
            self.z_label.config(text=f"{float(value):.1f} mm")
    
    def set_top_view(self):
        """Set view to top-down (looking at build plate)."""
        logger.info("Setting top view (build plate)")
        self.view_elevation.set(90.0)  # Looking straight down
        self.view_azimuth.set(0.0)
        self.update_3d_view()
    
    def set_front_view(self):
        """Set view to front (looking at layers edge-on)."""
        logger.info("Setting front view")
        self.view_elevation.set(0.0)  # Looking horizontally
        self.view_azimuth.set(0.0)
        self.update_3d_view()
    
    def set_isometric_view(self):
        """Set view to isometric (3D perspective)."""
        logger.info("Setting isometric view")
        self.view_elevation.set(30.0)
        self.view_azimuth.set(45.0)
        self.update_3d_view()
    
    def zoom_to_fit(self):
        """Reset camera to fit the entire billet in viewport."""
        if self.billet is None or self.vispy_viewer is None:
            return
        
        logger.info("Resetting camera to fit billet")
        self.vispy_viewer.reset_camera()
        self.status_text.set("Camera reset to fit")
    
    # ========================================================================
    # EXPORT FUNCTIONS (delegated to lib/gui_export.py)
    # ========================================================================
    
    def export_3d_model(self, format_type):
        """Export the billet as a 3D model file."""
        export_3d_model(self.root, self.billet, format_type, self.status_text)
    
    def export_cross_section(self):
        """Export the current cross-section as PNG."""
        export_cross_section(self.root, self.billet, self.z_position, self.status_text)
    
    def export_operation_log(self):
        """Export the operation history as JSON."""
        export_operation_log(self.root, self.billet, self.status_text)
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def update_status(self):
        """Update the status bar with current billet statistics."""
        if self.billet:
            layer_count = len(self.billet.layers)
            op_count = len(self.billet.operation_history)
            height = sum(l.thickness for l in self.billet.layers)
            self.stats_text.set(f"Layers: {layer_count} | Operations: {op_count}")
            logger.debug(f"Status updated: {layer_count} layers, {op_count} ops, {self.billet.width:.1f}x{self.billet.length:.1f}x{height:.1f}mm")
    
    def _remove_debug_console_handler(self):
        """Detach the live console log handler from the shared logger."""
        if self.debug_console_handler is not None:
            logger.removeHandler(self.debug_console_handler)
            self.debug_console_handler.close()
            self.debug_console_handler = None

    def show_debug_console(self):
        """Show a live debug console window (delegates to lib)."""
        result = show_debug_console(
            self.root, logger, SIM_LOGS_DIR,
            self.debug_console_window, self.debug_console_text, self.debug_console_handler
        )
        self.debug_console_window = result['window']
        self.debug_console_text = result['text']
        self.debug_console_handler = result['handler']
    
    def show_billet_stats(self):
        """Show detailed billet statistics."""
        show_billet_stats(self.root, self.billet, self.operation_history)
    
    def show_about(self):
        """Show About dialog."""
        show_about()
    
    def show_quick_start(self):
        """Show Quick Start Guide."""
        show_quick_start(self.root)
    
    # ========================================================================
    # REFERENCE VIEWERS (delegated to lib/gui_references.py)
    # ========================================================================
    
    def show_heat_treatment_guide(self):
        """Show comprehensive hardening & tempering guide."""
        show_heat_treatment_guide(self.root)
    
    def show_steel_properties(self):
        """Show steel properties database."""
        show_steel_properties(self.root)
    
    def show_add_custom_steel_dialog(self):
        """Show dialog for adding a custom steel."""
        show_add_custom_steel_dialog(self.root)
    
    def show_forging_losses(self):
        """Show forging losses reference."""
        show_forging_losses(self.root)
    
    def show_plasticity_guide(self):
        """Show steel plasticity guide."""
        show_plasticity_guide(self.root)
    
    # ========================================================================
    # MAIN EVENT LOOP
    # ========================================================================
    
    def run(self):
        """Start the GUI application."""
        logger.info("Starting GUI main loop")
        self.root.mainloop()
        self._remove_debug_console_handler()
        logger.info("GUI application closed")


def main():
    """
    Main entry point for Damascus 3D GUI application.
    
    Creates Tkinter root window and starts the GUI.
    """
    try:
        logger.info("="*70)
        logger.info("DAMASCUS 3D GUI APPLICATION STARTING")
        logger.info("="*70)
        
        root = tk.Tk()
        app = Damascus3DGUI(root)
        
        # Handle window close
        def on_closing():
            if messagebox.askokcancel("Quit", "Exit Damascus 3D Simulator?"):
                app._remove_debug_console_handler()
                logger.info("User closed application")
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        app.run()
        
    except Exception as e:
        logger.exception("FATAL ERROR in GUI application:")
        print(f"\nFATAL ERROR: {e}")
        print("Check the debug log file for details.")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
