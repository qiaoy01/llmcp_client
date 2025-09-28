#!/usr/bin/env python3
"""
MCP Server with HTTP Streaming (SSE) Transport
Based on MCP Inspector approach - no WebSocket, no stdio
"""

import logging
from typing import Optional, Callable
from mcp.mcp_streaming_server import MCPHTTPStreamServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMCPMCPServer:
    """MCP Server Manager with HTTP streaming"""
    
    def __init__(self, host='localhost', port=11809, 
                 log_message: Optional[Callable[[str], None]] = None, 
                 send_command: Optional[Callable[[str, str], None]] = None):
        self.log_message = log_message
        self.server = MCPHTTPStreamServer(use_https=False, host=host, port=port, log_message=log_message, send_command=send_command)
        self.is_running = False

        self.log_message("[MCP] Initialized HTTP Streaming MCP server")
    
    def start_server(self, transport="http"):
        """Start the MCP server"""
        self.log_message(f"[MCP] Using HTTP streaming transport (port 11809)")
        
        success = self.server.start_server()
        if success:
            self.is_running = True
        return success
    
    def stop_server(self):
        """Stop the MCP server"""
        self.server.stop_server()
        self.is_running = False
        self.log_message("[MCP] MCP Server stopped")
    
    def get_server_stats(self):
        """Get server statistics"""
        return self.server.get_server_stats()
    
    def handle_chrome_response(self, response_data):
        """Route Chrome Extension response to the MCP server"""
        if self.server:
            self.server.handle_chrome_response(response_data)