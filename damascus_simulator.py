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
        self.canvas_width = 1350  # Wider canvas for full window width
        self.canvas_height = 500  # Shorter to fit horizontal layout
        
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
        
        # Transformation history for undo and export steps
        self.transformation_steps = []  # List of (step_name, pattern_array) tuples
        self.current_step_index = -1  # Track which step we're viewing
        
        # Debug mode
        self.debug_mode = tk.BooleanVar(value=False)
        self.debug_mode.trace_add('write', self.on_debug_mode_change)
        self.debug_log = []
        
        # Canvas background
        self.canvas_bg_image = None
        self.canvas_bg_tile = None
        self.corner_logo_refs = []  # Store references to corner logo PhotoImages
        self.load_default_canvas_background()
        
        # Default save directory
        self.default_save_dir = os.path.expanduser('~/Documents/DPS')
        self.ensure_save_directory()
        
        self.setup_ui()
        self.load_default_pattern()
        # Delay canvas background until window is fully rendered
        self.root.after(100, self.update_canvas_background)
    
    def ensure_save_directory(self):
        """Ensure the default save directory exists"""
        try:
            os.makedirs(self.default_save_dir, exist_ok=True)
        except Exception as e:
            print(f"[WARNING] Could not create default save directory: {e}")
    
    def on_debug_mode_change(self, *args):
        """Called when debug mode checkbox is toggled"""
        if self.debug_mode.get():
            self.debug_print("Debug mode enabled")
        else:
            print("[INFO] Debug mode disabled")
    
    def load_default_canvas_background(self):
        """Load the default tiled canvas background"""
        # Load from project directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(script_dir, 'canvas_background.png')
        
        try:
            if os.path.exists(bg_path):
                self.canvas_bg_image = Image.open(bg_path).convert('RGB')
                print(f"[INFO] Loaded canvas background: {bg_path}")
            else:
                print(f"[WARNING] Canvas background not found: {bg_path}")
        except Exception as e:
            print(f"[WARNING] Could not load canvas background: {e}")
    
    def update_canvas_background(self):
        """Update the canvas background with dynamic green and corner logos"""
        try:
            # Delete old background elements
            self.canvas.delete("bg")
            self.corner_logo_refs.clear()
            
            # Get actual canvas size
            self.canvas.update_idletasks()
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            
            # Use defaults if canvas not yet sized
            if canvas_w <= 1:
                canvas_w = self.canvas_width
            if canvas_h <= 1:
                canvas_h = self.canvas_height
            
            # Draw solid green background as a canvas rectangle
            self.canvas.create_rectangle(0, 0, canvas_w, canvas_h, 
                                        fill='#00ff00', outline='', tags="bg")
            
            # Add logos if available
            if self.canvas_bg_image:
                # Extract single logo from 2x2 grid
                orig_width, orig_height = self.canvas_bg_image.size
                single_logo_width = orig_width // 2
                single_logo_height = orig_height // 2
                logo = self.canvas_bg_image.crop((0, 0, single_logo_width, single_logo_height))
                
                # Scale logo
                scale_factor = min(200 / single_logo_width, 150 / single_logo_height)
                new_width = int(single_logo_width * scale_factor)
                new_height = int(single_logo_height * scale_factor)
                logo_resized = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                padding = 10
                
                # Create PhotoImage for single logo
                logo_photo = ImageTk.PhotoImage(logo_resized)
                self.corner_logo_refs.append(logo_photo)
                
                # Place single logo in top-left corner
                self.canvas.create_image(padding, padding, anchor=tk.NW, 
                                        image=logo_photo, tags="bg")
            
            # Make sure background is behind everything
            self.canvas.tag_lower("bg")
            
        except Exception as e:
            print(f"[WARNING] Could not set canvas background: {e}")
    
    def change_canvas_background(self):
        """Allow user to change the canvas background"""
        # Create a dialog with options
        dialog = tk.Toplevel(self.root)
        dialog.title("Canvas Background")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Choose Canvas Background:", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 20))
        
        def use_default():
            self.load_default_canvas_background()
            self.update_canvas_background()
            self.update_pattern()
            dialog.destroy()
            messagebox.showinfo("Success", "Default background restored!")
        
        def use_image():
            dialog.destroy()
            filename = filedialog.askopenfilename(
                title="Select Canvas Background Image",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                try:
                    self.canvas_bg_image = Image.open(filename).convert('RGB')
                    self.update_canvas_background()
                    self.update_pattern()
                    messagebox.showinfo("Success", "Canvas background updated!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load image: {e}")
        
        def use_color():
            from tkinter import colorchooser
            dialog.destroy()
            
            color = colorchooser.askcolor(title="Choose Background Color")
            if color[1]:  # color[1] is the hex string
                try:
                    # Create solid color image
                    bg = Image.new('RGB', (self.canvas_width, self.canvas_height), color[0])
                    self.canvas_bg_image = bg
                    self.update_canvas_background()
                    self.update_pattern()
                    messagebox.showinfo("Success", "Canvas background color updated!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to set color: {e}")
        
        # Buttons
        ttk.Button(main_frame, text="Default (Gray Works Logo)", 
                  command=use_default).pack(fill=tk.X, pady=5)
        ttk.Button(main_frame, text="Custom Image...", 
                  command=use_image).pack(fill=tk.X, pady=5)
        ttk.Button(main_frame, text="Solid Color...", 
                  command=use_color).pack(fill=tk.X, pady=5)
        ttk.Button(main_frame, text="Cancel", 
                  command=dialog.destroy).pack(fill=tk.X, pady=15)
    
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
        """Create the user interface - horizontal layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top menu bar with split layout
        menubar = ttk.Frame(main_frame)
        menubar.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        # Left side menu items
        left_menu = ttk.Frame(menubar)
        left_menu.pack(side=tk.LEFT, fill=tk.X)
        
        ttk.Button(left_menu, text="Load Pattern", command=self.load_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Load Default", command=self.load_default_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Undo Last Step", command=self.undo_last_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Export Steps", command=self.export_steps).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Save as Layer", command=self.save_pattern_as_layer).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Export", command=self.save_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_menu, text="Print", command=self.print_pattern).pack(side=tk.LEFT, padx=2)
        
        # Right side menu items
        right_menu = ttk.Frame(menubar)
        right_menu.pack(side=tk.RIGHT, fill=tk.X)
        
        ttk.Checkbutton(right_menu, text="Debug", variable=self.debug_mode).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Canvas BG", command=self.change_canvas_background).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Report Issue", command=self.report_issue).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Reset Options", command=self.reset_options_only).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Reset All", command=self.reset_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="Check for Updates", command=self.check_for_updates).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_menu, text="About", command=self.show_about).pack(side=tk.LEFT, padx=2)
        
        # Canvas area - full width
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 10))
        
        # Canvas for image display with modern styling
        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, height=self.canvas_height, 
                               bg=self.colors['canvas_bg'], highlightthickness=2, 
                               highlightbackground=self.colors['border'])
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind canvas resize to update background and recenter pattern
        def on_canvas_resize(event):
            # Update canvas dimensions
            self.canvas_width = event.width
            self.canvas_height = event.height
            # Redraw background and pattern when canvas size changes
            self.update_canvas_background()
            if self.pattern_array is not None:
                self.update_pattern()
        self.canvas.bind('<Configure>', on_canvas_resize)
        
        # Bottom controls panel with horizontal scrollbar
        controls_container = ttk.Frame(main_frame)
        controls_container.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Create horizontal scrollbar and canvas for controls
        h_scrollbar = ttk.Scrollbar(controls_container, orient="horizontal")
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        controls_canvas = tk.Canvas(controls_container, height=320, bg=self.colors['bg'],
                                   highlightthickness=0, borderwidth=0,
                                   xscrollcommand=h_scrollbar.set)
        controls_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        h_scrollbar.config(command=controls_canvas.xview)
        
        # Scrollable frame for controls
        controls_frame = ttk.Frame(controls_canvas)
        controls_canvas.create_window((0, 0), window=controls_frame, anchor="nw")
        
        def _on_frame_configure(event):
            controls_canvas.configure(scrollregion=controls_canvas.bbox("all"))
        controls_frame.bind("<Configure>", _on_frame_configure)
        
        # Bind horizontal scroll with mouse wheel (Shift+wheel for horizontal)
        def _on_h_mousewheel(event):
            controls_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        controls_canvas.bind_all("<Shift-MouseWheel>", _on_h_mousewheel)
        
        # Layout all controls horizontally in the bottom panel
        # Transformations section
        transform_frame = ttk.LabelFrame(controls_frame, text="Transformations", padding=10)
        transform_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        
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
        
        # Grind angle (now first)
        ttk.Label(transform_frame, text="Grind Angle (degrees):").pack(anchor=tk.W, pady=(0,3))
        angle_frame = ttk.Frame(transform_frame)
        angle_frame.pack(fill=tk.X, pady=(0, 12))
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
        
        # Grind depth (now second)
        ttk.Label(transform_frame, text="Grind Depth (%):").pack(anchor=tk.W, pady=(0,3))
        grind_frame = ttk.Frame(transform_frame)
        grind_frame.pack(fill=tk.X, pady=(0, 0))
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
        
        # Layer thickness controls
        layer_frame = ttk.LabelFrame(controls_frame, text="Layer Thickness", padding=10)
        layer_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        
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
        
        # Rotation
        rotation_frame = ttk.LabelFrame(controls_frame, text="Rotation", padding=10)
        rotation_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        
        for angle in [0, 90, 180, 270]:
            ttk.Radiobutton(rotation_frame, text=f"{angle}°", 
                          variable=self.rotation_angle, value=angle,
                          command=self.update_pattern).pack(anchor=tk.W, pady=3)
        
        # Custom builders section
        builders_frame = ttk.LabelFrame(controls_frame, text="Pattern Builders", padding=10)
        builders_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        
        ttk.Button(builders_frame, text="Custom Layers",
                  command=self.open_custom_layer_builder).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(builders_frame, text="Create Mosaic",
                  command=self.open_mosaic_builder).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(builders_frame, text="Feather Pattern",
                  command=self.open_feather_builder).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(builders_frame, text="Raindrop Pattern",
                  command=self.open_raindrop_builder).pack(fill=tk.X)
        
        # Preset patterns
        preset_frame = ttk.LabelFrame(controls_frame, text="Preset Patterns", padding=10)
        preset_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 0))
        
        presets = [
            ("Simple Layers", self.create_simple_layers),
            ("Ladder Pattern", lambda: self.create_ladder_pattern(use_custom_stack=False)),
            ("W Pattern", lambda: self.create_w_pattern(use_custom_stack=False)),
            ("C Pattern", lambda: self.create_c_pattern(use_custom_stack=False)),
            ("Random Pattern", self.create_random_pattern),
        ]
        
        for name, func in presets:
            ttk.Button(preset_frame, text=name, command=func).pack(fill=tk.X, pady=2)
    
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
        elif self.current_pattern_type == 'ladder_pattern':
            self.create_ladder_pattern()
        # Note: feather_pattern and raindrop_pattern use stored configs
        # They require their builder dialogs to be reopened to change settings
    
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
        """Create a W pattern (C patterns stacked repeatedly in same orientation)
        
        REAL-WORLD FORGING PROCESS:
        1. Start with simple alternating layers
        2. Forge weld and compress on bias to create C pattern
        3. Draw out (stretch) the C-pattern billet
        4. Clean surface, cut into pieces
        5. Stack the C-pattern pieces VERTICALLY (on top of each other)
        6. Forge weld the stack - the repeating C curves create W waves
        
        VISUAL REPRESENTATION:
        - Shows TWO C patterns placed SIDE-BY-SIDE horizontally
        - This simulates what you see when looking at the edge of a W-pattern billet
        - In reality, the C's are stacked vertically during forging
        - The visual shows the final appearance after forging and grinding
        
        IMPORTANT DISTINCTION:
        - FORGING: C patterns are stacked vertically (like pancakes)
        - VISUAL: We show them side-by-side (what you see on the blade edge)
        - Both representations are correct for their context!
        """
        # If no custom stack specified, clear it to use default layers
        if use_custom_stack is False:
            self.custom_layer_stack = None
        
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        # Create W pattern using sine wave distortion
        # This creates the rounded wave pattern from stacked C patterns
        import math
        
        # Wave parameters
        wave_amplitude = 40  # How much the layers wave
        wave_frequency = 4   # Number of complete waves vertically
        
        for y in range(size):
            for x in range(size):
                # W pattern = two C patterns side by side
                # Split the canvas in half horizontally
                half_width = size / 2
                
                # Determine which half we're in
                if x < half_width:
                    # Left C pattern
                    x_normalized = x / half_width  # 0 to 1 within left half
                else:
                    # Right C pattern
                    x_normalized = (x - half_width) / half_width  # 0 to 1 within right half
                
                # Create C pattern (same as what we just had)
                # Base sinusoidal wave
                wave_offset = math.cos(x_normalized * math.pi * 2) * wave_amplitude * 1.2
                
                # Add parabolic curve at edges for C-shape
                distance_from_center = abs(x_normalized - 0.5) * 2
                edge_curve = (distance_from_center ** 2) * wave_amplitude * 1.0
                
                # Combine wave with edge curvature
                total_offset = int(wave_offset + edge_curve)
                
                # Apply to y position
                distorted_y = y + total_offset
                
                # Get color based on the distorted position
                color = self.get_layer_color_at_position(distorted_y)
                
                pixels[x, y] = color
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'w_pattern'
        self.update_pattern()
    
    def create_c_pattern(self, use_custom_stack=None):
        """Create a C pattern (made by compressing simple layers on a 45° bias)
        
        REAL-WORLD FORGING PROCESS:
        1. Start with simple alternating flat layers (horizontal)
        2. Compress the welded stack on a 45° bias angle
        3. The compression causes the edges to fold inward
        4. This creates the characteristic C/arc shape in the layers
        
        VISUAL REPRESENTATION:
        - Uses sinusoidal wave + parabolic edge curvature
        - Wave creates the flowing pattern
        - Edge curve simulates the inward fold from compression
        - This is the BASE pattern for creating W patterns
        
        IMPORTANT: C patterns are NOT a base pattern themselves - they are
        a transformation of simple alternating layers through bias compression.
        """
        # If no custom stack specified, clear it to use default layers
        if use_custom_stack is False:
            self.custom_layer_stack = None
        
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        import math
        
        # Wave parameters (same as W pattern for consistency)
        # These create the smooth flowing C curve
        wave_amplitude = 40
        
        for y in range(size):
            for x in range(size):
                # Create single C pattern across full width
                x_normalized = x / size  # 0 to 1
                
                # Base sinusoidal wave
                wave_offset = math.cos(x_normalized * math.pi * 2) * wave_amplitude * 1.2
                
                # Add parabolic curve at edges for C-shape
                distance_from_center = abs(x_normalized - 0.5) * 2
                edge_curve = (distance_from_center ** 2) * wave_amplitude * 1.0
                
                # Combine wave with edge curvature
                total_offset = int(wave_offset + edge_curve)
                
                # Apply to y position
                distorted_y = y + total_offset
                
                # Get color based on the distorted position
                color = self.get_layer_color_at_position(distorted_y)
                
                pixels[x, y] = color
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'c_pattern'
        self.update_pattern()
    
    def create_ladder_pattern(self, use_custom_stack=None):
        """Create a ladder pattern by simulating grooves cut across the billet
        
        REAL-WORLD FORGING PROCESS:
        1. Start with layered billet (usually simple layers)
        2. Cut/forge grooves 1/3 depth STAGGERED on both sides
        3. Hammer/press flat to level - this pushes layers sideways
        4. Creates oval/elongated shapes where layers are exposed
        
        VISUAL REPRESENTATION:
        - Oval/elongated shapes (not just lines) running across the width
        - Staggered on both sides creates the characteristic ladder look
        - Shows layer distortion from the pressing process
        """
        # If no custom stack specified, clear it to use default layers
        if use_custom_stack is False:
            self.custom_layer_stack = None
        
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        import math
        
        # Ladder parameters
        groove_spacing = 35  # pixels between ladder rungs
        oval_height = 20     # height of each oval rung
        oval_width = 8       # how much the layers bulge sideways
        
        for y in range(size):
            for x in range(size):
                # Start with base layer color
                base_y = y
                color = self.get_layer_color_at_position(base_y)
                
                # Determine if we're near a groove position (staggered pattern)
                # Stagger grooves: every other groove is offset by half spacing
                x_in_cycle = x % (groove_spacing * 2)
                
                # First set of grooves (at 0, 2*spacing, 4*spacing...)
                if x_in_cycle < groove_spacing:
                    groove_center = (x // (groove_spacing * 2)) * groove_spacing * 2
                    dist_from_groove = abs(x - groove_center)
                    
                    if dist_from_groove < oval_height:
                        # We're in a groove area - create oval distortion
                        # Calculate how much to shift layers (creates oval shape)
                        oval_factor = 1 - (dist_from_groove / oval_height)
                        y_shift = int(math.sin(oval_factor * math.pi) * oval_width)
                        adjusted_y = y + y_shift
                        color = self.get_layer_color_at_position(adjusted_y)
                else:
                    # Second set of grooves (offset by spacing)
                    groove_center = (x // (groove_spacing * 2)) * groove_spacing * 2 + groove_spacing
                    dist_from_groove = abs(x - groove_center)
                    
                    if dist_from_groove < oval_height:
                        # We're in a groove area - create oval distortion
                        oval_factor = 1 - (dist_from_groove / oval_height)
                        y_shift = int(math.sin(oval_factor * math.pi) * oval_width)
                        adjusted_y = y + y_shift
                        color = self.get_layer_color_at_position(adjusted_y)
        
                pixels[x, y] = color
        
        try:
            self.original_image = img
            self.pattern_array = np.array(img)
            self.current_pattern_type = 'ladder_pattern'
            self.update_pattern()
        except Exception as e:
            print(f"[ERROR] Failed to create ladder pattern: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to create ladder pattern: {e}")
    
    def open_feather_builder(self):
        """Open dialog to build feather pattern"""
        FeatherBuilderDialog(self.root, self)
    
    def open_raindrop_builder(self):
        """Open dialog to build raindrop pattern"""
        RaindropBuilderDialog(self.root, self)
    
    def create_feather_pattern(self, base_pattern='w', split_direction='width'):
        """Create a feather pattern by splitting a base pattern
        
        REAL-WORLD FORGING PROCESS:
        1. Start with W pattern (or simple layers)
        2. Split the billet from top face with DULL wedge against the grain
        3. Wedge pulls/smears layers creating elongated loops
        4. Rejoining seam creates the central vein
        5. Fine parallel lines extend from vein to edges like feather barbs
        
        Args:
            base_pattern: 'w' or 'simple' - pattern to start with
            split_direction: 'width' or 'length' - direction of split
        """
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        import math
        
        # Feather parameters
        vein_width = 4  # Central vein thickness
        
        for y in range(size):
            for x in range(size):
                if split_direction == 'width':
                    # Horizontal vein (split across width)
                    center_y = size / 2
                    distance_from_vein = abs(y - center_y)
                    
                    # Draw central vein as a distinct dark line
                    if distance_from_vein < vein_width:
                        # Central vein - dark
                        color = (30, 30, 30)
                    else:
                        # Create feather barbs extending from vein
                        # The wedge split smears/pulls layers creating elongated loops
                        if base_pattern == 'w':
                            # Start with W pattern layers
                            half_width = size / 2
                            if x < half_width:
                                x_normalized = x / half_width
                            else:
                                x_normalized = (x - half_width) / half_width
                            
                            wave_amplitude = 40
                            wave_offset = math.cos(x_normalized * math.pi * 2) * wave_amplitude * 1.2
                            distance_from_center = abs(x_normalized - 0.5) * 2
                            edge_curve = (distance_from_center ** 2) * wave_amplitude * 1.0
                            total_offset = int(wave_offset + edge_curve)
                            base_y = y + total_offset
                        else:
                            base_y = y
                        
                        # Apply wedge smearing effect - pulls layers toward vein
                        # Creates elongated loops that flow from vein to edges
                        smear_intensity = distance_from_vein / (size / 2)
                        x_oscillation = math.sin((x / size) * math.pi * 6) * 25 * smear_intensity
                        
                        # Pull layers toward the vein (creates the feather barb effect)
                        if y < center_y:
                            pull_toward_vein = int(x_oscillation)
                        else:
                            pull_toward_vein = int(x_oscillation)
                        
                        adjusted_y = base_y + pull_toward_vein
                        color = self.get_layer_color_at_position(adjusted_y)
                else:
                    # Vertical vein (split across length)
                    center_x = size / 2
                    distance_from_vein = abs(x - center_x)
                    
                    # Draw central vein
                    if distance_from_vein < vein_width:
                        color = (30, 30, 30)
                    else:
                        # Create feather barbs
                        if base_pattern == 'w':
                            half_width = size / 2
                            if x < half_width:
                                x_normalized = x / half_width
                            else:
                                x_normalized = (x - half_width) / half_width
                            
                            wave_amplitude = 40
                            wave_offset = math.cos(x_normalized * math.pi * 2) * wave_amplitude * 1.2
                            distance_from_center = abs(x_normalized - 0.5) * 2
                            edge_curve = (distance_from_center ** 2) * wave_amplitude * 1.0
                            total_offset = int(wave_offset + edge_curve)
                            base_y = y + total_offset
                        else:
                            base_y = y
                        
                        # Smearing effect perpendicular to vein
                        smear_intensity = distance_from_vein / (size / 2)
                        y_oscillation = math.sin((y / size) * math.pi * 6) * 25 * smear_intensity
                        
                        adjusted_y = base_y + int(y_oscillation)
                        color = self.get_layer_color_at_position(adjusted_y)
                
                pixels[x, y] = color
        
        try:
            self.original_image = img
            self.pattern_array = np.array(img)
            self.current_pattern_type = 'feather_pattern'
            self.update_pattern()
        except Exception as e:
            print(f"[ERROR] Failed to create feather pattern: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to create feather pattern: {e}")
    
    def create_raindrop_pattern(self, drill_configs):
        """Create a raindrop pattern with multiple drill sizes
        
        REAL-WORLD FORGING PROCESS:
        1. Start with layered billet (horizontal layers)
        2. Drill holes PERPENDICULAR to layers (into top/bottom face)
        3. Forge/hammer flat - this spreads the layers around each hole
        4. Creates concentric circular rings (like tree rings or bullseyes)
        
        IMPORTANT: Drills go into the TOP FACE (perpendicular to layers),
        NOT into the end grain. We're viewing the billet from above.
        
        Args:
            drill_configs: List of dicts with {'size': int, 'pattern': str, 'density': int}
        """
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        import math
        import random
        
        # Start with base layers (horizontal)
        for y in range(size):
            for x in range(size):
                pixels[x, y] = self.get_layer_color_at_position(y)
        
        # Apply raindrop effects - drilling creates concentric rings
        for config in drill_configs:
            drill_size = config['size']
            pattern_type = config['pattern']
            density = config['density']
            
            # Generate drill positions
            positions = []
            if pattern_type == 'random':
                num_drops = density
                random.seed()  # Ensure different pattern each time
                for _ in range(num_drops):
                    positions.append((random.randint(drill_size, size-drill_size), 
                                    random.randint(drill_size, size-drill_size)))
            elif pattern_type == 'grid':
                spacing = max(drill_size * 3, size // int(math.sqrt(density)))
                for gy in range(drill_size, size, spacing):
                    for gx in range(drill_size, size, spacing):
                        positions.append((gx, gy))
            elif pattern_type == 'offset':
                spacing = max(drill_size * 3, size // int(math.sqrt(density)))
                row = 0
                for gy in range(drill_size, size, spacing):
                    offset = (spacing // 2) if row % 2 == 1 else 0
                    for gx in range(offset + drill_size, size, spacing):
                        if gx < size - drill_size:
                            positions.append((gx, gy))
                    row += 1
            
            # Draw concentric rings around each drill position
            # When you drill perpendicular to layers, then forge flat,
            # the layers spread outward creating bullseye/ring patterns
            for (cx, cy) in positions:
                for y in range(max(0, cy - drill_size), min(size, cy + drill_size)):
                    for x in range(max(0, cx - drill_size), min(size, cx + drill_size)):
                        dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                        
                        if dist <= drill_size:
                            # Inside raindrop - show concentric layer rings
                            # The distance from center determines which layer ring we see
                            # This simulates how layers spread radially from the drill hole
                            ring_y_offset = int(dist * 2)  # Convert radial dist to layer depth
                            color = self.get_layer_color_at_position(cy + ring_y_offset)
                            pixels[x, y] = color
        
        try:
            self.original_image = img
            self.pattern_array = np.array(img)
            self.current_pattern_type = 'raindrop_pattern'
            self.update_pattern()
        except Exception as e:
            print(f"[ERROR] Failed to create raindrop pattern: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to create raindrop pattern: {e}")
    
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
        max_width = 0
        total_height = 0
        
        for i, layer in enumerate(layer_data):
            print(f"[DEBUG] Analyzing layer {i}: color={layer.get('color', 'UNKNOWN')}")
            
            if layer['color'] == 'pattern' and 'pattern_image' in layer:
                pattern_img = layer['pattern_image']
                if pattern_img is not None and hasattr(pattern_img, 'shape'):
                    pat_height, pat_width = pattern_img.shape[:2]
                    print(f"[DEBUG] Found pattern layer: {pat_height}x{pat_width}")
                    
                    # Calculate scaled height based on thickness (width stays original)
                    target_height = max(1, self.mm_to_pixels(layer['thickness']))
                    
                    max_width = max(max_width, pat_width)
                    total_height += target_height
                    print(f"[DEBUG] Pattern layer will be scaled to {target_height}x{pat_width}")
                    print(f"[DEBUG] Updated max_width to {max_width}, total_height to {total_height}")
                else:
                    print(f"[ERROR] Pattern layer {i} has invalid or missing pattern_image!")
            else:
                thickness = max(1, self.mm_to_pixels(layer['thickness']))
                total_height += thickness
                print(f"[DEBUG] Added {thickness}px for {layer['color']} layer, total_height now {total_height}")
        
        # Validate and set dimensions
        if total_height == 0:
            print(f"[ERROR] No height calculated from layers! Check layer thickness.")
            messagebox.showerror("Error", "Failed to calculate pattern height. Check layer thickness settings.")
            return
        
        # If no pattern images, use default width (for white/black only stacks)
        if max_width == 0:
            canvas_width = 400
            print(f"[INFO] No pattern images found, using default width: {canvas_width}px")
        else:
            canvas_width = max_width
        
        canvas_height = total_height
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
                    print(f"[DEBUG] Original pattern size: {pat_height}x{pat_width}")
                    
                    # Scale pattern HEIGHT to match specified thickness in mm
                    # Keep original WIDTH to preserve horizontal detail
                    target_height = max(1, self.mm_to_pixels(layer['thickness']))
                    print(f"[DEBUG] Target height for {layer['thickness']}mm: {target_height}px")
                    
                    # Resize pattern height only, keep original width
                    if pat_height != target_height:
                        print(f"[DEBUG] Scaling pattern height: {pat_height} -> {target_height}, keeping width: {pat_width}")
                        
                        # Resize using PIL - height only, preserve width
                        pattern_pil = Image.fromarray(pattern_img)
                        pattern_pil = pattern_pil.resize((pat_width, target_height), Image.Resampling.LANCZOS)
                        pattern_img = np.array(pattern_pil)
                        pat_height, pat_width = pattern_img.shape[:2]
                    
                    # Render the scaled pattern
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
Version 1.3
|
Simulate Damascus steel patterns with:
• Radial twist transformations
• Grind depth and angle control
• Custom layer stacks with pattern images
• Mosaic pattern generation
• W and C pattern presets
• Customizable canvas backgrounds
|
Created for Linux
Inspired by Thor II by Christian Schnura
|
GitHub: github.com/gboyce1967/damascus-pattern-simulator"""
        messagebox.showinfo("About", about_text)
    
    def apply_twist(self, pattern):
        """Apply twist transformation simulating a twisted round bar viewed from the end.
        
        When viewing the end grain of a twisted round bar, the layers create a
        radial/spiral pattern rotating around the center point.
        """
        twist = self.twist_amount.get()
        if twist == 0:
            return pattern
        
        height, width = pattern.shape[:2]
        result = np.zeros_like(pattern)
        
        # Center point
        center_y = height / 2
        center_x = width / 2
        
        # Convert twist amount to radians per unit radius
        twist_rate = twist * 0.05  # Adjust this factor for desired effect
        
        for y in range(height):
            for x in range(width):
                # Calculate distance from center
                dy = y - center_y
                dx = x - center_x
                radius = math.sqrt(dx*dx + dy*dy)
                
                if radius < 0.1:  # Avoid division by zero at center
                    result[y, x] = pattern[y, x]
                    continue
                
                # Calculate angle from center
                angle = math.atan2(dy, dx)
                
                # Apply twist: rotate the sampling angle based on radius
                # Layers further from center are twisted more
                twist_angle = radius * twist_rate
                source_angle = angle - twist_angle
                
                # Convert back to coordinates
                source_x = int(center_x + radius * math.cos(source_angle))
                source_y = int(center_y + radius * math.sin(source_angle))
                
                # Clamp to valid coordinates
                source_x = max(0, min(width - 1, source_x))
                source_y = max(0, min(height - 1, source_y))
                
                result[y, x] = pattern[source_y, source_x]
        
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
    
    def generate_simple_layers_for_export(self):
        """Generate simple alternating layers to show as the base for C and W patterns"""
        # Create simple horizontal alternating layers
        size = 400
        layer_thickness = 20  # Make layers clearly visible
        
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)
        
        y = 0
        layer_index = 0
        while y < size:
            # Alternate between white and black
            if layer_index % 2 == 0:
                color = (220, 220, 220)  # Light gray (represents high-nickel steel)
            else:
                color = (40, 40, 40)  # Dark gray (represents high-carbon steel)
            
            next_y = min(y + layer_thickness, size)
            draw.rectangle([0, y, size, next_y], fill=color)
            
            y = next_y
            layer_index += 1
        
        return np.array(img)
    
    def generate_c_pattern_for_export(self):
        """Generate C pattern to show as intermediate step for W pattern export"""
        import math
        size = 400
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        wave_amplitude = 40
        
        for y in range(size):
            for x in range(size):
                x_normalized = x / size
                wave_offset = math.cos(x_normalized * math.pi * 2) * wave_amplitude * 1.2
                distance_from_center = abs(x_normalized - 0.5) * 2
                edge_curve = (distance_from_center ** 2) * wave_amplitude * 1.0
                total_offset = int(wave_offset + edge_curve)
                distorted_y = y + total_offset
                
                # Use simple layer colors for export
                layer_thickness = 20
                layer_index = (distorted_y // layer_thickness) % 2
                if layer_index == 0:
                    color = (220, 220, 220)
                else:
                    color = (40, 40, 40)
                
                pixels[x, y] = color
        
        return np.array(img)
    
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
        
        # Don't update background on every pattern change - only when canvas resizes
        # This prevents flickering when sliders are moved
        
        if self.pattern_array is None:
            self.debug_print("No pattern_array to update")
            return
        
        try:
            # Record transformation steps for undo and export
            self.transformation_steps = []
            
            # For C and W patterns, show the simple layers first
            # These patterns are transformations of simple layers, not base patterns
            if self.current_pattern_type in ['c_pattern', 'w_pattern']:
                # Generate simple alternating layers to show the true base
                simple_layers = self.generate_simple_layers_for_export()
                
                if self.current_pattern_type == 'c_pattern':
                    self.transformation_steps.append(("1. Simple Alternating Layers (Base)", simple_layers))
                    self.transformation_steps.append(("2. After C Pattern (Bias Compression)", self.pattern_array.copy()))
                    step_offset = 2  # Next steps start at 3
                else:  # w_pattern
                    # W pattern needs to show: Simple → C → W progression
                    self.transformation_steps.append(("1. Simple Alternating Layers (Base)", simple_layers))
                    
                    # Generate C pattern as intermediate step
                    c_pattern = self.generate_c_pattern_for_export()
                    self.transformation_steps.append(("2. After C Pattern (Bias Compression)", c_pattern))
                    
                    self.transformation_steps.append(("3. After W Pattern (Two C Patterns Side by Side)", self.pattern_array.copy()))
                    step_offset = 3  # Next steps start at 4
            else:
                # For other patterns, they are the base
                self.transformation_steps.append(("1. Base Layer Stack", self.pattern_array.copy()))
                step_offset = 1  # Next steps start at 2
            
            # Start with base pattern
            result = self.pattern_array.copy()
            self.debug_print(f"Base pattern: {result.shape}")
            
            # Apply rotation first
            rotation = self.rotation_angle.get()
            if rotation != 0:
                self.debug_print(f"Applying rotation: {rotation}°")
                k = rotation // 90  # Number of 90-degree rotations
                result = np.rot90(result, k=k)
                self.transformation_steps.append((f"{step_offset + 1}. After Rotation ({rotation}°)", result.copy()))
            
            # Apply mosaic
            mosaic_val = self.mosaic_size.get()
            if mosaic_val > 1:
                self.debug_print(f"Applying mosaic: {mosaic_val}x{mosaic_val}")
                result = self.apply_mosaic(result)
                self.transformation_steps.append((f"{step_offset + 2}. After Mosaic ({mosaic_val}×{mosaic_val})", result.copy()))
            else:
                result = self.apply_mosaic(result)
            
            # Apply twist
            twist_val = self.twist_amount.get()
            self.debug_print(f"Twist value retrieved: {twist_val}")
            if twist_val > 0:
                self.debug_print(f"Applying twist: {twist_val}")
                result = self.apply_twist(result)
                self.transformation_steps.append((f"{step_offset + 3}. After Twist ({twist_val})", result.copy()))
            else:
                result = self.apply_twist(result)
            
            # Apply grind
            grind_val = self.grind_depth.get()
            grind_angle_val = self.grind_angle.get()
            self.debug_print(f"Grind values retrieved: depth={grind_val}, angle={grind_angle_val}")
            if grind_val > 0:
                self.debug_print(f"Applying grind: {grind_val}% at {grind_angle_val}°")
                result = self.apply_grind(result)
                self.transformation_steps.append((f"{step_offset + 4}. After Grind ({grind_val}%, {grind_angle_val}°)", result.copy()))
            else:
                result = self.apply_grind(result)
            
            # Convert to PIL Image
            img = Image.fromarray(result)
            
            # Get actual pattern dimensions
            pattern_width, pattern_height = img.size
            self.debug_print(f"Final pattern size: {pattern_width}x{pattern_height}")
            
            # Calculate scale to fit in canvas
            scale_w = (self.canvas_width - 20) / pattern_width
            scale_h = (self.canvas_height - 20) / pattern_height
            
            # For very wide/thin patterns (aspect ratio > 4:1), scale differently
            # to show more detail
            aspect_ratio = pattern_width / max(pattern_height, 1)
            
            if aspect_ratio > 4.0:
                # Wide/thin pattern - scale up to show more vertical detail
                # Use height-based scaling, allowing significant zoom
                target_display_height = min(600, self.canvas_height - 20)
                scale = target_display_height / pattern_height
                # Cap maximum zoom to avoid excessive pixelation
                scale = min(scale, 20.0)
            else:
                # Normal pattern - scale to fit both dimensions
                scale = min(scale_w, scale_h, 1.0)  # Don't scale up, only down
            
            if scale < 1.0:
                # Scale down to fit
                new_width = int(pattern_width * scale)
                new_height = int(pattern_height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Composite pattern over tiled background if available
            if self.canvas_bg_image:
                # Create tiled background
                final_width, final_height = img.size
                bg = Image.new('RGB', (final_width, final_height), self.colors['canvas_bg'])
                
                # Tile the background image
                bg_width, bg_height = self.canvas_bg_image.size
                for y_offset in range(0, final_height, bg_height):
                    for x_offset in range(0, final_width, bg_width):
                        bg.paste(self.canvas_bg_image, (x_offset, y_offset))
                
                # Convert pattern to RGBA for transparency
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Composite pattern over background
                bg.paste(img, (0, 0), img)
                img = bg
            
            # Convert to PhotoImage
            self.display_image = ImageTk.PhotoImage(img)
            
            # Display on canvas centered
            # Delete only the pattern, not the background
            self.canvas.delete("pattern")
            x = (self.canvas_width - img.width) // 2
            y = (self.canvas_height - img.height) // 2
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.display_image, tags="pattern")
            # Keep pattern above background
            self.canvas.tag_raise("pattern")
            self.debug_print(f"Canvas updated at position ({x}, {y})")
            
        except Exception as e:
            self.debug_print(f"ERROR in update_pattern: {e}")
            print(f"Error updating pattern: {e}")
    
    def undo_last_step(self):
        """Undo the last transformation step"""
        # Determine what to undo based on current settings
        # Order: grind > twist > mosaic > rotation
        
        if self.grind_depth.get() > 0:
            # Undo grind
            self.grind_depth.set(0)
            self.grind_angle.set(0)
            self.update_pattern()
            print("[INFO] Undid grind transformation")
        elif self.twist_amount.get() > 0:
            # Undo twist
            self.twist_amount.set(0)
            self.update_pattern()
            print("[INFO] Undid twist transformation")
        elif self.mosaic_size.get() > 1:
            # Undo mosaic
            self.mosaic_size.set(1)
            self.update_pattern()
            print("[INFO] Undid mosaic transformation")
        elif self.rotation_angle.get() != 0:
            # Undo rotation
            self.rotation_angle.set(0)
            self.update_pattern()
            print("[INFO] Undid rotation transformation")
        else:
            messagebox.showinfo("Info", "No transformations to undo. Pattern is at base state.")
    
    def export_steps(self):
        """Export transformation steps as a PDF showing the forging progression
        
        Creates a multi-page PDF document:
        - Page 1: Introductory page with ALL forging steps properly numbered
          - Organized by transformation type (C pattern, W pattern, etc.)
          - Clear step-by-step instructions matching real-world forging
        - Subsequent pages: Visual progression showing pattern at each stage
          - Just titles and pattern images (no duplicate instructions)
        
        IMPORTANT NOTES:
        - C and W patterns show simple layers as the true base
        - Instructions accurately reflect real forging (vertical stacking for W)
        - Works for any pattern combination the user creates
        """
        if not self.transformation_steps or len(self.transformation_steps) == 0:
            messagebox.showwarning("Warning", "No transformation steps to export. Apply some transformations first.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Transformation Steps",
            initialdir=self.default_save_dir,
            defaultextension=".pdf",
            initialfile="damascus_steps.pdf",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                from PIL import ImageDraw, ImageFont
                import textwrap
                
                # Create a list to hold all the step images
                pdf_images = []
                
                # Define step descriptions
                step_descriptions = {
                    "base_to_C": ["Forge weld the alternating layers together under heat and pressure to create a solid billet.", 
                                   "Compress the welded billet on a 45° bias. The compression causes edges to fold inward, creating C-shaped curves."],
                    "C_to_W": ["Draw out (stretch) the C-pattern billet to desired length.",
                               "Clean the surface, cut into pieces, and restack them vertically (on top of each other).",
                               "Forge weld the restacked C-pattern pieces together. The repeating stacked C curves create the W wave pattern."],
                    "to_Rotation": ["Rotate the billet to the desired orientation. This changes how the pattern will appear when the blade is ground."],
                    "to_Mosaic": ["Cut the billet into equal pieces and arrange them in a grid pattern.", "Forge weld the pieces together to create a mosaic effect."],
                    "to_Twist": ["Heat the billet and twist it along its length. The twisting distorts the layers, creating a spiral pattern."],
                    "to_Grind": ["Grind the billet from the side to reveal the cross-section of the layers. The grind depth and angle determine how much of the pattern is exposed."],
                }
                
                # Create introductory page with all forging steps
                intro_page = Image.new('RGB', (1600, 2000), 'white')
                draw = ImageDraw.Draw(intro_page)
                
                try:
                    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                    heading_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
                    step_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
                except:
                    title_font = ImageFont.load_default()
                    heading_font = ImageFont.load_default()
                    step_font = ImageFont.load_default()
                
                # Title
                draw.text((50, 40), "Damascus Pattern Forging Process", fill='black', font=title_font)
                
                # Collect all steps in order
                y_pos = 120
                step_num = 1
                
                for i, (step_name, _) in enumerate(self.transformation_steps[:-1]):
                    next_step_name = self.transformation_steps[i + 1][0]
                    
                    # Determine transition
                    transition_key = None
                    transition_title = None
                    
                    if "Simple" in step_name and "C Pattern" in next_step_name:
                        transition_key = "base_to_C"
                        transition_title = "Creating C Pattern from Simple Layers:"
                    elif "C Pattern" in step_name and "W Pattern" in next_step_name:
                        transition_key = "C_to_W"
                        transition_title = "Creating W Pattern from C Pattern:"
                    elif "Rotation" in next_step_name:
                        transition_key = "to_Rotation"
                        transition_title = "Rotation:"
                    elif "Mosaic" in next_step_name:
                        transition_key = "to_Mosaic"
                        transition_title = "Mosaic:"
                    elif "Twist" in next_step_name:
                        transition_key = "to_Twist"
                        transition_title = "Twist:"
                    elif "Grind" in next_step_name:
                        transition_key = "to_Grind"
                        transition_title = "Grinding:"
                    
                    if transition_key and transition_title:
                        # Draw section heading
                        draw.text((50, y_pos), transition_title, fill='#000080', font=heading_font)
                        y_pos += 50
                        
                        # Draw steps
                        for step_text in step_descriptions[transition_key]:
                            draw.text((80, y_pos), f"Step {step_num}: {step_text}", fill='black', font=step_font)
                            y_pos += 40
                            step_num += 1
                        
                        y_pos += 30  # Extra space between sections
                
                pdf_images.append(intro_page)
                
                for i, (step_name, pattern_array) in enumerate(self.transformation_steps):
                    # Convert pattern to PIL Image
                    step_img = Image.fromarray(pattern_array)
                    
                    # Scale image to reasonable size for PDF
                    # Use narrower width to ensure text has room
                    max_width = 1400
                    if step_img.width > max_width:
                        scale = max_width / step_img.width
                        new_size = (max_width, int(step_img.height * scale))
                        step_img = step_img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # More space for title and description
                    title_height = 150
                    # Make canvas wider than image to accommodate long text
                    canvas_width = max(step_img.width, 1600)
                    final_img = Image.new('RGB', (canvas_width, step_img.height + title_height), 'white')
                    
                    # Add title and description text
                    draw = ImageDraw.Draw(final_img)
                    try:
                        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                        desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
                    except:
                        title_font = ImageFont.load_default()
                        desc_font = ImageFont.load_default()
                    
                    # Draw the step name centered
                    text_bbox = draw.textbbox((0, 0), step_name, font=title_font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_x = (final_img.width - text_width) // 2
                    draw.text((text_x, 60), step_name, fill='black', font=title_font)
                    
                    # Paste the pattern image below the title/description (centered)
                    img_x = (canvas_width - step_img.width) // 2
                    final_img.paste(step_img, (img_x, title_height))
                    
                    pdf_images.append(final_img)
                
                # Save all images as a multi-page PDF
                if pdf_images:
                    pdf_images[0].save(
                        filename, 
                        "PDF", 
                        resolution=300.0, 
                        save_all=True, 
                        append_images=pdf_images[1:] if len(pdf_images) > 1 else []
                    )
                    messagebox.showinfo("Success", 
                        f"Transformation steps exported to:\n{filename}\n\n"
                        f"{len(pdf_images)} steps included in PDF.")
                else:
                    messagebox.showwarning("Warning", "No transformation steps to export.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export steps: {e}")
                import traceback
                traceback.print_exc()
    
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
                # Save the TRANSFORMED pattern (what user sees on screen)
                result = self.pattern_array.copy()
                
                # Apply rotation first
                rotation = self.rotation_angle.get()
                if rotation != 0:
                    k = rotation // 90
                    result = np.rot90(result, k=k)
                
                # Apply mosaic
                result = self.apply_mosaic(result)
                
                # Apply twist and grind
                result = self.apply_twist(result)
                result = self.apply_grind(result)
                
                img = Image.fromarray(result)
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
        
        # Auto-select all text in the spinbox for easy editing
        thickness_spinbox.selection_range(0, tk.END)
        thickness_spinbox.focus_set()
        
        # Buttons
        def save_changes(event=None):
            new_thickness = thickness_var.get()
            if new_thickness <= 0:
                messagebox.showwarning("Invalid Thickness", "Thickness must be greater than 0")
                return
            
            # Preserve pattern_image and pattern_name if this is a pattern layer
            old_layer = self.layers[idx]
            new_layer = {'color': color_var.get(), 'thickness': new_thickness}
            
            if 'pattern_image' in old_layer:
                new_layer['pattern_image'] = old_layer['pattern_image']
            if 'pattern_name' in old_layer:
                new_layer['pattern_name'] = old_layer['pattern_name']
            
            self.layers[idx] = new_layer
            self.update_listbox()
            self.layer_listbox.selection_set(idx)
            edit_dialog.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Bind Enter key to save changes
        thickness_spinbox.bind('<Return>', save_changes)
        edit_dialog.bind('<Return>', save_changes)
        
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
                
                # Add as a special "pattern" type layer with default thickness
                self.layers.append({
                    'color': 'pattern',
                    'thickness': 1.0,
                    'pattern_image': pattern_array,
                    'pattern_name': pattern_name
                })
                
                self.pattern_images.append(pattern_array)
                self.update_listbox()
                
                # Auto-select the newly added layer for quick editing
                self.layer_listbox.selection_clear(0, tk.END)
                self.layer_listbox.selection_set(len(self.layers) - 1)
                self.layer_listbox.see(len(self.layers) - 1)
                
                # Immediately open edit dialog to set thickness
                messagebox.showinfo("Set Thickness", 
                    f"Pattern '{pattern_name}' added!\n\n"
                    "Opening editor to set layer thickness...")
                self.edit_layer()
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

class FeatherBuilderDialog:
    """Dialog for building feather damascus patterns"""
    def __init__(self, parent, simulator):
        self.simulator = simulator
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Feather Pattern Builder")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Feather Damascus Pattern Builder",
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        ttk.Label(main_frame, text="Create feather patterns by splitting a base pattern with a wedge",
                 font=('Arial', 9)).pack(pady=(0, 20))
        
        # Base pattern selection
        base_frame = ttk.LabelFrame(main_frame, text="Base Pattern", padding=15)
        base_frame.pack(fill=tk.X, pady=10)
        
        self.base_pattern = tk.StringVar(value="w")
        ttk.Radiobutton(base_frame, text="W Pattern (more intricate)", 
                       variable=self.base_pattern, value="w").pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(base_frame, text="Simple Layers (less intricate)", 
                       variable=self.base_pattern, value="simple").pack(anchor=tk.W, pady=5)
        
        # Split direction
        dir_frame = ttk.LabelFrame(main_frame, text="Split Direction", padding=15)
        dir_frame.pack(fill=tk.X, pady=10)
        
        self.split_direction = tk.StringVar(value="width")
        ttk.Radiobutton(dir_frame, text="Across Width (horizontal vein)", 
                       variable=self.split_direction, value="width").pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(dir_frame, text="Across Length (vertical vein)", 
                       variable=self.split_direction, value="length").pack(anchor=tk.W, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Generate Feather Pattern",
                  command=self.generate_pattern).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="Cancel",
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    def generate_pattern(self):
        """Generate the feather pattern"""
        base = self.base_pattern.get()
        direction = self.split_direction.get()
        
        self.simulator.create_feather_pattern(base_pattern=base, split_direction=direction)
        self.dialog.destroy()
        messagebox.showinfo("Success", f"Created feather pattern from {base} base")

class RaindropBuilderDialog:
    """Dialog for building raindrop damascus patterns"""
    def __init__(self, parent, simulator):
        self.simulator = simulator
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Raindrop Pattern Builder")
        self.dialog.geometry("600x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Store drill configurations
        self.drill_configs = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Raindrop Damascus Pattern Builder",
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        ttk.Label(main_frame, text="Create raindrop patterns with multiple drill bit sizes",
                 font=('Arial', 9)).pack(pady=(0, 20))
        
        # Number of drill sizes
        size_frame = ttk.LabelFrame(main_frame, text="Number of Drill Sizes", padding=15)
        size_frame.pack(fill=tk.X, pady=10)
        
        self.num_sizes = tk.IntVar(value=2)
        ttk.Label(size_frame, text="How many different drill bit sizes:").pack(anchor=tk.W)
        size_spinbox = ttk.Spinbox(size_frame, from_=1, to=4, textvariable=self.num_sizes,
                                   width=10, command=self.update_config_sections)
        size_spinbox.pack(anchor=tk.W, pady=5)
        
        # Scrollable frame for drill configurations
        config_container = ttk.Frame(main_frame)
        config_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(config_container, height=250)
        scrollbar = ttk.Scrollbar(config_container, orient="vertical", command=canvas.yview)
        self.config_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=self.config_frame, anchor="nw")
        
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.config_frame.bind("<Configure>", _on_frame_configure)
        
        # Store widgets for each config
        self.config_widgets = []
        
        # Initial configuration sections
        self.update_config_sections()
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Generate Raindrop Pattern",
                  command=self.generate_pattern).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="Cancel",
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    def update_config_sections(self, *args):
        """Update the configuration sections based on number of drill sizes"""
        # Clear existing widgets
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        self.config_widgets.clear()
        
        num_sizes = self.num_sizes.get()
        
        for i in range(num_sizes):
            # Create a frame for each drill size config
            frame = ttk.LabelFrame(self.config_frame, text=f"Drill Size {i+1}", padding=10)
            frame.pack(fill=tk.X, pady=5)
            
            # Drill size (radius)
            size_var = tk.IntVar(value=15 - (i * 3))
            ttk.Label(frame, text="Drill Radius (pixels):").grid(row=0, column=0, sticky=tk.W, pady=3)
            ttk.Spinbox(frame, from_=5, to=30, textvariable=size_var, width=10).grid(row=0, column=1, padx=10, pady=3)
            
            # Pattern type
            pattern_var = tk.StringVar(value="random")
            ttk.Label(frame, text="Pattern Type:").grid(row=1, column=0, sticky=tk.W, pady=3)
            pattern_combo = ttk.Combobox(frame, textvariable=pattern_var, 
                                        values=["random", "grid", "offset"], 
                                        state="readonly", width=15)
            pattern_combo.grid(row=1, column=1, padx=10, pady=3)
            
            # Density
            density_var = tk.IntVar(value=30 - (i * 5))
            ttk.Label(frame, text="Density:").grid(row=2, column=0, sticky=tk.W, pady=3)
            ttk.Spinbox(frame, from_=5, to=100, textvariable=density_var, width=10).grid(row=2, column=1, padx=10, pady=3)
            
            self.config_widgets.append({
                'size': size_var,
                'pattern': pattern_var,
                'density': density_var
            })
    
    def generate_pattern(self):
        """Generate the raindrop pattern"""
        # Collect all drill configurations
        drill_configs = []
        for widgets in self.config_widgets:
            drill_configs.append({
                'size': widgets['size'].get(),
                'pattern': widgets['pattern'].get(),
                'density': widgets['density'].get()
            })
        
        if not drill_configs:
            messagebox.showwarning("No Configuration", "Please configure at least one drill size")
            return
        
        self.simulator.create_raindrop_pattern(drill_configs)
        self.dialog.destroy()
        messagebox.showinfo("Success", f"Created raindrop pattern with {len(drill_configs)} drill sizes")

def main():
    try:
        root = tk.Tk()
        app = DamascusSimulator(root)
        
        # Prevent accidental closure
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    except Exception as e:
        print(f"[ERROR] Application crashed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
