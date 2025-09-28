import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime

class UIWithLogTab():
    def setup_log_tab(self, notebook):
        """Setup server log tab"""
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Server Log")
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(log_controls, text="Clear Log", command=self.clear_log).pack(side='left', padx=5)
        ttk.Button(log_controls, text="Save Log", command=self.save_log).pack(side='left', padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_controls, text="Auto Scroll", variable=self.auto_scroll_var).pack(side='left', padx=5)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, log_entry)
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)
                
        self.root.after(0, update_log)

        # Log management
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
        
    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")