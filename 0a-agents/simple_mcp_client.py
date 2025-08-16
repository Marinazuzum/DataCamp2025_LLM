import json
import subprocess
import time
import threading
from typing import Dict, Any, List, Optional

class SimpleMCPClient:
    def __init__(self, server_command: List[str]):
        self.server_command = server_command
        self.process = None
        self.request_id = 0
        self.available_tools = {}
        self.is_initialized = False
        
    def start_server(self):
        """Start the FastMCP server process"""
        try:
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            print(f"Started server with PID: {self.process.pid}")
            
            # Give server time to start
            time.sleep(1)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise RuntimeError(f"Server failed to start. STDERR: {stderr}")
                
        except Exception as e:
            print(f"Failed to start server: {e}")
            raise
            
    def stop_server(self):
        """Stop the server process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            print("Server stopped")
            
    def _get_next_request_id(self) -> int:
        self.request_id += 1
        return self.request_id
        
    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
        """Send a JSON-RPC request with timeout"""
        if not self.process:
            raise RuntimeError("Server not started")
            
        if self.process.poll() is not None:
            raise RuntimeError("Server process has died")
            
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": method
        }
        
        if params:
            request["params"] = params
            
        # Send request
        request_str = json.dumps(request) + "\n"
        
        try:
            self.process.stdin.write(request_str)
            self.process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("Failed to write to server (broken pipe)")
        
        # Read response with timeout
        response_str = None
        
        def read_response():
            nonlocal response_str
            try:
                response_str = self.process.stdout.readline().strip()
            except:
                pass
                
        thread = threading.Thread(target=read_response)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive() or not response_str:
            raise RuntimeError(f"Timeout waiting for response to {method}")
            
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError as e:
            # Check for server errors
            stderr_data = ""
            try:
                # Non-blocking read of stderr
                import select
                import os
                if os.name != 'nt':  # Unix systems
                    ready, _, _ = select.select([self.process.stderr], [], [], 0)
                    if ready:
                        stderr_data = self.process.stderr.read()
            except:
                pass
                
            raise RuntimeError(f"Invalid JSON response: {response_str}. Server stderr: {stderr_data}")
        
        if "error" in response:
            raise Exception(f"Server error: {response['error']}")
            
        return response.get("result", {})
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize connection with server"""
        print("Initializing MCP connection...")
        
        result = self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "simple-test-client",
                    "version": "1.0.0"
                }
            }
        )
        
        # Send initialized notification
        try:
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            notification_str = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_str)
            self.process.stdin.flush()
        except Exception as e:
            print(f"Warning: Could not send initialized notification: {e}")
        
        self.is_initialized = True
        print("✅ MCP connection initialized successfully")
        return result

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from server"""
        if not self.is_initialized:
            raise RuntimeError("Client not initialized")
            
        print("Getting available tools...")
        result = self._send_request("tools/list")
        tools = result.get("tools", [])
        
        self.available_tools = {tool["name"]: tool for tool in tools}
        print(f"✅ Found {len(tools)} tools: {list(self.available_tools.keys())}")
        return tools
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool"""
        if not self.is_initialized:
            raise RuntimeError("Client not initialized")
            
        if tool_name not in self.available_tools:
            available = list(self.available_tools.keys())
            raise ValueError(f"Tool '{tool_name}' not available. Available: {available}")
            
        result = self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        return result

# Tool conversion functions (same as before)
def convert_mcp_tool_to_function_format(mcp_tool):
    """Convert MCP tool format to OpenAI function format"""
    try:
        # Debug: print the raw tool to see its structure
        print(f"DEBUG: Converting tool: {type(mcp_tool)} -> {mcp_tool}")
        
        # Handle different tool formats
        if hasattr(mcp_tool, 'name'):
            # It's an object with attributes
            name = mcp_tool.name
            description = mcp_tool.description
            input_schema = mcp_tool.inputSchema
        elif isinstance(mcp_tool, dict):
            # It's a dictionary
            name = mcp_tool.get('name')
            description = mcp_tool.get('description', '')
            input_schema = mcp_tool.get('inputSchema', {})
        else:
            raise ValueError(f"Unknown tool format: {type(mcp_tool)}")
        
        if not name:
            raise ValueError(f"Tool missing name: {mcp_tool}")
        
        # Clean up description
        clean_description = description.split('\n\n')[0] if '\n\n' in description else description
        clean_description = clean_description.strip() if clean_description else f"Tool: {name}"
        
        # Create parameters object
        parameters = {
            "type": "object",
            "properties": {},
            "required": input_schema.get('required', []) if input_schema else []
        }
        
        # Add properties if they exist
        if input_schema and 'properties' in input_schema:
            for prop_name, prop_info in input_schema['properties'].items():
                parameters["properties"][prop_name] = {
                    "type": prop_info.get('type', 'string'),
                    "description": prop_info.get('description', f"{prop_name.replace('_', ' ').title()}")
                }
        
        # Return in correct OpenAI format
        function_tool = {
            "type": "function",
            "function": {
                "name": name,
                "description": clean_description,
                "parameters": parameters
            }
        }
        
        print(f"DEBUG: Converted tool: {json.dumps(function_tool, indent=2)}")
        return function_tool
        
    except Exception as e:
        print(f"ERROR converting tool {mcp_tool}: {e}")
        import traceback
        traceback.print_exc()
        raise

class SimpleMCPTools:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.tools = None
    
    def get_tools(self):
        if self.tools is None:
            try:
                print("DEBUG: Getting MCP tools...")
                mcp_tools = self.mcp_client.get_tools()
                print(f"DEBUG: Raw MCP tools: {mcp_tools}")
                
                self.tools = []
                for i, tool in enumerate(mcp_tools):
                    try:
                        converted = convert_mcp_tool_to_function_format(tool)
                        self.tools.append(converted)
                        print(f"DEBUG: Successfully converted tool {i}")
                    except Exception as e:
                        print(f"ERROR: Failed to convert tool {i}: {e}")
                        continue
                        
                print(f"DEBUG: Successfully converted {len(self.tools)} tools")
                
            except Exception as e:
                print(f"ERROR: Failed to get tools: {e}")
                import traceback
                traceback.print_exc()
                self.tools = []
                
        return self.tools