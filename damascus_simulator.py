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
        self.root.geometry("1200x900")
        
        # Image variables
        self.original_image = None
        self.display_image = None
        self.pattern_array = None
        self.canvas_width = 800
        self.canvas_height = 600
        
        # Pattern parameters
        self.twist_amount = tk.DoubleVar(value=0.0)
        self.grind_depth = tk.DoubleVar(value=0.0)
        self.mosaic_size = tk.IntVar(value=1)
        self.white_layer_thickness = tk.DoubleVar(value=1.0)  # in mm
        self.black_layer_thickness = tk.DoubleVar(value=1.0)  # in mm
        self.unit_system = tk.StringVar(value="metric")  # metric or imperial
        self.pixels_per_mm = 10  # Scale factor for visualization
        self.current_pattern_type = None  # Track which pattern is active
        self.custom_layer_stack = None  # Store custom layer stack for W/C patterns
        
        self.setup_ui()
        self.load_default_pattern()
        
    def setup_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Canvas
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas for image display
        self.canvas = tk.Canvas(left_frame, width=self.canvas_width, height=self.canvas_height, 
                               bg='gray20', highlightthickness=1, highlightbackground='gray50')
        self.canvas.pack(padx=5, pady=5)
        
        # Right panel - Controls with scrollbar
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        right_frame.pack_propagate(False)
        
        # Create canvas and scrollbar for right panel
        canvas = tk.Canvas(right_frame, width=285)
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
        
        # Title
        title = ttk.Label(right_frame, text="Damascus Simulator", 
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)
        
        # File operations
        file_frame = ttk.LabelFrame(right_frame, text="File Operations", padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_frame, text="Load Pattern", 
                  command=self.load_pattern).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Load Default", 
                  command=self.load_default_pattern).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Export Pattern", 
                  command=self.save_pattern).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Print Pattern", 
                  command=self.print_pattern).pack(fill=tk.X, pady=2)
        
        # Pattern controls
        controls_frame = ttk.LabelFrame(right_frame, text="Pattern Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=5)
        
        # Twist amount
        ttk.Label(controls_frame, text="Twist Amount:").pack(anchor=tk.W)
        twist_scale = ttk.Scale(controls_frame, from_=0, to=10, 
                               variable=self.twist_amount, 
                               command=self.update_pattern)
        twist_scale.pack(fill=tk.X, pady=5)
        ttk.Label(controls_frame, textvariable=self.twist_amount, 
                 font=('Arial', 8)).pack(anchor=tk.E)
        
        # Grind depth
        ttk.Label(controls_frame, text="Grind Depth:").pack(anchor=tk.W, pady=(10,0))
        grind_scale = ttk.Scale(controls_frame, from_=0, to=100, 
                               variable=self.grind_depth, 
                               command=self.update_pattern)
        grind_scale.pack(fill=tk.X, pady=5)
        ttk.Label(controls_frame, textvariable=self.grind_depth, 
                 font=('Arial', 8)).pack(anchor=tk.E)
        
        # Layer thickness controls
        layer_frame = ttk.LabelFrame(right_frame, text="Layer Thickness", padding=10)
        layer_frame.pack(fill=tk.X, pady=5)
        
        # Unit selection
        unit_frame = ttk.Frame(layer_frame)
        unit_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(unit_frame, text="Units:").pack(side=tk.LEFT)
        ttk.Radiobutton(unit_frame, text="mm", variable=self.unit_system, 
                       value="metric", command=self.update_unit_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(unit_frame, text="inches", variable=self.unit_system, 
                       value="imperial", command=self.update_unit_display).pack(side=tk.LEFT, padx=5)
        
        # White layer thickness
        self.white_label = ttk.Label(layer_frame, text="White Layer (mm):")
        self.white_label.pack(anchor=tk.W)
        white_scale = ttk.Scale(layer_frame, from_=0.1, to=5.0, 
                               variable=self.white_layer_thickness, 
                               command=self.on_layer_change)
        white_scale.pack(fill=tk.X, pady=5)
        self.white_value_label = ttk.Label(layer_frame, text="1.0 mm", font=('Arial', 8))
        self.white_value_label.pack(anchor=tk.E)
        
        # Black layer thickness
        self.black_label = ttk.Label(layer_frame, text="Black Layer (mm):")
        self.black_label.pack(anchor=tk.W, pady=(10,0))
        black_scale = ttk.Scale(layer_frame, from_=0.1, to=5.0, 
                               variable=self.black_layer_thickness, 
                               command=self.on_layer_change)
        black_scale.pack(fill=tk.X, pady=5)
        self.black_value_label = ttk.Label(layer_frame, text="1.0 mm", font=('Arial', 8))
        self.black_value_label.pack(anchor=tk.E)
        
        # Mosaic controls
        mosaic_frame = ttk.LabelFrame(right_frame, text="Mosaic Stacking", padding=10)
        mosaic_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mosaic_frame, text="Mosaic Size:").pack(anchor=tk.W)
        mosaic_options = ttk.Frame(mosaic_frame)
        mosaic_options.pack(fill=tk.X, pady=5)
        
        for i, size in enumerate([1, 2, 3]):
            ttk.Radiobutton(mosaic_options, text=f"{size}x{size}", 
                          variable=self.mosaic_size, value=size,
                          command=self.update_pattern).pack(side=tk.LEFT, padx=5)
        
        # Preset patterns
        preset_frame = ttk.LabelFrame(right_frame, text="Preset Patterns", padding=10)
        preset_frame.pack(fill=tk.X, pady=5)
        
        presets = [
            ("Simple Layers", self.create_simple_layers),
            ("Checkerboard", self.create_checkerboard),
            ("Random Pattern", self.create_random_pattern),
            ("W Pattern", lambda: self.create_w_pattern(use_custom_stack=False)),
            ("C Pattern", lambda: self.create_c_pattern(use_custom_stack=False)),
            ("Custom Layers...", self.open_custom_layer_builder),
        ]
        
        for name, func in presets:
            ttk.Button(preset_frame, text=name, 
                      command=func).pack(fill=tk.X, pady=2)
        
        # Reset button
        ttk.Button(right_frame, text="Reset All", 
                  command=self.reset_controls).pack(fill=tk.X, pady=10)
        
        # Info
        info_frame = ttk.LabelFrame(right_frame, text="Info", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        info_text = """Damascus Pattern Simulator

Load a pattern image representing 
the end grain of a Damascus billet.

Twist: Simulates twisting the billet
Grind: Shows pattern at depth
Layers: Adjust thickness of layers
Mosaic: Creates tiled arrangements
W/C: Special patterns

Created for Linux
Inspired by Thor II"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                 font=('Arial', 8)).pack()
    
    def load_pattern(self):
        """Load a pattern image from file"""
        filename = filedialog.askopenfilename(
            title="Select Pattern Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                self.original_image = Image.open(filename).convert('RGB')
                self.pattern_array = np.array(self.original_image)
                self.update_pattern()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
    
    def load_default_pattern(self):
        """Load a default pattern"""
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
            self.white_value_label.config(text=f"{self.white_layer_thickness.get():.2f} mm")
            self.black_value_label.config(text=f"{self.black_layer_thickness.get():.2f} mm")
        else:
            self.white_label.config(text="White Layer (in):")
            self.black_label.config(text="Black Layer (in):")
            white_inches = self.mm_to_inches(self.white_layer_thickness.get())
            black_inches = self.mm_to_inches(self.black_layer_thickness.get())
            self.white_value_label.config(text=f"{white_inches:.3f} in")
            self.black_value_label.config(text=f"{black_inches:.3f} in")
    
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
        self.reset_controls()
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
        self.reset_controls()
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
    
    def create_custom_layers(self, layer_data):
        """Create pattern from custom layer data"""
        size = 400
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)
        
        # Store the custom layer stack
        self.custom_layer_stack = layer_data.copy()
        
        # Draw layers from bottom to top, repeating to fill the canvas
        y = 0
        while y < size:
            for layer in layer_data:
                color = (200, 200, 200) if layer['color'] == 'white' else (50, 50, 50)
                thickness = max(1, self.mm_to_pixels(layer['thickness']))
                
                # Draw the layer
                y_end = min(y + thickness, size)
                draw.rectangle([0, y, size, y_end], fill=color)
                y += thickness
                
                # Stop if we've filled the canvas
                if y >= size:
                    break
        
        self.original_image = img
        self.pattern_array = np.array(img)
        self.current_pattern_type = 'custom'
        self.update_pattern()
    
    def reset_controls(self):
        """Reset all control values"""
        self.twist_amount.set(0.0)
        self.grind_depth.set(0.0)
        self.mosaic_size.set(1)
        self.white_layer_thickness.set(1.0)
        self.black_layer_thickness.set(1.0)
        self.update_unit_display()
        self.update_pattern()
    
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
        """Simulate grinding depth"""
        grind = self.grind_depth.get()
        if grind == 0:
            return pattern
        
        height, width = pattern.shape[:2]
        result = pattern.copy()
        
        # Simulate depth by shifting pattern
        shift_amount = int((grind / 100) * height * 0.3)
        
        if shift_amount > 0:
            result = np.roll(result, shift_amount, axis=0)
        
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
        if self.pattern_array is None:
            return
        
        try:
            # Start with mosaic (applies to base pattern)
            result = self.apply_mosaic(self.pattern_array.copy())
            
            # Apply transformations in order
            result = self.apply_twist(result)
            result = self.apply_grind(result)
            
            # Convert to PIL Image
            img = Image.fromarray(result)
            
            # Resize to fit canvas while maintaining aspect ratio
            img.thumbnail((self.canvas_width - 10, self.canvas_height - 10), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.display_image = ImageTk.PhotoImage(img)
            
            # Display on canvas
            self.canvas.delete("all")
            x = (self.canvas_width - img.width) // 2
            y = (self.canvas_height - img.height) // 2
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.display_image)
            
        except Exception as e:
            print(f"Error updating pattern: {e}")
    
    def save_pattern(self):
        """Save the current pattern to file"""
        if self.display_image is None:
            messagebox.showwarning("Warning", "No pattern to save!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Pattern",
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
    
    def print_pattern(self):
        """Print the current pattern using native print dialog"""
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
        self.dialog.geometry("600x850")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.layers = []  # List of {color: 'white'/'black', thickness: float}
        
        self.setup_ui()
        
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
        ttk.Button(action_frame, text="Generate Pattern", 
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
        
        # Save/Load pattern buttons
        save_frame = ttk.LabelFrame(main_frame, text="Pattern Management", padding=10)
        save_frame.pack(fill=tk.X, pady=5)
        ttk.Button(save_frame, text="Save Layer Stack", 
                  command=self.save_layer_stack).pack(fill=tk.X, pady=2)
        ttk.Button(save_frame, text="Load Layer Stack", 
                  command=self.load_layer_stack).pack(fill=tk.X, pady=2)
        
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
                with open(filename, 'w') as f:
                    json.dump(self.layers, f, indent=2)
                messagebox.showinfo("Success", f"Layer stack saved to {filename}")
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
                
                for layer in loaded_layers:
                    if not isinstance(layer, dict) or 'color' not in layer or 'thickness' not in layer:
                        raise ValueError("Invalid layer format")
                    if layer['color'] not in ['white', 'black']:
                        raise ValueError("Invalid layer color")
                    if not isinstance(layer['thickness'], (int, float)) or layer['thickness'] <= 0:
                        raise ValueError("Invalid layer thickness")
                
                self.layers = loaded_layers
                self.update_listbox()
                messagebox.showinfo("Success", f"Loaded {len(self.layers)} layers")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load layer stack: {e}")

def main():
    root = tk.Tk()
    app = DamascusSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
