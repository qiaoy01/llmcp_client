import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tools.tooltip import ToolTip
from datetime import datetime

class UIWithDetailPanel:
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
        
    def setup_detail_panel_content(self, selector_data):
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
    

