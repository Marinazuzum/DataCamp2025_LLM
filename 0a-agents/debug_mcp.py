#!/usr/bin/env python3

import subprocess
import json
import time
import sys

def test_server_standalone():
    """Test if the server runs without errors"""
    print("=== Testing server standalone ===")
    try:
        process = subprocess.Popen(
            ["python", "0a-agents/weather_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit and then terminate
        time.sleep(2)
        process.terminate()
        stdout, stderr = process.communicate()
        
        print(f"Return code: {process.returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        
        if stderr:
            print("❌ Server has errors!")
            return False
        else:
            print("✅ Server starts without errors")
            return True
            
    except Exception as e:
        print(f"❌ Error running server: {e}")
        return False

def test_manual_communication():
    """Test manual JSON-RPC communication"""
    print("\n=== Testing manual JSON-RPC communication ===")
    
    try:
        process = subprocess.Popen(
            ["python", "weather_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialize request...")
        request_str = json.dumps(init_request) + "\n"
        print(f"Request: {request_str.strip()}")
        
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # Try to read response with timeout
        print("Waiting for response...")
        
        # Use a simple timeout mechanism
        import select
        import os
        
        if os.name == 'nt':  # Windows
            # On Windows, we can't use select, so just try to read
            try:
                response = process.stdout.readline()
                if response:
                    print(f"✅ Got response: {response.strip()}")
                    try:
                        parsed = json.loads(response)
                        print(f"✅ Valid JSON response: {parsed}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON: {e}")
                else:
                    print("❌ No response received")
            except Exception as e:
                print(f"❌ Error reading response: {e}")
        else:  # Unix/Linux/Mac
            ready, _, _ = select.select([process.stdout], [], [], 5.0)  # 5 second timeout
            
            if ready:
                response = process.stdout.readline()
                if response:
                    print(f"✅ Got response: {response.strip()}")
                    try:
                        parsed = json.loads(response)
                        print(f"✅ Valid JSON response: {parsed}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON: {e}")
                else:
                    print("❌ Empty response")
            else:
                print("❌ Timeout waiting for response")
        
        # Check for any stderr output
        if process.poll() is None:  # Process still running
            process.terminate()
        
        _, stderr = process.communicate()
        if stderr:
            print(f"STDERR: {stderr}")
            
    except Exception as e:
        print(f"❌ Error in manual communication test: {e}")
        import traceback
        traceback.print_exc()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n=== Checking dependencies ===")
    
    try:
        import fastmcp
        print("✅ fastmcp is available")
    except ImportError:
        print("❌ fastmcp not found. Install with: pip install fastmcp")
        return False
    
    try:
        with open("0a-agents/weather_server.py", "r") as f:
            content = f.read()
            if "FastMCP" in content:
                print("✅ weather_server.py looks correct")
            else:
                print("❌ weather_server.py doesn't seem to use FastMCP")
                return False
    except FileNotFoundError:
        print("❌ weather_server.py not found")
        return False
        
    return True

def main():
    print("MCP Connection Debugger")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency issues found. Please fix them first.")
        return
    
    # Test server standalone
    if not test_server_standalone():
        print("\n❌ Server has issues running standalone. Check the error messages above.")
        return
    
    # Test manual communication
    test_manual_communication()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check the results above.")

if __name__ == "__main__":
    main()
