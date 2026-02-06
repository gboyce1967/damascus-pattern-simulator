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
│ Menu Bar (File, View, Help)                        │
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
import matplotlib
matplotlib.use('TkAgg')  # Use Tkinter backend for 2D cross-sections only
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import logging
from datetime import datetime
import json

# Import our 3D Damascus engine
from damascus_3d_simulator import Damascus3DBillet, DamascusLayer, logger
import open3d as o3d

# Import VisPy 3D viewer (replaces matplotlib 3D)
from vispy_3d_viewer import DamascusVispyViewer

# Import steel database
from steel_database import get_database


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
        - 3D viewport (top 60%) - VisPy OpenGL viewer
        - Cross-section preview (bottom 40%) - Matplotlib 2D
        """
        # 3D Viewport (top) - VisPy
        viewport_frame = ttk.LabelFrame(parent, text="3D Billet View (VisPy OpenGL)", padding=5)
        viewport_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
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
        
        # Cross-section preview (bottom)
        xsection_frame = ttk.LabelFrame(parent, text="Cross-Section Preview", padding=5)
        xsection_frame.pack(fill=tk.BOTH, expand=True)
        
        # Z-position slider
        slider_frame = ttk.Frame(xsection_frame)
        slider_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(slider_frame, text="Z Position:").pack(side=tk.LEFT, padx=5)
        self.z_position = tk.DoubleVar(value=0.0)
        self.z_slider = ttk.Scale(slider_frame, from_=-50, to=50, 
                                 variable=self.z_position, orient=tk.HORIZONTAL,
                                 command=self.on_z_position_change)
        self.z_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.z_label = ttk.Label(slider_frame, text="0.0 mm")
        self.z_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(slider_frame, text="Update", 
                  command=self.update_cross_section).pack(side=tk.LEFT, padx=5)
        
        # Canvas for cross-section image
        self.xsection_canvas = tk.Canvas(xsection_frame, bg='#2d2d2d', 
                                        highlightthickness=1, 
                                        highlightbackground=self.colors['border'])
        self.xsection_canvas.pack(fill=tk.BOTH, expand=True)
        
        logger.debug("Right panel created with 3D viewport and cross-section preview")
    
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
        """
        Forge the billet into a square cross-section bar through multiple hammer strikes.
        
        REAL FORGING PHYSICS:
        - Volume is conserved (material doesn't disappear)
        - Each hammer strike compresses the cross-section
        - Material flows lengthwise (bar extends)
        - Multiple heats required to achieve target size
        """
        if self.billet is None:
            messagebox.showwarning("No Billet", "Please create a billet first")
            return
        
        # Create dialog to get forging parameters from user
        dialog = tk.Toplevel(self.root)
        dialog.title("Forge to Square Bar")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Current dimensions info
        current_height = sum(l.thickness for l in self.billet.layers)
        current_volume = self.billet.width * self.billet.length * current_height
        
        info_frame = ttk.LabelFrame(dialog, text="Current Billet", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(info_frame, text=f"Width: {self.billet.width:.1f} mm").pack(anchor='w')
        ttk.Label(info_frame, text=f"Length: {self.billet.length:.1f} mm").pack(anchor='w')
        ttk.Label(info_frame, text=f"Height: {current_height:.1f} mm").pack(anchor='w')
        ttk.Label(info_frame, text=f"Volume: {current_volume:.0f} mm³").pack(anchor='w')
        
        # Target dimensions
        params_frame = ttk.LabelFrame(dialog, text="Target Bar Dimensions", padding=10)
        params_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(params_frame, text="Bar Size (width = height, mm):").grid(row=0, column=0, sticky='w', pady=2)
        bar_size_var = tk.DoubleVar(value=15.0)
        bar_size_spinbox = ttk.Spinbox(params_frame, from_=5.0, to=100.0, increment=1.0, 
                                       textvariable=bar_size_var, width=10)
        bar_size_spinbox.grid(row=0, column=1, pady=2)
        
        ttk.Label(params_frame, text="Number of Heats:").grid(row=1, column=0, sticky='w', pady=2)
        heats_var = tk.IntVar(value=5)
        heats_spinbox = ttk.Spinbox(params_frame, from_=1, to=20, increment=1, 
                                    textvariable=heats_var, width=10)
        heats_spinbox.grid(row=1, column=1, pady=2)
        
        # Calculated result preview
        result_frame = ttk.LabelFrame(dialog, text="Calculated Result", padding=10)
        result_frame.pack(fill='x', padx=10, pady=5)
        
        result_label = ttk.Label(result_frame, text="", justify='left')
        result_label.pack(anchor='w')
        
        def update_preview(*args):
            bar_size = bar_size_var.get()
            final_length = current_volume / (bar_size * bar_size)
            extension_ratio = final_length / self.billet.length
            result_label.config(text=f"Final length: {final_length:.1f} mm ({extension_ratio:.2f}x extension)\n"
                               f"Cross-section: {bar_size:.1f} × {bar_size:.1f} mm")
        
        bar_size_var.trace_add('write', update_preview)
        heats_var.trace_add('write', update_preview)
        update_preview()
        
        # Buttons
        result = {'confirmed': False}
        
        def on_confirm():
            result['confirmed'] = True
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Forge", command=on_confirm).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)
        
        # Center dialog and size to content
        dialog.update_idletasks()
        dialog_width = dialog.winfo_reqwidth() + 40
        dialog_height = dialog.winfo_reqheight() + 20
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        dialog.wait_window()
        
        if not result['confirmed']:
            logger.info("Forging cancelled by user")
            return
        
        # Execute forging with user parameters
        target_bar_size = bar_size_var.get()
        num_heats = heats_var.get()
        
        logger.info(f"Forging billet to square bar: {target_bar_size}mm, {num_heats} heats")
        self.status_text.set(f"Forging to square bar ({num_heats} heats)...")
        self.root.update()
        
        # Calculate dimensions
        original_width = self.billet.width
        original_length = self.billet.length
        original_height = current_height
        original_volume = current_volume
        
        # Volume conservation: width × height × length = constant
        # target_bar_size² × final_length = original_volume
        final_length = original_volume / (target_bar_size * target_bar_size)
        
        logger.debug(f"Original: {original_width:.1f}W × {original_length:.1f}L × {original_height:.1f}H mm")
        logger.debug(f"Target: {target_bar_size:.1f}W × {final_length:.1f}L × {target_bar_size:.1f}H mm")
        logger.debug(f"Volume: {original_volume:.1f} mm³")
        
        # Check if forged bar will fit on build plate
        plate_w = self.build_plate_width.get()
        plate_l = self.build_plate_length.get()
        
        if target_bar_size > plate_w or final_length > plate_l:
            logger.warning(f"Forged bar ({target_bar_size:.1f}×{final_length:.1f}mm) exceeds build plate ({plate_w}×{plate_l}mm)")
            
            # Create custom dialog with three options
            warning_dialog = tk.Toplevel(self.root)
            warning_dialog.title("Build Plate Size Warning")
            warning_dialog.transient(self.root)
            warning_dialog.grab_set()
            
            # Warning message
            warn_msg_frame = ttk.Frame(warning_dialog, padding=20)
            warn_msg_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(warn_msg_frame, text="⚠️ Forged Bar Exceeds Build Plate!", 
                     font=('Arial', 12, 'bold')).pack(pady=(0, 10))
            ttk.Label(warn_msg_frame, text=f"Bar: {target_bar_size:.0f}mm × {final_length:.0f}mm").pack()
            ttk.Label(warn_msg_frame, text=f"Build Plate: {plate_w:.0f}mm × {plate_l:.0f}mm").pack(pady=(0, 15))
            
            ttk.Label(warn_msg_frame, text="The forged bar will extend beyond the workspace.",
                     font=('Arial', 9, 'italic')).pack(pady=(0, 10))
            
            # Store user choice
            forge_choice = {'action': None}
            
            def auto_resize_forge():
                forge_choice['action'] = 'resize'
                warning_dialog.destroy()
            
            def continue_forge():
                forge_choice['action'] = 'continue'
                warning_dialog.destroy()
            
            def cancel_forge():
                forge_choice['action'] = 'cancel'
                warning_dialog.destroy()
            
            # Buttons
            warn_button_frame = ttk.Frame(warning_dialog, padding=(20, 0, 20, 20))
            warn_button_frame.pack(fill=tk.X)
            
            # Calculate new build plate size (10% larger than needed, squared for symmetry)
            new_size = max(target_bar_size * 1.1, final_length * 1.1)
            
            ttk.Button(warn_button_frame, text=f"📐 Auto-Resize Build Plate\n({new_size:.0f} × {new_size:.0f} mm)",
                      command=auto_resize_forge).pack(fill=tk.X, pady=2)
            ttk.Button(warn_button_frame, text="✓ Continue Anyway",
                      command=continue_forge).pack(fill=tk.X, pady=2)
            ttk.Button(warn_button_frame, text="✗ Cancel Forging",
                      command=cancel_forge).pack(fill=tk.X, pady=2)
            
            # Center dialog
            warning_dialog.update_idletasks()
            warn_width = warning_dialog.winfo_reqwidth() + 40
            warn_height = warning_dialog.winfo_reqheight() + 20
            warn_x = (warning_dialog.winfo_screenwidth() - warn_width) // 2
            warn_y = (warning_dialog.winfo_screenheight() - warn_height) // 2
            warning_dialog.geometry(f"{warn_width}x{warn_height}+{warn_x}+{warn_y}")
            
            warning_dialog.wait_window()
            
            # Handle user choice
            if forge_choice['action'] == 'cancel':
                logger.info("Forging cancelled by user due to build plate size")
                return
            elif forge_choice['action'] == 'resize':
                # Auto-resize build plate (squared for symmetry)
                self.build_plate_width.set(new_size)
                self.build_plate_length.set(new_size)
                logger.info(f"Auto-resized build plate to {new_size:.0f}×{new_size:.0f}mm")
                self.status_text.set(f"Build plate resized to {new_size:.0f}×{new_size:.0f}mm")
            # If 'continue', proceed without changes
        
        # Store original vertex positions BEFORE any transformation
        logger.debug(f"Storing original vertex positions for {len(self.billet.layers)} layers...")
        original_vertices = []
        for layer in self.billet.layers:
            original_vertices.append(np.asarray(layer.mesh.vertices).copy())
        
        # Store original layer properties
        original_layer_thickness = [layer.thickness for layer in self.billet.layers]
        original_layer_z_pos = [layer.z_position for layer in self.billet.layers]
        
        # Apply progressive forging (each heat compresses and extends)
        logger.debug(f"Starting {num_heats} forging heats...")
        
        for heat_num in range(num_heats):
            progress = (heat_num + 1) / num_heats
            
            # Target dimensions for this heat (interpolate from original to final)
            target_width = original_width + (target_bar_size - original_width) * progress
            target_height = original_height + (target_bar_size - original_height) * progress
            target_length = original_length + (final_length - original_length) * progress
            
            logger.info(f"Heat {heat_num + 1}/{num_heats}: {target_width:.1f}W × {target_length:.1f}L × {target_height:.1f}H mm")
            
            # CUMULATIVE scale factors (from ORIGINAL dimensions to current target)
            scale_x = target_width / original_width
            scale_y = target_length / original_length
            scale_z = target_height / original_height
            
            logger.debug(f"  Cumulative scale from original: X={scale_x:.3f}, Y={scale_y:.3f}, Z={scale_z:.3f}")
            
            # Apply to each layer (transform from ORIGINAL vertices)
            for layer_idx, layer in enumerate(self.billet.layers):
                # Get ORIGINAL vertices for this layer
                vertices = original_vertices[layer_idx].copy()
                
                if layer_idx == 0 and heat_num == 0:
                    logger.debug(f"  Layer 0 original vertex[0]: {vertices[0]}")
                
                # Apply transformation from original positions
                for i in range(len(vertices)):
                    x, y, z = vertices[i]
                    vertices[i, 0] = x * scale_x  # Compress width from original
                    vertices[i, 1] = y * scale_y  # Extend length from original
                    vertices[i, 2] = z * scale_z  # Compress height from original
                
                if layer_idx == 0:
                    logger.debug(f"  Layer 0 transformed vertex[0]: {vertices[0]}")
                
                # Update mesh with transformed vertices
                layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
                layer.mesh.compute_vertex_normals()
            
            # Update layer positions and thicknesses (from original values)
            for layer_idx, layer in enumerate(self.billet.layers):
                layer.thickness = original_layer_thickness[layer_idx] * scale_z
                layer.z_position = original_layer_z_pos[layer_idx] * scale_z
                
                if layer_idx < 2 and heat_num == num_heats - 1:
                    logger.debug(f"  Layer {layer_idx} final: thickness={layer.thickness:.3f}mm, z_pos={layer.z_position:.3f}mm")
        
        # Update billet dimensions
        self.billet.width = target_bar_size
        self.billet.length = final_length
        self.is_forged = True
        
        # CRITICAL DEBUG: Check if vertices were actually updated
        logger.debug("POST-FORGING VERTEX CHECK:")
        for layer_idx in [0, len(self.billet.layers)-1]:  # Check first and last layer
            verts_check = np.asarray(self.billet.layers[layer_idx].mesh.vertices)
            y_min = verts_check[:, 1].min()
            y_max = verts_check[:, 1].max()
            logger.debug(f"  Layer {layer_idx} Y range in mesh: [{y_min:.1f}, {y_max:.1f}]")
            logger.debug(f"  Layer {layer_idx} expected Y range: [{-final_length/2:.1f}, {final_length/2:.1f}]")
        
        # Verify volume conservation
        final_height = sum(l.thickness for l in self.billet.layers)
        final_volume = self.billet.width * self.billet.length * final_height
        volume_ratio = final_volume / original_volume
        
        logger.info(f"Forging complete. Volume ratio: {volume_ratio:.3f} (should be ~1.0)")
        
        # Add to history
        op_desc = f"Forged to square: {target_bar_size:.1f}×{target_bar_size:.1f}mm, length {final_length:.1f}mm ({num_heats} heats)"
        self.operation_history.append(op_desc)
        self.billet.operation_history.append({
            'operation': 'forge_square',
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'target_bar_size': target_bar_size,
                'num_heats': num_heats,
                'final_length': final_length,
                'extension_ratio': final_length / original_length,
                'volume_ratio': volume_ratio
            }
        })
        
        # Update displays
        logger.debug(f"Updating displays after forging. Billet dims: {self.billet.width}x{self.billet.length}")
        self.update_3d_view()
        self.update_cross_section()
        self.update_status()
        
        # Update GUI
        self.root.update_idletasks()
        self.root.update()
        
        self.status_text.set(f"Forged to square: {target_bar_size:.1f}mm × {final_length:.1f}mm")
        logger.info(f"Display updated. Showing completion dialog.")
        
        messagebox.showinfo("Forging Complete", 
                           f"Billet forged to square bar:\n"
                           f"Cross-section: {target_bar_size:.1f} × {target_bar_size:.1f} mm\n"
                           f"Length: {final_length:.1f} mm ({final_length/original_length:.1f}x extension)\n"
                           f"Heats: {num_heats}\n"
                           f"Volume conserved: {volume_ratio:.3f}\n\n"
                           "You can now apply twist operations!")
    
    def forge_to_octagon(self):
        """
        Forge the billet into an octagonal cross-section bar through multiple hammer strikes.
        
        Creates an 8-sided profile by forging to square then chamfering corners.
        This is traditional for twist Damascus.
        """
        if self.billet is None:
            messagebox.showwarning("No Billet", "Please create a billet first")
            return
        
        # Create dialog to get forging parameters from user
        dialog = tk.Toplevel(self.root)
        dialog.title("Forge to Octagonal Bar")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Current dimensions info
        current_height = sum(l.thickness for l in self.billet.layers)
        current_volume = self.billet.width * self.billet.length * current_height
        
        info_frame = ttk.LabelFrame(dialog, text="Current Billet", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(info_frame, text=f"Width: {self.billet.width:.1f} mm").pack(anchor='w')
        ttk.Label(info_frame, text=f"Length: {self.billet.length:.1f} mm").pack(anchor='w')
        ttk.Label(info_frame, text=f"Height: {current_height:.1f} mm").pack(anchor='w')
        ttk.Label(info_frame, text=f"Volume: {current_volume:.0f} mm³").pack(anchor='w')
        
        # Target dimensions
        params_frame = ttk.LabelFrame(dialog, text="Target Bar Dimensions", padding=10)
        params_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(params_frame, text="Bar Size (across flats, mm):").grid(row=0, column=0, sticky='w', pady=2)
        bar_size_var = tk.DoubleVar(value=15.0)
        bar_size_spinbox = ttk.Spinbox(params_frame, from_=5.0, to=100.0, increment=1.0, 
                                       textvariable=bar_size_var, width=10)
        bar_size_spinbox.grid(row=0, column=1, pady=2)
        
        ttk.Label(params_frame, text="Number of Heats:").grid(row=1, column=0, sticky='w', pady=2)
        heats_var = tk.IntVar(value=5)
        heats_spinbox = ttk.Spinbox(params_frame, from_=1, to=20, increment=1, 
                                    textvariable=heats_var, width=10)
        heats_spinbox.grid(row=1, column=1, pady=2)
        
        ttk.Label(params_frame, text="Chamfer %:").grid(row=2, column=0, sticky='w', pady=2)
        chamfer_var = tk.DoubleVar(value=15.0)
        chamfer_spinbox = ttk.Spinbox(params_frame, from_=5.0, to=30.0, increment=1.0, 
                                      textvariable=chamfer_var, width=10)
        chamfer_spinbox.grid(row=2, column=1, pady=2)
        
        # Calculated result preview
        result_frame = ttk.LabelFrame(dialog, text="Calculated Result", padding=10)
        result_frame.pack(fill='x', padx=10, pady=5)
        
        result_label = ttk.Label(result_frame, text="", justify='left')
        result_label.pack(anchor='w')
        
        def update_preview(*args):
            bar_size = bar_size_var.get()
            # Octagon approximation: slightly larger than bar_size due to chamfers
            octagon_area = bar_size * bar_size * 0.95  # Approximate area
            final_length = current_volume / octagon_area
            extension_ratio = final_length / self.billet.length
            result_label.config(text=f"Final length: {final_length:.1f} mm ({extension_ratio:.2f}x extension)\n"
                               f"Octagonal cross-section: ~{bar_size:.1f} mm across flats")
        
        bar_size_var.trace_add('write', update_preview)
        heats_var.trace_add('write', update_preview)
        chamfer_var.trace_add('write', update_preview)
        update_preview()
        
        # Buttons
        result = {'confirmed': False}
        
        def on_confirm():
            result['confirmed'] = True
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Forge", command=on_confirm).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)
        
        # Center dialog and size to content
        dialog.update_idletasks()
        dialog_width = dialog.winfo_reqwidth() + 40
        dialog_height = dialog.winfo_reqheight() + 20
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        dialog.wait_window()
        
        if not result['confirmed']:
            logger.info("Forging cancelled by user")
            return
        
        # Execute forging with user parameters
        target_bar_size = bar_size_var.get()
        num_heats = heats_var.get()
        chamfer_percent = chamfer_var.get() / 100.0
        
        logger.info(f"Forging billet to octagonal bar: {target_bar_size}mm, {num_heats} heats, {chamfer_percent*100}% chamfer")
        self.status_text.set(f"Forging to octagonal bar ({num_heats} heats)...")
        self.root.update()
        
        # Calculate dimensions (octagon approximation)
        original_width = self.billet.width
        original_length = self.billet.length
        original_height = current_height
        original_volume = current_volume
        
        # Volume conservation with octagonal cross-section
        octagon_area = target_bar_size * target_bar_size * 0.95  # Approximate
        final_length = original_volume / octagon_area
        
        logger.debug(f"Original: {original_width:.1f}W × {original_length:.1f}L × {original_height:.1f}H mm")
        logger.debug(f"Target octagon: ~{target_bar_size:.1f} across flats, length {final_length:.1f}mm")
        
        # Check if forged bar will fit on build plate
        plate_w = self.build_plate_width.get()
        plate_l = self.build_plate_length.get()
        
        if target_bar_size > plate_w or final_length > plate_l:
            logger.warning(f"Forged octagon bar ({target_bar_size:.1f}×{final_length:.1f}mm) exceeds build plate ({plate_w}×{plate_l}mm)")
            
            # Create custom dialog with three options
            oct_warning_dialog = tk.Toplevel(self.root)
            oct_warning_dialog.title("Build Plate Size Warning")
            oct_warning_dialog.transient(self.root)
            oct_warning_dialog.grab_set()
            
            # Warning message
            oct_warn_msg_frame = ttk.Frame(oct_warning_dialog, padding=20)
            oct_warn_msg_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(oct_warn_msg_frame, text="⚠️ Forged Bar Exceeds Build Plate!", 
                     font=('Arial', 12, 'bold')).pack(pady=(0, 10))
            ttk.Label(oct_warn_msg_frame, text=f"Bar: ~{target_bar_size:.0f}mm × {final_length:.0f}mm").pack()
            ttk.Label(oct_warn_msg_frame, text=f"Build Plate: {plate_w:.0f}mm × {plate_l:.0f}mm").pack(pady=(0, 15))
            
            ttk.Label(oct_warn_msg_frame, text="The forged octagonal bar will extend beyond the workspace.",
                     font=('Arial', 9, 'italic')).pack(pady=(0, 10))
            
            # Store user choice
            oct_forge_choice = {'action': None}
            
            def auto_resize_oct_forge():
                oct_forge_choice['action'] = 'resize'
                oct_warning_dialog.destroy()
            
            def continue_oct_forge():
                oct_forge_choice['action'] = 'continue'
                oct_warning_dialog.destroy()
            
            def cancel_oct_forge():
                oct_forge_choice['action'] = 'cancel'
                oct_warning_dialog.destroy()
            
            # Buttons
            oct_warn_button_frame = ttk.Frame(oct_warning_dialog, padding=(20, 0, 20, 20))
            oct_warn_button_frame.pack(fill=tk.X)
            
            # Calculate new build plate size (10% larger than needed, squared for symmetry)
            oct_new_size = max(target_bar_size * 1.1, final_length * 1.1)
            
            ttk.Button(oct_warn_button_frame, text=f"📐 Auto-Resize Build Plate\n({oct_new_size:.0f} × {oct_new_size:.0f} mm)",
                      command=auto_resize_oct_forge).pack(fill=tk.X, pady=2)
            ttk.Button(oct_warn_button_frame, text="✓ Continue Anyway",
                      command=continue_oct_forge).pack(fill=tk.X, pady=2)
            ttk.Button(oct_warn_button_frame, text="✗ Cancel Forging",
                      command=cancel_oct_forge).pack(fill=tk.X, pady=2)
            
            # Center dialog
            oct_warning_dialog.update_idletasks()
            oct_warn_width = oct_warning_dialog.winfo_reqwidth() + 40
            oct_warn_height = oct_warning_dialog.winfo_reqheight() + 20
            oct_warn_x = (oct_warning_dialog.winfo_screenwidth() - oct_warn_width) // 2
            oct_warn_y = (oct_warning_dialog.winfo_screenheight() - oct_warn_height) // 2
            oct_warning_dialog.geometry(f"{oct_warn_width}x{oct_warn_height}+{oct_warn_x}+{oct_warn_y}")
            
            oct_warning_dialog.wait_window()
            
            # Handle user choice
            if oct_forge_choice['action'] == 'cancel':
                logger.info("Forging cancelled by user due to build plate size")
                return
            elif oct_forge_choice['action'] == 'resize':
                # Auto-resize build plate (squared for symmetry)
                self.build_plate_width.set(oct_new_size)
                self.build_plate_length.set(oct_new_size)
                logger.info(f"Auto-resized build plate to {oct_new_size:.0f}×{oct_new_size:.0f}mm")
                self.status_text.set(f"Build plate resized to {oct_new_size:.0f}×{oct_new_size:.0f}mm")
            # If 'continue', proceed without changes
        
        # Store original vertex positions BEFORE any transformation
        logger.debug(f"Storing original vertex positions for {len(self.billet.layers)} layers...")
        original_vertices = []
        for layer in self.billet.layers:
            original_vertices.append(np.asarray(layer.mesh.vertices).copy())
        
        # Store original layer properties
        original_layer_thickness = [layer.thickness for layer in self.billet.layers]
        original_layer_z_pos = [layer.z_position for layer in self.billet.layers]
        
        # Apply progressive forging
        logger.debug(f"Starting {num_heats} forging heats with chamfering...")
        
        for heat_num in range(num_heats):
            progress = (heat_num + 1) / num_heats
            
            # Target dimensions for this heat (interpolate from original to final)
            target_width = original_width + (target_bar_size - original_width) * progress
            target_height = original_height + (target_bar_size - original_height) * progress
            target_length = original_length + (final_length - original_length) * progress
            
            logger.info(f"Heat {heat_num + 1}/{num_heats}: {target_width:.1f}W × {target_length:.1f}L × {target_height:.1f}H mm")
            
            # CUMULATIVE scale factors (from ORIGINAL dimensions to current target)
            scale_x = target_width / original_width
            scale_y = target_length / original_length
            scale_z = target_height / original_height
            
            # Chamfer factor increases with progress
            current_chamfer = chamfer_percent * progress
            
            logger.debug(f"  Cumulative scale from original: X={scale_x:.3f}, Y={scale_y:.3f}, Z={scale_z:.3f}, Chamfer={current_chamfer:.3f}")
            
            # Apply to each layer (transform from ORIGINAL vertices)
            chamfered_vertices_count = 0
            for layer_idx, layer in enumerate(self.billet.layers):
                # Get ORIGINAL vertices for this layer
                vertices = original_vertices[layer_idx].copy()
                layer_chamfered = 0
                
                if layer_idx == 0 and heat_num == 0:
                    logger.debug(f"  Layer 0 original vertex[0]: {vertices[0]}")
                
                # Apply transformation from original positions
                for i in range(len(vertices)):
                    x, y, z = vertices[i]
                    
                    # Apply forging transformation from original
                    x_forged = x * scale_x
                    y_forged = y * scale_y
                    z_forged = z * scale_z
                    
                    # Apply chamfer to corners (creates octagon from square)
                    abs_x = abs(x_forged)
                    abs_y = abs(y_forged)
                    corner_threshold = target_width / 2 - (target_width * current_chamfer)
                    
                    if abs_x > corner_threshold and abs_y > corner_threshold:
                        # Vertex is in corner - chamfer it
                        chamfer_scale = 1.0 - current_chamfer
                        x_forged *= chamfer_scale
                        y_forged *= chamfer_scale
                        layer_chamfered += 1
                    
                    vertices[i, 0] = x_forged
                    vertices[i, 1] = y_forged
                    vertices[i, 2] = z_forged
                
                if layer_idx == 0:
                    logger.debug(f"  Layer 0 transformed vertex[0]: {vertices[0]}")
                
                chamfered_vertices_count += layer_chamfered
                
                # Update mesh with transformed vertices
                layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
                layer.mesh.compute_vertex_normals()
            
            logger.debug(f"  Chamfered vertices this heat: {chamfered_vertices_count}")
            
            # Update layer positions and thicknesses (from original values)
            for layer_idx, layer in enumerate(self.billet.layers):
                layer.thickness = original_layer_thickness[layer_idx] * scale_z
                layer.z_position = original_layer_z_pos[layer_idx] * scale_z
                
                if layer_idx < 2 and heat_num == num_heats - 1:
                    logger.debug(f"  Layer {layer_idx} final: thickness={layer.thickness:.3f}mm, z_pos={layer.z_position:.3f}mm")
        
        # Update billet dimensions
        self.billet.width = target_bar_size
        self.billet.length = final_length
        self.is_forged = True
        
        # CRITICAL DEBUG: Check if vertices were actually updated
        logger.debug("POST-FORGING VERTEX CHECK:")
        for layer_idx in [0, len(self.billet.layers)-1]:  # Check first and last layer
            verts_check = np.asarray(self.billet.layers[layer_idx].mesh.vertices)
            y_min = verts_check[:, 1].min()
            y_max = verts_check[:, 1].max()
            logger.debug(f"  Layer {layer_idx} Y range in mesh: [{y_min:.1f}, {y_max:.1f}]")
            logger.debug(f"  Layer {layer_idx} expected Y range: [{-final_length/2:.1f}, {final_length/2:.1f}]")
        
        # Verify volume conservation
        final_height = sum(l.thickness for l in self.billet.layers)
        final_volume = self.billet.width * self.billet.length * final_height * 0.95  # Octagon area approximation
        volume_ratio = final_volume / original_volume
        
        logger.info(f"Forging complete. Volume ratio: {volume_ratio:.3f} (should be ~0.95 for octagon)")
        
        # Add to history
        op_desc = f"Forged to octagon: ~{target_bar_size:.1f}mm across flats, length {final_length:.1f}mm ({num_heats} heats)"
        self.operation_history.append(op_desc)
        self.billet.operation_history.append({
            'operation': 'forge_octagon',
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'target_bar_size': target_bar_size,
                'num_heats': num_heats,
                'chamfer_percent': chamfer_percent * 100,
                'final_length': final_length,
                'extension_ratio': final_length / original_length,
                'volume_ratio': volume_ratio
            }
        })
        
        # Update displays
        logger.debug(f"Updating displays after forging. Billet dims: {self.billet.width}x{self.billet.length}")
        self.update_3d_view()
        self.update_cross_section()
        self.update_status()
        
        # Update GUI
        self.root.update_idletasks()
        self.root.update()
        
        self.status_text.set(f"Forged to octagon: ~{target_bar_size:.1f}mm × {final_length:.1f}mm")
        logger.info(f"Display updated. Showing completion dialog.")
        
        messagebox.showinfo("Forging Complete",
                           f"Billet forged to octagonal bar:\n"
                           f"Cross-section: ~{target_bar_size:.1f} mm across flats\n"
                           f"Length: {final_length:.1f} mm ({final_length/original_length:.1f}x extension)\n"
                           f"Heats: {num_heats}\n"
                           f"Volume conserved: {volume_ratio:.3f}\n\n"
                           "You can now apply twist operations!")
    
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
        if self.billet is None:
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
    # EXPORT FUNCTIONS
    # ========================================================================
    
    def export_3d_model(self, format_type):
        """Export the billet as a 3D model file."""
        if self.billet is None:
            logger.warning("Export 3D model attempted with no billet")
            messagebox.showwarning("No Billet", "Please create a billet first")
            return
        
        logger.debug(f"Opening file dialog for {format_type} export")
        filename = filedialog.asksaveasfilename(
            title=f"Save 3D Model (.{format_type})",
            defaultextension=f".{format_type}",
            filetypes=[(f"{format_type.upper()} files", f"*.{format_type}"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                logger.info(f"Exporting 3D model ({format_type}) to: {filename}")
                logger.debug(f"  Billet dimensions: {self.billet.width}x{self.billet.length}, {len(self.billet.layers)} layers")
                self.status_text.set(f"Exporting {format_type.upper()} model...")
                self.root.update()
                
                self.billet.export_3d_model(filename, merge_layers=True)
                
                logger.info(f"3D model export successful: {filename}")
                self.status_text.set(f"Export complete: {format_type.upper()}")
                messagebox.showinfo("Success", f"3D model saved to:\n{filename}")
            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to export: {e}")
                self.status_text.set("Export failed")
        else:
            logger.debug("Export cancelled by user")
    
    def export_cross_section(self):
        """Export the current cross-section as PNG."""
        if self.billet is None:
            logger.warning("Export cross-section attempted with no billet")
            messagebox.showwarning("No Billet", "Please create a billet first")
            return
        
        logger.debug(f"Opening file dialog for cross-section export (Z={self.z_position.get():.1f}mm)")
        filename = filedialog.asksaveasfilename(
            title="Save Cross-Section Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                z_pos = self.z_position.get()
                logger.info(f"Exporting cross-section at Z={z_pos:.1f}mm to: {filename}")
                self.status_text.set(f"Exporting cross-section...")
                self.root.update()
                
                self.billet.save_cross_section_image(
                    z_slice=z_pos,
                    output_path=filename,
                    resolution=1600
                )
                
                logger.info(f"Cross-section export successful: {filename}")
                self.status_text.set(f"Export complete: PNG")
                messagebox.showinfo("Success", f"Cross-section saved to:\n{filename}")
            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to export: {e}")
                self.status_text.set("Export failed")
        else:
            logger.debug("Export cancelled by user")
    
    def export_operation_log(self):
        """Export the operation history as JSON."""
        if self.billet is None:
            logger.warning("Export operation log attempted with no billet")
            messagebox.showwarning("No Billet", "Please create a billet first")
            return
        
        logger.debug(f"Opening file dialog for operation log export ({len(self.billet.operation_history)} operations)")
        filename = filedialog.asksaveasfilename(
            title="Save Operation Log",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                logger.info(f"Exporting operation log to: {filename}")
                logger.debug(f"  Operations: {len(self.billet.operation_history)}")
                self.status_text.set("Exporting operation log...")
                self.root.update()
                
                self.billet.save_operation_log(filename)
                
                logger.info(f"Operation log export successful: {filename}")
                self.status_text.set("Export complete: JSON")
                messagebox.showinfo("Success", f"Operation log saved to:\n{filename}")
            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to export: {e}")
                self.status_text.set("Export failed")
        else:
            logger.debug("Export cancelled by user")
    
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
    
    def show_debug_console(self):
        """Show debug console window with recent log entries."""
        logger.info("Opening debug console window")
        console = tk.Toplevel(self.root)
        console.title("Debug Console")
        console.geometry("900x700")
        
        text_area = scrolledtext.ScrolledText(console, wrap=tk.WORD, 
                                              bg='#1e1e1e', fg='#00ff00',
                                              font=('Courier', 9))
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load recent log file
        import glob
        log_files = sorted(glob.glob('damascus_3d_debug_*.log'), reverse=True)
        logger.debug(f"Found {len(log_files)} debug log files")
        
        if log_files:
            logger.debug(f"Loading most recent log: {log_files[0]}")
            with open(log_files[0], 'r') as f:
                log_content = f.read()
                text_area.insert(tk.END, log_content)
                logger.debug(f"Loaded {len(log_content)} characters from log")
            text_area.see(tk.END)
        else:
            logger.warning("No debug log files found")
            text_area.insert(tk.END, "No debug log available yet.\n")
        
        text_area.config(state=tk.DISABLED)
    
    def show_billet_stats(self):
        """Show detailed billet statistics."""
        if self.billet is None:
            logger.warning("Show stats attempted with no billet")
            messagebox.showwarning("No Billet", "Please create a billet first")
            return
        
        logger.info("Displaying billet statistics window")
        stats = self.billet.get_billet_stats()
        logger.debug(f"Stats: {stats['layer_count']} layers, {stats['total_vertices']} vertices, {stats['operation_count']} ops")
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Billet Statistics")
        stats_window.geometry("600x500")
        
        text_area = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD,
                                              font=('Courier', 9))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format statistics
        text_area.insert(tk.END, "DAMASCUS BILLET STATISTICS\n")
        text_area.insert(tk.END, "="*60 + "\n\n")
        text_area.insert(tk.END, f"Timestamp: {stats['timestamp']}\n\n")
        text_area.insert(tk.END, f"Dimensions:\n")
        text_area.insert(tk.END, f"  Width: {stats['width_mm']:.1f} mm\n")
        text_area.insert(tk.END, f"  Length: {stats['length_mm']:.1f} mm\n")
        text_area.insert(tk.END, f"  Height: {stats['total_height_mm']:.1f} mm\n\n")
        text_area.insert(tk.END, f"Layers: {stats['layer_count']}\n")
        text_area.insert(tk.END, f"Total Vertices: {stats['total_vertices']}\n")
        text_area.insert(tk.END, f"Total Triangles: {stats['total_triangles']}\n")
        text_area.insert(tk.END, f"Operations Applied: {stats['operation_count']}\n\n")
        
        if self.operation_history:
            text_area.insert(tk.END, "Operation History:\n")
            for i, op in enumerate(self.operation_history, 1):
                text_area.insert(tk.END, f"  {i}. {op}\n")
        
        text_area.config(state=tk.DISABLED)
    
    def show_about(self):
        """Show About dialog."""
        messagebox.showinfo("About", 
            "Damascus 3D Pattern Simulator\n"
            "Version 2.0 (3D Mesh-Based)\n\n"
            "BREAKTHROUGH APPROACH:\n"
            "Uses real 3D mesh layers with physics-based\n"
            "deformation, not 2D pixel manipulation.\n\n"
            "Created by: Damascus Pattern Simulator Team\n"
            "Date: 2026-02-02"
        )
    
    def show_quick_start(self):
        """Show Quick Start Guide."""
        guide = tk.Toplevel(self.root)
        guide.title("Quick Start Guide")
        guide.geometry("700x600")
        
        text_area = scrolledtext.ScrolledText(guide, wrap=tk.WORD, font=('Arial', 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        guide_text = """
DAMASCUS 3D SIMULATOR - QUICK START GUIDE
==========================================

STEP 1: CREATE A BILLET
------------------------
1. Configure layer settings in "Layer Configuration" panel
   - Number of Layers: 20-40 recommended
   - Layer Thickness: 0.5-1.5mm typical
   - Billet Dimensions: Width/Length as desired

2. Click "Create New Billet"
   - This creates the starting layered billet
   - View appears in 3D viewport
   
STEP 2: SELECT A PATTERN
-------------------------
Click one of the pattern buttons:

🪶 FEATHER DAMASCUS (Wedge Split)
  - Creates waterfall pattern with central vein
  - Parameters: Wedge Depth, Angle, Split Gap
  - Best with: 25-35 layers

🔄 TWIST/LADDER DAMASCUS
  - Creates ladder/spiral pattern
  - Parameters: Twist Angle, Compression
  - Best with: 20-30 layers

💧 RAINDROP DAMASCUS (Drilling)
  - Creates organic raindrop/eye patterns
  - Parameters: Hole Radius, Spacing, Grid Size
  - Best with: 20-30 layers

STEP 3: ADJUST PARAMETERS
--------------------------
Use the sliders in "Pattern Parameters" panel to adjust:
  - Drag sliders to change values
  - See current value on right side
  - Experiment to find your preferred look

STEP 4: APPLY OPERATION
------------------------
Click "▶ Apply Operation" button
  - 3D view updates to show deformed billet
  - Cross-section shows the resulting pattern
  - Can apply multiple operations in sequence

STEP 5: VIEW CROSS-SECTION
---------------------------
Use the Z Position slider to:
  - Slice through billet at different depths
  - See how pattern changes along length
  - Find the best view for export

STEP 6: EXPORT YOUR WORK
-------------------------
Use Export buttons to save:
  💾 3D Model - For 3D printing or CAD software
  🖼️ Cross-Section - High-res PNG of the pattern
  📋 Operation Log - JSON file to reproduce exact results

TIPS:
-----
- Start with default values and adjust incrementally
- View → Show Billet Statistics for detailed info
- View → Show Debug Console for troubleshooting
- Operations are additive - try combining patterns!
- Reset Billet to start over
        """
        
        text_area.insert(tk.END, guide_text)
        text_area.config(state=tk.DISABLED)
    
    # ========================================================================
    # REFERENCE VIEWERS
    # ========================================================================
    
    def show_heat_treatment_guide(self):
        """
        Show comprehensive hardening & tempering guide for all steels.
        Displays data from Hardening-tempering.txt in a tabbed, searchable interface.
        """
        logger.info("Opening Hardening & Tempering Guide")
        
        # Create window
        guide_window = tk.Toplevel(self.root)
        guide_window.title("📚 Hardening & Tempering Guide - Damascus Steels")
        guide_window.geometry("1000x800")
        guide_window.transient(self.root)
        
        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(guide_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Get steel data from database
        db = get_database()
        steels = db.get_all_steels()
        logger.debug(f"Loaded {len(steels)} steels from database")
        
        # Create tab for each steel
        for steel_key, steel in steels.items():
            tab_frame = ttk.Frame(notebook)
            notebook.add(tab_frame, text=steel.name)
            
            # Create scrolled text widget
            text_widget = scrolledtext.ScrolledText(
                tab_frame,
                wrap=tk.WORD,
                font=('Consolas', 11),  # Larger, more readable font
                bg='#ffffff',  # Pure white background
                fg='#1a1a1a',  # Dark gray text (better than pure black)
                padx=20,
                pady=15,
                spacing1=3,  # Space before paragraph
                spacing2=2,  # Space between lines
                spacing3=3   # Space after paragraph
            )
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            # Insert steel data with formatting
            text_widget.insert(tk.END, steel.get_display_text())
            text_widget.config(state=tk.DISABLED)
        
        # Add search bar at bottom
        search_frame = ttk.Frame(guide_window)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        def search_text():
            query = search_var.get()
            if not query:
                return
            
            # Get current tab
            current_tab_idx = notebook.index(notebook.select())
            current_tab = notebook.winfo_children()[current_tab_idx]
            text_widget = current_tab.winfo_children()[0]
            
            # Clear previous highlights
            text_widget.tag_remove('highlight', '1.0', tk.END)
            
            # Search and highlight
            idx = '1.0'
            count = 0
            while True:
                idx = text_widget.search(query, idx, nocase=True, stopindex=tk.END)
                if not idx:
                    break
                end_idx = f"{idx}+{len(query)}c"
                text_widget.tag_add('highlight', idx, end_idx)
                count += 1
                idx = end_idx
            
            # Configure highlight tag
            text_widget.tag_config('highlight', background='yellow', foreground='black')
            
            if count > 0:
                # Scroll to first match
                text_widget.see('1.0')
                first_match = text_widget.search(query, '1.0', nocase=True)
                if first_match:
                    text_widget.see(first_match)
                logger.debug(f"Search: Found {count} matches for '{query}'")
            else:
                logger.debug(f"Search: No matches for '{query}'")
                messagebox.showinfo("Search", f"No matches found for: {query}")
        
        ttk.Button(search_frame, text="Find", command=search_text).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to search
        search_entry.bind('<Return>', lambda e: search_text())
        
        logger.info("Heat treatment guide window opened")
    
    def _parse_heat_treatment_data(self, content):
        """
        Parse Hardening-tempering.txt into structured sections per steel.
        
        Returns:
            dict: {steel_name: formatted_text}
        """
        steels = {}
        
        # Split by numbered sections (1., 2., 3., etc.) OR steel names like "15N20"
        import re
        # Match either numbered sections or 15N20-style headers
        sections = re.split(r'((?:\d+\.\s+)?[A-Z0-9]+\s+[A-Z][A-Za-z\s\-/()]+(?:Steel|STEEL)?)', content)
        
        current_steel = None
        current_content = []
        
        for section in sections:
            if not section.strip():
                continue
            
            # Check if this is a steel header
            # Numbered: "1. O1 OIL-HARDENING TOOL STEEL"
            # OR unnumbered: "15N20 High Nickel Alloy Steel"
            if re.match(r'^(?:\d+\.\s+)?[A-Z0-9]+\s+[A-Z]', section):
                # Save previous steel if exists
                if current_steel:
                    steel_name = re.sub(r'^\d+\.\s+', '', current_steel)
                    steels[steel_name] = current_steel + "\n" + ''.join(current_content)
                
                # Start new steel
                current_steel = section.strip()
                current_content = []
            else:
                # This is content for current steel
                if current_steel:
                    current_content.append(section)
        
        # Save last steel
        if current_steel:
            steel_name = re.sub(r'^\d+\.\s+', '', current_steel)
            steels[steel_name] = current_steel + "\n" + ''.join(current_content)
        
        return steels
    
    def show_steel_properties(self):
        """Show steel properties database with option to add custom steels."""
        logger.info("Opening Steel Properties Database")
        
        # Create window
        db_window = tk.Toplevel(self.root)
        db_window.title("🔬 Steel Properties Database")
        db_window.geometry("900x700")
        db_window.transient(self.root)
        
        # Button frame at top
        button_frame = ttk.Frame(db_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="➕ Add Custom Steel", 
                  command=self.show_add_custom_steel_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Refresh Database", 
                  command=lambda: self._refresh_steel_list(steel_listbox, db)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📧 Submit New Steel", 
                  command=lambda: self._submit_steel_via_email(steel_listbox, db)).pack(side=tk.LEFT, padx=5)
        
        # Create listbox frame
        list_frame = ttk.LabelFrame(db_window, text="Available Steels", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Listbox with scrollbar
        list_scroll = ttk.Scrollbar(list_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        steel_listbox = tk.Listbox(
            list_frame,
            font=('Arial', 10),
            bg='#ffffff',
            fg='#000000',
            yscrollcommand=list_scroll.set,
            height=20
        )
        steel_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=steel_listbox.yview)
        
        # Load steels
        db = get_database()
        self._refresh_steel_list(steel_listbox, db)
        
        # Info label
        info_label = ttk.Label(
            db_window,
            text=f"Built-in: {len([s for s in db.get_all_steels().values() if not s.is_custom])} | "
                 f"Custom: {len([s for s in db.get_all_steels().values() if s.is_custom])} | "
                 f"Total: {len(db.get_all_steels())}",
            font=('Arial', 9, 'italic')
        )
        info_label.pack(pady=(0, 10))
        
        logger.info("Steel properties database window opened")
    
    def _refresh_steel_list(self, listbox, db):
        """Refresh the steel listbox."""
        listbox.delete(0, tk.END)
        
        # Group by built-in and custom
        builtin = [(k, s) for k, s in db.get_all_steels().items() if not s.is_custom]
        custom = [(k, s) for k, s in db.get_all_steels().items() if s.is_custom]
        
        # Add built-in steels
        if builtin:
            listbox.insert(tk.END, "═══ BUILT-IN STEELS ═══")
            for key, steel in sorted(builtin, key=lambda x: x[1].name):
                listbox.insert(tk.END, f"  {steel.name} ({steel.category})")
        
        # Add custom steels
        if custom:
            listbox.insert(tk.END, "")
            listbox.insert(tk.END, "═══ CUSTOM STEELS ═══")
            for key, steel in sorted(custom, key=lambda x: x[1].name):
                listbox.insert(tk.END, f"  ⭐ {steel.name} ({steel.category})")
    
    def _submit_steel_via_email(self, listbox, db):
        """Export selected custom steel to zip file for email submission."""
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a custom steel to submit")
            return
        
        # Get selected steel name
        selected_text = listbox.get(selection[0])
        if "⭐" not in selected_text:
            messagebox.showinfo("Built-in Steel", "Only custom steels can be submitted")
            return
        
        # Find the steel
        for key, steel in db.get_all_steels().items():
            if steel.is_custom and steel.name in selected_text:
                try:
                    # Ask user where to save the zip file
                    # Create safe filename from steel name
                    safe_name = "".join(c for c in steel.name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_name = safe_name.replace(' ', '_')
                    default_filename = f"steel_submission_{safe_name}.zip"
                    
                    filepath = filedialog.asksavedirectory(
                        title="Choose where to save steel submission",
                        initialdir=os.path.expanduser("~")
                    )
                    
                    if not filepath:
                        return  # User cancelled
                    
                    zip_path = os.path.join(filepath, default_filename)
                    
                    # Create JSON file with steel data
                    steel_dict = steel.to_dict()
                    
                    # Create zip file
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        # Add JSON data
                        json_data = json.dumps(steel_dict, indent=2)
                        zipf.writestr(f"{safe_name}.json", json_data)
                        
                        # Add markdown documentation
                        markdown = db.export_steel_for_github(steel)
                        zipf.writestr(f"{safe_name}_README.md", markdown)
                    
                    # Show success message with email instructions
                    messagebox.showinfo(
                        "Steel Submission Ready",
                        f"Steel data exported to:\n{zip_path}\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "TO SUBMIT YOUR STEEL:\n\n"
                        "1. Email the zip file to:\n"
                        "   devsupport@grayworkscrafts.com\n\n"
                        "2. Use subject line:\n"
                        "   New Steel: " + steel.name + "\n\n"
                        "3. Attach the zip file\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "We'll review your submission and potentially\n"
                        "add it to the built-in steel database!\n\n"
                        "Thank you for contributing!"
                    )
                    
                    logger.info(f"Exported steel '{steel.name}' to {zip_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to export steel: {e}")
                    messagebox.showerror(
                        "Export Error",
                        f"Failed to create steel submission file:\n{str(e)}"
                    )
                break
    
    def show_add_custom_steel_dialog(self):
        """Show dialog for adding a custom steel to the database."""
        logger.info("Opening Add Custom Steel dialog")
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Add Custom Steel")
        dialog.geometry("700x850")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create scrollable canvas
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Entry storage
        entries = {}
        
        # Helper function to create labeled entry
        def create_entry(parent, label_text, row, tooltip="", width=40):
            ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, padx=5, pady=3)
            entry = ttk.Entry(parent, width=width)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
            if tooltip:
                # Simple tooltip via label below
                ttk.Label(parent, text=f"  ℹ️ {tooltip}", font=('Arial', 8, 'italic'), 
                         foreground='#666666').grid(row=row+1, column=1, sticky=tk.W, padx=5)
                return entry, 2  # Return entry and row increment
            return entry, 1
        
        # === BASIC INFO SECTION ===
        row = 0
        basic_frame = ttk.LabelFrame(scrollable_frame, text="Basic Information", padding=10)
        basic_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
        basic_frame.columnconfigure(1, weight=1)
        
        entries['name'], inc = create_entry(basic_frame, "Steel Name *:", 0, "e.g., '1095 High Carbon Steel'")
        row_offset = inc
        
        ttk.Label(basic_frame, text="Category *:").grid(row=row_offset, column=0, sticky=tk.W, padx=5, pady=3)
        entries['category'] = ttk.Combobox(basic_frame, width=37, 
            values=["High Carbon", "Low Alloy", "Tool Steel", "Stainless", "Damascus", "Other"])
        entries['category'].grid(row=row_offset, column=1, sticky=tk.EW, padx=5, pady=3)
        entries['category'].set("High Carbon")
        
        # === PHYSICAL PROPERTIES SECTION ===
        row += 1
        phys_frame = ttk.LabelFrame(scrollable_frame, text="Physical Properties", padding=10)
        phys_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
        phys_frame.columnconfigure(1, weight=1)
        
        entries['density'], inc = create_entry(phys_frame, "Density (lb/in³):", 0, "Typical: 0.280-0.290")
        row_offset = inc
        entries['thermal_exp'], inc = create_entry(phys_frame, "Thermal Expansion (µin/in/°F):", row_offset, "Typical: 6.0-8.0")
        row_offset += inc
        entries['thermal_cond'], inc = create_entry(phys_frame, "Thermal Conductivity (BTU/hr/ft/°F):", row_offset, "Typical: 25-35")
        row_offset += inc
        entries['modulus'], inc = create_entry(phys_frame, "Modulus of Elasticity (10⁶ psi):", row_offset, "Typical: 28-32")
        
        # === HEAT TREATMENT SECTION ===
        row += 1
        ht_frame = ttk.LabelFrame(scrollable_frame, text="Heat Treatment", padding=10)
        ht_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
        ht_frame.columnconfigure(1, weight=1)
        
        entries['aust_min'], inc = create_entry(ht_frame, "Austenitizing Min (°F):", 0, "Lower temp of austenizing range")
        row_offset = inc
        entries['aust_max'], inc = create_entry(ht_frame, "Austenitizing Max (°F):", row_offset, "Upper temp of austenizing range")
        row_offset += inc
        entries['quench'], inc = create_entry(ht_frame, "Quench Method:", row_offset, "e.g., 'Oil', 'Water', 'Air', 'Plate'")
        row_offset += inc
        
        ttk.Label(ht_frame, text="Tempering Data:", font=('Arial', 9, 'bold')).grid(
            row=row_offset, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 3))
        row_offset += 1
        ttk.Label(ht_frame, text="  Format: temp1,hardness1; temp2,hardness2; temp3,hardness3").grid(
            row=row_offset, column=0, columnspan=2, sticky=tk.W, padx=5, pady=3)
        row_offset += 1
        ttk.Label(ht_frame, text="  Example: 350,61.5; 400,59.5; 450,57.5", 
                 font=('Arial', 8, 'italic'), foreground='#666666').grid(
            row=row_offset, column=0, columnspan=2, sticky=tk.W, padx=5, pady=3)
        row_offset += 1
        entries['tempering'] = ttk.Entry(ht_frame, width=40)
        entries['tempering'].grid(row=row_offset, column=1, sticky=tk.EW, padx=5, pady=3)
        
        # === FORGING CHARACTERISTICS SECTION ===
        row += 1
        forge_frame = ttk.LabelFrame(scrollable_frame, text="Forging Characteristics", padding=10)
        forge_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
        forge_frame.columnconfigure(1, weight=1)
        
        entries['forge_min'], inc = create_entry(forge_frame, "Forging Range Min (°F):", 0, "Lower safe forging temp")
        row_offset = inc
        entries['forge_max'], inc = create_entry(forge_frame, "Forging Range Max (°F):", row_offset, "Upper safe forging temp")
        row_offset += inc
        
        ttk.Label(forge_frame, text="Movement Level (1-10):").grid(row=row_offset, column=0, sticky=tk.W, padx=5, pady=3)
        entries['movement'] = ttk.Spinbox(forge_frame, from_=1, to=10, width=38)
        entries['movement'].set(5)
        entries['movement'].grid(row=row_offset, column=1, sticky=tk.EW, padx=5, pady=3)
        row_offset += 1
        ttk.Label(forge_frame, text="  ℹ️ 1=very easy to move, 10=very stiff", 
                 font=('Arial', 8, 'italic'), foreground='#666666').grid(
            row=row_offset, column=1, sticky=tk.W, padx=5)
        row_offset += 1
        
        entries['scale_min'], inc = create_entry(forge_frame, "Scale Loss Min (%):", row_offset, "Lower bound of scale loss range")
        row_offset += inc
        entries['scale_max'], inc = create_entry(forge_frame, "Scale Loss Max (%):", row_offset, "Upper bound of scale loss range")
        row_offset += inc
        entries['decarb_min'], inc = create_entry(forge_frame, "Decarb Depth Min (in):", row_offset, "Lower bound of decarb depth")
        row_offset += inc
        entries['decarb_max'], inc = create_entry(forge_frame, "Decarb Depth Max (in):", row_offset, "Upper bound of decarb depth")
        
        # === ETCHING SECTION ===
        row += 1
        etch_frame = ttk.LabelFrame(scrollable_frame, text="Etching & Appearance", padding=10)
        etch_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
        etch_frame.columnconfigure(1, weight=1)
        
        ttk.Label(etch_frame, text="Etch Color:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        entries['etch_color'] = ttk.Combobox(etch_frame, width=37, values=["dark", "light", "gray", "mixed"])
        entries['etch_color'].grid(row=0, column=1, sticky=tk.EW, padx=5, pady=3)
        entries['etch_color'].set("dark")
        
        # === NOTES SECTION ===
        row += 1
        notes_frame = ttk.LabelFrame(scrollable_frame, text="Additional Notes (Optional)", padding=10)
        notes_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
        notes_frame.columnconfigure(0, weight=1)
        
        entries['notes'] = tk.Text(notes_frame, height=4, width=60, wrap=tk.WORD, font=('Arial', 9))
        entries['notes'].grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(notes_frame, text="  e.g., normalizing procedures, special handling, composition details", 
                 font=('Arial', 8, 'italic'), foreground='#666666').grid(
            row=1, column=0, sticky=tk.W, padx=5)
        
        # === BUTTON FRAME ===
        row += 1
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=20)
        
        def save_custom_steel():
            """Validate and save the custom steel."""
            # Get required fields
            name = entries['name'].get().strip()
            category = entries['category'].get().strip()
            
            if not name:
                messagebox.showerror("Missing Info", "Steel name is required")
                return
            if not category:
                messagebox.showerror("Missing Info", "Category is required")
                return
            
            # Parse tempering data
            tempering_data = []
            tempering_str = entries['tempering'].get().strip()
            if tempering_str:
                try:
                    pairs = [p.strip() for p in tempering_str.split(';')]
                    for pair in pairs:
                        temp, hardness = pair.split(',')
                        tempering_data.append((float(temp.strip()), float(hardness.strip())))
                except:
                    messagebox.showerror("Parse Error", 
                        "Tempering data format invalid.\nUse: temp1,hardness1; temp2,hardness2")
                    return
            
            # Helper to get float or None
            def get_float(key):
                val = entries[key].get().strip()
                return float(val) if val else None
            
            # Create Steel object
            try:
                from steel_database import Steel
                
                # Build steel data dictionary
                steel_data = {
                    'name': name,
                    'category': category,
                    'is_custom': True,
                    'created_by': 'User'
                }
                
                # Add optional properties (only if provided)
                if get_float('density'):
                    steel_data['density'] = get_float('density')
                if get_float('thermal_exp'):
                    steel_data['thermal_expansion'] = get_float('thermal_exp')
                if get_float('thermal_cond'):
                    steel_data['thermal_conductivity'] = get_float('thermal_cond')
                if get_float('modulus'):
                    steel_data['modulus_elasticity'] = get_float('modulus')
                    
                if get_float('aust_min'):
                    steel_data['austenitizing_temp'] = (get_float('aust_min'), get_float('aust_max') or get_float('aust_min'))
                
                quench = entries['quench'].get().strip()
                if quench:
                    steel_data['quench_method'] = quench
                    
                if tempering_data:
                    steel_data['tempering_data'] = tempering_data
                    
                if get_float('forge_min'):
                    steel_data['forging_range'] = (get_float('forge_min'), get_float('forge_max') or get_float('forge_min'))
                    
                movement = entries['movement'].get()
                if movement:
                    steel_data['movement_level'] = int(movement)
                    
                if get_float('scale_min'):
                    steel_data['scale_loss'] = (get_float('scale_min'), get_float('scale_max') or get_float('scale_min'))
                if get_float('decarb_min'):
                    steel_data['decarb_depth'] = (get_float('decarb_min'), get_float('decarb_max') or get_float('decarb_min'))
                    
                etch = entries['etch_color'].get()
                if etch:
                    steel_data['etch_color'] = etch
                    
                notes = entries['notes'].get('1.0', tk.END).strip()
                if notes:
                    steel_data['notes'] = notes
                
                # Add to database
                db = get_database()
                # Generate a unique key from the name (lowercase, no spaces)
                key = name.lower().replace(' ', '_').replace('-', '_')
                # Make sure key is unique
                counter = 1
                original_key = key
                while key in db.get_all_steels():
                    key = f"{original_key}_{counter}"
                    counter += 1
                
                steel = db.add_custom_steel(key, steel_data)
                
                messagebox.showinfo("Success", f"Custom steel '{name}' has been added to the database!")
                logger.info(f"Added custom steel: {name} with key: {key}")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save steel:\n{str(e)}")
                logger.error(f"Error saving custom steel: {e}")
        
        ttk.Button(button_frame, text="✅ Save Steel", command=save_custom_steel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        logger.info("Add Custom Steel dialog created")
    
    def show_forging_losses(self):
        """
        Show forging losses reference from steel-losses-during-forging.txt.
        """
        logger.info("Opening Forging Losses Reference")
        
        try:
            with open('steel-losses-during-forging.txt', 'r') as f:
                content = f.read()
        except FileNotFoundError:
            messagebox.showerror("File Not Found", 
                "steel-losses-during-forging.txt not found")
            return
        
        # Create window
        ref_window = tk.Toplevel(self.root)
        ref_window.title("📖 Forging Losses Reference")
        ref_window.geometry("900x700")
        
        text_area = scrolledtext.ScrolledText(
            ref_window,
            wrap=tk.WORD,
            font=('Courier', 10),
            bg='#f5f5f5',
            padx=10,
            pady=10
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_area.insert(tk.END, content)
        text_area.config(state=tk.DISABLED)
        
        logger.info("Forging losses reference displayed")
    
    def show_plasticity_guide(self):
        """
        Show steel plasticity guide from steel-plasticity.txt.
        """
        logger.info("Opening Steel Plasticity Guide")
        
        try:
            with open('steel-plasticity.txt', 'r') as f:
                content = f.read()
        except FileNotFoundError:
            messagebox.showerror("File Not Found", 
                "steel-plasticity.txt not found")
            return
        
        # Create window
        ref_window = tk.Toplevel(self.root)
        ref_window.title("⚒️ Steel Plasticity Guide")
        ref_window.geometry("900x700")
        
        text_area = scrolledtext.ScrolledText(
            ref_window,
            wrap=tk.WORD,
            font=('Courier', 10),
            bg='#f5f5f5',
            padx=10,
            pady=10
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_area.insert(tk.END, content)
        text_area.config(state=tk.DISABLED)
        
        logger.info("Steel plasticity guide displayed")
    
    # ========================================================================
    # MAIN EVENT LOOP
    # ========================================================================
    
    def run(self):
        """Start the GUI application."""
        logger.info("Starting GUI main loop")
        self.root.mainloop()
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
