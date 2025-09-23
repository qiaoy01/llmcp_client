from tkinter import ttk, scrolledtext, messagebox, filedialog
from ui_generators.toolkit_ui import ToolkitUI
import tkinter as tk
import json

class UIWithDebuggerTab:

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

    def display_response(self, response):
        """Display response in the response text area"""
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(1.0, json.dumps(response, indent=2))