import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

class ToolkitUI:
    def init(self, title, geometry="1280x1024"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(geometry)

    def copy_to_clipboard(self, text):
        """Copy text to system clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log_message(f"[UI] Copied to clipboard: {text[:50]}...")