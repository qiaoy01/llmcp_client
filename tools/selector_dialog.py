import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime

class SelectorDialog:
    """Dialog for adding/editing CSS selectors"""
    
    def __init__(self, parent, existing_selector=None):
        self.result = None
        self.existing_selector = existing_selector
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit CSS Selector" if existing_selector else "Add CSS Selector")
        self.dialog.geometry("600x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_dialog()
        
        # If editing, populate fields
        if existing_selector:
            self.populate_fields()
            
        # Wait for dialog to close before returning
        self.dialog.wait_window()
        
    def setup_dialog(self):
        """Setup dialog UI"""
        # Name field
        ttk.Label(self.dialog, text="Name:").pack(anchor='w', padx=10, pady=5)
        self.name_entry = ttk.Entry(self.dialog, width=70)
        self.name_entry.pack(fill='x', padx=10, pady=5)
        
        # Selector field
        ttk.Label(self.dialog, text="CSS Selector:").pack(anchor='w', padx=10, pady=5)
        self.selector_entry = ttk.Entry(self.dialog, width=70)
        self.selector_entry.pack(fill='x', padx=10, pady=5)
        
        # Action selection
        action_frame = ttk.Frame(self.dialog)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(action_frame, text="Action:").pack(side='left')
        self.action_var = tk.StringVar(value="click")
        action_combo = ttk.Combobox(action_frame, textvariable=self.action_var, width=15, values=[
            "click",
            "input", 
            "get_text",
            "send_key",
            "screenshot"
        ])
        action_combo.pack(side='left', padx=5)
        action_combo.bind('<<ComboboxSelected>>', self.on_action_change)
        
        # Dynamic fields frame
        self.dynamic_frame = ttk.Frame(self.dialog)
        self.dynamic_frame.pack(fill='x', padx=10, pady=5)
        
        # Text field (for input action)
        self.text_label = ttk.Label(self.dynamic_frame, text="Text to Input:")
        self.text_entry = ttk.Entry(self.dynamic_frame, width=70)
        
        # Key field (for send_key action)
        self.key_label = ttk.Label(self.dynamic_frame, text="Key to Send:")
        self.key_entry = ttk.Entry(self.dynamic_frame, width=30)
        
        # Bias field (for screenshot action)
        self.bias_label = ttk.Label(self.dynamic_frame, text="Screenshot Bias (x,y,w,h):")
        self.bias_entry = ttk.Entry(self.dynamic_frame, width=30)
        
        # Description field
        ttk.Label(self.dialog, text="Description:").pack(anchor='w', padx=10, pady=(10,5))
        self.desc_text = tk.Text(self.dialog, height=5, width=70)
        self.desc_text.pack(fill='x', padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        save_text = "Update" if self.existing_selector else "Save"
        ttk.Button(button_frame, text=save_text, command=self.save).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right', padx=5)
        
        # Initialize dynamic fields
        self.on_action_change()
        
        # Focus on name field
        self.name_entry.focus()
        
        # Handle window close button (X)
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
    def populate_fields(self):
        """Populate fields when editing existing selector"""
        if self.existing_selector:
            self.name_entry.insert(0, self.existing_selector.get('name', ''))
            self.selector_entry.insert(0, self.existing_selector.get('selector', ''))
            self.action_var.set(self.existing_selector.get('action', 'click'))
            
            # Populate action-specific fields
            action = self.existing_selector.get('action', 'click')
            if action == 'input' and self.existing_selector.get('text'):
                self.text_entry.insert(0, self.existing_selector.get('text'))
            elif action == 'send_key' and self.existing_selector.get('key'):
                self.key_entry.insert(0, self.existing_selector.get('key'))
            elif action == 'screenshot' and self.existing_selector.get('bias'):
                self.bias_entry.insert(0, self.existing_selector.get('bias'))
                
            # Populate description
            self.desc_text.insert(1.0, self.existing_selector.get('description', ''))
            
            # Update dynamic fields based on action
            self.on_action_change()
        
    def on_action_change(self, event=None):
        """Handle action selection change"""
        # Hide all dynamic fields first
        self.text_label.pack_forget()
        self.text_entry.pack_forget()
        self.key_label.pack_forget()
        self.key_entry.pack_forget()
        self.bias_label.pack_forget()
        self.bias_entry.pack_forget()
        
        # Show relevant fields based on action
        action = self.action_var.get()
        
        if action == "input":
            self.text_label.pack(anchor='w', pady=2)
            self.text_entry.pack(fill='x', pady=2)
        elif action == "send_key":
            self.key_label.pack(anchor='w', pady=2)
            self.key_entry.pack(anchor='w', pady=2)
        elif action == "screenshot":
            self.bias_label.pack(anchor='w', pady=2)
            self.bias_entry.pack(anchor='w', pady=2)
        
    def save(self):
        """Save the selector"""
        name = self.name_entry.get().strip()
        selector = self.selector_entry.get().strip()
        action = self.action_var.get()
        
        if not name or not selector:
            messagebox.showwarning("Warning", "Name and selector are required")
            return
            
        # Validate action-specific requirements
        if action == "input":
            text = self.text_entry.get().strip()
            if not text:
                messagebox.showwarning("Warning", "Text is required for input action")
                return
        elif action == "send_key":
            key = self.key_entry.get().strip()
            if not key:
                messagebox.showwarning("Warning", "Key is required for send_key action")
                return
                
        # Build result dictionary
        self.result = {
            "name": name,
            "selector": selector,
            "action": action,
            "description": self.desc_text.get(1.0, tk.END).strip(),
            "created": self.existing_selector.get('created', datetime.now().isoformat()) if self.existing_selector else datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "usage_count": self.existing_selector.get('usage_count', 0) if self.existing_selector else 0
        }
        
        # Add action-specific data
        if action == "input":
            self.result["text"] = self.text_entry.get().strip()
        elif action == "send_key":
            self.result["key"] = self.key_entry.get().strip()
        elif action == "screenshot":
            bias = self.bias_entry.get().strip()
            if bias:
                self.result["bias"] = bias
        
        # Close dialog - this will cause wait_window() to return
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel the dialog"""
        self.result = None  # Explicitly set to None
        self.dialog.destroy()
