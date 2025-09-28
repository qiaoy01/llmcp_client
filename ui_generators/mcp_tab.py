import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import json
import os

class UIWithMCPTab:
    """
    MCP Tab UI - HTTP Streaming Transport Version
    """
    
    def setup_mcp_tab(self, notebook):
        """Setup MCP Server monitoring and management tab"""
        mcp_frame = ttk.Frame(notebook)
        notebook.add(mcp_frame, text="MCP Server")
        
        # Server Status Section
        status_section = ttk.LabelFrame(mcp_frame, text="MCP Server Status")
        status_section.pack(fill='x', padx=5, pady=5)
        
        status_info_frame = ttk.Frame(status_section)
        status_info_frame.pack(fill='x', padx=5, pady=5)
        
        # Status indicators
        self.mcp_status_label = ttk.Label(status_info_frame, text="Status: Not Started")
        self.mcp_status_label.pack(side='left', padx=5)
        
        self.mcp_clients_label = ttk.Label(status_info_frame, text="SSE Clients: 0")
        self.mcp_clients_label.pack(side='left', padx=20)
        
        self.mcp_requests_label = ttk.Label(status_info_frame, text="Requests: 0")
        self.mcp_requests_label.pack(side='left', padx=20)
        
        self.mcp_last_activity_label = ttk.Label(status_info_frame, text="Last Activity: Never")
        self.mcp_last_activity_label.pack(side='left', padx=20)
        
        # Server controls
        control_frame = ttk.Frame(status_section)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        self.mcp_start_btn = ttk.Button(control_frame, text="Start MCP Server", command=self.start_mcp_server)
        self.mcp_start_btn.pack(side='left', padx=5)
        
        self.mcp_stop_btn = ttk.Button(control_frame, text="Stop MCP Server", command=self.stop_mcp_server)
        self.mcp_stop_btn.pack(side='left', padx=5)
        
        self.mcp_restart_btn = ttk.Button(control_frame, text="Restart MCP Server", command=self.restart_mcp_server)
        self.mcp_restart_btn.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Refresh Stats", command=self.refresh_mcp_stats).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Test Connection", command=self.test_http_connection).pack(side='left', padx=5)
        
        # Transport info - HTTP Streaming
        transport_frame = ttk.Frame(status_section)
        transport_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(transport_frame, text="Transport:").pack(side='left')
        ttk.Label(transport_frame, text="HTTP Streaming", font=('', 9, 'bold')).pack(side='left', padx=5)
        ttk.Label(transport_frame, text="MCP Port: 11809", font=('Consolas', 9)).pack(side='left', padx=10)
        ttk.Label(transport_frame, text="Extension Port: 11808", font=('Consolas', 9)).pack(side='left', padx=10)
        
        # SDK Status
        sdk_frame = ttk.Frame(status_section)
        sdk_frame.pack(fill='x', padx=5, pady=2)
        
        self.mcp_sdk_status_label = ttk.Label(sdk_frame, text="MCP SDK: Checking...")
        self.mcp_sdk_status_label.pack(side='left')
        
        # Configuration Section
        config_section = ttk.LabelFrame(mcp_frame, text="Server Configuration")
        config_section.pack(fill='x', padx=5, pady=5)
        
        # Server info
        info_frame = ttk.Frame(config_section)
        info_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(info_frame, text="Server Name:").grid(row=0, column=0, sticky='w', padx=5)
        ttk.Label(info_frame, text="llmcp-browser-automation", font=('Consolas', 9)).grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(info_frame, text="Protocol Version:").grid(row=1, column=0, sticky='w', padx=5)
        ttk.Label(info_frame, text="2024-11-05", font=('Consolas', 9)).grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(info_frame, text="Available Tools:").grid(row=2, column=0, sticky='w', padx=5)
        self.mcp_tools_count_label = ttk.Label(info_frame, text="10", font=('Consolas', 9))
        self.mcp_tools_count_label.grid(row=2, column=1, sticky='w', padx=5)
        
        # HTTP Endpoints
        endpoints_frame = ttk.LabelFrame(config_section, text="HTTP Endpoints")
        endpoints_frame.pack(fill='x', padx=5, pady=5)
        
        endpoints_text = """• POST http://localhost:11809/mcp/v1/message - Send MCP messages
• GET  http://localhost:11809/mcp/v1/sse - Server-Sent Events stream
• GET  http://localhost:11809/mcp/v1/health - Health check"""
        
        ttk.Label(endpoints_frame, text=endpoints_text, font=('Consolas', 9), justify='left').pack(padx=5, pady=5)
        
        # Available Tools Section
        tools_section = ttk.LabelFrame(mcp_frame, text="Available MCP Tools")
        tools_section.pack(fill='x', padx=5, pady=5)
        
        # Create treeview for tools
        tools_frame = ttk.Frame(tools_section)
        tools_frame.pack(fill='x', padx=5, pady=5)
        
        columns = ('Tool', 'Description', 'Parameters')
        self.mcp_tools_tree = ttk.Treeview(tools_frame, columns=columns, show='headings', height=8)
        
        self.mcp_tools_tree.heading('Tool', text='Tool Name')
        self.mcp_tools_tree.column('Tool', width=200)
        
        self.mcp_tools_tree.heading('Description', text='Description')
        self.mcp_tools_tree.column('Description', width=300)
        
        self.mcp_tools_tree.heading('Parameters', text='Parameters')
        self.mcp_tools_tree.column('Parameters', width=200)
        
        # Add scrollbar for tools
        tools_scrollbar = ttk.Scrollbar(tools_frame, orient='vertical', command=self.mcp_tools_tree.yview)
        self.mcp_tools_tree.configure(yscrollcommand=tools_scrollbar.set)
        
        self.mcp_tools_tree.pack(side='left', fill='both', expand=True)
        tools_scrollbar.pack(side='right', fill='y')
        
        # Connection Guide Section - HTTP Client
        guide_section = ttk.LabelFrame(mcp_frame, text="Connection Guide (HTTP Streaming)")
        guide_section.pack(fill='x', padx=5, pady=5)
        
        guide_text = tk.Text(guide_section, height=12, wrap='word', bg='#f8f9fa')
        guide_text.pack(fill='x', padx=5, pady=5)
        
        # Get script paths
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            client_path = os.path.join(current_dir, "mcp_http_client.py")
        except:
            client_path = "path/to/mcp_http_client.py"
        
        guide_content = f"""How to connect Claude Desktop to this MCP Server:

1. Architecture:
   - Chrome Extension ←→ WebSocket(11808) ←→ LLMCP App
   - Claude Desktop ←→ HTTP Client ←→ HTTP(11809) ←→ MCP Server
   - MCP Server provides SSE for real-time event streaming

2. Setup for Claude Desktop:
   Add to claude_desktop_config.json:

{{
  "mcpServers": {{
    "llmcp-browser-automation": {{
      "command": "python",
      "args": ["{client_path}", "--server", "http://localhost:11809"]
    }}
  }}
}}

3. Direct HTTP Testing:
   - Initialize: POST http://localhost:11809/mcp/v1/message
     Body: {{"jsonrpc": "2.0", "method": "initialize", "id": 1}}
   
   - List tools: POST http://localhost:11809/mcp/v1/message
     Body: {{"jsonrpc": "2.0", "method": "tools/list", "id": 2}}

4. SSE Monitoring:
   Connect to http://localhost:11809/mcp/v1/sse for real-time events"""
        
        guide_text.insert(1.0, guide_content)
        guide_text.configure(state='disabled')
        
        # Copy config button
        button_frame = ttk.Frame(guide_section)
        button_frame.pack(anchor='e', padx=5, pady=2)
        
        ttk.Button(button_frame, text="Copy Config to Clipboard", 
                  command=self.copy_mcp_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Copy Client Path", 
                  command=self.copy_client_path).pack(side='left', padx=5)
        
        # MCP Activity Log Section
        log_section = ttk.LabelFrame(mcp_frame, text="MCP Activity Log")
        log_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        log_controls = ttk.Frame(log_section)
        log_controls.pack(fill='x', padx=5, pady=2)
        
        ttk.Button(log_controls, text="Clear MCP Log", command=self.clear_mcp_log).pack(side='left', padx=5)
        ttk.Button(log_controls, text="Export MCP Log", command=self.export_mcp_log).pack(side='left', padx=5)
        
        self.mcp_auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_controls, text="Auto Scroll", variable=self.mcp_auto_scroll_var).pack(side='left', padx=5)
        
        self.mcp_log_text = scrolledtext.ScrolledText(log_section, height=10)
        self.mcp_log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize tools list
        self.populate_mcp_tools()
        
        # Start periodic stats update
        self.update_mcp_stats()
    
    def populate_mcp_tools(self):
        """Populate the MCP tools list"""
        tools_info = [
            ("find_element", "Find an element using CSS selector", "selector: str"),
            ("click_element", "Click an element on the page", "selector: str"),
            ("input_text", "Input text into an element", "selector: str, text: str"),
            ("get_element_text", "Get text content from element", "selector: str"),
            ("send_key", "Send key press to element", "selector: str, key: str"),
            ("get_page_info", "Get current page information", "None"),
            ("get_last_clicked_element", "Get last clicked element info", "None"),
            ("list_saved_selectors", "List all saved CSS selectors", "None")
        ]
        
        for tool_name, description, params in tools_info:
            self.mcp_tools_tree.insert('', 'end', values=(tool_name, description, params))
    
    def test_http_connection(self):
        """Test HTTP connection to MCP server"""
        try:
            import requests
            
            # Test health endpoint
            response = requests.get("http://localhost:11809/mcp/v1/health", timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                status = "Running" if data.get("is_running") else "Not Running"
                clients = data.get("clients_connected", 0)
                requests_count = data.get("requests_processed", 0)
                
                message = f"Server Status: {status}\nSSE Clients: {clients}\nRequests Processed: {requests_count}"
                messagebox.showinfo("Connection Test", f"Successfully connected to MCP Server!\n\n{message}")
                self.log_mcp_message("HTTP connection test successful")
            else:
                messagebox.showerror("Connection Test", f"Server returned status code: {response.status_code}")
                self.log_mcp_message(f"Connection test failed: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Test", "Cannot connect to MCP Server at http://localhost:11809")
            self.log_mcp_message("Connection test failed: Server not reachable")
        except Exception as e:
            messagebox.showerror("Connection Test", f"Connection test failed: {e}")
            self.log_mcp_message(f"Connection test error: {e}")
    
    def start_mcp_server(self):
        """Start the MCP server"""
        try:
            if hasattr(self, 'mcp_server') and self.mcp_server:
                success = self.mcp_server.start_server("http")
                
                if success:
                    self.mcp_start_btn.configure(state='disabled')
                    self.mcp_stop_btn.configure(state='normal')
                    self.mcp_restart_btn.configure(state='normal')
                    self.log_mcp_message("MCP Server started successfully (HTTP on port 11809)")
                    messagebox.showinfo("Success", "MCP HTTP Server started successfully!\nListening on http://localhost:11809")
                else:
                    self.log_mcp_message("Failed to start MCP Server")
                    messagebox.showerror("Error", "Failed to start MCP Server")
            else:
                self.log_mcp_message("MCP Server not initialized")
                messagebox.showerror("Error", "MCP Server not available")
                
        except Exception as e:
            self.log_mcp_message(f"Error starting MCP Server: {e}")
            messagebox.showerror("Error", f"Failed to start MCP Server: {e}")
    
    def stop_mcp_server(self):
        """Stop the MCP server"""
        try:
            if hasattr(self, 'mcp_server') and self.mcp_server:
                self.mcp_server.stop_server()
                self.mcp_start_btn.configure(state='normal')
                self.mcp_stop_btn.configure(state='disabled')
                self.mcp_restart_btn.configure(state='disabled')
                self.log_mcp_message("MCP Server stopped")
                messagebox.showinfo("Info", "MCP Server stopped")
                
        except Exception as e:
            self.log_mcp_message(f"Error stopping MCP Server: {e}")
            messagebox.showerror("Error", f"Failed to stop MCP Server: {e}")
    
    def restart_mcp_server(self):
        """Restart the MCP server"""
        self.log_mcp_message("Restarting MCP Server...")
        self.stop_mcp_server()
        self.root.after(2000, self.start_mcp_server)
    
    def refresh_mcp_stats(self):
        """Manually refresh MCP server statistics"""
        self.update_mcp_stats()
        self.log_mcp_message("MCP Server statistics refreshed")
    
    def update_mcp_stats(self):
        """Update MCP server statistics display"""
        try:
            if hasattr(self, 'mcp_server') and self.mcp_server:
                stats = self.mcp_server.get_server_stats()
                
                # Update status labels
                status = "Running" if stats['is_running'] else "Stopped"
                self.mcp_status_label.config(text=f"Status: {status}")
                
                self.mcp_clients_label.config(text=f"SSE Clients: {stats['clients_connected']}")
                self.mcp_requests_label.config(text=f"Requests: {stats['requests_processed']}")
                self.mcp_last_activity_label.config(text=f"Last Activity: {stats['last_activity']}")
                
                # Update tools count
                self.mcp_tools_count_label.config(text=str(stats.get('available_tools', 10)))
                
                # Update SDK status
                transport = stats.get('transport', 'http').upper()
                sdk_status = f"Available ({transport})" if stats.get('mcp_sdk_available') else "Not Available"
                sdk_color = "green" if stats.get('mcp_sdk_available') else "red"
                self.mcp_sdk_status_label.config(text=f"MCP SDK: {sdk_status}", foreground=sdk_color)
                
            else:
                self.mcp_status_label.config(text="Status: Not Initialized")
                self.mcp_clients_label.config(text="SSE Clients: N/A")
                self.mcp_requests_label.config(text="Requests: N/A")
                self.mcp_last_activity_label.config(text="Last Activity: N/A")
                self.mcp_sdk_status_label.config(text="MCP SDK: Not Available", foreground="red")
                
        except Exception as e:
            self.log_mcp_message(f"Error updating stats: {e}")
        
        # Schedule next update
        self.root.after(5000, self.update_mcp_stats)
    
    def log_mcp_message(self, message):
        """Add message to MCP activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def update_mcp_log():
            if hasattr(self, 'mcp_log_text'):
                self.mcp_log_text.insert(tk.END, log_entry)
                if self.mcp_auto_scroll_var.get():
                    self.mcp_log_text.see(tk.END)
                    
        self.root.after(0, update_mcp_log)
    
    def clear_mcp_log(self):
        """Clear the MCP activity log"""
        if hasattr(self, 'mcp_log_text'):
            self.mcp_log_text.delete(1.0, tk.END)
            self.log_mcp_message("MCP log cleared")
    
    def export_mcp_log(self):
        """Export MCP log to file"""
        if not hasattr(self, 'mcp_log_text'):
            return
            
        filename = filedialog.asksaveasfilename(
            title="Export MCP Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                content = self.mcp_log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"LLMCP MCP Server Activity Log\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(content)
                    
                messagebox.showinfo("Success", f"MCP log exported to {filename}")
                self.log_mcp_message(f"Log exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export log: {e}")
                self.log_mcp_message(f"Export failed: {e}")
    
    def copy_mcp_config(self):
        """Copy MCP server configuration to clipboard"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            client_path = os.path.join(current_dir, "mcp_http_client.py")
        except:
            client_path = "path/to/mcp_http_client.py"
        
        config = {
            "mcpServers": {
                "llmcp-browser-automation": {
                    "command": "python",
                    "args": [client_path, "--server", "http://localhost:11809"],
                    "description": "Browser automation server for web interaction (HTTP)"
                }
            }
        }
        
        config_json = json.dumps(config, indent=2)
        
        try:
            self.copy_to_clipboard(config_json)
            self.log_mcp_message("MCP server configuration copied to clipboard")
            messagebox.showinfo("Copied", "MCP server configuration copied to clipboard!")
        except Exception as e:
            self.log_mcp_message(f"Failed to copy config: {e}")
            messagebox.showerror("Error", f"Failed to copy configuration: {e}")
    
    def copy_client_path(self):
        """Copy client script path to clipboard"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            client_path = os.path.join(current_dir, "mcp_http_client.py")
        except:
            client_path = "path/to/mcp_http_client.py"
        
        try:
            self.copy_to_clipboard(client_path)
            self.log_mcp_message(f"Client path copied: {client_path}")
            messagebox.showinfo("Copied", f"Client path copied to clipboard:\n{client_path}")
        except Exception as e:
            self.log_mcp_message(f"Failed to copy client path: {e}")
            messagebox.showerror("Error", f"Failed to copy path: {e}")