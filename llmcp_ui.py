#!/usr/bin/env python3
"""
LLMCP UI Debugger with MCP Server
A comprehensive debugging tool for LLMCP Chrome Extension using WebSocket communication
Now includes MCP Server functionality for AI integration
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import traceback
import requests
import os
import sys
import uuid
import threading
from datetime import datetime
from tools.tooltip import ToolTip
from networks.socket_server import LLMCPWebSocketServer
from mcp.mcp_server import LLMCPMCPServer
from tools.selector_dialog import SelectorDialog
from ui_generators.debugger_tab import UIWithDebuggerTab
from ui_generators.selector_tab import UIWithSelectorTab
from ui_generators.mcp_tab import UIWithMCPTab
from ui_generators.log_tab import UIWithLogTab
from ui_generators.toolkit_ui import ToolkitUI
from ui_generators.ai_tab import UIWithAITab
from llm.claude import ClaudeAPI

class LLMCPDebugger(ToolkitUI, ClaudeAPI, UIWithSelectorTab,
        UIWithDebuggerTab, UIWithAITab, UIWithMCPTab, UIWithLogTab):
    """Complete LLMCP Debugger with all features including MCP Server"""
    
    def __init__(self, mcp_server_only=False):
        self.mcp_server_only = mcp_server_only
        
        # Request tracking for proper response routing
        self.request_tracker = {}  # Maps request_id to source info
        self.request_lock = threading.Lock()
        
        if not mcp_server_only:
            self.init(title="Model Context Debug & Control", geometry="768x1024")
            super().__init__()

        # CSS Selector storage
        self.selector_file = "llmcp_selectors.json"

        # Load existing selectors and auto-load on startup
        self.selectors = self.load_selectors()

        # Current selected selector index for detail panel
        self.current_selected_index = None

        # WebSocket server components
        self.ws_server = LLMCPWebSocketServer(log_message=self.log_message, handle_extension_response=self.handle_extension_response)
        self.is_server_running = False
        
        # MCP server components
        self.mcp_server = LLMCPMCPServer(host="localhost", port=11809, log_message=self.log_mcp_message, send_command=self.send_command)
        
        if mcp_server_only:
            # Run only as MCP server
            self.run_mcp_server_only()
        else:
            # UI components
            self.setup_ui()
            
            # Apply loaded AI config to UI
            self.apply_ai_config_to_ui()
            
            # Auto-start WebSocket server
            self.start_server()
        
    def run_mcp_server_only(self):
        """Run only as MCP server without UI"""
        print("Starting LLMCP MCP Server...")
        print("Server Name: llmcp-browser-automation")
        print("Available Tools: 10 browser automation tools")
        print("Transport: HTTP")
        print("Port: 11809")
        print("Press Ctrl+C to stop")
        
        try:
            # Start the WebSocket server in background for Chrome extension communication
            self.ws_server.start_server()
            
            # Start MCP server (blocking)
            success = self.mcp_server.start_server("http")
            if not success:
                print("Failed to start MCP server")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\nShutting down MCP server...")
            self.mcp_server.stop_server()
            self.ws_server.stop_server()
            sys.exit(0)
        except Exception as e:
            print(f"MCP server error: {e}")
            sys.exit(1)
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Chrome Extension Debugger
        self.setup_debugger_tab(notebook)
        
        # Tab 2: CSS Selector Manager
        self.setup_selector_tab(notebook)
        
        # Tab 3: AI Assistant (Claude)
        self.setup_ai_tab(notebook)

        # Tab 4: MCP Server
        self.setup_mcp_tab(notebook)
        
        # Tab 5: Server Log
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
    
    def send_command(self, command, source="debugger"):
        """Send command to Chrome extension with source tracking
        
        Args:
            command: The command dictionary to send
            source: Either "debugger" (UI) or "mcp" (MCP server)
        """
        log_command_message = None
        if source == "debugger":
            log_command_message = self.log_message
            log_command_message(f"received command from debugger, command={command}")
        elif source == "mcp":
            log_command_message = self.log_mcp_message
            log_command_message(f"received command from mcp, command={command}")

        try:
            if "source" not in command:
                command["source"] = source
                
            # Generate request_id if not present
            if 'request_id' not in command:
                command['request_id'] = str(uuid.uuid4())
            
            request_id = command['request_id']
            
            # Track the request source
            with self.request_lock:
                self.request_tracker[request_id] = {
                    'source': source,
                    'timestamp': datetime.now(),
                    'command': command.get('action', 'unknown')
                }
            
            # Send via WebSocket
            if self.ws_server:
                success = self.ws_server.send_command_sync(command)
                if success:
                    log_command_message(f"[{source.upper()}] Command sent: {command.get('action', 'unknown')}")
                    return {"status": "sent", "message": "Command sent to extension", "request_id": request_id}
                else:
                    # Clean up tracking on failure
                    with self.request_lock:
                        self.request_tracker.pop(request_id, None)
                    return {"error": "No WebSocket clients connected"}
            else:
                # Clean up tracking on failure
                with self.request_lock:
                    self.request_tracker.pop(request_id, None)
                return {"error": "WebSocket server not running"}
                
        except Exception as e:
            # Clean up tracking on error
            if 'request_id' in command:
                with self.request_lock:
                    self.request_tracker.pop(command['request_id'], None)
            return {"error": str(e)}
    
    def handle_extension_response(self, response_data):
        """Handle response from Chrome extension and route to appropriate handler"""
        def update_ui():
            self.log_message(response_data)
            '''
                #code from js
               this.sendMessage({
                type: 'dom_operation_result',
                command: command,
                result: result,
                tabId: tab.id,
                url: tab.url,
                timestamp: new Date().toISOString()
                });
            '''
            source = None
            request_id = None
            if "type" in response_data and "command" in response_data and response_data["type"]=="dom_operation_result":
                original_command = response_data["command"]
                if "request_id" in original_command and "source" in original_command:
                    request_id = original_command.get('request_id')
                    source =  original_command.get("source")
            
            # Determine the source of this response
            self.log_message(f"[MCP Response] {json.dumps(response_data)[:200]}")
            if source=="debugger":
                self.display_response(response_data)
            elif source == "mcp":
                self.mcp_server.handle_chrome_response(response_data)
            elif source is None or request_id is None:
                # Handle special UI cases
                self._handle_ui_specific_responses(response_data)
            
            # Clean up old tracked requests (older than 60 seconds)
            self._cleanup_old_requests()
            
        self.root.after(0, update_ui)
    
    def _handle_ui_specific_responses(self, response_data):
        """Handle UI-specific response processing"""
        # Check if we're waiting for element data for Claude analysis
        if hasattr(self, 'waiting_for_element_analysis') and self.waiting_for_element_analysis:
            self.waiting_for_element_analysis = False
            if response_data.get('result', {}).get('success') and response_data.get('result', {}).get('element'):
                element_data = response_data['result']['element']
                self.analyze_element_with_claude(element_data)
            else:
                self.log_message("[AI] No element data available for analysis")
                if hasattr(self, 'ai_response_text'):
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
                if hasattr(self, 'ai_response_text'):
                    self.ai_response_text.delete(1.0, tk.END)
                    self.ai_response_text.insert(1.0, "Error: No element data available. Please click on an element first.")
    
    def _cleanup_old_requests(self):
        """Clean up tracked requests older than 60 seconds"""
        with self.request_lock:
            current_time = datetime.now()
            expired_ids = [
                req_id for req_id, info in self.request_tracker.items()
                if (current_time - info['timestamp']).total_seconds() > 60
            ]
            for req_id in expired_ids:
                del self.request_tracker[req_id]
            
            if expired_ids:
                self.log_message(f"[Cleanup] Removed {len(expired_ids)} expired request trackers")
    
    # Command implementations - all use source="debugger" by default
    def get_last_click_location(self):
        """Get last click location"""
        command = {
            "type": "dom_operation",
            "action": "get_last_clicked_location"
        }
        response = self.send_command(command, source="debugger")
        return response
        
    def get_last_click_element(self):
        """Get last clicked element"""
        command = {
            "type": "dom_operation",
            "action": "get_last_clicked_element"
        }
        response = self.send_command(command, source="debugger")
        
        # Auto-fill selector if successful
        if response.get("status") == "sent":
            # Wait for actual response to populate selector
            pass
        
        return response
            
    def get_page_info(self):
        """Get page information"""
        command = {
            "type": "dom_operation",
            "action": "get_page_info"
        }
        response = self.send_command(command, source="debugger")
        return response
        
    def click_element(self, from_debugger=True, selector=None):
        """Click element by selector"""
        if from_debugger:
            selector = self.selector_entry.get().strip()
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return {"Warning":"Please enter a CSS selector"}
            
        command = {
            "type": "dom_operation",
            "action": "click_element",
            "selector": selector
        }
        response = self.send_command(command, source="debugger")
        return response
        
    def get_text(self, from_debugger=True, selector=None):
        """Get text from element"""
        if from_debugger:
            selector = self.selector_entry.get().strip()
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return {"Warning":"Please enter a CSS selector"}
            
        command = {
            "type": "dom_operation",
            "action": "get_text",
            "selector": selector
        }
        response = self.send_command(command, source="debugger")
        return response
        
    def input_text(self, from_debugger=True, selector=None, text=None):
        """Input text to element"""
        if from_debugger:
            selector = self.selector_entry.get().strip()
            text = self.text_entry.get()
        
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return {"Warning":"Please enter a CSS selector"}
        if not text:
            messagebox.showwarning("Warning", "Please enter text to input")
            return {"Warning":"Please enter text to input"}
            
        command = {
            "type": "dom_operation",
            "action": "input_text",
            "selector": selector,
            "text": text
        }
        response = self.send_command(command, source="debugger")
        return response
    
    def send_key(self, from_debugger=True, selector=None, key=None):
        """Send key to element"""
        if from_debugger:
            selector = self.selector_entry.get().strip()
            key = self.key_entry.get().strip()
        
        if not selector:
            messagebox.showwarning("Warning", "Please enter a CSS selector")
            return {"Warning":"Please enter a CSS selector"}

        if not key:
            messagebox.showwarning("Warning", "Please enter a key")
            return {"Warning":"Please enter a key"}
            
        command = {
            "type": "dom_operation",
            "action": "send_key",
            "selector": selector,
            "key": key
        }
        response = self.send_command(command, source="debugger")
        return response
    
    def execute_selected_selectors(self, from_debugger=True, selected_indices=0):
        """Execute all selected selectors"""
        if from_debugger:
            selected_indices = self.get_selected_selectors()
        if not selected_indices:
            messagebox.showwarning("Warning", "No selectors selected")
            return {"Warning":"No selectors selected"}
            
        for index in selected_indices:
            if index < len(self.selectors):
                selector_data = self.selectors[index]
                self.execute_single_selector(selector_data)
        return {"result":"executed"}
                
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
            else:
                self.click_element()
                
            self.log_message(f"[Selector] Executed: {selector_data['name']} ({action})")
            
        except Exception as e:
            self.log_message(f"[Selector] Execution failed: {e}")
            
    def analyze_last_clicked(self):
        """Analyze the last clicked element using Claude API"""
        command = {
            "type": "dom_operation",
            "action": "get_last_clicked_element"
        }
        
        self.send_command(command, source="debugger")
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
            self.send_command(command, source="debugger")
            
            # Set a flag to process the next response for Claude analysis
            self.waiting_for_element_analysis = True
            
        except Exception as e:
            self.log_message(f"[AI] Failed to fetch element data: {e}")

    def generate_best_selector(self):
        """Generate the best CSS selector for automation"""
        try:
            self.log_message("[AI] Getting element data for best selector generation...")
            
            command = {
                "type": "dom_operation",
                "action": "get_last_clicked_element"
            }
            self.send_command(command, source="debugger")
            
            # Set flag to process next response for best selector generation
            self.waiting_for_best_selector = True
            
        except Exception as e:
            self.log_message(f"[AI] Failed to generate selector: {e}")
            
    def run(self):
        """Run the debugger"""
        if not self.mcp_server_only:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        
    def on_closing(self):
        """Handle application closing"""
        if self.ws_server:
            self.ws_server.stop_server()
        if hasattr(self, 'mcp_server') and self.mcp_server:
            self.mcp_server.stop_server()
        self.root.destroy()


def print_usage():
    """Print usage information"""
    print("""
