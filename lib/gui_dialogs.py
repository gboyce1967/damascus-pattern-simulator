"""
GUI Dialogs for Damascus Pattern Simulator
============================================

Standalone dialog functions that can be called from any Tkinter application.
Each function accepts the necessary state rather than relying on a class.

Usage:
    from lib.gui_dialogs import show_debug_console, show_billet_stats, show_about
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging

from lib.logging_config import logger, LOGS_DIR
from lib.tk_log_handler import TkTextLogHandler


def show_debug_console(root, existing_window=None, existing_handler=None):
    """
    Show a live debug console window that streams logger output.

    Args:
        root: Tkinter root window
        existing_window: If a console is already open, pass it to raise it
        existing_handler: Existing TkTextLogHandler to remove before creating new

    Returns:
        tuple: (console_window, console_text_widget, log_handler)
    """
    if existing_window and existing_window.winfo_exists():
        existing_window.lift()
        existing_window.focus_force()
        logger.info("Debug console already open")
        return existing_window, None, existing_handler

    logger.info("Opening debug console window")
    console = tk.Toplevel(root)
    console.title("Debug Console (Live)")
    console.geometry("1000x700")

    text_area = scrolledtext.ScrolledText(
        console,
        wrap=tk.WORD,
        bg='#1e1e1e',
        fg='#00ff00',
        font=('Courier', 9)
    )
    text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Preload the latest log file so context is visible immediately
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_files = sorted(LOGS_DIR.glob('damascus_3d_debug_*.log'), reverse=True)
    logger.debug(f"Found {len(log_files)} debug log files")
    if log_files:
        logger.debug(f"Loading most recent log: {log_files[0]}")
        with open(log_files[0], 'r', encoding='utf-8', errors='replace') as f:
            tail_lines = f.readlines()[-3000:]
            text_area.insert(tk.END, ''.join(tail_lines))
        text_area.see(tk.END)
    else:
        text_area.insert(tk.END, "No debug log available yet.\n")

    text_area.config(state=tk.DISABLED)

    # Remove existing handler if any
    if existing_handler is not None:
        logger.removeHandler(existing_handler)
        existing_handler.close()

    # Attach a live log stream for everything (DEBUG+)
    handler = TkTextLogHandler(root, text_area)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return console, text_area, handler


def show_billet_stats(root, billet, operation_history):
    """
    Show detailed billet statistics in a new window.

    Args:
        root: Tkinter root window
        billet: Damascus3DBillet instance
        operation_history: List of operation description strings
    """
    if billet is None:
        logger.warning("Show stats attempted with no billet")
        messagebox.showwarning("No Billet", "Please create a billet first")
        return

    logger.info("Displaying billet statistics window")
    stats = billet.get_billet_stats()
    logger.debug(f"Stats: {stats['layer_count']} layers, {stats['total_vertices']} vertices, {stats['operation_count']} ops")

    stats_window = tk.Toplevel(root)
    stats_window.title("Billet Statistics")
    stats_window.geometry("600x500")

    text_area = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD,
                                          font=('Courier', 9))
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    text_area.insert(tk.END, "DAMASCUS BILLET STATISTICS\n")
    text_area.insert(tk.END, "=" * 60 + "\n\n")
    text_area.insert(tk.END, f"Timestamp: {stats['timestamp']}\n\n")
    text_area.insert(tk.END, f"Dimensions:\n")
    text_area.insert(tk.END, f"  Width: {stats['width_mm']:.1f} mm\n")
    text_area.insert(tk.END, f"  Length: {stats['length_mm']:.1f} mm\n")
    text_area.insert(tk.END, f"  Height: {stats['total_height_mm']:.1f} mm\n\n")
    text_area.insert(tk.END, f"Layers: {stats['layer_count']}\n")
    text_area.insert(tk.END, f"Total Vertices: {stats['total_vertices']}\n")
    text_area.insert(tk.END, f"Total Triangles: {stats['total_triangles']}\n")
    text_area.insert(tk.END, f"Operations Applied: {stats['operation_count']}\n\n")

    if operation_history:
        text_area.insert(tk.END, "Operation History:\n")
        for i, op in enumerate(operation_history, 1):
            text_area.insert(tk.END, f"  {i}. {op}\n")

    text_area.config(state=tk.DISABLED)


def show_about(root):
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


def show_quick_start(root):
    """Show Quick Start Guide in a new window."""
    guide = tk.Toplevel(root)
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


def show_build_plate_warning(root, item_label, item_dims, plate_dims):
    """
    Show a build plate size warning dialog with resize/continue/cancel options.

    Args:
        root: Tkinter root window
        item_label: Description of what exceeds (e.g. "Billet", "Forged Bar")
        item_dims: tuple (width, length) of the item in mm
        plate_dims: tuple (width, length) of the build plate in mm

    Returns:
        dict: {'action': 'resize'|'continue'|'cancel', 'new_size': (w, l) or None}
    """
    item_w, item_l = item_dims
    plate_w, plate_l = plate_dims

    dialog = tk.Toplevel(root)
    dialog.title("Build Plate Size Warning")
    dialog.transient(root)
    dialog.grab_set()

    msg_frame = ttk.Frame(dialog, padding=20)
    msg_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(msg_frame, text=f"⚠️ {item_label} Exceeds Build Plate!",
              font=('Arial', 12, 'bold')).pack(pady=(0, 10))
    ttk.Label(msg_frame, text=f"{item_label}: {item_w:.0f}mm × {item_l:.0f}mm").pack()
    ttk.Label(msg_frame, text=f"Build Plate: {plate_w:.0f}mm × {plate_l:.0f}mm").pack(pady=(0, 15))

    ttk.Label(msg_frame, text=f"The {item_label.lower()} will extend beyond the workspace.",
              font=('Arial', 9, 'italic')).pack(pady=(0, 10))

    result = {'action': None, 'new_size': None}

    new_plate_w = max(plate_w, item_w * 1.1)
    new_plate_l = max(plate_l, item_l * 1.1)

    def auto_resize():
        result['action'] = 'resize'
        result['new_size'] = (new_plate_w, new_plate_l)
        dialog.destroy()

    def continue_anyway():
        result['action'] = 'continue'
        dialog.destroy()

    def cancel_operation():
        result['action'] = 'cancel'
        dialog.destroy()

    button_frame = ttk.Frame(dialog, padding=(20, 0, 20, 20))
    button_frame.pack(fill=tk.X)

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

    return result
