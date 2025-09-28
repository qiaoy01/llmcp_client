#!/usr/bin/env python3
"""
MCP Proxy for Claude Desktop (HTTP Streaming Protocol)
This proxy connects Claude Desktop to the HTTP Streaming MCP server
"""

import asyncio
import aiohttp
import json
import sys
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPProxy:
    def __init__(self, host='localhost', port=11809):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session = None
        self.sse_task = None
        self.pending_requests = {}  # 存储等待响应的请求
        
    async def connect_to_server(self):
        """Connect to HTTP MCP server"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connection with health check
            async with self.session.get(f"{self.base_url}/mcp/v1/health") as resp:
                if resp.status == 200:
                    health_data = await resp.json()
                    return True
                else:
                    logger.error(f"Server health check failed: {resp.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def start_sse_connection(self):
        """Start Server-Sent Events connection for monitoring"""
        try:
            sse_url = f"{self.base_url}/mcp/v1/sse"
            
            async with self.session.get(sse_url) as resp:
                if resp.status != 200:
                    logger.error(f"SSE connection failed: {resp.status}")
                    return
                
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        try:
                            data = json.loads(data_str)
                            await self.handle_sse_message(data)
                        except json.JSONDecodeError:
                            logger.debug(f"Non-JSON SSE data: {data_str}")
                            continue
                    elif line.startswith('event: '):
                        event_type = line[7:]  # Remove 'event: ' prefix
                    elif line.startswith(':'):
                        # Keepalive comment
                        pass
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            pass
    
    async def handle_sse_message(self, data: dict):
        """Handle messages from SSE connection"""
        
        # This is primarily for monitoring/debugging
        # Actual request-response communication happens via HTTP POST
        message_type = data.get('type')
        if message_type == 'request':
            pass
        elif message_type == 'response':
            pass
    
    async def send_request_to_server(self, request: dict) -> Optional[dict]:
        """Send request to MCP server via HTTP POST"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            
            async with self.session.post(
                f"{self.base_url}/mcp/v1/message",
                json=request,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            ) as resp:
                
                if resp.status == 204:
                    # No content response (for notifications)
                    return None
                elif resp.status == 200:
                    response = await resp.json()
                    return response
                else:
                    logger.error(f"Server returned error: {resp.status}")
                    error_text = await resp.text()
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32000,
                            "message": f"Server error: {resp.status} - {error_text}"
                        }
                    }
                    
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {request.get('method')}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32000,
                    "message": "Request timeout"
                }
            }
        except Exception as e:
            logger.error(f"Error sending request to server: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32000,
                    "message": f"Connection error: {str(e)}"
                }
            }
    
    async def handle_stdin(self):
        """Read JSON-RPC requests from stdin (Claude Desktop)"""
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # 非阻塞读取标准输入
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON-RPC request
                request = json.loads(line)
                
                # Send to HTTP server and get response
                response = await self.send_request_to_server(request)
                
                # Send response back to Claude Desktop if there is one
                if response is not None:
                    sys.stdout.write(json.dumps(response) + '\n')
                    sys.stdout.flush()
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from stdin: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                sys.stdout.write(json.dumps(error_response) + '\n')
                sys.stdout.flush()
                
            except Exception as e:
                break
    
    async def run(self):
        """Run the proxy"""
        if not await self.connect_to_server():
            sys.exit(1)
        
        try:
            # Start SSE connection for monitoring (optional, runs in background)
            self.sse_task = asyncio.create_task(self.start_sse_connection())
            
            # Handle stdin (main communication channel)
            await self.handle_stdin()
            
        except KeyboardInterrupt:
            logger.info("Proxy interrupted")
        finally:
            if self.sse_task and not self.sse_task.done():
                self.sse_task.cancel()
                try:
                    await self.sse_task
                except asyncio.CancelledError:
                    pass
            if self.session:
                await self.session.close()

def main():
    """Main entry point"""
    # 确保 Windows 上的 asyncio 正确工作
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    proxy = MCPProxy()
    
    try:
        asyncio.run(proxy.run())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()