LLMCP Debugger v2.2 - Browser Automation Tool with MCP Server and Ollama Client

Usage:
    python llmcp_ui.py                 Run with full UI (default)
    python llmcp_ui.py --mcp-server    Run as MCP server only (no UI)
    python llmcp_ui.py --help          Show this help

MCP Server Mode:
    When run with --mcp-server, the application runs as a Model Context Protocol
    server exposing browser automation capabilities to AI clients like Claude.
    
    Available MCP Tools:
    - find_element: Find elements using CSS selectors
    - click_element: Click elements on web pages
    - input_text: Input text into form fields
    - get_element_text: Extract text from elements
    - send_key: Send keyboard input to elements
    - get_page_info: Get current page information
    - get_last_clicked_element: Get info about last clicked element
    - list_saved_selectors: List all saved CSS selectors

UI Mode:
    Full-featured browser automation debugger with:
    - WebSocket server for Chrome extension communication
    - CSS selector management and testing
    - AI-powered selector analysis with Claude
    - MCP server monitoring and management
    - Ollama MCP Client for local AI-driven browser automation
    - Comprehensive logging and debugging tools
    """)


def main():
    """Main function"""
    try:
        # Parse command line arguments
        if len(sys.argv) > 1:
            if "--help" in sys.argv or "-h" in sys.argv:
                print_usage()
                return
            elif "--mcp-server" in sys.argv:
                # Run as MCP server only
                debugger = LLMCPDebugger(mcp_server_only=True)
                return
            else:
                print(f"Unknown argument: {sys.argv[1]}")
                print("Use --help for usage information")
                return
        
        # Default: Run with full UI
        debugger = LLMCPDebugger()
        debugger.run()
        
    except Exception as e:
        print(f"Failed to start debugger: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()