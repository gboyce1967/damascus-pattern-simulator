"""
Tkinter Text Log Handler
=========================

Logging handler that streams log messages into a Tkinter text widget,
allowing real-time debug output in the GUI.

Usage:
    from lib.tk_log_handler import TkTextLogHandler
    handler = TkTextLogHandler(root, text_widget)
    logger.addHandler(handler)
"""

import tkinter as tk
import logging


class TkTextLogHandler(logging.Handler):
    """Logging handler that streams log messages into a Tkinter text widget."""

    def __init__(self, root, text_widget):
        """
        Args:
            root: Tkinter root window (needed for thread-safe after() calls)
            text_widget: Tkinter Text or ScrolledText widget to append to
        """
        super().__init__()
        self.root = root
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        ))

    def emit(self, record):
        try:
            message = self.format(record)
            self.root.after(0, self._append, message)
        except Exception:
            self.handleError(record)

    def _append(self, message):
        if not self.text_widget or not self.text_widget.winfo_exists():
            return

        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
