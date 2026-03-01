"""
GUI Reference Viewers for Damascus Pattern Simulator
=====================================================

Standalone functions that display reference material (heat treatment guides,
steel properties, forging losses, plasticity data) in Tkinter windows.

Usage:
    from lib.gui_references import show_heat_treatment_guide, show_steel_properties
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import re
import json
import zipfile
import logging

from lib.logging_config import logger

# Lazy import to avoid circular dependency — caller provides db via get_database()
_get_database = None


def _ensure_database():
    """Lazy-load the steel database accessor."""
    global _get_database
    if _get_database is None:
        from data.steel_database import get_database
        _get_database = get_database
    return _get_database()


def show_heat_treatment_guide(root):
    """
    Show comprehensive hardening & tempering guide for all steels.
    Displays data from the steel database in a tabbed, searchable interface.

    Args:
        root: Tkinter root window
    """
    logger.info("Opening Hardening & Tempering Guide")

    guide_window = tk.Toplevel(root)
    guide_window.title("📚 Hardening & Tempering Guide - Damascus Steels")
    guide_window.geometry("1000x800")
    guide_window.transient(root)

    notebook = ttk.Notebook(guide_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    db = _ensure_database()
    steels = db.get_all_steels()
    logger.debug(f"Loaded {len(steels)} steels from database")

    for steel_key, steel in steels.items():
        tab_frame = ttk.Frame(notebook)
        notebook.add(tab_frame, text=steel.name)

        text_widget = scrolledtext.ScrolledText(
            tab_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg='#ffffff',
            fg='#1a1a1a',
            padx=20,
            pady=15,
            spacing1=3,
            spacing2=2,
            spacing3=3
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, steel.get_display_text())
        text_widget.config(state=tk.DISABLED)

    # Search bar
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

        current_tab_idx = notebook.index(notebook.select())
        current_tab = notebook.winfo_children()[current_tab_idx]
        text_widget = current_tab.winfo_children()[0]

        text_widget.tag_remove('highlight', '1.0', tk.END)

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

        text_widget.tag_config('highlight', background='yellow', foreground='black')

        if count > 0:
            text_widget.see('1.0')
            first_match = text_widget.search(query, '1.0', nocase=True)
            if first_match:
                text_widget.see(first_match)
            logger.debug(f"Search: Found {count} matches for '{query}'")
        else:
            logger.debug(f"Search: No matches for '{query}'")
            messagebox.showinfo("Search", f"No matches found for: {query}")

    ttk.Button(search_frame, text="Find", command=search_text).pack(side=tk.LEFT, padx=5)
    search_entry.bind('<Return>', lambda e: search_text())

    logger.info("Heat treatment guide window opened")


def show_steel_properties(root):
    """
    Show steel properties database with option to add custom steels.

    Args:
        root: Tkinter root window
    """
    logger.info("Opening Steel Properties Database")

    db = _ensure_database()

    db_window = tk.Toplevel(root)
    db_window.title("🔬 Steel Properties Database")
    db_window.geometry("900x700")
    db_window.transient(root)

    button_frame = ttk.Frame(db_window)
    button_frame.pack(fill=tk.X, padx=10, pady=10)

    ttk.Button(button_frame, text="➕ Add Custom Steel",
               command=lambda: show_add_custom_steel_dialog(root)).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="🔄 Refresh Database",
               command=lambda: _refresh_steel_list(steel_listbox, db)).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="📧 Submit New Steel",
               command=lambda: _submit_steel_via_email(steel_listbox, db)).pack(side=tk.LEFT, padx=5)

    list_frame = ttk.LabelFrame(db_window, text="Available Steels", padding=10)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

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

    _refresh_steel_list(steel_listbox, db)

    info_label = ttk.Label(
        db_window,
        text=f"Built-in: {len([s for s in db.get_all_steels().values() if not s.is_custom])} | "
             f"Custom: {len([s for s in db.get_all_steels().values() if s.is_custom])} | "
             f"Total: {len(db.get_all_steels())}",
        font=('Arial', 9, 'italic')
    )
    info_label.pack(pady=(0, 10))

    logger.info("Steel properties database window opened")


def _refresh_steel_list(listbox, db):
    """Refresh the steel listbox."""
    listbox.delete(0, tk.END)

    builtin = [(k, s) for k, s in db.get_all_steels().items() if not s.is_custom]
    custom = [(k, s) for k, s in db.get_all_steels().items() if s.is_custom]

    if builtin:
        listbox.insert(tk.END, "═══ BUILT-IN STEELS ═══")
        for key, steel in sorted(builtin, key=lambda x: x[1].name):
            listbox.insert(tk.END, f"  {steel.name} ({steel.category})")

    if custom:
        listbox.insert(tk.END, "")
        listbox.insert(tk.END, "═══ CUSTOM STEELS ═══")
        for key, steel in sorted(custom, key=lambda x: x[1].name):
            listbox.insert(tk.END, f"  ⭐ {steel.name} ({steel.category})")


def _submit_steel_via_email(listbox, db):
    """Export selected custom steel to zip file for email submission."""
    selection = listbox.curselection()
    if not selection:
        messagebox.showwarning("No Selection", "Please select a custom steel to submit")
        return

    selected_text = listbox.get(selection[0])
    if "⭐" not in selected_text:
        messagebox.showinfo("Built-in Steel", "Only custom steels can be submitted")
        return

    for key, steel in db.get_all_steels().items():
        if steel.is_custom and steel.name in selected_text:
            try:
                safe_name = "".join(c for c in steel.name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')
                default_filename = f"steel_submission_{safe_name}.zip"

                filepath = filedialog.askdirectory(
                    title="Choose where to save steel submission",
                    initialdir=os.path.expanduser("~")
                )

                if not filepath:
                    return

                zip_path = os.path.join(filepath, default_filename)

                steel_dict = steel.to_dict()

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    json_data = json.dumps(steel_dict, indent=2)
                    zipf.writestr(f"{safe_name}.json", json_data)

                    markdown = db.export_steel_for_github(steel)
                    zipf.writestr(f"{safe_name}_README.md", markdown)

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


def show_add_custom_steel_dialog(root):
    """
    Show dialog for adding a custom steel to the database.

    Args:
        root: Tkinter root window
    """
    logger.info("Opening Add Custom Steel dialog")

    dialog = tk.Toplevel(root)
    dialog.title("➕ Add Custom Steel")
    dialog.geometry("700x850")
    dialog.transient(root)
    dialog.grab_set()

    canvas = tk.Canvas(dialog)
    scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    entries = {}

    def create_entry(parent, label_text, row, tooltip="", width=40):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, padx=5, pady=3)
        entry = ttk.Entry(parent, width=width)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        if tooltip:
            ttk.Label(parent, text=f"  ℹ️ {tooltip}", font=('Arial', 8, 'italic'),
                      foreground='#666666').grid(row=row + 1, column=1, sticky=tk.W, padx=5)
            return entry, 2
        return entry, 1

    # === BASIC INFO ===
    row = 0
    basic_frame = ttk.LabelFrame(scrollable_frame, text="Basic Information", padding=10)
    basic_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
    basic_frame.columnconfigure(1, weight=1)

    entries['name'], inc = create_entry(basic_frame, "Steel Name *:", 0, "e.g., '1095 High Carbon Steel'")
    row_offset = inc

    ttk.Label(basic_frame, text="Category *:").grid(row=row_offset, column=0, sticky=tk.W, padx=5, pady=3)
    entries['category'] = ttk.Combobox(basic_frame, width=37,
                                       values=["High Carbon", "Low Alloy", "Tool Steel", "Stainless", "Damascus",
                                                "Other"])
    entries['category'].grid(row=row_offset, column=1, sticky=tk.EW, padx=5, pady=3)
    entries['category'].set("High Carbon")

    # === PHYSICAL PROPERTIES ===
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

    # === HEAT TREATMENT ===
    row += 1
    ht_frame = ttk.LabelFrame(scrollable_frame, text="Heat Treatment", padding=10)
    ht_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
    ht_frame.columnconfigure(1, weight=1)

    entries['aust_min'], inc = create_entry(ht_frame, "Austenitizing Min (°F):", 0)
    row_offset = inc
    entries['aust_max'], inc = create_entry(ht_frame, "Austenitizing Max (°F):", row_offset)
    row_offset += inc
    entries['quench'], inc = create_entry(ht_frame, "Quench Method:", row_offset, "e.g., 'Oil', 'Water', 'Air'")
    row_offset += inc

    ttk.Label(ht_frame, text="Tempering Data:", font=('Arial', 9, 'bold')).grid(
        row=row_offset, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 3))
    row_offset += 1
    ttk.Label(ht_frame, text="  Format: temp1,hardness1; temp2,hardness2").grid(
        row=row_offset, column=0, columnspan=2, sticky=tk.W, padx=5, pady=3)
    row_offset += 1
    entries['tempering'] = ttk.Entry(ht_frame, width=40)
    entries['tempering'].grid(row=row_offset, column=1, sticky=tk.EW, padx=5, pady=3)

    # === FORGING ===
    row += 1
    forge_frame = ttk.LabelFrame(scrollable_frame, text="Forging Characteristics", padding=10)
    forge_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
    forge_frame.columnconfigure(1, weight=1)

    entries['forge_min'], inc = create_entry(forge_frame, "Forging Range Min (°F):", 0)
    row_offset = inc
    entries['forge_max'], inc = create_entry(forge_frame, "Forging Range Max (°F):", row_offset)
    row_offset += inc

    ttk.Label(forge_frame, text="Movement Level (1-10):").grid(row=row_offset, column=0, sticky=tk.W, padx=5, pady=3)
    entries['movement'] = ttk.Spinbox(forge_frame, from_=1, to=10, width=38)
    entries['movement'].set(5)
    entries['movement'].grid(row=row_offset, column=1, sticky=tk.EW, padx=5, pady=3)
    row_offset += 1

    entries['scale_min'], inc = create_entry(forge_frame, "Scale Loss Min (%):", row_offset)
    row_offset += inc
    entries['scale_max'], inc = create_entry(forge_frame, "Scale Loss Max (%):", row_offset)
    row_offset += inc
    entries['decarb_min'], inc = create_entry(forge_frame, "Decarb Depth Min (in):", row_offset)
    row_offset += inc
    entries['decarb_max'], inc = create_entry(forge_frame, "Decarb Depth Max (in):", row_offset)

    # === ETCHING ===
    row += 1
    etch_frame = ttk.LabelFrame(scrollable_frame, text="Etching & Appearance", padding=10)
    etch_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
    etch_frame.columnconfigure(1, weight=1)

    ttk.Label(etch_frame, text="Etch Color:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
    entries['etch_color'] = ttk.Combobox(etch_frame, width=37, values=["dark", "light", "gray", "mixed"])
    entries['etch_color'].grid(row=0, column=1, sticky=tk.EW, padx=5, pady=3)
    entries['etch_color'].set("dark")

    # === NOTES ===
    row += 1
    notes_frame = ttk.LabelFrame(scrollable_frame, text="Additional Notes (Optional)", padding=10)
    notes_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=10)
    notes_frame.columnconfigure(0, weight=1)

    entries['notes'] = tk.Text(notes_frame, height=4, width=60, wrap=tk.WORD, font=('Arial', 9))
    entries['notes'].grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)

    # === BUTTONS ===
    row += 1
    button_frame = ttk.Frame(scrollable_frame)
    button_frame.grid(row=row, column=0, sticky=tk.EW, padx=10, pady=20)

    def save_custom_steel():
        name = entries['name'].get().strip()
        category = entries['category'].get().strip()

        if not name:
            messagebox.showerror("Missing Info", "Steel name is required")
            return
        if not category:
            messagebox.showerror("Missing Info", "Category is required")
            return

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

        def get_float(key):
            val = entries[key].get().strip()
            return float(val) if val else None

        try:
            steel_data = {
                'name': name,
                'category': category,
                'is_custom': True,
                'created_by': 'User'
            }

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

            db = _ensure_database()
            key = name.lower().replace(' ', '_').replace('-', '_')
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

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    logger.info("Add Custom Steel dialog created")


def show_forging_losses(root, file_path):
    """
    Show forging losses reference from a text file.

    Args:
        root: Tkinter root window
        file_path: Path to steel-losses-during-forging.txt
    """
    logger.info("Opening Forging Losses Reference")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except FileNotFoundError:
        messagebox.showerror("File Not Found",
                             f"Reference file not found:\n{file_path}")
        return

    ref_window = tk.Toplevel(root)
    ref_window.title("📖 Forging Losses Reference")
    ref_window.geometry("900x700")

    text_area = scrolledtext.ScrolledText(
        ref_window, wrap=tk.WORD, font=('Courier', 10),
        bg='#f5f5f5', padx=10, pady=10
    )
    text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_area.insert(tk.END, content)
    text_area.config(state=tk.DISABLED)

    logger.info("Forging losses reference displayed")


def show_plasticity_guide(root, file_path):
    """
    Show steel plasticity guide from a text file.

    Args:
        root: Tkinter root window
        file_path: Path to steel-plasticity.txt
    """
    logger.info("Opening Steel Plasticity Guide")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except FileNotFoundError:
        messagebox.showerror("File Not Found",
                             f"Reference file not found:\n{file_path}")
        return

    ref_window = tk.Toplevel(root)
    ref_window.title("⚒️ Steel Plasticity Guide")
    ref_window.geometry("900x700")

    text_area = scrolledtext.ScrolledText(
        ref_window, wrap=tk.WORD, font=('Courier', 10),
        bg='#f5f5f5', padx=10, pady=10
    )
    text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_area.insert(tk.END, content)
    text_area.config(state=tk.DISABLED)

    logger.info("Steel plasticity guide displayed")
