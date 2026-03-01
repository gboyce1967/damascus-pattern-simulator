"""
GUI Export Functions for Damascus Pattern Simulator
====================================================

Standalone export functions with file dialogs, usable from any Tkinter app.

Usage:
    from lib.gui_export import export_3d_model, export_cross_section, export_operation_log
"""

import tkinter as tk
from tkinter import filedialog, messagebox

from lib.logging_config import logger


def export_3d_model(root, billet, format_type, status_text=None):
    """
    Export the billet as a 3D model file via a save-file dialog.

    Args:
        root: Tkinter root window
        billet: Damascus3DBillet instance
        format_type: File format ('obj' or 'stl')
        status_text: Optional tk.StringVar for status bar updates
    """
    if billet is None:
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
            logger.debug(f"  Billet dimensions: {billet.width}x{billet.length}, {len(billet.layers)} layers")
            if status_text:
                status_text.set(f"Exporting {format_type.upper()} model...")
                root.update()

            billet.export_3d_model(filename, merge_layers=True)

            logger.info(f"3D model export successful: {filename}")
            if status_text:
                status_text.set(f"Export complete: {format_type.upper()}")
            messagebox.showinfo("Success", f"3D model saved to:\n{filename}")
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to export: {e}")
            if status_text:
                status_text.set("Export failed")
    else:
        logger.debug("Export cancelled by user")


def export_cross_section(root, billet, z_position, status_text=None):
    """
    Export the current cross-section as PNG via a save-file dialog.

    Args:
        root: Tkinter root window
        billet: Damascus3DBillet instance
        z_position: Z position to slice at (mm)
        status_text: Optional tk.StringVar for status bar updates
    """
    if billet is None:
        logger.warning("Export cross-section attempted with no billet")
        messagebox.showwarning("No Billet", "Please create a billet first")
        return

    logger.debug(f"Opening file dialog for cross-section export (Z={z_position:.1f}mm)")
    filename = filedialog.asksaveasfilename(
        title="Save Cross-Section Image",
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )

    if filename:
        try:
            logger.info(f"Exporting cross-section at Z={z_position:.1f}mm to: {filename}")
            if status_text:
                status_text.set(f"Exporting cross-section...")
                root.update()

            billet.save_cross_section_image(
                z_slice=z_position,
                output_path=filename,
                resolution=1600
            )

            logger.info(f"Cross-section export successful: {filename}")
            if status_text:
                status_text.set(f"Export complete: PNG")
            messagebox.showinfo("Success", f"Cross-section saved to:\n{filename}")
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to export: {e}")
            if status_text:
                status_text.set("Export failed")
    else:
        logger.debug("Export cancelled by user")


def export_operation_log(root, billet, status_text=None):
    """
    Export the operation history as JSON via a save-file dialog.

    Args:
        root: Tkinter root window
        billet: Damascus3DBillet instance
        status_text: Optional tk.StringVar for status bar updates
    """
    if billet is None:
        logger.warning("Export operation log attempted with no billet")
        messagebox.showwarning("No Billet", "Please create a billet first")
        return

    logger.debug(f"Opening file dialog for operation log export ({len(billet.operation_history)} operations)")
    filename = filedialog.asksaveasfilename(
        title="Save Operation Log",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )

    if filename:
        try:
            logger.info(f"Exporting operation log to: {filename}")
            logger.debug(f"  Operations: {len(billet.operation_history)}")
            if status_text:
                status_text.set("Exporting operation log...")
                root.update()

            billet.save_operation_log(filename)

            logger.info(f"Operation log export successful: {filename}")
            if status_text:
                status_text.set("Export complete: JSON")
            messagebox.showinfo("Success", f"Operation log saved to:\n{filename}")
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to export: {e}")
            if status_text:
                status_text.set("Export failed")
    else:
        logger.debug("Export cancelled by user")
