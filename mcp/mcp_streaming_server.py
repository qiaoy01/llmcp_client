#!/usr/bin/env python3
"""
MCP Server with HTTP/HTTPS Streaming (SSE) Transport
Based on MCP Inspector approach - no WebSocket, no stdio

Dependencies for HTTPS support:
- For self-signed certificates: pip install cryptography
- Or provide your own certificate files
- Or install OpenSSL (fallback option)

Usage Examples:
    # HTTP Server (default)
    server = MCPServerConfig.create_http_server()
    
    # HTTPS with self-signed cert (requires cryptography)
    server = MCPServerConfig.create_https_server_self_signed()
    
    # HTTPS with provided certificates
    server = MCPServerConfig.create_https_server_with_certs(
        cert_file="cert.pem", key_file="key.pem"
    )
"""

import asyncio
import json
import logging
import uuid
import time
import ssl
from typing import Any, Dict, Optional, Set, Callable
from datetime import datetime
import threading
from pathlib import Path
from aiohttp import web
import aiohttp_cors
from asyncio import Queue
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPHTTPStreamServer:
    """HTTP/HTTPS Streaming-based MCP Server Implementation"""
    
    def __init__(self, host='localhost', port=11809, 
                 log_message: Optional[Callable[[str], None]] = None, 
                 send_command: Optional[Callable[[str, str], None]] = None,
                 use_https=False, ssl_cert_file=None, ssl_key_file=None):
        self.log_message = log_message
        self.send_command = send_command
        self.host = host
        self.port = port
        self.use_https = use_https
        self.ssl_cert_file = ssl_cert_file
        self.ssl_key_file = ssl_key_file
        
        self.app = None
        self.runner = None
        self.site = None
        self.server_thread = None
        self.is_running = False
        self.requests_processed = 0
        self.last_activity = None
        self.tools = self.setup_tools()
        
        # SSE client management
        self.sse_clients: Set[Queue] = set()
        
        # Request-Response tracking
        self.pending_requests = {}  
        self.request_timeout = 30
        
        # Request queue for FIFO fallback
        self.request_queue = deque()
        self.request_lock = threading.Lock()
        
        # Setup HTTP app
        self.setup_app()
        
    def setup_app(self):
        """Setup aiohttp application with CORS"""
        self.app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add routes
        route1 = self.app.router.add_route('POST', '/mcp/v1/message', self.handle_message)
        cors.add(route1)
        
        route2 = self.app.router.add_route('GET', '/mcp/v1/sse', self.handle_sse)
        cors.add(route2)
        
        route3 = self.app.router.add_route('GET', '/mcp/v1/health', self.handle_health)
        cors.add(route3)
    
    def setup_tools(self):
        """Setup available MCP tools"""
        return {
            "find_element": {
                "description": "Find an element using CSS selector",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"}
                    },
                    "required": ["selector"]
                }
            },
            "click_element": {
                "description": "Click an element on the page", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"}
                    },
                    "required": ["selector"]
                }
            },
            "input_text": {
                "description": "Input text into an element",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "text": {"type": "string", "description": "Text to input"}
                    },
                    "required": ["selector", "text"]
                }
            },
            "get_element_text": {
                "description": "Get text content from an element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"}
                    },
                    "required": ["selector"]
                }
            },
            "send_key": {
                "description": "Send key press to an element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "key": {"type": "string", "description": "Key to send"}
                    },
                    "required": ["selector", "key"]
                }
            },
            "get_page_info": {
                "description": "Get current page information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "get_last_clicked_element": {
                "description": "Get last clicked element info",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_saved_selectors": {
                "description": "List all saved CSS selectors from llmcp_selectors.json",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    def create_ssl_context(self):
        """Create SSL context for HTTPS"""
        if not self.use_https:
            return None
            
        if not self.ssl_cert_file or not self.ssl_key_file:
            # Create self-signed certificate for development
            return self.create_self_signed_ssl_context()
        
        # Load provided certificate files
        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.ssl_cert_file, self.ssl_key_file)
            self.log_communication(f"[SSL] Loaded certificate: {self.ssl_cert_file}")
            return ssl_context
        except Exception as e:
            self.log_communication(f"[SSL Error] Failed to load certificate: {e}")
            self.log_communication(f"[SSL] Falling back to self-signed certificate")
            return self.create_self_signed_ssl_context()
    
    def create_self_signed_ssl_context(self):
        """Create self-signed SSL context for development using cryptography library"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import tempfile
            import os
            from datetime import datetime, timedelta
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Development"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MCP Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, self.host),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            )
            
            # Build subject alternative names
            san_list = [
                x509.DNSName("localhost"),
            ]
            
            # Add host as DNS name if it's not an IP
            import ipaddress
            try:
                # Try to parse as IP address
                ip_addr = ipaddress.ip_address(self.host)
                san_list.append(x509.IPAddress(ip_addr))
                # Also add localhost IP
                san_list.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
            except ValueError:
                # Host is a domain name, not IP
                san_list.append(x509.DNSName(self.host))
                # Add localhost IP
                san_list.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
            
            cert = cert.add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Save to temporary files
            temp_dir = tempfile.mkdtemp()
            cert_file = os.path.join(temp_dir, 'cert.pem')
            key_file = os.path.join(temp_dir, 'key.pem')
            
            # Write certificate
            with open(cert_file, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Write private key
            with open(key_file, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Create SSL context
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(cert_file, key_file)
            
            self.log_communication(f"[SSL] Created self-signed certificate for {self.host}")
            self.log_communication(f"[SSL] Certificate saved to: {cert_file}")
            
            return ssl_context
                
        except ImportError as e:
            self.log_communication(f"[SSL Error] cryptography library not found: {e}")
            self.log_communication(f"[SSL] Please install: pip install cryptography")
            return self._create_fallback_ssl_context()
        except Exception as e:
            self.log_communication(f"[SSL Error] Failed to create self-signed certificate: {e}")
            self.log_communication(f"[SSL] Trying fallback method...")
            return self._create_fallback_ssl_context()
    
    def _create_fallback_ssl_context(self):
        """Fallback SSL context creation using OpenSSL command"""
        try:
            import tempfile
            import subprocess
            import os
            
            # Try to find OpenSSL in common locations on Windows
            openssl_paths = [
                'openssl',  # In PATH
                'C:\\Program Files\\OpenSSL-Win64\\bin\\openssl.exe',
                'C:\\Program Files (x86)\\OpenSSL-Win32\\bin\\openssl.exe',
                'C:\\OpenSSL-Win64\\bin\\openssl.exe',
                'C:\\OpenSSL-Win32\\bin\\openssl.exe'
            ]
            
            openssl_cmd = None
            for path in openssl_paths:
                try:
                    result = subprocess.run([path, 'version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        openssl_cmd = path
                        self.log_communication(f"[SSL] Found OpenSSL at: {path}")
                        break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
            if not openssl_cmd:
                raise Exception("OpenSSL not found in system")
            
            # Create temporary directory for certificates
            temp_dir = tempfile.mkdtemp()
            cert_file = os.path.join(temp_dir, 'cert.pem')
            key_file = os.path.join(temp_dir, 'key.pem')
            
            # Generate self-signed certificate using openssl
            cmd = [
                openssl_cmd, 'req', '-x509', '-newkey', 'rsa:2048',
                '-keyout', key_file, '-out', cert_file,
                '-days', '365', '-nodes',
                '-subj', f'/CN={self.host}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(cert_file, key_file)
                self.log_communication(f"[SSL] Created self-signed certificate using OpenSSL")
                return ssl_context
            else:
                raise Exception(f"OpenSSL error: {result.stderr}")
                
        except Exception as e:
            self.log_communication(f"[SSL Error] Fallback method failed: {e}")
            self.log_communication(f"[SSL] Options:")
            self.log_communication(f"[SSL]   1. Install cryptography: pip install cryptography")
            self.log_communication(f"[SSL]   2. Install OpenSSL for Windows")
            self.log_communication(f"[SSL]   3. Provide your own certificate files")
            self.log_communication(f"[SSL]   4. Use HTTP mode instead (use_https=False)")
            raise
    
    async def handle_health(self, request):
        """Health check endpoint"""
        protocol = "https" if self.use_https else "http"
        return web.json_response({
            "status": "healthy",
            "is_running": self.is_running,
            "protocol": protocol,
            "host": self.host,
            "port": self.port,
            "clients_connected": len(self.sse_clients),
            "requests_processed": self.requests_processed,
            "pending_requests": len(self.pending_requests),
            "ssl_enabled": self.use_https
        })
    
    async def handle_sse(self, request):
        """Handle Server-Sent Events connection"""
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['X-Accel-Buffering'] = 'no'
        
        await response.prepare(request)
        
        # Create queue for this client
        client_queue = Queue()
        self.sse_clients.add(client_queue)
        
        # Send initial connection event
        protocol = "https" if self.use_https else "http"
        await response.write(f'event: connected\ndata: {{"connected": true, "protocol": "{protocol}"}}\n\n'.encode())
        
        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        client_queue.get(), 
                        timeout=30.0
                    )
                    
                    if message is None:
                        break
                        
                    event_data = f"data: {json.dumps(message)}\n\n"
                    await response.write(event_data.encode())
                    
                except asyncio.TimeoutError:
                    await response.write(b':keepalive\n\n')
                    
        except Exception as e:
            logger.error(f"SSE error: {e}")
        finally:
            self.sse_clients.discard(client_queue)
            
        return response
    
    async def broadcast_to_sse(self, message: dict):
        """Broadcast message to all SSE clients"""
        for client_queue in self.sse_clients:
            try:
                await client_queue.put(message)
            except Exception as e:
                logger.error(f"Failed to send to SSE client: {e}")
    
    async def handle_message(self, request):
        """Handle incoming MCP message via HTTP POST"""
        try:
            data = await request.json()
            
            # Process the JSON-RPC request
            response = await self.handle_jsonrpc_request(data)
            
            if response is not None:
                return web.json_response(response)
            else:
                return web.Response(status=204)
                
        except json.JSONDecodeError:
            return web.json_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }, status=400)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": str(e)}
            }, status=500)
    
    async def handle_jsonrpc_request(self, request: dict) -> dict:
        """Handle JSON-RPC 2.0 request"""
        method = request.get("method")
        request_id = request.get("id")
        
        self.log_communication(f"[Claude→MCP] Method: {method}")
        
        # Broadcast to SSE clients for monitoring
        await self.broadcast_to_sse({
            "type": "request",
            "method": method,
            "id": request_id,
            "timestamp": datetime.now().isoformat()
        })
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "llmcp-browser-automation",
                        "version": "1.0.0"
                    }
                }
            }
            self.log_communication(f"[MCP→Claude] Initialized")
            return response
        
        elif method == "notifications/initialized":
            self.log_communication(f"[MCP→Claude] Notification acknowledged")
            return None
        
        elif method.startswith("notifications/"):
            self.log_communication(f"[MCP→Claude] Notification {method} acknowledged")
            return None
        
        elif method == "tools/list":
            tools_list = [
                {
                    "name": name,
                    "description": info["description"],
                    "inputSchema": info["inputSchema"]
                } 
                for name, info in self.tools.items()
            ]
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_list}
            }
            self.log_communication(f"[MCP→Claude] Listing {len(tools_list)} tools")
            return response
        
        elif method == "prompts/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"prompts": []}
            }
            self.log_communication(f"[MCP→Claude] No prompts available")
            return response
        
        elif method == "resources/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"resources": []}
            }
            self.log_communication(f"[MCP→Claude] No resources available")
            return response
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            self.log_communication(f"[Claude→MCP] Calling tool: {tool_name}")
            
            result = await self.execute_tool_async(tool_name, arguments)
            
            if result.get("success") == False:
                error_text = result.get("error", "Unknown error")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: {error_text}"
                            }
                        ],
                        "isError": True
                    }
                }
            else:
                clean_result = {k: v for k, v in result.items() if k not in ['success']}
                formatted_result = json.dumps(clean_result, indent=2) if clean_result else json.dumps(result, indent=2)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": formatted_result
                            }
                        ]
                    }
                }
            
            self.log_communication(f"[MCP→Claude] Tool result sent")
            return response
        
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            self.log_communication(f"[MCP→Claude] Error: Method not found")
            return response
    
    async def execute_tool_async(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.execute_tool, tool_name, arguments
        )
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call with proper response handling"""
        self.last_activity = datetime.now()
        self.requests_processed += 1
        request_id = str(uuid.uuid4())
        
        self.log_communication(f"[MCP→App] Tool: {tool_name}, Request ID: {request_id[:8]}")
        
        try:
            # Special handling for list_saved_selectors (local operation)
            if tool_name == "list_saved_selectors":
                result = self.read_saved_selectors()
                self.log_communication(f"[App→MCP] Local result: {len(result.get('selectors', []))} selectors found")
                return result
            
            # Map tool names to Chrome Extension actions
            action_mapping = {
                "find_element": "find_element",
                "click_element": "click_element", 
                "input_text": "input_text",
                "get_element_text": "get_text",
                "send_key": "send_key",
                "get_page_info": "get_page_info",
                "get_last_clicked_element": "get_last_clicked_element"
            }
            
            action = action_mapping.get(tool_name, tool_name)
            
            # Construct command for Chrome Extension
            command = {
                "type": "dom_operation",
                "action": action,
                "request_id": request_id
            }
            command.update(arguments)
            
            self.log_communication(f"[MCP] Sending command to Chrome: {action}")
            
            # Setup response tracking
            response_event = threading.Event()
            response_container = {"data": None}
            
            # Store in pending_requests
            with self.request_lock:
                self.pending_requests[request_id] = {
                    "event": response_event,
                    "container": response_container,
                    "tool_name": tool_name,
                    "timestamp": time.time()
                }
                self.request_queue.append(request_id)
            
            # Use the updated send_command with source parameter
            send_result = self.send_command(command, "mcp")
            
            if send_result.get("status") != "sent":
                error_msg = send_result.get("error", "Failed to send command")
                self.log_communication(f"[Error] {error_msg}")
                return {"success": False, "error": error_msg}
            
            self.log_communication(f"[MCP] Command sent, waiting for response...")
            
            # Wait for response with timeout
            if response_event.wait(timeout=self.request_timeout):
                response = response_container["data"]
                
                if response is None:
                    self.log_communication(f"[Error] Received None response")
                    return {"success": False, "error": "No response data received"}
                
                self.log_communication(f"[Chrome→MCP] Response received: {json.dumps(response)[:200]}")
                
                # Parse response based on structure
                if isinstance(response, dict):
                    # Check various response formats
                    if 'result' in response:
                        result = response['result']
                    elif 'success' in response:
                        result = response
                    elif 'type' in response and response['type'] == 'dom_operation_result':
                        result = response
                    else:
                        result = response
                    
                    # Special handling for get_element_text
                    if tool_name == "get_element_text" and isinstance(result, dict):
                        if result.get('success'):
                            if 'text' in result:
                                return {
                                    "success": True,
                                    "text": result['text'],
                                    "element_info": result.get('elementInfo', {})
                                }
                            elif 'elementInfo' in result:
                                element_info = result['elementInfo']
                                text = element_info.get('innerText', '') or element_info.get('textContent', '')
                                return {
                                    "success": True,
                                    "text": text,
                                    "element_info": element_info
                                }
                    
                    return result
                else:
                    return {"success": False, "error": f"Invalid response format: {type(response)}"}
            else:
                self.log_communication(f"[Error] Request timeout after {self.request_timeout}s for {tool_name}")
                
                # Try FIFO fallback
                if self.request_queue and not response_container["data"]:
                    self.log_communication(f"[MCP] Checking for any unmatched responses...")
                    time.sleep(1)  # Brief wait for late responses
                    
                    if response_container["data"]:
                        response = response_container["data"]
                        self.log_communication(f"[MCP] Late response received")
                        return response if isinstance(response, dict) else {"success": False, "error": "Invalid late response"}
                
                return {"success": False, "error": f"Request timeout - Chrome extension did not respond within {self.request_timeout} seconds"}

                
        except Exception as e:
            error_msg = f"Tool execution error: {e}"
            logger.error(error_msg)
            self.log_communication(f"[Error] {error_msg}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
        finally:
            # Clean up
            with self.request_lock:
                self.pending_requests.pop(request_id, None)
                try:
                    self.request_queue.remove(request_id)
                except ValueError:
                    pass
    
    def handle_chrome_response(self, response_data):
        """Handle response from Chrome Extension"""
        self.log_communication(f"[MCP] Received Chrome response")
        
        request_id = response_data.get('command').get("request_id")
        
        with self.request_lock:
            # Method 1: Direct ID match
            if request_id and request_id in self.pending_requests:
                pending = self.pending_requests[request_id]
                pending["container"]["data"] = response_data
                pending["event"].set()
                self.log_communication(f"[MCP] Matched response for request {request_id[:8]}")
                return
            
            # Method 2: FIFO fallback for unmatched responses
            if self.request_queue and not request_id:
                oldest_id = self.request_queue[0]
                if oldest_id in self.pending_requests:
                    pending = self.pending_requests[oldest_id]
                    
                    # Validate this looks like the right response
                    tool_name = pending.get('tool_name')
                    if self._validate_response_for_tool(response_data, tool_name):
                        self.request_queue.popleft()
                        pending["container"]["data"] = response_data
                        pending["event"].set()
                        self.log_communication(f"[MCP] FIFO matched response for tool: {tool_name}")
                        return
            
            self.log_communication(f"[MCP] Warning: Unmatched response (request_id: {request_id})")
            self.log_communication(f"[MCP] Pending requests: {list(self.pending_requests.keys())}")
    
    def _validate_response_for_tool(self, response_data: dict, tool_name: str) -> bool:
        """Validate if response matches expected format for tool"""
        if not isinstance(response_data, dict):
            return False
        
        # General validation
        if any(key in response_data for key in ['success', 'result', 'error', 'type']):
            return True
        
        # Tool-specific validation
        if tool_name == "get_page_info" and ('url' in response_data or 'title' in response_data):
            return True
        if tool_name in ["get_element_text", "get_last_clicked_element"] and 'element' in response_data:
            return True
        
        return False
    
    def read_saved_selectors(self) -> Dict[str, Any]:
        """Read saved selectors from llmcp_selectors.json"""
        try:
            selectors_file = Path("llmcp_selectors.json")
            
            if not selectors_file.exists():
                script_dir = Path(__file__).parent
                selectors_file = script_dir / "llmcp_selectors.json"
            
            if not selectors_file.exists():
                return {
                    "success": False,
                    "error": "llmcp_selectors.json file not found",
                    "selectors": []
                }
            
            with open(selectors_file, 'r', encoding='utf-8') as f:
                selectors_data = json.load(f)
            
            return {
                "success": True,
                "message": "Saved selectors loaded successfully",
                "file_path": str(selectors_file.absolute()),
                "selectors": selectors_data
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON format: {str(e)}",
                "selectors": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read selectors: {str(e)}",
                "selectors": []
            }
    
    def log_communication(self, message: str):
        """Log communication between components"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        
        # Log to console
        logger.info(log_entry)
        
        # Log to MCP tab if UI is available
        if self.log_message:
            self.log_message(message)
    
    def start_server(self):
        """Start HTTP/HTTPS MCP server"""
        def run_server():
            async def start_http_server():
                try:
                    self.runner = web.AppRunner(self.app)
                    await self.runner.setup()
                    
                    # Create SSL context if HTTPS is enabled
                    ssl_context = None
                    if self.use_https:
                        ssl_context = self.create_ssl_context()
                    
                    self.site = web.TCPSite(
                        self.runner, 
                        self.host, 
                        self.port,
                        ssl_context=ssl_context
                    )
                    
                    await self.site.start()
                    
                    self.is_running = True
                    protocol = "https" if self.use_https else "http"
                    self.log_communication(f"[Server] MCP {protocol.upper()} Server started on {protocol}://{self.host}:{self.port}")
                    
                    if self.use_https and not (self.ssl_cert_file and self.ssl_key_file):
                        self.log_communication(f"[SSL] Using self-signed certificate (development only)")
                        self.log_communication(f"[SSL] For production, provide cert_file and key_file parameters")
                    
                    while self.is_running:
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"MCP Server error: {e}")
                    self.log_communication(f"[Server Error] {e}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(start_http_server())
            except Exception as e:
                logger.error(f"Loop error: {e}")
            finally:
                loop.close()
        
        try:
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop HTTP/HTTPS server"""
        self.is_running = False
        protocol = "https" if self.use_https else "http"
        self.log_communication(f"[Server] Stopping MCP {protocol.upper()} Server")
        
        for client_queue in self.sse_clients:
            try:
                client_queue.put_nowait(None)
            except:
                pass
    
    def get_server_stats(self):
        """Get server statistics"""
        protocol = "https" if self.use_https else "http"
        return {
            "is_running": self.is_running,
            "protocol": protocol,
            "ssl_enabled": self.use_https,
            "clients_connected": len(self.sse_clients),
            "requests_processed": self.requests_processed,
            "pending_requests": len(self.pending_requests),
            "last_activity": self.last_activity.strftime("%Y-%m-%d %H:%M:%S") if self.last_activity else "Never",
            "available_tools": len(self.tools),
            "mcp_sdk_available": True,
            "transport": protocol,
            "host": self.host,
            "port": self.port
        }
