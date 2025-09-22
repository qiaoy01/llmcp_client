#!/usr/bin/env python3
"""
LLMCP UI Debugger - Complete WebSocket Version (Improved UI)
A comprehensive debugging tool for LLMCP Chrome Extension using WebSocket communication
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import traceback
import requests
import os
from datetime import datetime
from tools.tooltip import ToolTip
from networks.socket_server import LLMCPWebSocketServer
from tools.selector_dialog import SelectorDialog

class LLMCPDebugger:
    """Complete LLMCP Debugger with all features"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LLMCP Debugger v2.0 (WebSocket)")
        self.root.geometry("1200x800")
        
        # WebSocket server components
        self.ws_server = LLMCPWebSocketServer(self)
        self.is_server_running = False
        
        # CSS Selector storage
        self.selector_file = "llmcp_selectors.json"
        self.config_file = "llmcp_config.json"
        
        # Load existing selectors and auto-load on startup
        self.selectors = self.load_selectors()
        
        # Load AI configuration
        self.ai_config = self.load_ai_config_file()
        
        # Current selected selector index for detail panel
        self.current_selected_index = None
        
        # UI components
        self.setup_ui()
        
        # Apply loaded AI config to UI
        self.apply_ai_config_to_ui()
        
        # Auto-start server
        self.start_server()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Main Debugger
        self.setup_debugger_tab(notebook)
        
        # Tab 2: CSS Selector Manager
        self.setup_selector_tab(notebook)
        
        # Tab 3: AI Assistant
        self.setup_ai_tab(notebook)
        
        # Tab 4: Server Log
        self.setup_log_tab(notebook)
        
    def setup_debugger_tab(self, notebook):
        """Setup main debugger tab"""
        debug_frame = ttk.Frame(notebook)
        notebook.add(debug_frame, text="Debugger")
        
        # Server status
        status_frame = ttk.LabelFrame(debug_frame, text="WebSocket Server Status")
        status_frame.pack(fill='x', padx=5, pady=5)
        
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(fill='x', padx=5, pady=5)
        
        self.status_label = ttk.Label(status_info_frame, text="Starting WebSocket server...")
        self.status_label.pack(side='left', padx=5, pady=5)
        
        self.clients_label = ttk.Label(status_info_frame, text="Clients: 0")
        self.clients_label.pack(side='left', padx=20, pady=5)
        
        ttk.Button(status_info_frame, text="Restart Server", command=self.restart_server).pack(side='right', padx=5, pady=5)
        
        # Quick commands
        commands_frame = ttk.LabelFrame(debug_frame, text="Quick Commands")
        commands_frame.pack(fill='x', padx=5, pady=5)
        
        # Row 1: Click tracking
        row1 = ttk.Frame(commands_frame)
        row1.pack(fill='x', pady=2)
        ttk.Button(row1, text="Get Last Click Location", command=self.get_last_click_location).pack(side='left', padx=2)
        ttk.Button(row1, text="Get Last Click Element", command=self.get_last_click_element).pack(side='left', padx=2)
        ttk.Button(row1, text="Get Page Info", command=self.get_page_info).pack(side='left', padx=2)
        
        # Row 2: Element operations
        row2 = ttk.Frame(commands_frame)
        row2.pack(fill='x', pady=2)
        
        ttk.Label(row2, text="Selector:").pack(side='left')
        self.selector_entry = ttk.Entry(row2, width=40)
        self.selector_entry.pack(side='left', padx=5)
        
        ttk.Button(row2, text="Click", command=self.click_element).pack(side='left', padx=2)
        ttk.Button(row2, text="Get Text", command=self.get_text).pack(side='left', padx=2)
        
        # Row 3: Input operations
        row3 = ttk.Frame(commands_frame)
        row3.pack(fill='x', pady=2)
        
        ttk.Label(row3, text="Text:").pack(side='left')
        self.text_entry = ttk.Entry(row3, width=25)
        self.text_entry.pack(side='left', padx=5)
        
        ttk.Button(row3, text="Input Text", command=self.input_text).pack(side='left', padx=2)
        
        ttk.Label(row3, text="Key:").pack(side='left', padx=(10,0))
        self.key_entry = ttk.Entry(row3, width=10)
        self.key_entry.pack(side='left', padx=5)
        
        ttk.Button(row3, text="Send Key", command=self.send_key).pack(side='left', padx=2)
        
        # Row 4: Screenshot
        row4 = ttk.Frame(commands_frame)
        row4.pack(fill='x', pady=2)
        
        ttk.Label(row4, text="Bias (x,y,w,h):").pack(side='left')
        self.bias_entry = ttk.Entry(row4, width=20)
        self.bias_entry.pack(side='left', padx=5)
        
        ttk.Button(row4, text="Screenshot Element", command=self.screenshot_element).pack(side='left', padx=2)
        
        # Response display
        response_frame = ttk.LabelFrame(debug_frame, text="Last Response")
        response_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.response_text = scrolledtext.ScrolledText(response_frame, height=15)
        self.response_text.pack(fill='both', expand=True, padx=5, pady=5)
        
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
        
        # Initialize detail panel with placeholder
        self.setup_detail_panel_placeholder()
        
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
        
    def setup_detail_panel_placeholder(self):
        """Setup placeholder content for detail panel"""
        # Clear existing content
        for widget in self.detail_content_frame.winfo_children():
            widget.destroy()
            
        placeholder = ttk.Label(self.detail_content_frame, 
                               text="Select a selector from the list\nto view detailed information",
                               justify='center',
                               foreground='gray')
        placeholder.pack(expand=True, pady=50)
        
    def setup_detail_panel_content(self, selector_data, index):
        """Setup detail panel with selector information"""
        # Clear existing content
        for widget in self.detail_content_frame.winfo_children():
            widget.destroy()
            
        # Selector name header
        name_frame = ttk.Frame(self.detail_content_frame)
        name_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(name_frame, text=selector_data.get('name', 'Unnamed'), 
                 font=('Arial', 12, 'bold')).pack(anchor='w')
        
        # Status indicator
        status_frame = ttk.Frame(self.detail_content_frame)
        status_frame.pack(fill='x', padx=5, pady=2)
        
        status_color = self.get_status_color(selector_data)
        status_text = self.get_status_text(selector_data)
        
        status_label = ttk.Label(status_frame, text=f"● {status_text}", foreground=status_color)
        status_label.pack(anchor='w')
        
        # Add tooltip for status
        ToolTip(status_label, self.get_status_tooltip(selector_data))
        
        # Separator
        ttk.Separator(self.detail_content_frame, orient='horizontal').pack(fill='x', padx=5, pady=10)
        
        # CSS Selector section
        selector_section = ttk.LabelFrame(self.detail_content_frame, text="CSS Selector")
        selector_section.pack(fill='x', padx=5, pady=5)
        
        selector_text = tk.Text(selector_section, height=3, wrap='word', font=('Consolas', 9))
        selector_text.pack(fill='x', padx=5, pady=5)
        selector_text.insert(1.0, selector_data.get('selector', ''))
        selector_text.configure(state='disabled')
        
        # Copy button for selector
        copy_btn = ttk.Button(selector_section, text="Copy Selector", 
                             command=lambda: self.copy_to_clipboard(selector_data.get('selector', '')))
        copy_btn.pack(anchor='e', padx=5, pady=2)
        
        # Action and Parameters section
        action_section = ttk.LabelFrame(self.detail_content_frame, text="Action & Parameters")
        action_section.pack(fill='x', padx=5, pady=5)
        
        action = selector_data.get('action', 'click')
        ttk.Label(action_section, text=f"Action Type: {action.title()}", 
                 font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=2)
        
        # Display action-specific parameters
        self.display_action_parameters(action_section, selector_data)
        
        # Description section
        if selector_data.get('description'):
            desc_section = ttk.LabelFrame(self.detail_content_frame, text="Description")
            desc_section.pack(fill='x', padx=5, pady=5)
            
            desc_text = tk.Text(desc_section, height=4, wrap='word')
            desc_text.pack(fill='x', padx=5, pady=5)
            desc_text.insert(1.0, selector_data.get('description', ''))
            desc_text.configure(state='disabled')
        
        # Metadata section
        meta_section = ttk.LabelFrame(self.detail_content_frame, text="Metadata")
        meta_section.pack(fill='x', padx=5, pady=5)
        
        # Creation date
        created = selector_data.get('created', 'Unknown')
        if created != 'Unknown':
            try:
                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created = created_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        ttk.Label(meta_section, text=f"Created: {created}").pack(anchor='w', padx=5, pady=1)
        
        # Last modified
        modified = selector_data.get('modified', 'Unknown')
        if modified != 'Unknown':
            try:
                modified_dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                modified = modified_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        ttk.Label(meta_section, text=f"Modified: {modified}").pack(anchor='w', padx=5, pady=1)
        
        # Usage count (if available)
        usage_count = selector_data.get('usage_count', 0)
        ttk.Label(meta_section, text=f"Usage Count: {usage_count}").pack(anchor='w', padx=5, pady=1)
        
    def display_action_parameters(self, parent_frame, selector_data):
        """Display action-specific parameters in detail panel"""
        action = selector_data.get('action', 'click')
        
        if action == 'input':
            text_value = selector_data.get('text', '')
            param_frame = ttk.Frame(parent_frame)
            param_frame.pack(fill='x', padx=5, pady=2)
            
            ttk.Label(param_frame, text="Input Text:", foreground='gray').pack(anchor='w')
            text_display = tk.Text(param_frame, height=2, wrap='word', font=('Consolas', 9))
            text_display.pack(fill='x', pady=2)
            text_display.insert(1.0, text_value)
            text_display.configure(state='disabled')
            
        elif action == 'send_key':
            key_value = selector_data.get('key', '')
            param_frame = ttk.Frame(parent_frame)
            param_frame.pack(fill='x', padx=5, pady=2)
            
            ttk.Label(param_frame, text="Key to Send:", foreground='gray').pack(anchor='w')
            ttk.Label(param_frame, text=key_value, font=('Consolas', 10, 'bold')).pack(anchor='w', padx=10)
            
        elif action == 'screenshot':
            bias_value = selector_data.get('bias', '')
            param_frame = ttk.Frame(parent_frame)
            param_frame.pack(fill='x', padx=5, pady=2)
            
            ttk.Label(param_frame, text="Screenshot Bias:", foreground='gray').pack(anchor='w')
            if bias_value:
                ttk.Label(param_frame, text=bias_value, font=('Consolas', 10)).pack(anchor='w', padx=10)
            else:
                ttk.Label(param_frame, text="No bias specified", foreground='gray').pack(anchor='w', padx=10)
                
        else:
            ttk.Label(parent_frame, text="No additional parameters", 
                     foreground='gray').pack(anchor='w', padx=5, pady=5)
            
    def get_status_color(self, selector_data):
        """Get status color for selector"""
        last_result = selector_data.get('last_execution_result', None)
        if last_result is None:
            return 'gray'
        elif last_result.get('success', False):
            return 'green'
        else:
            return 'red'
            
    def get_status_text(self, selector_data):
        """Get status text for selector"""
        last_result = selector_data.get('last_execution_result', None)
        if last_result is None:
            return 'Not tested'
        elif last_result.get('success', False):
            return 'Last execution: Success'
        else:
            return 'Last execution: Failed'
            
    def get_status_tooltip(self, selector_data):
        """Get detailed status tooltip"""
        last_result = selector_data.get('last_execution_result', None)
        if last_result is None:
            return 'This selector has not been executed yet'
        
        timestamp = last_result.get('timestamp', 'Unknown time')
        if last_result.get('success', False):
            return f'Last successful execution: {timestamp}'
        else:
            error = last_result.get('error', 'Unknown error')
            return f'Last failed execution: {timestamp}\nError: {error}'
    
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
                    self.setup_detail_panel_content(self.selectors[index], index)
                    self.log_message(f"[Selector] Selected: {self.selectors[index].get('name', 'Unnamed')}")
            except (ValueError, IndexError):
                pass
        else:
            self.current_selected_index = None
            self.setup_detail_panel_placeholder()
            
    def execute_current_selector(self):
        """Execute currently selected selector"""
        if self.current_selected_index is not None and self.current_selected_index < len(self.selectors):
            selector_data = self.selectors[self.current_selected_index]
            self.execute_single_selector(selector_data)
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
                self.setup_detail_panel_content(dialog.result, self.current_selected_index)
                self.log_message(f"[Selector] Edited: {dialog.result['name']}")
        else:
            messagebox.showwarning("Warning", "No selector selected")
            
    def test_current_selector(self):
        """Test currently selected selector by getting its text"""
        if self.current_selected_index is not None and self.current_selected_index < len(self.selectors):
            selector_data = self.selectors[self.current_selected_index]
            
            # Copy selector to debugger
            self.selector_entry.delete(0, tk.END)
            self.selector_entry.insert(0, selector_data['selector'])
            
            # Test by getting text (non-destructive)
            self.get_text()
            self.log_message(f"[Selector] Tested: {selector_data.get('name', 'Unnamed')}")
        else:
            messagebox.showwarning("Warning", "No selector selected")
            
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
                    self.setup_detail_panel_content(self.selectors[self.current_selected_index], self.current_selected_index)
                except:
                    self.current_selected_index = None
                    self.setup_detail_panel_placeholder()
            else:
                self.setup_detail_panel_placeholder()

    def copy_to_clipboard(self, text):
        """Copy text to system clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log_message(f"[UI] Copied to clipboard: {text[:50]}...")

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
    
    def setup_ai_tab(self, notebook):
        """Setup AI assistant tab"""
        ai_frame = ttk.Frame(notebook)
        notebook.add(ai_frame, text="AI Assistant")
        
        # Claude API Configuration
        config_frame = ttk.LabelFrame(ai_frame, text="Claude API Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # API Key
        ttk.Label(config_frame, text="Claude API Key:").pack(anchor='w', padx=5, pady=2)
        self.api_key_entry = ttk.Entry(config_frame, width=80, show="*")
        self.api_key_entry.pack(fill='x', padx=5, pady=2)
        
        # Model Selection
        model_frame = ttk.Frame(config_frame)
        model_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(model_frame, text="Model:").pack(side='left')
        self.model_var = tk.StringVar(value="claude-3-5-sonnet-20241022")
        model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, width=30, values=[
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", 
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ])
        model_combo.pack(side='left', padx=5)
        
        # Config buttons
        config_buttons = ttk.Frame(config_frame)
        config_buttons.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(config_buttons, text="Save Config", command=self.save_ai_config).pack(side='left', padx=5)
        ttk.Button(config_buttons, text="Load Config", command=self.load_ai_config).pack(side='left', padx=5)
        ttk.Button(config_buttons, text="Test Connection", command=self.test_claude_api).pack(side='left', padx=5)
        
        # Automatic Analysis
        analysis_frame = ttk.LabelFrame(ai_frame, text="Automatic CSS Selector Analysis")
        analysis_frame.pack(fill='x', padx=5, pady=5)
        
        # Analysis Strategy Checkboxes
        strategy_frame = ttk.LabelFrame(analysis_frame, text="Analysis Strategy Hints")
        strategy_frame.pack(fill='x', padx=5, pady=5)
        
        # Create checkbox variables
        self.content_based_var = tk.BooleanVar()
        self.list_index_var = tk.BooleanVar()
        self.table_based_var = tk.BooleanVar()
        self.label_up_down_var = tk.BooleanVar()
        self.label_left_right_var = tk.BooleanVar()
        self.label_north_west_var = tk.BooleanVar()
        
        # Row 1: Content and List strategies
        strategy_row1 = ttk.Frame(strategy_frame)
        strategy_row1.pack(fill='x', padx=5, pady=2)
        
        ttk.Checkbutton(strategy_row1, text="Content-based", 
                       variable=self.content_based_var,
                       command=self.on_strategy_change).pack(side='left', padx=5)
        ttk.Checkbutton(strategy_row1, text="List (ul/li, ol/li) index-based", 
                       variable=self.list_index_var,
                       command=self.on_strategy_change).pack(side='left', padx=5)
        ttk.Checkbutton(strategy_row1, text="Table-based", 
                       variable=self.table_based_var,
                       command=self.on_strategy_change).pack(side='left', padx=5)
        
        # Row 2: Label-based strategies
        strategy_row2 = ttk.Frame(strategy_frame)
        strategy_row2.pack(fill='x', padx=5, pady=2)
        
        ttk.Checkbutton(strategy_row2, text="Label-based (up-down)", 
                       variable=self.label_up_down_var,
                       command=self.on_strategy_change).pack(side='left', padx=5)
        ttk.Checkbutton(strategy_row2, text="Label-based (left-right)", 
                       variable=self.label_left_right_var,
                       command=self.on_strategy_change).pack(side='left', padx=5)
        ttk.Checkbutton(strategy_row2, text="Label-based (north-west)", 
                       variable=self.label_north_west_var,
                       command=self.on_strategy_change).pack(side='left', padx=5)
        
        # Strategy description
        self.strategy_description = ttk.Label(strategy_frame, 
                                            text="Select hints to help AI understand element context for better selector generation",
                                            foreground="gray")
        self.strategy_description.pack(fill='x', padx=5, pady=2)
        
        # Quick Strategy Presets
        presets_frame = ttk.Frame(strategy_frame)
        presets_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(presets_frame, text="Quick Presets:").pack(side='left')
        ttk.Button(presets_frame, text="Form Field", command=self.preset_form_field).pack(side='left', padx=2)
        ttk.Button(presets_frame, text="Menu Item", command=self.preset_menu_item).pack(side='left', padx=2)
        ttk.Button(presets_frame, text="Table Cell", command=self.preset_table_cell).pack(side='left', padx=2)
        ttk.Button(presets_frame, text="Button/Link", command=self.preset_button_link).pack(side='left', padx=2)
        ttk.Button(presets_frame, text="Clear All", command=self.preset_clear_all).pack(side='left', padx=10)
        
        # Analysis buttons
        analysis_buttons = ttk.Frame(analysis_frame)
        analysis_buttons.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(analysis_buttons, text="Analyze Last Clicked Element", command=self.analyze_last_clicked).pack(side='left', padx=5)
        ttk.Button(analysis_buttons, text="Generate Best Selector", command=self.generate_best_selector).pack(side='left', padx=5)
        ttk.Button(analysis_buttons, text="Validate Current Page", command=self.validate_page_selectors).pack(side='left', padx=5)
        
        # Suggested Selectors
        suggestions_frame = ttk.LabelFrame(ai_frame, text="AI Suggested Selectors")
        suggestions_frame.pack(fill='x', padx=5, pady=5)
        
        # Create frame for selector suggestions with copy buttons
        self.suggestions_container = ttk.Frame(suggestions_frame)
        self.suggestions_container.pack(fill='x', padx=5, pady=5)
        
        # AI Response
        ai_response_frame = ttk.LabelFrame(ai_frame, text="Claude Analysis Results")
        ai_response_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.ai_response_text = scrolledtext.ScrolledText(ai_response_frame, height=15)
        self.ai_response_text.pack(fill='both', expand=True, padx=5, pady=5)
        
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
        
    def start_server(self):
        """Start WebSocket server"""
        try:
            success = self.ws_server.start_server()
            if success:
                self.is_server_running = True
                self.status_label.config(text="WebSocket server running on ws://localhost:11808")
                self.log_message("[Debugger] WebSocket server started on port 11808")
                
                # Start periodic client count updates
                self.update_client_count()
            else:
                self.status_label.config(text="Failed to start WebSocket server")
                self.log_message("[Debugger] Failed to start WebSocket server")
                
        except Exception as e:
            self.status_label.config(text=f"Server failed: {e}")
            self.log_message(f"[Debugger] Server start failed: {e}")
            
    def update_client_count(self):
        """Update connected clients count display"""
        if hasattr(self, 'clients_label'):
            client_count = len(self.ws_server.clients) if self.ws_server else 0
            self.clients_label.config(text=f"Clients: {client_count}")
        
        # Update every 2 seconds
        self.root.after(2000, self.update_client_count)
        
    def restart_server(self):
        """Restart WebSocket server"""
        if self.ws_server:
            self.ws_server.stop_server()
            
        self.is_server_running = False
        self.status_label.config(text="Restarting WebSocket server...")
        
        self.root.after(1000, self.start_server)
        
    def send_command(self, command):
        """Send command to Chrome extension"""
        try:
            if self.ws_server:
                success = self.ws_server.send_command_sync(command)
                if success:
                    self.log_message(f"[Debugger] Command sent via WebSocket: {command}")
                    return {"status": "sent", "message": "Command sent to extension"}
                else:
                    return {"error": "No WebSocket clients connected"}
            else:
                return {"error": "WebSocket server not running"}
                
        except Exception as e:
            return {"error": str(e)}
            
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, log_entry)
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)
                
        self.root.after(0, update_log)
        
    def handle_extension_response(self, response_data):
        """Handle response from Chrome extension"""
        def update_ui():
            # Display response in the main response area
            self.display_response(response_data)
            
            # Log the response
            self.log_message(f"[Extension Response] {response_data}")
            
            # Check if we're waiting for element data for Claude analysis
            if hasattr(self, 'waiting_for_element_analysis') and self.waiting_for_element_analysis:
                self.waiting_for_element_analysis = False
                if response_data.get('result', {}).get('success') and response_data.get('result', {}).get('element'):
                    element_data = response_data['result']['element']
                    self.analyze_element_with_claude(element_data)
                else:
                    self.log_message("[AI] No element data available for analysis")
                    self.ai_response_text.delete(1.0, tk.END)
                    self.ai_response_text.insert(1.0, "Error: No element data available. Please click on an element first.")
                    
            # Check if we're waiting for element data for best selector generation
            elif hasattr(self, 'waiting_for_best_selector') and self.waiting_for_best_selector:
                self.waiting_for_best_selector = False
                if response_data.get('result', {}).get('success') and response_data.get('result', {}).get('element'):
                    element_data = response_data['result']['element']
                    self.generate_best_selector_with_data(element_data)
                else:
                    self.log_message("[AI] No element data available for best selector generation")
                    self.ai_response_text.delete(1.0, tk.END)
                    self.ai_response_text.insert(1.0, "Error: No element data available. Please click on an element first.")
            
        self.root.after(0, update_ui)
        
    def display_response(self, response):
        """Display response in the response text area"""
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(1.0, json.dumps(response, indent=2))
        
    # Command implementations
    def get_last_click_location(self):
        """Get last click location"""
        command = {
            "type": "dom_operation",
            "action": "get_last_clicked_location"
        }
        response = self.send_command(command)
        self.display_response(response)
        
    def get_last_click_element(self):
        """Get last clicked element"""
        command = {
            "type": "dom_operation",
            "action": "get_last_clicked_element"
        }
        response = self.send_command(command)
        self.display_response(response)
        
        # Auto-fill selector if successful
        if response.get("success") and response.get("element", {}).get("selector"):
            self.selector_entry.delete(0, tk.END)
            self.selector_entry.insert(0, response["element"]["selector"])
            
    def get_page_info(self):
        """Get page information"""
        command = {
            "type": "dom_operation",
            "action": "get_page_info"
        }
        response = self.send_command(command)
        self.display_response(response)
        
    def click_element(self):
        """Click element by selector"""
        selector = self.selector_entry.get().strip()
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return
            
        command = {
            "type": "dom_operation",
            "action": "click_element",
            "selector": selector
        }
        response = self.send_command(command)
        self.display_response(response)
        
    def get_text(self):
        """Get text from element"""
        selector = self.selector_entry.get().strip()
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return
            
        command = {
            "type": "dom_operation",
            "action": "get_text",
            "selector": selector
        }
        response = self.send_command(command)
        self.display_response(response)
        
    def input_text(self):
        """Input text to element"""
        selector = self.selector_entry.get().strip()
        text = self.text_entry.get()
        
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return
        if not text:
            messagebox.showwarning("Warning", "Please enter text to input")
            return
            
        command = {
            "type": "dom_operation",
            "action": "input_text",
            "selector": selector,
            "text": text
        }
        response = self.send_command(command)
        self.display_response(response)
        
    def send_key(self):
        """Send key to element"""
        selector = self.selector_entry.get().strip()
        key = self.key_entry.get().strip()
        
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return
        if not key:
            messagebox.showwarning("Warning", "Please enter a key")
            return
            
        command = {
            "type": "dom_operation",
            "action": "send_key",
            "selector": selector,
            "key": key
        }
        response = self.send_command(command)
        self.display_response(response)
        
    def screenshot_element(self):
        """Take screenshot of element"""
        selector = self.selector_entry.get().strip()
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return
            
        bias_str = self.bias_entry.get().strip()
        bias = {"x": 0, "y": 0, "width": 0, "height": 0}
        
        if bias_str:
            try:
                parts = bias_str.split(',')
                if len(parts) >= 4:
                    bias = {
                        "x": int(parts[0].strip()),
                        "y": int(parts[1].strip()),
                        "width": int(parts[2].strip()),
                        "height": int(parts[3].strip())
                    }
            except ValueError:
                messagebox.showwarning("Warning", "Invalid bias format. Use: x,y,width,height")
                return
                
        command = {
            "type": "dom_operation",
            "action": "screenshot_element",
            "selector": selector,
            "bias": bias
        }
        response = self.send_command(command)
        self.display_response(response)
        
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
            
    def execute_selected_selectors(self):
        """Execute all selected selectors"""
        selected_indices = self.get_selected_selectors()
        if not selected_indices:
            messagebox.showwarning("Warning", "No selectors selected")
            return
            
        for index in selected_indices:
            if index < len(self.selectors):
                selector_data = self.selectors[index]
                self.execute_single_selector(selector_data)
                
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
                
    def execute_single_selector(self, selector_data):
        """Execute a single selector with its action"""
        # Fill in the debugger fields
        self.selector_entry.delete(0, tk.END)
        self.selector_entry.insert(0, selector_data['selector'])
        
        action = selector_data.get('action', 'click')
        
        try:
            if action == 'click':
                self.click_element()
            elif action == 'input':
                if selector_data.get('text'):
                    self.text_entry.delete(0, tk.END)
                    self.text_entry.insert(0, selector_data['text'])
                self.input_text()
            elif action == 'get_text':
                self.get_text()
            elif action == 'send_key':
                if selector_data.get('key'):
                    self.key_entry.delete(0, tk.END)
                    self.key_entry.insert(0, selector_data['key'])
                self.send_key()
            elif action == 'screenshot':
                if selector_data.get('bias'):
                    self.bias_entry.delete(0, tk.END)
                    self.bias_entry.insert(0, selector_data['bias'])
                self.screenshot_element()
            else:
                self.click_element()
                
            self.log_message(f"[Selector] Executed: {selector_data['name']} ({action})")
            
        except Exception as e:
            self.log_message(f"[Selector] Execution failed: {e}")
            
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
                
    # AI Assistant Strategy Methods
    def on_strategy_change(self):
        """Handle strategy checkbox changes"""
        selected_strategies = []
        
        if self.content_based_var.get():
            selected_strategies.append("Content-based")
        if self.list_index_var.get():
            selected_strategies.append("List index-based")
        if self.table_based_var.get():
            selected_strategies.append("Table-based")
        if self.label_up_down_var.get():
            selected_strategies.append("Label-based (up-down)")
        if self.label_left_right_var.get():
            selected_strategies.append("Label-based (left-right)")
        if self.label_north_west_var.get():
            selected_strategies.append("Label-based (north-west)")
            
        if selected_strategies:
            description = f"Active strategies: {', '.join(selected_strategies)}"
        else:
            description = "Select hints to help AI understand element context for better selector generation"
            
        self.strategy_description.config(text=description)
        
    def get_strategy_hints(self):
        """Get selected strategy hints for AI analysis"""
        hints = []
        
        if self.content_based_var.get():
            hints.append({
                "type": "content-based",
                "description": "Focus on the clicked text itself - the text content is likely unique on the page and can be used for text-based selectors",
                "techniques": ["text() contains", "exact text match", "partial text matching"]
            })
            
        if self.list_index_var.get():
            hints.append({
                "type": "list-index-based", 
                "description": "This element is part of a list (ul/li or ol/li) - use index-based selectors for flexibility",
                "techniques": ["nth-child()", "nth-of-type()", "li:nth-child(n)", "position-based selectors"]
            })
            
        if self.table_based_var.get():
            hints.append({
                "type": "table-based",
                "description": "This element is in a table structure - use tr/td with index for flexible table navigation",
                "techniques": ["tr:nth-child()", "td:nth-child()", "table row/column positioning", "tbody indexing"]
            })
            
        if self.label_up_down_var.get():
            hints.append({
                "type": "label-up-down",
                "description": "This element has a meaningful label positioned above it (vertical relationship)",
                "techniques": ["following-sibling", "adjacent selectors", "parent-child relationships", "label + input patterns"]
            })
            
        if self.label_left_right_var.get():
            hints.append({
                "type": "label-left-right", 
                "description": "This element has a meaningful label positioned to its left (horizontal relationship)",
                "techniques": ["sibling selectors", "same-row positioning", "label + input combinations", "flex/grid layouts"]
            })
            
        if self.label_north_west_var.get():
            hints.append({
                "type": "label-north-west",
                "description": "This element has a meaningful label positioned at its top-left (diagonal relationship)",
                "techniques": ["complex parent-child navigation", "grid positioning", "form field associations", "multi-level selectors"]
            })
            
        return hints
    
    # Strategy preset methods
    def preset_form_field(self):
        """Set checkboxes for form field analysis"""
        self.preset_clear_all()
        self.content_based_var.set(True)
        self.label_left_right_var.set(True)
        self.label_up_down_var.set(True)
        self.on_strategy_change()
        self.log_message("[AI] Applied Form Field preset: content-based, label-left-right, label-up-down")
        
    def preset_menu_item(self):
        """Set checkboxes for menu item analysis"""
        self.preset_clear_all()
        self.content_based_var.set(True)
        self.list_index_var.set(True)
        self.on_strategy_change()
        self.log_message("[AI] Applied Menu Item preset: content-based, list-index-based")
        
    def preset_table_cell(self):
        """Set checkboxes for table cell analysis"""
        self.preset_clear_all()
        self.content_based_var.set(True)
        self.table_based_var.set(True)
        self.on_strategy_change()
        self.log_message("[AI] Applied Table Cell preset: content-based, table-based")
        
    def preset_button_link(self):
        """Set checkboxes for button/link analysis"""
        self.preset_clear_all()
        self.content_based_var.set(True)
        self.on_strategy_change()
        self.log_message("[AI] Applied Button/Link preset: content-based")
        
    def preset_clear_all(self):
        """Clear all strategy checkboxes"""
        self.content_based_var.set(False)
        self.list_index_var.set(False)
        self.table_based_var.set(False)
        self.label_up_down_var.set(False)
        self.label_left_right_var.set(False)
        self.label_north_west_var.set(False)
        self.on_strategy_change()
                
    # AI Assistant functions
    def load_ai_config_file(self):
        """Load AI configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log_message(f"[AI] Failed to load config: {e}")
        return {"api_key": "", "model": "claude-3-5-sonnet-20241022"}
    
    def apply_ai_config_to_ui(self):
        """Apply loaded configuration to UI elements"""
        if hasattr(self, 'api_key_entry'):
            self.api_key_entry.insert(0, self.ai_config.get('api_key', ''))
        if hasattr(self, 'model_var'):
            self.model_var.set(self.ai_config.get('model', 'claude-3-5-sonnet-20241022'))
    
    def save_ai_config(self):
        """Save AI configuration to file"""
        try:
            config = {
                "api_key": self.api_key_entry.get().strip(),
                "model": self.model_var.get(),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
            self.ai_config = config
            messagebox.showinfo("Success", f"AI configuration saved to {self.config_file}")
            self.log_message("[AI] Configuration saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save AI config: {e}")
            
    def load_ai_config(self):
        """Load AI configuration from file"""
        self.ai_config = self.load_ai_config_file()
        self.apply_ai_config_to_ui()
        messagebox.showinfo("Success", "AI configuration loaded")
        
    def test_claude_api(self):
        """Test Claude API connection"""
        api_key = self.api_key_entry.get().strip()
        model = self.model_var.get()
        
        if not api_key:
            messagebox.showwarning("Warning", "Please enter Claude API key")
            return
            
        try:
            response = self.call_claude_api(
                "Please respond with 'API connection successful' to test the connection.",
                api_key,
                model
            )
            
            if "successful" in response.lower():
                messagebox.showinfo("Success", "Claude API connection successful!")
                self.log_message("[AI] Claude API connection test passed")
            else:
                messagebox.showwarning("Warning", f"Unexpected response: {response[:100]}...")
                
        except Exception as e:
            messagebox.showerror("Error", f"Claude API test failed: {e}")
            self.log_message(f"[AI] Claude API test failed: {e}")
            
    def call_claude_api(self, prompt, api_key=None, model=None):
        """Call Claude API with given prompt"""
        try:
            
            if not api_key:
                api_key = self.api_key_entry.get().strip()
            if not model:
                model = self.model_var.get()
                
            if not api_key:
                raise Exception("No API key provided")
                
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": model,
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                raise Exception(f"API error {response.status_code}: {response.text}")
                
        except ImportError:
            raise Exception("Please install 'requests' library: pip install requests")
        except Exception as e:
            raise Exception(f"Claude API call failed: {e}")
            
    def analyze_last_clicked(self):
        """Analyze the last clicked element using Claude API"""
        # First get the last clicked element data
        command = {
            "type": "dom_operation",
            "action": "get_last_clicked_element"
        }
        
        self.send_command(command)
        self.log_message("[AI] Getting last clicked element data...")
        
        # Wait for response and then analyze
        self.root.after(2000, self.fetch_element_and_analyze)
        
    def fetch_element_and_analyze(self):
        """Fetch element data and send to Claude for analysis"""
        try:
            self.current_analysis_step = "fetching_element"
            
            command = {
                "type": "dom_operation",
                "action": "get_last_clicked_element"
            }
            self.send_command(command)
            
            # Set a flag to process the next response for Claude analysis
            self.waiting_for_element_analysis = True
            
        except Exception as e:
            self.log_message(f"[AI] Failed to fetch element data: {e}")
            
    def analyze_element_with_claude(self, element_data):
        """Analyze specific element data with Claude API"""
        try:
            # Build comprehensive prompt with actual element data and strategy hints
            prompt = self.build_element_analysis_prompt(element_data)
            
            self.log_message("[AI] Sending element data to Claude for analysis...")
            
            # Call Claude API
            response = self.call_claude_api(prompt)
            
            # Display response
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, response)
            
            # Extract suggested selectors and create copy buttons
            self.extract_and_display_selectors(response)
            
            self.log_message("[AI] Element analysis completed successfully")
            
        except Exception as e:
            error_msg = f"Claude analysis failed: {e}"
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, error_msg)
            self.log_message(f"[AI] {error_msg}")
            
    def build_element_analysis_prompt(self, element_data):
        """Build comprehensive prompt with actual element data and strategy hints"""
        
        # Extract key information from element data
        tag_name = element_data.get('tagName', 'UNKNOWN')
        element_id = element_data.get('id', '')
        class_name = element_data.get('className', '')
        text_content = element_data.get('textContent', '')[:200]  # Limit text length
        attributes = element_data.get('attributes', {})
        current_selector = element_data.get('selector', '')
        
        # Get strategy hints
        strategy_hints = self.get_strategy_hints()
        
        # Build simulated HTML based on element data
        html_attributes = []
        if element_id:
            html_attributes.append(f'id="{element_id}"')
        if class_name:
            html_attributes.append(f'class="{class_name}"')
            
        # Add other important attributes
        for attr, value in attributes.items():
            if attr not in ['id', 'class'] and attr.startswith(('data-', 'aria-', 'name', 'type', 'role')):
                html_attributes.append(f'{attr}="{value}"')
                
        attr_string = ' '.join(html_attributes)
        simulated_html = f'<{tag_name.lower()}{" " + attr_string if attr_string else ""}>{text_content[:50]}{"..." if len(text_content) > 50 else ""}</{tag_name.lower()}>'
        
        # Build strategy-specific guidance
        strategy_guidance = ""
        if strategy_hints:
            strategy_guidance = "\n\nSTRATEGY HINTS (Focus on these approaches):\n"
            for hint in strategy_hints:
                strategy_guidance += f"""
{hint['type'].upper()} APPROACH:
- Context: {hint['description']}
- Recommended techniques: {', '.join(hint['techniques'])}
"""
        else:
            strategy_guidance = "\n\nNo specific strategy hints selected - provide general robust selectors."

        prompt = f"""As a web automation expert, analyze this HTML element and provide the most robust CSS selectors for automation.

ELEMENT TO ANALYZE:
```html
{simulated_html}
```

ELEMENT DETAILS:
- Tag: {tag_name}
- ID: {element_id if element_id else 'None'}
- Classes: {class_name if class_name else 'None'}
- Text Content: {text_content[:100] if text_content else 'None'}
- Current Generated Selector: {current_selector}
- Available Attributes: {', '.join(attributes.keys()) if attributes else 'None'}

{strategy_guidance}

REQUIREMENTS:
1. Provide 3-5 different CSS selector options ranked by stability and reliability
2. If strategy hints are provided above, prioritize those approaches first
3. Consider these priority factors:
   - Uniqueness and specificity
   - Resistance to page changes
   - Cross-browser compatibility
   - Performance efficiency
   - Strategy hint alignment (if applicable)

4. For each selector, explain:
   - Why it's reliable
   - Which strategy it follows (if applicable)
   - Potential failure scenarios
   - Stability score (1-10)

5. Format your response like this:
```
RECOMMENDED SELECTORS:
1. [SELECTOR] - Strategy: [strategy] - Score: X/10 - [Reason]
2. [SELECTOR] - Strategy: [strategy] - Score: X/10 - [Reason]
3. [SELECTOR] - Strategy: [strategy] - Score: X/10 - [Reason]

ANALYSIS:
[Detailed explanation of the element and why certain approaches work better, especially focusing on selected strategies]

BEST CHOICE: [selector] - [explanation why this is the most reliable for the given context and strategies]
```

Focus on creating selectors that work reliably for web automation while following the selected strategy hints when provided."""

        return prompt

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
            
    def generate_best_selector(self):
        """Generate the best CSS selector for automation"""
        try:
            # First get element data
            self.log_message("[AI] Getting element data for best selector generation...")
            
            command = {
                "type": "dom_operation",
                "action": "get_last_clicked_element"
            }
            self.send_command(command)
            
            # Set flag to process next response for best selector generation
            self.waiting_for_best_selector = True
            
        except Exception as e:
            self.log_message(f"[AI] Failed to generate selector: {e}")
            
    def generate_best_selector_with_data(self, element_data):
        """Generate best selector with actual element data and strategy hints"""
        try:
            # Get strategy hints
            strategy_hints = self.get_strategy_hints()
            
            # Build strategy-specific guidance for best selector generation
            strategy_guidance = ""
            if strategy_hints:
                strategy_guidance = "\n\nSTRATEGY PRIORITIES (Focus on these approaches in order of preference):\n"
                for i, hint in enumerate(strategy_hints, 1):
                    strategy_guidance += f"{i}. {hint['type'].upper()}: {hint['description']}\n   Techniques: {', '.join(hint['techniques'])}\n\n"
            else:
                strategy_guidance = "\n\nNo specific strategy hints - focus on general stability and uniqueness."
            
            # Build focused prompt for single best selector with strategy hints
            prompt = f"""Based on this HTML element, generate the single BEST CSS selector for web automation:

ELEMENT DETAILS:
- Tag: {element_data.get('tagName', 'UNKNOWN')}
- ID: {element_data.get('id', 'None')}
- Classes: {element_data.get('className', 'None')}
- Text: {element_data.get('textContent', '')[:100]}
- Attributes: {list(element_data.get('attributes', {}).keys())}
- Current selector: {element_data.get('selector', '')}

{strategy_guidance}

REQUIREMENTS:
- Maximum stability across page updates
- Uniqueness and precision
- Automation best practices
- Avoid fragile selectors (nth-child, absolute positions) UNLESS specifically requested in strategy hints
- If strategy hints are provided, prioritize those approaches first
- Consider the element's context based on the selected strategies

Respond with ONLY the CSS selector, no explanation needed."""

            response = self.call_claude_api(prompt)
            
            # Extract just the selector
            selector = response.strip().strip('`"\'')
            
            # Copy directly to debugger
            self.selector_entry.delete(0, tk.END)
            self.selector_entry.insert(0, selector)
            
            # Log which strategies were used
            strategy_info = ""
            if strategy_hints:
                strategy_names = [hint['type'] for hint in strategy_hints]
                strategy_info = f" (Using strategies: {', '.join(strategy_names)})"
                
            self.log_message(f"[AI] Generated best selector{strategy_info}: {selector}")
            
            # Show in response area with strategy information
            result_text = f"Best Selector Generated:\n{selector}\n\nCopied to debugger input field."
            
            if strategy_hints:
                result_text += f"\n\nStrategies Applied:\n"
                for hint in strategy_hints:
                    result_text += f"- {hint['type']}: {hint['description']}\n"
            
            result_text += f"\nElement analyzed:\n- Tag: {element_data.get('tagName')}\n- ID: {element_data.get('id', 'None')}\n- Classes: {element_data.get('className', 'None')}"
            
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, result_text)
            
        except Exception as e:
            self.log_message(f"[AI] Failed to generate selector: {e}")
            
    def validate_page_selectors(self):
        """Validate all saved selectors on current page"""
        try:
            if not self.selectors:
                messagebox.showinfo("Info", "No saved selectors to validate")
                return
                
            # Build validation prompt
            selector_list = []
            for i, sel in enumerate(self.selectors):
                selector_list.append(f"{i+1}. {sel.get('name', 'Unnamed')}: {sel.get('selector', '')}")
                
            prompt = f"""Analyze these CSS selectors for robustness and suggest improvements:

{chr(10).join(selector_list)}

For each selector, provide:
1. Stability rating (1-10)
2. Potential issues
3. Improved version if needed

Format as a numbered list matching the input."""

            response = self.call_claude_api(prompt)
            
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, f"SELECTOR VALIDATION RESULTS:\n{'='*40}\n\n{response}")
            
            self.log_message("[AI] Page selector validation completed")
            
        except Exception as e:
            self.log_message(f"[AI] Validation failed: {e}")

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
                
    def run(self):
        """Run the debugger"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Handle application closing"""
        if self.ws_server:
            self.ws_server.stop_server()
        self.root.destroy()


def main():
    """Main function"""
    try:
            
        debugger = LLMCPDebugger()
        debugger.run()
    except Exception as e:
        print(f"Failed to start debugger: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()