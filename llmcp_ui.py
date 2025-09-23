#!/usr/bin/env python3
"""
LLMCP UI Debugger
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
from ui_generators.debugger_tab import UIWithDebuggerTab
from ui_generators.selector_tab import UIWithSelectorTab
from ui_generators.log_tab import UIWithLogTab

from ui_generators.toolkit_ui import ToolkitUI
from ui_generators.ai_tab import UIWithAITab
from llm.claude import ClaudeAPI

class LLMCPDebugger(ToolkitUI,ClaudeAPI, UIWithSelectorTab,
        UIWithDebuggerTab, UIWithAITab,  UIWithLogTab):
    """Complete LLMCP Debugger with all features"""
    
    def __init__(self):
        self.init(title="LLMCP Debugger v2.0 (WebSocket Version)", geometry="1280x1024")
        super().__init__()

        # CSS Selector storage
        self.selector_file = "llmcp_selectors.json"

        # Load existing selectors and auto-load on startup
        self.selectors = self.load_selectors()

        # Current selected selector index for detail panel
        self.current_selected_index = None

        # WebSocket server components
        self.ws_server = LLMCPWebSocketServer(self)
        self.is_server_running = False
        
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
        
            
    def execute_current_selector(self):
        """Execute currently selected selector"""
        if self.current_selected_index is not None and self.current_selected_index < len(self.selectors):
            selector_data = self.selectors[self.current_selected_index]
            self.execute_single_selector(selector_data)
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