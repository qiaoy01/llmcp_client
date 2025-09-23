import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

class UIWithAITab:
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