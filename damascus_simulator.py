#!/usr/bin/env python3
"""
Damascus Steel Pattern Simulator - Linux Version
A tool for simulating twisted Damascus steel patterns
Inspired by Thor II by Christian Schnura
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import math
import os

class DamascusSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Damascus Pattern Simulator")
        self.root.geometry("1400x900")
        
        # Modern color scheme
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#e0e0e0',
            'canvas_bg': '#2d2d2d',
            'accent': '#0d7377',
            'accent_hover': '#14a098',
            'panel_bg': '#252525',
            'border': '#404040'
        }
        
        # Configure modern style
        self.setup_style()
        
        # Image variables
        self.original_image = None
        self.display_image = None
        self.pattern_array = None
        self.canvas_width = 900
        self.canvas_height = 700
        
        # Pattern parameters
        self.twist_amount = tk.DoubleVar(value=0.0)
        self.grind_depth = tk.DoubleVar(value=0.0)
        self.grind_angle = tk.DoubleVar(value=0.0)  # Grind bevel angle in degrees
        self.rotation_angle = tk.IntVar(value=0)  # Pattern rotation (0, 90, 180, 270)
        self.mosaic_size = tk.IntVar(value=1)
        self.white_layer_thickness = tk.DoubleVar(value=1.0)  # in mm
        self.black_layer_thickness = tk.DoubleVar(value=1.0)  # in mm
        self.unit_system = tk.StringVar(value="metric")  # metric or imperial
        self.pixels_per_mm = 10  # Scale factor for visualization
        self.current_pattern_type = None  # Track which pattern is active
        self.custom_layer_stack = None  # Store custom layer stack for W/C patterns
        
        # Debug mode
        self.debug_mode = tk.BooleanVar(value=False)
        self.debug_log = []
        
        # Default save directory
        self.default_save_dir = os.path.expanduser('~/Documents/DPS')
        self.ensure_save_directory()
        
        self.setup_ui()
        self.load_default_pattern()
    
    def ensure_save_directory(self):
        """Ensure the default save directory exists"""
        try:
            os.makedirs(self.default_save_dir, exist_ok=True)
        except Exception as e:
            print(f"[WARNING] Could not create default save directory: {e}")
    
    def debug_print(self, message):
        """Print debug message and log it if debug mode is enabled"""
        if self.debug_mode.get():
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            print(log_entry.strip())
            self.debug_log.append(log_entry)
            
            # Save to file
            debug_file = os.path.join(self.default_save_dir, 'debug.log')
            try:
                with open(debug_file, 'a') as f:
                    f.write(log_entry)
            except Exception as e:
                print(f"[WARNING] Could not write to debug log: {e}")
            
            # Keep only last 100 entries in memory
            if len(self.debug_log) > 100:
                self.debug_log = self.debug_log[-100:]
    
    def setup_style(self):
        """Configure modern ttk style"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'], font=('Segoe UI', 9))
        style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['fg'], 
                       bordercolor=self.colors['border'], relief='flat')
        style.configure('TLabelframe.Label', background=self.colors['bg'], foreground=self.colors['accent'],
                       font=('Segoe UI', 9, 'bold'))
        
        # Modern buttons with rounded edges and shadow effect
        style.configure('TButton', 
                       background=self.colors['accent'], 
                       foreground='white',
                       borderwidth=1,
                       relief='raised',
                       bordercolor='#0a5a5d',
                       lightcolor='#14a098',
                       darkcolor='#084f52',
                       focuscolor='none', 
                       font=('Segoe UI', 9, 'bold'),
                       padding=(10, 6))
        style.map('TButton', 
                 background=[('active', self.colors['accent_hover']), ('pressed', '#0a5a5d')],
                 relief=[('pressed', 'sunken')])
        
        style.configure('TRadiobutton', background=self.colors['bg'], foreground=self.colors['fg'],
                       font=('Segoe UI', 9))
        style.configure('TCheckbutton', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TScale', background=self.colors['bg'])
        style.configure('TSpinbox', background=self.colors['panel_bg'], foreground=self.colors['fg'],
                       fieldbackground=self.colors['panel_bg'], borderwidth=1)
        
        self.root.configure(bg=self.colors['bg'])
        
    def setup_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top menu bar with split layout
        menubar = ttk.Frame(main_frame)
        menubar.pack(fill=tk.X, padx=15, pady=(10, 0))
        
        # Left side menu items
        left_menu = ttk.Frame(menubar)
        left_menu.pack(side=tk.LEFT, fill=tk.X)
        
        ttk.Button(left_menu, text="Load Pattern", command=self.load_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Load Default", command=self.load_default_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Save as Layer", command=self.save_pattern_as_layer).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Export", command=self.save_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Print", command=self.print_pattern).pack(side=tk.LEFT, padx=2)
        
        # Right side menu items
        right_menu = ttk.Frame(menubar)
        right_menu.pack(side=tk.RIGHT, fill=tk.X)
        
        ttk.Checkbutton(right_menu, text="Debug", variable=self.debug_mode).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Report Issue", command=self.report_issue).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Reset Options", command=self.reset_options_only).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Reset All", command=self.reset_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Check for Updates", command=self.check_for_updates).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="About", command=self.show_about).pack(side=tk.LEFT, padx=2)
        
        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Left panel - Canvas
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Canvas for image display with modern styling
        canvas_container = ttk.Frame(left_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_container, width=self.canvas_width, height=self.canvas_height, 
                               bg=self.colors['canvas_bg'], highlightthickness=2, 
                               highlightbackground=self.colors['border'])
        self.canvas.pack(padx=5, pady=5)
        
        # Right panel - Controls with scrollbar
        right_frame = ttk.Frame(content_frame, width=420)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_frame.pack_propagate(False)
        
        # Create canvas and scrollbar for right panel
        canvas = tk.Canvas(right_frame, width=405, bg=self.colors['bg'], 
                          highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Use scrollable_frame instead of right_frame for all controls
        right_frame = scrollable_frame
        
        # Transformations section
        transform_frame = ttk.LabelFrame(right_frame, text="Transformations", padding=15)
        transform_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Twist amount
        ttk.Label(transform_frame, text="Twist Amount:").pack(anchor=tk.W, pady=(0,3))
        twist_frame = ttk.Frame(transform_frame)
        twist_frame.pack(fill=tk.X, pady=(0, 12))
        twist_scale = ttk.Scale(twist_frame, from_=0, to=10, 
                               variable=self.twist_amount, 
                               command=self.update_pattern)
        twist_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        twist_spinbox = ttk.Spinbox(twist_frame, from_=0, to=10, increment=0.1,
                                   textvariable=self.twist_amount, width=8,
                                   command=self.update_pattern)
        twist_spinbox.pack(side=tk.LEFT, padx=(8,0))
        twist_spinbox.bind('<Return>', lambda e: self.update_pattern())
        twist_spinbox.bind('<FocusOut>', lambda e: self.update_pattern())
        
        # Grind depth
        ttk.Label(transform_frame, text="Grind Depth (%):").pack(anchor=tk.W, pady=(0,3))
        grind_frame = ttk.Frame(transform_frame)
        grind_frame.pack(fill=tk.X, pady=(0, 12))
        grind_scale = ttk.Scale(grind_frame, from_=0, to=100, 
                               variable=self.grind_depth, 
                               command=self.update_pattern)
        grind_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        grind_spinbox = ttk.Spinbox(grind_frame, from_=0, to=100, increment=1,
                                   textvariable=self.grind_depth, width=8,
                                   command=self.update_pattern)
        grind_spinbox.pack(side=tk.LEFT, padx=(8,0))
        grind_spinbox.bind('<Return>', lambda e: self.update_pattern())
        grind_spinbox.bind('<FocusOut>', lambda e: self.update_pattern())
        
        # Grind angle
        ttk.Label(transform_frame, text="Grind Angle (degrees):").pack(anchor=tk.W, pady=(0,3))
        angle_frame = ttk.Frame(transform_frame)
        angle_frame.pack(fill=tk.X, pady=(0, 0))
        angle_scale = ttk.Scale(angle_frame, from_=0, to=45, 
                               variable=self.grind_angle, 
                               command=self.update_pattern)
        angle_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        angle_spinbox = ttk.Spinbox(angle_frame, from_=0, to=45, increment=1,
                                   textvariable=self.grind_angle, width=8,
                                   command=self.update_pattern)
        angle_spinbox.pack(side=tk.LEFT, padx=(8,0))
        angle_spinbox.bind('<Return>', lambda e: self.update_pattern())
        angle_spinbox.bind('<FocusOut>', lambda e: self.update_pattern())
        
        # Layer thickness controls
        layer_frame = ttk.LabelFrame(right_frame, text="Layer Thickness", padding=15)
        layer_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Unit selection
        unit_frame = ttk.Frame(layer_frame)
        unit_frame.pack(fill=tk.X, pady=(0,12))
        ttk.Label(unit_frame, text="Units:").pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(unit_frame, text="mm", variable=self.unit_system, 
                       value="metric", command=self.update_unit_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(unit_frame, text="inches", variable=self.unit_system, 
                       value="imperial", command=self.update_unit_display).pack(side=tk.LEFT, padx=5)
        
        # White layer thickness
        self.white_label = ttk.Label(layer_frame, text="White Layer (mm):")
        self.white_label.pack(anchor=tk.W, pady=(0,3))
        white_frame = ttk.Frame(layer_frame)
        white_frame.pack(fill=tk.X, pady=(0, 12))
        white_scale = ttk.Scale(white_frame, from_=0.1, to=5.0, 
                               variable=self.white_layer_thickness, 
                               command=self.on_layer_change)
        white_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        white_spinbox = ttk.Spinbox(white_frame, from_=0.1, to=5.0, increment=0.1,
                                   textvariable=self.white_layer_thickness, width=8,
                                   command=self.on_layer_change)
        white_spinbox.pack(side=tk.LEFT, padx=(8,0))
        white_spinbox.bind('<Return>', lambda e: self.on_layer_change())
        white_spinbox.bind('<FocusOut>', lambda e: self.on_layer_change())
        
        # Black layer thickness
        self.black_label = ttk.Label(layer_frame, text="Black Layer (mm):")
        self.black_label.pack(anchor=tk.W, pady=(0,3))
        black_frame = ttk.Frame(layer_frame)
        black_frame.pack(fill=tk.X, pady=(0, 0))
        black_scale = ttk.Scale(black_frame, from_=0.1, to=5.0, 
                               variable=self.black_layer_thickness, 
                               command=self.on_layer_change)
        black_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        black_spinbox = ttk.Spinbox(black_frame, from_=0.1, to=5.0, increment=0.1,
                                   textvariable=self.black_layer_thickness, width=8,
                                   command=self.on_layer_change)
        black_spinbox.pack(side=tk.LEFT, padx=(8,0))
        black_spinbox.bind('<Return>', lambda e: self.on_layer_change())
        black_spinbox.bind('<FocusOut>', lambda e: self.on_layer_change())
        
        # Two column layout for rotation and mosaic
        layout_frame = ttk.Frame(right_frame)
        layout_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Left column - Rotation
        rotation_frame = ttk.LabelFrame(layout_frame, text="Rotation", padding=15)
        rotation_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        
        for angle in [0, 90, 180, 270]:
            ttk.Radiobutton(rotation_frame, text=f"{angle}°", 
                          variable=self.rotation_angle, value=angle,
                          command=self.update_pattern).pack(anchor=tk.W, pady=3)
        
        # Right column - Quick Mosaic
        mosaic_frame = ttk.LabelFrame(layout_frame, text="Quick Mosaic", padding=15)
        mosaic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        
        for i, size in enumerate([1, 2, 3]):
            ttk.Radiobutton(mosaic_frame, text=f"{size}×{size}", 
                          variable=self.mosaic_size, value=size,
                          command=self.update_pattern).pack(anchor=tk.W, pady=3)
        
        # Custom builders section
        builders_frame = ttk.LabelFrame(right_frame, text="Pattern Builders", padding=15)
        builders_frame.pack(fill=tk.X, pady=(0, 8))
        
        builder_buttons = ttk.Frame(builders_frame)
        builder_buttons.pack(fill=tk.X)
        
        ttk.Button(builder_buttons, text="Custom Layers",
                  command=self.open_custom_layer_builder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ttk.Button(builder_buttons, text="Custom Mosaic",
                  command=self.open_mosaic_builder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        
        # Preset patterns
        preset_frame = ttk.LabelFrame(right_frame, text="Preset Patterns", padding=15)
        preset_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Two-column grid for presets
        preset_grid = ttk.Frame(preset_frame)
        preset_grid.pack(fill=tk.X)
        
        presets = [
            ("Simple Layers", self.create_simple_layers),
            ("Random Pattern", self.create_random_pattern),
            ("W Pattern", lambda: self.create_w_pattern(use_custom_stack=False)),
            ("C Pattern", lambda: self.create_c_pattern(use_custom_stack=False)),
        ]
        
        for i, (name, func) in enumerate(presets):
            row = i // 2
            col = i % 2
            padx = (0, 4) if col == 0 else (4, 0)
            ttk.Button(preset_grid, text=name, command=func).grid(
                row=row, column=col, sticky="ew", pady=2, padx=padx)
        
        # Make columns equal width
        preset_grid.columnconfigure(0, weight=1)
        preset_grid.columnconfigure(1, weight=1)
    
    def load_pattern(self):
        """Load a pattern image from file"""
        self.debug_print("load_pattern() called")
        filename = filedialog.askopenfilename(
            title="Select Pattern Image",
            initialdir=self.default_save_dir,
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.debug_print(f"File selected: {filename}")
            try:
                self.debug_print("Opening image file...")
                self.original_image = Image.open(filename).convert('RGB')
                self.debug_print("Converting to array...")
                self.pattern_array = np.array(self.original_image)
                self.debug_print(f"Image loaded: {self.pattern_array.shape}")
                self.update_pattern()
                self.debug_print("Pattern display updated")
            except Exception as e:
                self.debug_print(f"ERROR loading image: {e}")
                messagebox.showerror("Error", f"Failed to load image: {e}")
        else:
            self.debug_print("No file selected (dialog canceled)")
    
    def load_default_pattern(self):
        """Load a default pattern"""
        self.debug_print("load_default_pattern() called")
        self.create_simple_layers()
    
    def mm_to_pixels(self, mm):
        """Convert millimeters to pixels for display"""
        return int(mm * self.pixels_per_mm)
    
    def inches_to_mm(self, inches):
        """Convert inches to millimeters"""
        return inches * 25.4
    
    def mm_to_inches(self, mm):
        """Convert millimeters to inches"""
        return mm / 25.4
    
    def update_unit_display(self):
        """Update the unit labels when unit system changes"""
        if self.unit_system.get() == "metric":
            self.white_label.config(text="White Layer (mm):")
            self.black_label.config(text="Black Layer (mm):")
        else:
            self.white_label.config(text="White Layer (in):")
            self.black_label.config(text="Black Layer (in):")
            # Convert the internal mm values for display
            white_inches = self.mm_to_inches(self.white_layer_thickness.get())
            black_inches = self.mm_to_inches(self.black_layer_thickness.get())
            self.white_layer_thickness.set(white_inches)
            self.black_layer_thickness.set(black_inches)
    
    def on_layer_change(self, *args):
        """Handle layer thickness slider changes"""
        self.update_unit_display()
        # Regenerate current pattern in real-time
        if self.current_pattern_type == 'simple_layers':
            self.create_simple_layers()
        elif self.current_pattern_type == 'w_pattern':
            self.create_w_pattern()
        elif self.current_pattern_type == 'c_pattern':
            self.create_c_pattern()
    
    def get_layer_color_at_position(self, y_position):
        """Get the color at a given y position based on current layer stack"""
        if self.custom_layer_stack:
            # Use custom layer stack
            current_y = 0
            for layer in self.custom_layer_stack:
                layer_thickness = self.mm_to_pixels(layer['thickness'])
                if current_y <= y_position < current_y + layer_thickness:
                    return (200, 200, 200) if layer['color'] == 'white' else (50, 50, 50)
                current_y += layer_thickness
            # Repeat pattern if we exceed the stack height
            total_height = sum(self.mm_to_pixels(l['thickness']) for l in self.custom_layer_stack)
            if total_height > 0:
                adjusted_y = y_position % total_height
                return self.get_layer_color_at_position(adjusted_y)
            return (50, 50, 50)
        else:
            # Use simple alternating layers
            white_thick = max(1, self.mm_to_pixels(self.white_layer_thickness.get()))
            black_thick = max(1, self.mm_to_pixels(self.black_layer_thickness.get()))
            total_thickness = white_thick + black_thick
            layer_num = (int(y_position) // total_thickness) % 2
            pos_in_layer = int(y_position) % total_thickness
            
            if layer_num == 0 and pos_in_layer < white_thick:
                return (200, 200, 200)
            else:
                return (50, 50, 50)
    
    def create_simple_layers(self):
        """Create a simple layered pattern with current thickness settings"""
        size = 400
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)
        
        # Convert mm to pixels
        white_thick = max(1, self.mm_to_pixels(self.white_layer_thickness.get()))
        black_thick = max(1, self.mm_to_pixels(self.black_layer_thickness.get()))
        
        y = 0
        is_white = True
        while y < size:
            if is_white:
                color = (200, 200, 200)
                thickness = white_thick
            else:
                color = (50, 50, 50)
                thickness = black_thick
            
            draw.rectangle([0, y, size, min(y + thickness, size)], fill=color)
            y += thickness
            is_white = not is_white
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'simple_layers'
        self.update_pattern()
    
    def create_checkerboard(self):
        """Create a checkerboard pattern"""
        size = 400
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)
        
        square_size = size // 10
        for i in range(10):
            for j in range(10):
                if (i + j) % 2 == 0:
                    color = (200, 200, 200)
                else:
                    color = (50, 50, 50)
                x = j * square_size
                y = i * square_size
                draw.rectangle([x, y, x + square_size, y + square_size], fill=color)
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'checkerboard'
        self.update_pattern()
    
    def create_random_pattern(self):
        """Create a random pattern"""
        size = 400
        np.random.seed(None)
        
        # Create random stripes
        pattern = np.zeros((size, size, 3), dtype=np.uint8)
        num_stripes = 30
        
        for i in range(num_stripes):
            y_start = np.random.randint(0, size)
            height = np.random.randint(5, 30)
            brightness = np.random.randint(30, 220)
            
            pattern[y_start:min(y_start + height, size), :] = [brightness, brightness, brightness]
        
        self.original_image = Image.fromarray(pattern)
        self.pattern_array = pattern
        self.current_pattern_type = 'random'
        self.update_pattern()
    
    def create_w_pattern(self, use_custom_stack=None):
        """Create a W pattern (chevron/zigzag layers forming W shapes)"""
        # If no custom stack specified, clear it to use default layers
        if use_custom_stack is False:
            self.custom_layer_stack = None
        
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        # Create W pattern - layers form chevron/V shapes
        # The pattern creates alternating peaks and valleys
        wavelength = size // 4  # Width of each V in the W
        amplitude = 60  # Height of the V shapes
        
        for x in range(size):
            for y in range(size):
                # Calculate the position in the W wave pattern
                # Create W shape using absolute sine-like pattern
                wave_pos = x % (wavelength * 2)
                if wave_pos < wavelength:
                    # Upward slope (forming left side of V)
                    offset = int((wave_pos / wavelength) * amplitude)
                else:
                    # Downward slope (forming right side of V)
                    offset = int(((wavelength * 2 - wave_pos) / wavelength) * amplitude)
                
                # Calculate which layer we're in
                adjusted_y = y - offset
                
                # Get color based on current layer stack (custom or simple)
                color = self.get_layer_color_at_position(adjusted_y)
                
                pixels[x, y] = color
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'w_pattern'
        self.update_pattern()
    
    def create_c_pattern(self, use_custom_stack=None):
        """Create a C pattern (curved/arced layers)"""
        # If no custom stack specified, clear it to use default layers
        if use_custom_stack is False:
            self.custom_layer_stack = None
        
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        # Create C pattern - layers that curve in an arc
        # This simulates layers that have been bent into curves
        center_y = size // 2
        curve_strength = 0.3  # How much the layers curve
        
        for x in range(size):
            for y in range(size):
                # Calculate curve - layers bend based on horizontal position
                # Creates a parabolic curve
                distance_from_center = abs(x - size // 2)
                curve_offset = int((distance_from_center ** 2) * curve_strength / size)
                
                # Adjust y position based on curve
                adjusted_y = y + curve_offset
                
                # Get color based on current layer stack (custom or simple)
                color = self.get_layer_color_at_position(adjusted_y)
                
                pixels[x, y] = color
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'c_pattern'
        self.update_pattern()
    
    def open_custom_layer_builder(self):
        """Open dialog to build custom layer stack"""
        CustomLayerDialog(self.root, self)
    
    def open_mosaic_builder(self):
        """Open dialog to build custom mosaic patterns"""
        MosaicBuilderDialog(self.root, self)
    
    def create_custom_layers(self, layer_data):
        """Create pattern from custom layer data"""
        print(f"[DEBUG] Creating custom layers with {len(layer_data)} layers")
        
        # Debug: inspect layer_data
        for i, layer in enumerate(layer_data):
            print(f"[DEBUG] Layer {i}: color={layer['color']}, has pattern_image={'pattern_image' in layer}")
            if 'pattern_image' in layer:
                print(f"[DEBUG]   pattern_image shape: {layer['pattern_image'].shape}")
        
        # First pass: determine required canvas size
        max_width = 400  # Minimum width
        total_height = 0
        
        for layer in layer_data:
            if layer['color'] == 'pattern' and 'pattern_image' in layer:
                pat_height, pat_width = layer['pattern_image'].shape[:2]
                print(f"[DEBUG] Found pattern layer: {pat_height}x{pat_width}")
                max_width = max(max_width, pat_width)
                total_height += pat_height
                print(f"[DEBUG] Updated max_width to {max_width}, total_height to {total_height}")
            else:
                thickness = max(1, self.mm_to_pixels(layer['thickness']))
                total_height += thickness
                print(f"[DEBUG] Added {thickness}px for {layer['color']} layer, total_height now {total_height}")
        
        # Create canvas large enough for all layers
        canvas_width = max_width
        canvas_height = max(400, total_height)
        print(f"[DEBUG] Canvas size: {canvas_width}x{canvas_height}")
        
        img = Image.new('RGB', (canvas_width, canvas_height))
        pixels = img.load()
        
        # Store the custom layer stack
        self.custom_layer_stack = layer_data.copy()
        
        # Save a deep copy for editing later
        import copy
        self.last_custom_layer_stack = copy.deepcopy(layer_data)
        
        # Draw layers from bottom to top
        y = 0
        for layer in layer_data:
            print(f"[DEBUG] Processing layer: color={layer['color']}, thickness={layer.get('thickness', 'N/A')}, y={y}")
            
            if layer['color'] == 'pattern':
                # Use pattern image for this layer
                pattern_img = layer.get('pattern_image')
                if pattern_img is not None:
                    # Get the pattern dimensions
                    pat_height, pat_width = pattern_img.shape[:2]
                    print(f"[DEBUG] Rendering pattern: {pat_height}x{pat_width}")
                    
                    # For pattern layers, use the full pattern size
                    for py in range(pat_height):
                        if y + py >= canvas_height:
                            break
                        
                        for px in range(canvas_width):
                            # Tile horizontally if needed
                            src_x = px % pat_width
                            pixels[px, y + py] = tuple(pattern_img[py, src_x])
                    
                    # Update y position
                    y += pat_height
            else:
                # Regular color layer
                thickness = max(1, self.mm_to_pixels(layer['thickness']))
                color = (200, 200, 200) if layer['color'] == 'white' else (50, 50, 50)
                
                for py in range(thickness):
                    if y + py >= canvas_height:
                        break
                    for px in range(canvas_width):
                        pixels[px, y + py] = color
                
                y += thickness
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'custom'
        self.update_pattern()
    
    def reset_options_only(self):
        """Reset slider values without changing the base pattern"""
        print("[DEBUG] Reset Options clicked")
        self.twist_amount.set(0.0)
        self.grind_depth.set(0.0)
        self.grind_angle.set(0.0)
        self.rotation_angle.set(0)
        self.mosaic_size.set(1)
        self.white_layer_thickness.set(1.0)
        self.black_layer_thickness.set(1.0)
        self.update_unit_display()
        # Update pattern to show effect of reset sliders
        self.update_pattern()
        print("[DEBUG] Reset Options complete")
    
    def reset_all(self):
        """Reset all controls AND reload default pattern"""
        try:
            print("[DEBUG] Reset All clicked")
            # Reset sliders first
            self.twist_amount.set(0.0)
            self.grind_depth.set(0.0)
            self.grind_angle.set(0.0)
            self.rotation_angle.set(0)
            self.mosaic_size.set(1)
            self.white_layer_thickness.set(1.0)
            self.black_layer_thickness.set(1.0)
            self.custom_layer_stack = None
            self.last_custom_layer_stack = None
            self.update_unit_display()
            # Load default pattern which will also call update_pattern()
            self.load_default_pattern()
            print("[DEBUG] Reset All complete")
        except Exception as e:
            print(f"[ERROR] Reset All failed: {e}")
            import traceback
            traceback.print_exc()
    
    def report_issue(self):
        """Generate and open GitHub issue with debug information"""
        import platform
        import sys
        import urllib.parse
        import webbrowser
        
        # Collect system info
        system_info = f"""**System Information:**
- OS: {platform.system()} {platform.release()}
- Python: {sys.version.split()[0]}
- DPS Version: 1.2

"""
        
        # Add debug log if available
        debug_info = ""
        if self.debug_log:
            debug_info = f"""**Debug Log:**
```
{"".join(self.debug_log[-20:])}
```

"""
        else:
            debug_info = "**Debug Log:** No debug information available (Debug mode was off)\n\n"
        
        # Create issue template
        issue_title = "Bug Report: "
        issue_body = f"""## Description
[Please describe the issue you're experiencing]

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

{system_info}{debug_info}---
*This issue was generated using the Report Issue feature in DPS v1.2*
"""
        
        # URL encode the parameters
        github_url = "https://github.com/gboyce1967/damascus-pattern-simulator/issues/new"
        params = {
            "title": issue_title,
            "body": issue_body
        }
        url = f"{github_url}?{urllib.parse.urlencode(params)}"
        
        try:
            webbrowser.open(url)
            if self.debug_log:
                messagebox.showinfo(
                    "Report Issue",
                    "Opening GitHub in your browser...\n\n"
                    "Debug information has been included.\n"
                    "Please describe the issue you're experiencing."
                )
            else:
                messagebox.showinfo(
                    "Report Issue",
                    "Opening GitHub in your browser...\n\n"
                    "Tip: Enable Debug mode and reproduce the issue\n"
                    "to include detailed debug information."
                )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not open browser: {e}\n\n"
                f"Please visit:\n{github_url}"
            )
    
    def check_for_updates(self):
        """Check for updates via the update script"""
        import subprocess
        import sys
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        update_script = os.path.join(script_dir, 'update-DPS.sh')
        
        if not os.path.exists(update_script):
            messagebox.showinfo(
                "Update Check",
                "Update script not found.\n\n"
                "This feature requires installation via git clone.\n"
                "Visit: github.com/gboyce1967/damascus-pattern-simulator"
            )
            return
        
        try:
            # Run update script in a terminal
            terminal_commands = [
                ['x-terminal-emulator', '-e', f'bash -c "{update_script}; echo; read -p \"Press Enter to close...\""'],
                ['gnome-terminal', '--', 'bash', '-c', f'{update_script}; echo; read -p "Press Enter to close..."'],
                ['xterm', '-e', f'bash -c "{update_script}; echo; read -p \"Press Enter to close...\""'],
                ['konsole', '-e', f'bash -c "{update_script}; echo; read -p \"Press Enter to close...\""']
            ]
            
            success = False
            for cmd in terminal_commands:
                try:
                    subprocess.Popen(cmd)
                    success = True
                    break
                except FileNotFoundError:
                    continue
            
            if not success:
                messagebox.showinfo(
                    "Update Check",
                    "Could not open terminal.\n\n"
                    f"Please run manually:\n{update_script}"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check for updates: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Damascus Pattern Simulator
Version 1.2
|
Simulate Damascus steel patterns with:
• Twist transformations
• Grind depth and angle control
• Custom layer stacks with pattern images
• Mosaic pattern generation
• W and C pattern presets
• Dynamic canvas sizing
|
Created for Linux
Inspired by Thor II by Christian Schnura
|
GitHub: github.com/gboyce1967/damascus-pattern-simulator"""
        messagebox.showinfo("About", about_text)
    
    def apply_twist(self, pattern):
        """Apply twist transformation to the pattern"""
        twist = self.twist_amount.get()
        if twist == 0:
            return pattern
        
        height, width = pattern.shape[:2]
        result = np.zeros_like(pattern)
        
        center_x = width / 2
        center_y = height / 2
        
        for y in range(height):
            for x in range(width):
                # Calculate distance from center
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Calculate twist angle based on distance
                angle = (distance / width) * twist * math.pi
                
                # Apply rotation
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                
                new_x = int(center_x + dx * cos_a - dy * sin_a)
                new_y = int(center_y + dx * sin_a + dy * cos_a)
                
                # Boundary check
                if 0 <= new_x < width and 0 <= new_y < height:
                    result[y, x] = pattern[new_y, new_x]
        
        return result
    
    def apply_grind(self, pattern):
        """Simulate grinding from the side - creates a slice showing layer cross-section"""
        grind_depth = self.grind_depth.get()
        grind_angle = self.grind_angle.get()
        
        if grind_depth == 0:
            return pattern
        
        height, width = pattern.shape[:2]
        result = np.zeros_like(pattern)
        
        # The pattern represents the end grain of the billet
        # When grinding from the side, we're cutting perpendicular to what we see
        # We need to show a cross-section at the grind depth
        
        # Calculate grind depth as a fraction through the depth of the billet
        # We'll simulate depth by using the X-axis of the pattern as the depth dimension
        max_depth = width
        grind_pixels = int((grind_depth / 100) * max_depth * 0.8)
        
        # Apply bevel angle
        angle_rad = math.radians(grind_angle)
        
        # For each position on the resulting ground surface
        for y in range(height):
            for x in range(width):
                # Calculate depth at this position based on bevel angle
                # Bevel: depth varies across the width (left to right creates angled surface)
                if grind_angle > 0:
                    # Normalize x position (0 to 1)
                    x_norm = x / width
                    # Calculate additional depth due to bevel
                    bevel_depth = int(x_norm * grind_pixels * math.tan(angle_rad) * 2)
                    total_depth = grind_pixels + bevel_depth
                else:
                    total_depth = grind_pixels
                
                # Sample from the pattern at this depth
                # Use the pattern column at total_depth as the source
                depth_x = min(total_depth, width - 1)
                result[y, x] = pattern[y, depth_x]
        
        return result
    
    def apply_mosaic(self, pattern):
        """Apply mosaic stacking"""
        mosaic = self.mosaic_size.get()
        if mosaic == 1:
            return pattern
        
        height, width = pattern.shape[:2]
        new_height = height // mosaic
        new_width = width // mosaic
        
        # Resize pattern to fit mosaic tile
        tile = Image.fromarray(pattern).resize((new_width, new_height))
        tile_array = np.array(tile)
        
        # Create mosaic
        result = np.zeros((height, width, 3), dtype=np.uint8)
        
        for i in range(mosaic):
            for j in range(mosaic):
                y_start = i * new_height
                x_start = j * new_width
                y_end = min((i + 1) * new_height, height)
                x_end = min((j + 1) * new_width, width)
                
                # Alternate rotation for visual interest
                if (i + j) % 2 == 1:
                    rotated_tile = np.rot90(tile_array, k=2)
                    result[y_start:y_end, x_start:x_end] = rotated_tile[:y_end-y_start, :x_end-x_start]
                else:
                    result[y_start:y_end, x_start:x_end] = tile_array[:y_end-y_start, :x_end-x_start]
        
        return result
    
    def update_pattern(self, *args):
        """Update the displayed pattern with all transformations"""
        self.debug_print("update_pattern() called")
        if self.pattern_array is None:
            self.debug_print("No pattern_array to update")
            return
        
        try:
            # Start with base pattern
            result = self.pattern_array.copy()
            self.debug_print(f"Base pattern: {result.shape}")
            
            # Apply rotation first
            rotation = self.rotation_angle.get()
            if rotation != 0:
                self.debug_print(f"Applying rotation: {rotation}°")
                k = rotation // 90  # Number of 90-degree rotations
                result = np.rot90(result, k=k)
            
            # Apply mosaic
            mosaic_val = self.mosaic_size.get()
            if mosaic_val > 1:
                self.debug_print(f"Applying mosaic: {mosaic_val}x{mosaic_val}")
            result = self.apply_mosaic(result)
            
            # Apply other transformations
            twist_val = self.twist_amount.get()
            if twist_val > 0:
                self.debug_print(f"Applying twist: {twist_val}")
            result = self.apply_twist(result)
            
            grind_val = self.grind_depth.get()
            if grind_val > 0:
                self.debug_print(f"Applying grind: {grind_val}% at {self.grind_angle.get()}°")
            result = self.apply_grind(result)
            
            # Convert to PIL Image
            img = Image.fromarray(result)
            
            # Get actual pattern dimensions
            pattern_width, pattern_height = img.size
            self.debug_print(f"Final pattern size: {pattern_width}x{pattern_height}")
            print(f"[DEBUG] Pattern size: {pattern_width}x{pattern_height}")
            
            # Calculate scale to fit in canvas while maintaining aspect ratio
            scale_w = (self.canvas_width - 20) / pattern_width
            scale_h = (self.canvas_height - 20) / pattern_height
            scale = min(scale_w, scale_h, 1.0)  # Don't scale up, only down
            
            if scale < 1.0:
                # Scale down to fit
                new_width = int(pattern_width * scale)
                new_height = int(pattern_height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.display_image = ImageTk.PhotoImage(img)
            
            # Display on canvas centered
            self.canvas.delete("all")
            x = (self.canvas_width - img.width) // 2
            y = (self.canvas_height - img.height) // 2
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.display_image)
            self.debug_print(f"Canvas updated at position ({x}, {y})")
            
        except Exception as e:
            self.debug_print(f"ERROR in update_pattern: {e}")
            print(f"Error updating pattern: {e}")
    
    def save_pattern(self):
        """Save the current pattern to file"""
        self.debug_print("save_pattern() called")
        if self.display_image is None:
            messagebox.showwarning("Warning", "No pattern to save!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Pattern",
            initialdir=self.default_save_dir,
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                # Recreate the pattern at full resolution
                result = self.apply_mosaic(self.pattern_array.copy())
                result = self.apply_twist(result)
                result = self.apply_grind(result)
                
                img = Image.fromarray(result)
                
                # Save as PDF if requested
                if filename.lower().endswith('.pdf'):
                    img.save(filename, "PDF", resolution=300.0)
                else:
                    img.save(filename)
                
                messagebox.showinfo("Success", f"Pattern exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export image: {e}")
    
    def save_pattern_as_layer(self):
        """Save current pattern as a layer image file for use in custom layer builder"""
        self.debug_print("save_pattern_as_layer() called")
        if self.pattern_array is None:
            messagebox.showwarning("Warning", "No pattern to save!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Pattern as Layer Image",
            initialdir=self.default_save_dir,
            defaultextension=".png",
            initialfile="damascus_layer.png",
            filetypes=[
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                # Save the BASE pattern without transformations
                # This is what will be used as a repeating layer
                img = Image.fromarray(self.pattern_array)
                img.save(filename)
                
                messagebox.showinfo("Success", 
                    f"Pattern saved as layer image:\n{filename}\n\n"
                    "You can now use this image in the Custom Layer Builder.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save pattern: {e}")
    
    def print_pattern(self):
        """Print the current pattern using native print dialog"""
        self.debug_print("print_pattern() called")
        if self.display_image is None:
            messagebox.showwarning("Warning", "No pattern to print!")
            return
        
        try:
            import tempfile
            import subprocess
            import sys
            
            # Recreate the pattern at full resolution
            result = self.apply_mosaic(self.pattern_array.copy())
            result = self.apply_twist(result)
            result = self.apply_grind(result)
            
            img = Image.fromarray(result)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name
                img.save(temp_path, 'PNG', dpi=(300, 300))
            
            # Create a helper script to run GTK print dialog in separate process
            print_script = f'''#!/usr/bin/env python3
import sys
import os
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GdkPixbuf, Gdk
    
    class PrintHandler:
        def __init__(self, image_path):
            self.image_path = image_path
            self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            
        def draw_page(self, operation, context, page_nr):
            cr = context.get_cairo_context()
            width = context.get_width()
            height = context.get_height()
            
            # Scale image to fit page while maintaining aspect ratio
            img_width = self.pixbuf.get_width()
            img_height = self.pixbuf.get_height()
            scale = min(width / img_width, height / img_height)
            
            # Center the image
            x_offset = (width - img_width * scale) / 2 / scale
            y_offset = (height - img_height * scale) / 2 / scale
            
            cr.scale(scale, scale)
            Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, x_offset, y_offset)
            cr.paint()
        
        def print_image(self):
            print_op = Gtk.PrintOperation()
            print_op.connect('draw-page', self.draw_page)
            print_op.set_n_pages(1)
            print_op.set_unit(Gtk.Unit.POINTS)
            print_op.set_job_name("Damascus Pattern")
            
            result = print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, None)
            
            # Clean up
            try:
                os.unlink(self.image_path)
            except:
                pass
            
            return result
    
    handler = PrintHandler(sys.argv[1])
    handler.print_image()
    
except Exception as e:
    print(f"Print error: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
            
            # Write helper script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                script_path = script_file.name
                script_file.write(print_script)
            
            # Make script executable
            import os
            os.chmod(script_path, 0o755)
            
            # Run print dialog in separate process to avoid event loop conflicts
            process = subprocess.Popen([sys.executable, script_path, temp_path])
            
            # Schedule cleanup after process completes
            def cleanup():
                process.wait()
                try:
                    os.unlink(script_path)
                except:
                    pass
            
            import threading
            threading.Thread(target=cleanup, daemon=True).start()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print: {e}")

class CustomLayerDialog:
    """Dialog window for building custom layer stacks"""
    def __init__(self, parent, simulator):
        self.simulator = simulator
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Custom Layer Builder")
        self.dialog.geometry("850x1100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Load existing layer stack if available
        if hasattr(simulator, 'last_custom_layer_stack') and simulator.last_custom_layer_stack:
            # Deep copy to avoid modifying the original
            import copy
            self.layers = copy.deepcopy(simulator.last_custom_layer_stack)
        else:
            self.layers = []  # List of {color: 'white'/'black', thickness: float}
        
        self.pattern_images = []  # List to store loaded pattern images
        
        self.setup_ui()
        
        # Update the listbox to show loaded layers
        if self.layers:
            self.update_listbox()
        
    def setup_ui(self):
        """Create the dialog UI"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Build Your Custom Layer Stack", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        ttk.Label(main_frame, text="Add layers from bottom to top. Units are in mm.",
                 font=('Arial', 9)).pack(pady=(0, 10))
        
        # Layer list with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.layer_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                        height=15, font=('Courier', 10))
        self.layer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.layer_listbox.yview)
        
        # Bind double-click to edit layer
        self.layer_listbox.bind('<Double-Button-1>', lambda e: self.edit_layer())
        
        # Add layer controls
        add_frame = ttk.LabelFrame(main_frame, text="Add Layer", padding=10)
        add_frame.pack(fill=tk.X, pady=5)
        
        # Color selection
        color_frame = ttk.Frame(add_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT, padx=(0, 10))
        self.color_var = tk.StringVar(value="white")
        ttk.Radiobutton(color_frame, text="White", variable=self.color_var, 
                       value="white").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(color_frame, text="Black", variable=self.color_var, 
                       value="black").pack(side=tk.LEFT, padx=5)
        
        # Thickness input
        thickness_frame = ttk.Frame(add_frame)
        thickness_frame.pack(fill=tk.X, pady=5)
        ttk.Label(thickness_frame, text="Thickness (mm):").pack(side=tk.LEFT, padx=(0, 10))
        self.thickness_var = tk.DoubleVar(value=1.0)
        thickness_spinbox = ttk.Spinbox(thickness_frame, from_=0.1, to=10.0, 
                                       increment=0.1, textvariable=self.thickness_var,
                                       width=10)
        thickness_spinbox.pack(side=tk.LEFT)
        
        # Add button
        ttk.Button(add_frame, text="Add Layer", 
                  command=self.add_layer).pack(pady=5)
        
        # Quick add buttons
        quick_frame = ttk.Frame(add_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quick_frame, text="Quick Add:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_frame, text="5 Alternating", 
                  command=lambda: self.add_alternating(5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="10 Alternating", 
                  command=lambda: self.add_alternating(10)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="20 Alternating", 
                  command=lambda: self.add_alternating(20)).pack(side=tk.LEFT, padx=2)
        
        # Layer management buttons
        mgmt_frame = ttk.Frame(main_frame)
        mgmt_frame.pack(fill=tk.X, pady=5)
        ttk.Button(mgmt_frame, text="Edit Selected", 
                  command=self.edit_layer).pack(side=tk.LEFT, padx=2)
        ttk.Button(mgmt_frame, text="Remove Selected", 
                  command=self.remove_layer).pack(side=tk.LEFT, padx=2)
        ttk.Button(mgmt_frame, text="Clear All", 
                  command=self.clear_layers).pack(side=tk.LEFT, padx=2)
        ttk.Button(mgmt_frame, text="Move Up", 
                  command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(mgmt_frame, text="Move Down", 
                  command=self.move_down).pack(side=tk.LEFT, padx=2)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        ttk.Button(action_frame, text="Apply Pattern", 
                  command=self.generate_pattern, 
                  style='Accent.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        # Apply to W/C pattern buttons
        apply_frame = ttk.Frame(main_frame)
        apply_frame.pack(fill=tk.X, pady=5)
        ttk.Label(apply_frame, text="Apply to Special Pattern:", 
                 font=('Arial', 9, 'bold')).pack(pady=(0, 5))
        button_row = ttk.Frame(apply_frame)
        button_row.pack(fill=tk.X)
        ttk.Button(button_row, text="Apply to W Pattern", 
                  command=self.apply_to_w).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(button_row, text="Apply to C Pattern", 
                  command=self.apply_to_c).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # Pattern image management
        save_frame = ttk.LabelFrame(main_frame, text="Load Pattern Images", padding=10)
        save_frame.pack(fill=tk.X, pady=5)
        ttk.Label(save_frame, text="Load saved pattern images to use as layers:",
                 font=('Arial', 9)).pack(anchor=tk.W, pady=(0, 5))
        ttk.Button(save_frame, text="Load Pattern Image as Layer", 
                  command=self.load_pattern_image).pack(fill=tk.X, pady=2)
        
        ttk.Button(main_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(fill=tk.X, padx=5, pady=5)
        
        # Layer count display
        self.count_label = ttk.Label(main_frame, text="Layers: 0", font=('Arial', 9))
        self.count_label.pack()
        
    def add_layer(self):
        """Add a layer to the stack"""
        color = self.color_var.get()
        thickness = self.thickness_var.get()
        
        if thickness <= 0:
            messagebox.showwarning("Invalid Thickness", "Thickness must be greater than 0")
            return
        
        self.layers.append({'color': color, 'thickness': thickness})
        self.update_listbox()
        
    def add_alternating(self, count):
        """Add alternating white/black layers"""
        thickness = self.thickness_var.get()
        for i in range(count):
            color = 'white' if i % 2 == 0 else 'black'
            self.layers.append({'color': color, 'thickness': thickness})
        self.update_listbox()
    
    def edit_layer(self):
        """Edit selected layer"""
        selection = self.layer_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a layer to edit")
            return
        
        idx = selection[0]
        layer = self.layers[idx]
        
        # Create edit dialog
        edit_dialog = tk.Toplevel(self.dialog)
        edit_dialog.title(f"Edit Layer {idx + 1}")
        edit_dialog.geometry("350x250")
        edit_dialog.transient(self.dialog)
        edit_dialog.resizable(False, False)
        
        frame = ttk.Frame(edit_dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Update window before grab_set
        edit_dialog.update_idletasks()
        
        # Color selection
        ttk.Label(frame, text="Color:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        color_var = tk.StringVar(value=layer['color'])
        color_frame = ttk.Frame(frame)
        color_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Radiobutton(color_frame, text="White", variable=color_var, 
                       value="white").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(color_frame, text="Black", variable=color_var, 
                       value="black").pack(side=tk.LEFT, padx=5)
        
        # Thickness input
        ttk.Label(frame, text="Thickness (mm):", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        thickness_var = tk.DoubleVar(value=layer['thickness'])
        thickness_spinbox = ttk.Spinbox(frame, from_=0.1, to=10.0, 
                                       increment=0.1, textvariable=thickness_var,
                                       width=15)
        thickness_spinbox.pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons
        def save_changes():
            new_thickness = thickness_var.get()
            if new_thickness <= 0:
                messagebox.showwarning("Invalid Thickness", "Thickness must be greater than 0")
                return
            
            self.layers[idx] = {'color': color_var.get(), 'thickness': new_thickness}
            self.update_listbox()
            self.layer_listbox.selection_set(idx)
            edit_dialog.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Grab focus after all widgets are created
        edit_dialog.grab_set()
        
    def remove_layer(self):
        """Remove selected layer"""
        selection = self.layer_listbox.curselection()
        if selection:
            idx = selection[0]
            del self.layers[idx]
            self.update_listbox()
            
    def clear_layers(self):
        """Clear all layers"""
        if messagebox.askyesno("Clear All", "Remove all layers?"):
            self.layers = []
            self.update_listbox()
            
    def move_up(self):
        """Move selected layer up"""
        selection = self.layer_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            self.layers[idx], self.layers[idx-1] = self.layers[idx-1], self.layers[idx]
            self.update_listbox()
            self.layer_listbox.selection_set(idx-1)
            
    def move_down(self):
        """Move selected layer down"""
        selection = self.layer_listbox.curselection()
        if selection and selection[0] < len(self.layers) - 1:
            idx = selection[0]
            self.layers[idx], self.layers[idx+1] = self.layers[idx+1], self.layers[idx]
            self.update_listbox()
            self.layer_listbox.selection_set(idx+1)
            
    def update_listbox(self):
        """Update the layer listbox display"""
        self.layer_listbox.delete(0, tk.END)
        for i, layer in enumerate(self.layers):
            if layer['color'] == 'pattern':
                # Pattern image layer
                pattern_name = layer.get('pattern_name', 'Unknown')
                text = f"{i+1:3d}. PATTERN - {pattern_name} ({layer['thickness']:.2f} mm)"
            else:
                # Regular color layer
                color_text = "WHITE" if layer['color'] == 'white' else "BLACK"
                text = f"{i+1:3d}. {color_text:5s} - {layer['thickness']:.2f} mm"
            self.layer_listbox.insert(tk.END, text)
        
        self.count_label.config(text=f"Layers: {len(self.layers)}")
        
    def generate_pattern(self):
        """Generate the pattern and close dialog"""
        if not self.layers:
            messagebox.showwarning("No Layers", "Please add at least one layer")
            return
        
        self.simulator.create_custom_layers(self.layers)
        self.dialog.destroy()
    
    def apply_to_w(self):
        """Apply custom layer stack to W pattern"""
        if not self.layers:
            messagebox.showwarning("No Layers", "Please add at least one layer")
            return
        
        self.simulator.custom_layer_stack = self.layers.copy()
        self.simulator.create_w_pattern()
        self.dialog.destroy()
    
    def apply_to_c(self):
        """Apply custom layer stack to C pattern"""
        if not self.layers:
            messagebox.showwarning("No Layers", "Please add at least one layer")
            return
        
        self.simulator.custom_layer_stack = self.layers.copy()
        self.simulator.create_c_pattern()
        self.dialog.destroy()
    
    def save_layer_stack(self):
        """Save layer stack to a JSON file"""
        if not self.layers:
            messagebox.showwarning("No Layers", "Please add at least one layer to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Layer Stack",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                import json
                # Create a copy of layers without pattern_image data (can't serialize numpy arrays)
                save_layers = []
                has_patterns = False
                for layer in self.layers:
                    if layer['color'] == 'pattern':
                        # Skip pattern layers - they can't be saved to JSON
                        has_patterns = True
                        continue
                    save_layers.append({'color': layer['color'], 'thickness': layer['thickness']})
                
                with open(filename, 'w') as f:
                    json.dump(save_layers, f, indent=2)
                
                msg = f"Layer stack saved to {filename}"
                if has_patterns:
                    msg += "\n\nNote: Pattern image layers were not saved (only white/black layers)."
                messagebox.showinfo("Success", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save layer stack: {e}")
    
    def load_layer_stack(self):
        """Load layer stack from a JSON file"""
        filename = filedialog.askopenfilename(
            title="Load Layer Stack",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                import json
                with open(filename, 'r') as f:
                    loaded_layers = json.load(f)
                
                # Validate the loaded data
                if not isinstance(loaded_layers, list):
                    raise ValueError("Invalid layer stack format")
                
                # Filter and validate layers
                valid_layers = []
                skipped_patterns = 0
                
                for layer in loaded_layers:
                    if not isinstance(layer, dict) or 'color' not in layer or 'thickness' not in layer:
                        raise ValueError("Invalid layer format")
                    
                    # Skip pattern layers without image data (can't be loaded from JSON)
                    if layer['color'] == 'pattern' and 'pattern_image' not in layer:
                        skipped_patterns += 1
                        continue
                    
                    if layer['color'] not in ['white', 'black', 'pattern']:
                        raise ValueError(f"Invalid layer color: {layer['color']}")
                    if not isinstance(layer['thickness'], (int, float)) or layer['thickness'] <= 0:
                        raise ValueError("Invalid layer thickness")
                    
                    valid_layers.append(layer)
                
                self.layers = valid_layers
                self.update_listbox()
                
                msg = f"Loaded {len(self.layers)} layers"
                if skipped_patterns > 0:
                    msg += f"\n\nNote: {skipped_patterns} pattern layer(s) were skipped because " \
                           f"pattern images cannot be saved to JSON files."
                messagebox.showinfo("Success", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load layer stack: {e}")
    
    def load_pattern_image(self):
        """Load a pattern image and add it as a custom layer"""
        filename = filedialog.askopenfilename(
            title="Load Pattern Image as Layer",
            initialdir=self.simulator.default_save_dir,
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                # Load the image
                img = Image.open(filename).convert('RGB')
                pattern_array = np.array(img)
                
                # Store the pattern image with filename reference
                import os
                pattern_name = os.path.basename(filename)
                
                # Debug info
                print(f"[DEBUG] Loaded pattern: {pattern_name}")
                print(f"[DEBUG] Pattern size: {pattern_array.shape}")
                print(f"[DEBUG] Sample pixel values: {pattern_array[0:3, 0:3]}")
                
                # Add as a special "pattern" type layer
                self.layers.append({
                    'color': 'pattern',
                    'thickness': 1.0,
                    'pattern_image': pattern_array,
                    'pattern_name': pattern_name
                })
                
                self.pattern_images.append(pattern_array)
                self.update_listbox()
                
                messagebox.showinfo("Success", 
                    f"Pattern image '{pattern_name}' added as a layer!\n\n"
                    f"When you generate the pattern, this image will be used as a repeating layer.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load pattern image: {e}")

class MosaicBuilderDialog:
    """Dialog for building custom mosaic patterns"""
    def __init__(self, parent, simulator):
        self.simulator = simulator
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Custom Mosaic Builder")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Custom Mosaic Pattern Builder",
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        ttk.Label(main_frame, text="Create custom mosaic arrangements using your current pattern",
                 font=('Arial', 9)).pack(pady=(0, 20))
        
        # Pattern type selection
        type_frame = ttk.LabelFrame(main_frame, text="Mosaic Type", padding=15)
        type_frame.pack(fill=tk.X, pady=10)
        
        self.mosaic_type = tk.StringVar(value="straight")
        ttk.Radiobutton(type_frame, text="Straight Line", variable=self.mosaic_type,
                       value="straight").pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(type_frame, text="Checkerboard", variable=self.mosaic_type,
                       value="checkerboard").pack(anchor=tk.W, pady=5)
        
        # Tile count configuration
        count_frame = ttk.LabelFrame(main_frame, text="Tile Configuration", padding=15)
        count_frame.pack(fill=tk.X, pady=10)
        
        # Horizontal tiles
        ttk.Label(count_frame, text="Horizontal Tiles:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.h_tiles = tk.IntVar(value=2)
        h_spinbox = ttk.Spinbox(count_frame, from_=1, to=10, textvariable=self.h_tiles, width=10)
        h_spinbox.grid(row=0, column=1, padx=(10,0), pady=5)
        
        # Vertical tiles
        ttk.Label(count_frame, text="Vertical Tiles:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.v_tiles = tk.IntVar(value=2)
        v_spinbox = ttk.Spinbox(count_frame, from_=1, to=10, textvariable=self.v_tiles, width=10)
        v_spinbox.grid(row=1, column=1, padx=(10,0), pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Generate Mosaic",
                  command=self.generate_mosaic).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="Cancel",
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    def generate_mosaic(self):
        """Generate the custom mosaic pattern"""
        if self.simulator.original_image is None:
            messagebox.showwarning("No Pattern", "Please create or load a pattern first")
            return
        
        mosaic_type = self.mosaic_type.get()
        h_tiles = self.h_tiles.get()
        v_tiles = self.v_tiles.get()
        
        # Get the base pattern and apply rotation if set
        # This ensures we use the pattern as it currently appears (with rotation)
        tile_pattern = self.simulator.pattern_array.copy()
        
        # Apply rotation to match what user sees
        rotation = self.simulator.rotation_angle.get()
        if rotation != 0:
            k = rotation // 90  # Number of 90-degree rotations
            tile_pattern = np.rot90(tile_pattern, k=k)
        
        tile_height, tile_width = tile_pattern.shape[:2]
        
        # Calculate result dimensions based on number of tiles
        # h_tiles = number of tiles horizontally (across width)
        # v_tiles = number of tiles vertically (down height)
        result_width = tile_width * h_tiles
        result_height = tile_height * v_tiles
        
        # Create mosaic canvas
        result = np.zeros((result_height, result_width, 3), dtype=np.uint8)
        
        # Fill with tiles - each tile is the complete pattern
        # i = vertical index (rows), j = horizontal index (columns)
        for i in range(v_tiles):
            for j in range(h_tiles):
                y_start = i * tile_height
                x_start = j * tile_width
                y_end = y_start + tile_height
                x_end = x_start + tile_width
                
                if mosaic_type == "checkerboard":
                    # Alternate rotation for checkerboard pattern
                    if (i + j) % 2 == 1:
                        rotated_tile = np.rot90(tile_pattern, k=2)
                        result[y_start:y_end, x_start:x_end] = rotated_tile
                    else:
                        result[y_start:y_end, x_start:x_end] = tile_pattern
                else:
                    # Straight line - all tiles same orientation
                    result[y_start:y_end, x_start:x_end] = tile_pattern
        
        # Update the simulator with new mosaic pattern
        self.simulator.original_image = Image.fromarray(result)
        self.simulator.pattern_array = result
        self.simulator.current_pattern_type = 'custom_mosaic'
        
        # Reset rotation since it's now baked into the mosaic
        self.simulator.rotation_angle.set(0)
        
        self.simulator.update_pattern()
        
        self.dialog.destroy()
        messagebox.showinfo("Success", f"Created {h_tiles}x{v_tiles} {mosaic_type} mosaic pattern")

def main():
    root = tk.Tk()
    app = DamascusSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
