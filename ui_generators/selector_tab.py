import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
from tools.selector_dialog import SelectorDialog
from ui_generators.detail_panel import UIWithDetailPanel

class UIWithSelectorTab(UIWithDetailPanel):

    def setup_selector_tab(self, notebook):
        """Setup improved CSS selector management tab with three-panel layout"""
        selector_frame = ttk.Frame(notebook)
        notebook.add(selector_frame, text="CSS Selectors")
        
        # Top controls panel
        controls_frame = ttk.Frame(selector_frame)
        controls_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Add Selector", command=self.add_selector).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Save Selectors", command=self.save_selectors).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Load Selectors", command=self.load_selectors_file).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Clear All", command=self.clear_selectors).pack(side='left', padx=5)
        
        # Separator
        separator = ttk.Separator(selector_frame, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)
        
        # Main content area with three panels
        main_frame = ttk.Frame(selector_frame)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel: Simplified selector list
        left_panel = ttk.LabelFrame(main_frame, text="Selector List")
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Create treeview with simplified columns
        columns = ('Select', 'Name', 'Action', 'Status')
        self.selector_tree = ttk.Treeview(left_panel, columns=columns, show='headings', height=20)
        
        # Configure simplified columns
        self.selector_tree.heading('Select', text='✓')
        self.selector_tree.column('Select', width=40, anchor='center')
        
        self.selector_tree.heading('Name', text='Name')
        self.selector_tree.column('Name', width=180)
        
        self.selector_tree.heading('Action', text='Action')
        self.selector_tree.column('Action', width=100)
        
        self.selector_tree.heading('Status', text='Status')
        self.selector_tree.column('Status', width=80, anchor='center')
        
        # Add scrollbar for left panel
        left_scrollbar = ttk.Scrollbar(left_panel, orient='vertical', command=self.selector_tree.yview)
        self.selector_tree.configure(yscrollcommand=left_scrollbar.set)
        
        self.selector_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        left_scrollbar.pack(side='right', fill='y')
        
        # Right panel: Detail information
        right_panel = ttk.LabelFrame(main_frame, text="Selector Details")
        right_panel.pack(side='right', fill='both', expand=False, padx=(5, 0))
        right_panel.configure(width=400)
        right_panel.pack_propagate(False)  # Maintain fixed width
        
        # Detail panel content
        detail_scroll_frame = ttk.Frame(right_panel)
        detail_scroll_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create scrollable detail area
        detail_canvas = tk.Canvas(detail_scroll_frame, width=380)
        detail_scrollbar = ttk.Scrollbar(detail_scroll_frame, orient="vertical", command=detail_canvas.yview)
        self.detail_content_frame = ttk.Frame(detail_canvas)
        
        self.detail_content_frame.bind(
            "<Configure>",
            lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all"))
        )
        
        detail_canvas.create_window((0, 0), window=self.detail_content_frame, anchor="nw")
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        
        detail_canvas.pack(side="left", fill="both", expand=True)
        detail_scrollbar.pack(side="right", fill="y")
        
        # Bottom operations panel
        operations_frame = ttk.LabelFrame(selector_frame, text="Operations")
        operations_frame.pack(fill='x', padx=5, pady=5)
        
        # Row 1: Selection operations
        selection_row = ttk.Frame(operations_frame)
        selection_row.pack(fill='x', pady=2)
        
        ttk.Button(selection_row, text="Select All", command=self.select_all_selectors).pack(side='left', padx=5)
        ttk.Button(selection_row, text="Deselect All", command=self.deselect_all_selectors).pack(side='left', padx=5)
        ttk.Label(selection_row, text="|").pack(side='left', padx=10)
        ttk.Button(selection_row, text="Execute Selected", command=self.execute_selected_selectors).pack(side='left', padx=5)
        ttk.Button(selection_row, text="Delete Selected", command=self.delete_selected_selectors).pack(side='left', padx=5)
        
        # Row 2: Current selector operations
        current_row = ttk.Frame(operations_frame)
        current_row.pack(fill='x', pady=2)
        
        ttk.Label(current_row, text="Current Selector:").pack(side='left', padx=5)
        ttk.Button(current_row, text="Execute", command=self.execute_current_selector).pack(side='left', padx=5)
        ttk.Button(current_row, text="Edit", command=self.edit_current_selector).pack(side='left', padx=5)
        ttk.Button(current_row, text="Test", command=self.test_current_selector).pack(side='left', padx=5)
        ttk.Button(current_row, text="Copy to Debugger", command=self.copy_to_debugger).pack(side='left', padx=5)
        
        # Bind events
        self.selector_tree.bind('<Button-1>', self.on_selector_click)
        self.selector_tree.bind('<Double-1>', self.on_selector_double_click)
        self.selector_tree.bind('<<TreeviewSelect>>', self.on_selector_select)
        
        # Initialize selector data storage
        self.selector_checkboxes = {}  # Track checkbox states
        
        # Load existing selectors
        self.refresh_selector_list()

        # CSS Selector management
    def load_selectors(self):
        """Load selectors from file"""
        try:
            if os.path.exists(self.selector_file):
                with open(self.selector_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log_message(f"[Debugger] Failed to load selectors: {e}")
        return []
        
    def save_selectors(self):
        """Save selectors to file"""
        try:
            with open(self.selector_file, 'w', encoding='utf-8') as f:
                json.dump(self.selectors, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Selectors saved to {self.selector_file}")
            self.log_message(f"[Debugger] Selectors saved to {self.selector_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save selectors: {e}")
            
    def load_selectors_file(self):
        """Load selectors from chosen file"""
        filename = filedialog.askopenfilename(
            title="Load Selectors",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.selectors = json.load(f)
                self.refresh_selector_list()
                messagebox.showinfo("Success", f"Selectors loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load selectors: {e}")
                
    def add_selector(self):
        """Add new selector"""
        dialog = SelectorDialog(self.root)
        if dialog.result:
            self.selectors.append(dialog.result)
            self.refresh_selector_list()
            # Auto-save selectors after adding
            self.save_selectors_silently()
            self.log_message(f"[Debugger] Added selector: {dialog.result['name']} (Action: {dialog.result.get('action', 'click')})")
            
    def save_selectors_silently(self):
        """Save selectors to file without showing dialog"""
        try:
            with open(self.selector_file, 'w', encoding='utf-8') as f:
                json.dump(self.selectors, f, indent=2, ensure_ascii=False)
            self.log_message(f"[Debugger] Selectors auto-saved to {self.selector_file}")
        except Exception as e:
            self.log_message(f"[Debugger] Failed to auto-save selectors: {e}")
            
    def clear_selectors(self):
        """Clear all selectors"""
        if messagebox.askyesno("Confirm", "Clear all selectors?"):
            self.selectors.clear()
            self.refresh_selector_list()
            # Auto-save after clearing
            self.save_selectors_silently()

    def edit_selected_selector(self):
        """Edit the selected selector (only one at a time)"""
        selected_indices = self.get_selected_selectors()
        if not selected_indices:
            messagebox.showwarning("Warning", "No selectors selected")
            return
        if len(selected_indices) > 1:
            messagebox.showwarning("Warning", "Please select only one selector to edit")
            return
            
        index = selected_indices[0]
        if index < len(self.selectors):
            selector_data = self.selectors[index]
            dialog = SelectorDialog(self.root, selector_data)
            if dialog.result:
                self.selectors[index] = dialog.result
                self.save_selectors_silently()
                self.refresh_selector_list()
                self.log_message(f"[Selector] Edited: {dialog.result['name']}")
                
    def delete_selected_selectors(self):
        """Delete all selected selectors"""
        selected_indices = self.get_selected_selectors()
        if not selected_indices:
            messagebox.showwarning("Warning", "No selectors selected")
            return
            
        if messagebox.askyesno("Confirm", f"Delete {len(selected_indices)} selected selectors?"):
            # Sort indices in reverse order to delete from end to beginning
            for index in sorted(selected_indices, reverse=True):
                if index < len(self.selectors):
                    removed = self.selectors.pop(index)
                    self.log_message(f"[Selector] Deleted: {removed.get('name', 'Unknown')}")
                    
            self.save_selectors_silently()
            self.refresh_selector_list()
            
    def select_all_selectors(self):
        """Select all selectors"""
        for item_id in self.selector_checkboxes:
            if not self.selector_checkboxes[item_id]:
                self.toggle_selector_checkbox(item_id)
                
    def deselect_all_selectors(self):
        """Deselect all selectors"""
        for item_id in self.selector_checkboxes:
            if self.selector_checkboxes[item_id]:
                self.toggle_selector_checkbox(item_id)
    
    def get_selected_selectors(self):
        """Get list of selected selector indices"""
        selected = []
        for item_id, is_checked in self.selector_checkboxes.items():
            if is_checked:
                try:
                    index = int(item_id)
                    selected.append(index)
                except ValueError:
                    pass
        return selected
    
    def create_selector_suggestion_ui(self, selector, index):
        """Create UI elements for a selector suggestion"""
        frame = ttk.Frame(self.suggestions_container)
        frame.pack(fill='x', pady=2)
        
        # Selector text (truncated if too long)
        display_selector = selector[:60] + "..." if len(selector) > 60 else selector
        ttk.Label(frame, text=f"{index+1}. {display_selector}").pack(side='left', padx=5)
        
        # Copy to test button
        copy_btn = ttk.Button(
            frame, 
            text="Copy & Test",
            command=lambda s=selector: self.copy_selector_and_test(s)
        )
        copy_btn.pack(side='right', padx=5)
        
        # Copy to clipboard button
        clip_btn = ttk.Button(
            frame,
            text="Copy",
            command=lambda s=selector: self.copy_to_clipboard(s)
        )
        clip_btn.pack(side='right', padx=2)
        
    def copy_selector_and_test(self, selector):
        """Copy selector to debugger input and optionally test it"""
        # Copy to main debugger selector field
        self.selector_entry.delete(0, tk.END)
        self.selector_entry.insert(0, selector)
        
        # Also copy to clipboard
        self.copy_to_clipboard(selector)
        
        # Switch to debugger tab
        # Find the notebook and switch to first tab
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Notebook):
                widget.select(0)  # Select first tab (Debugger)
                break
                
        self.log_message(f"[AI] Copied selector to debugger: {selector}")
        
        # Ask if user wants to test immediately
        if messagebox.askyesno("Test Selector", f"Test this selector now?\n{selector}"):
            self.get_text()  # Test by getting text

    def extract_selector_from_line(self, line):
        """Extract CSS selector from a line of text"""
        # Look for common CSS selector patterns
        import re
        
        # Patterns to match CSS selectors
        patterns = [
            r'`([^`]+)`',  # Selector in backticks
            r'"([^"]+)"',  # Selector in quotes
            r"'([^']+)'",  # Selector in single quotes
            r'(\#[\w-]+)',  # ID selectors
            r'(\.[\w-]+(?:\.[\w-]+)*)',  # Class selectors
            r'(\w+\[[\w-]+[*^$|~]?="[^"]*"\])',  # Attribute selectors
            r'(\w+:\w+(?:\(\d+\))?)',  # Pseudo selectors
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                # Basic validation - should look like a CSS selector
                if (match.startswith(('.', '#')) or 
                    '[' in match or 
                    ':' in match or
                    ' ' in match):
                    return match.strip()
                    
        return None
    
    def extract_and_display_selectors(self, claude_response):
        """Extract selectors from Claude response and create copy buttons"""
        # Clear previous suggestions
        for widget in self.suggestions_container.winfo_children():
            widget.destroy()
            
        # Extract selectors using simple text processing
        lines = claude_response.split('\n')
        selectors = []
        
        for line in lines:
            line = line.strip()
            # Look for numbered selectors or selector patterns
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                'BEST CHOICE:' in line or
                line.startswith('- ')):
                
                # Extract potential CSS selectors
                selector = self.extract_selector_from_line(line)
                if selector:
                    selectors.append(selector)
                    
        # Create UI for each found selector
        for i, selector in enumerate(selectors[:5]):  # Limit to 5 suggestions
            self.create_selector_suggestion_ui(selector, i)

    def toggle_selector_checkbox(self, item_id):
        """Toggle checkbox state for a selector"""
        if item_id in self.selector_checkboxes:
            # Toggle state
            self.selector_checkboxes[item_id] = not self.selector_checkboxes[item_id]
            
            # Update display - get current values and update only checkbox column
            current_values = list(self.selector_tree.item(item_id, 'values'))
            current_values[0] = '☑' if self.selector_checkboxes[item_id] else '☐'
            self.selector_tree.item(item_id, values=current_values)
            
            checked_count = sum(1 for checked in self.selector_checkboxes.values() if checked)
            action_text = "selected" if self.selector_checkboxes[item_id] else "deselected"
            self.log_message(f"[Selector] Checkbox {action_text}. Total selected: {checked_count}")

    def refresh_selector_list(self):
        """Refresh the simplified selector list display"""
        if hasattr(self, 'selector_tree'):
            # Clear existing items
            for item in self.selector_tree.get_children():
                self.selector_tree.delete(item)
                
            # Clear checkbox states
            self.selector_checkboxes.clear()
                
            # Add selectors to tree
            for i, selector in enumerate(self.selectors):
                # Determine status
                last_result = selector.get('last_execution_result', None)
                if last_result is None:
                    status = "●"
                elif last_result.get('success', False):
                    status = "●"
                else:
                    status = "●"
                
                # Insert item
                item_id = str(i)
                self.selector_tree.insert('', 'end', iid=item_id, values=(
                    "☐",  # Unchecked checkbox
                    selector.get('name', f'Selector {i+1}'),
                    selector.get('action', 'click').title(),
                    status
                ))
                
                # Initialize checkbox state
                self.selector_checkboxes[item_id] = False
            
            # If we had a selection, try to restore it
            if self.current_selected_index is not None and self.current_selected_index < len(self.selectors):
                try:
                    self.selector_tree.selection_set(str(self.current_selected_index))
                    self.setup_detail_panel_content(self.selectors[self.current_selected_index])
                except:
                    self.current_selected_index = None
                    self.setup_detail_panel_placeholder()
            else:
                self.setup_detail_panel_placeholder()

    def on_selector_click(self, event):
        """Handle clicking on selector list"""
        item = self.selector_tree.selection()[0] if self.selector_tree.selection() else None
        if item:
            column = self.selector_tree.identify_column(event.x)
            if column == '#1':  # Clicked on checkbox column
                self.toggle_selector_checkbox(item)
                
    def on_selector_double_click(self, event):
        """Handle double-clicking on selector"""
        self.execute_current_selector()
        
    def on_selector_select(self, event):
        """Handle selector selection change"""
        selection = self.selector_tree.selection()
        if selection:
            item_id = selection[0]
            try:
                index = int(item_id)
                if 0 <= index < len(self.selectors):
                    self.current_selected_index = index
                    self.setup_detail_panel_content(self.selectors[index])
                    self.log_message(f"[Selector] Selected: {self.selectors[index].get('name', 'Unnamed')}")
            except (ValueError, IndexError):
                pass
        else:
            self.current_selected_index = None
            self.setup_detail_panel_placeholder()
    
    def copy_to_debugger(self):
        """Copy current selector to debugger tab"""
        if self.current_selected_index is not None and self.current_selected_index < len(self.selectors):
            selector_data = self.selectors[self.current_selected_index]
            
            # Copy to debugger fields
            self.selector_entry.delete(0, tk.END)
            self.selector_entry.insert(0, selector_data['selector'])
            
            # Copy action-specific data
            action = selector_data.get('action', 'click')
            if action == 'input' and selector_data.get('text'):
                self.text_entry.delete(0, tk.END)
                self.text_entry.insert(0, selector_data['text'])
            elif action == 'send_key' and selector_data.get('key'):
                self.key_entry.delete(0, tk.END)
                self.key_entry.insert(0, selector_data['key'])
            elif action == 'screenshot' and selector_data.get('bias'):
                self.bias_entry.delete(0, tk.END)
                self.bias_entry.insert(0, selector_data['bias'])
                
            # Switch to debugger tab
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    widget.select(0)  # Select first tab (Debugger)
                    break
                    
            self.log_message(f"[Selector] Copied to debugger: {selector_data.get('name', 'Unnamed')}")
            messagebox.showinfo("Copied", f"Selector '{selector_data.get('name', 'Unnamed')}' copied to debugger tab")
        else:
            messagebox.showwarning("Warning", "No selector selected")

    def edit_current_selector(self):
        """Edit currently selected selector"""
        if self.current_selected_index is not None and self.current_selected_index < len(self.selectors):
            selector_data = self.selectors[self.current_selected_index]
            dialog = SelectorDialog(self.root, selector_data)
            if dialog.result:
                self.selectors[self.current_selected_index] = dialog.result
                self.save_selectors_silently()
                self.refresh_selector_list()
                # Reselect the edited item
                self.selector_tree.selection_set(str(self.current_selected_index))
                self.setup_detail_panel_content(dialog.result)
                self.log_message(f"[Selector] Edited: {dialog.result['name']}")
        else:
            messagebox.showwarning("Warning", "No selector selected")