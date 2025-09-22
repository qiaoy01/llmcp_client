import asyncio
import websockets
import json
import time
import threading

class LLMCPWebSocketServer:
    """WebSocket Server for Chrome Extension Communication"""
    
    def __init__(self, debugger, host='localhost', port=11808):
        self.debugger = debugger
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None
        self.loop = None
        self.server_thread = None
        
    async def register_client(self, websocket):
        """Register new WebSocket connection"""
        self.clients.add(websocket)
        client_addr = getattr(websocket, 'remote_address', 'unknown')
        self.debugger.log_message(f"[WebSocket] Client connected from {client_addr}")
        
        try:
            await websocket.send(json.dumps({
                "type": "connection_established",
                "message": "Connected to LLMCP Debugger Server",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }))
        except Exception as e:
            self.debugger.log_message(f"[WebSocket] Failed to send welcome: {e}")
        
    async def unregister_client(self, websocket):
        """Unregister WebSocket connection"""
        self.clients.discard(websocket)
        self.debugger.log_message("[WebSocket] Client disconnected")
        
    async def handle_message(self, websocket, data):
        """Handle received messages"""
        message_type = data.get('type', 'unknown')
        self.debugger.log_message(f"[WebSocket] Received: {message_type}")
        
        try:
            if message_type == 'dom_operation_result':
                self.debugger.handle_extension_response(data)
            elif message_type == 'heartbeat':
                await websocket.send(json.dumps({
                    "type": "heartbeat_response",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }))
            elif message_type == 'status_request':
                await websocket.send(json.dumps({
                    "type": "status_response",
                    "status": "running",
                    "connected_clients": len(self.clients),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }))
            elif message_type in ['tab_updated', 'tab_activated']:
                url = data.get('url', 'Unknown URL')
                self.debugger.log_message(f"[WebSocket] {message_type.replace('_', ' ').title()}: {url}")
            
            # Send confirmation response
            await websocket.send(json.dumps({
                "type": "message_received",
                "original_type": message_type,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }))
            
        except Exception as e:
            self.debugger.log_message(f"[WebSocket] Error handling message: {e}")
            
    async def broadcast_command(self, command):
        """Broadcast command to all connected clients"""
        if not self.clients:
            return False
            
        message = json.dumps(command)
        successful_sends = 0
        disconnected = set()
        
        for client in list(self.clients):
            try:
                await client.send(message)
                successful_sends += 1
            except:
                disconnected.add(client)
                
        # Clean up disconnected clients
        self.clients -= disconnected
        
        return successful_sends > 0
        
    def start_server(self):
        """Start WebSocket server"""
        def run_server():
            async def websocket_handler(websocket):
                """WebSocket connection handler"""
                await self.register_client(websocket)
                try:
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self.handle_message(websocket, data)
                        except json.JSONDecodeError as e:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": f"Invalid JSON: {e}",
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                            }))
                        except Exception as e:
                            self.debugger.log_message(f"[WebSocket] Message error: {e}")
                            
                except websockets.exceptions.ConnectionClosed:
                    self.debugger.log_message("[WebSocket] Connection closed")
                except Exception as e:
                    self.debugger.log_message(f"[WebSocket] Connection error: {e}")
                finally:
                    await self.unregister_client(websocket)
            
            async def start_websocket_server():
                try:
                    self.server = await websockets.serve(
                        websocket_handler,
                        self.host,
                        self.port,
                        ping_interval=30,
                        ping_timeout=10
                    )
                    
                    self.debugger.log_message(f"[WebSocket] Server started on ws://{self.host}:{self.port}")
                    
                    # Wait for server to close
                    await self.server.wait_closed()
                    
                except Exception as e:
                    self.debugger.log_message(f"[WebSocket] Server error: {e}")
                    
            try:
                # Create event loop
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                
                # Run server
                self.loop.run_until_complete(start_websocket_server())
                
            except Exception as e:
                self.debugger.log_message(f"[WebSocket] Loop error: {e}")
            finally:
                if self.loop and not self.loop.is_closed():
                    self.loop.close()
                    
        try:
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            time.sleep(0.5)  # Wait for server to start
            return True
            
        except Exception as e:
            self.debugger.log_message(f"[WebSocket] Failed to start thread: {e}")
            return False
            
    def stop_server(self):
        """Stop WebSocket server"""
        if self.server and self.loop:
            try:
                asyncio.run_coroutine_threadsafe(self._stop_server(), self.loop)
            except:
                pass
                
    async def _stop_server(self):
        """Async stop server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
    def send_command_sync(self, command):
        """Send command synchronously"""
        if not self.loop or self.loop.is_closed():
            return False
            
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.broadcast_command(command), 
                self.loop
            )
            return future.result(timeout=3.0)
        except:
            return False
