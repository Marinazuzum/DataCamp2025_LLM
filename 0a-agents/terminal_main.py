#!/usr/bin/env python3

import os
from openai import OpenAI
from terminal_chat_assistant import TerminalChatAssistant, TerminalChatInterface
from simple_mcp_client import SimpleMCPClient, SimpleMCPTools

def main():
    # Initialize MCP client with the weather server command
    mcp_client = SimpleMCPClient(["python", "0a-agents/weather_server.py"])
    
    try:
        # Start the MCP server
        print("🚀 Starting MCP weather server...")
        mcp_client.start_server()
        
        # Initialize the MCP connection
        print("🔗 Initializing MCP connection...")
        mcp_client.initialize()
        
        # Create MCP tools wrapper
        mcp_tools = SimpleMCPTools(mcp_client)
        
        # Get and verify tools (without verbose debugging)
        available_tools = mcp_tools.get_tools()
        tool_names = [tool.get('function', {}).get('name', 'UNKNOWN') for tool in available_tools]
        print(f"✅ Found {len(available_tools)} tools: {', '.join(tool_names)}")
        
        # Create chat interface and OpenAI client
        chat_interface = TerminalChatInterface()
        
        # Initialize OpenAI client
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Error: OPENAI_API_KEY environment variable not set!")
            print("Please set it with: export OPENAI_API_KEY='your-api-key'")
            return
            
        client = OpenAI()
        print("✅ OpenAI client initialized")
        
        # Define the system prompt for the weather assistant
        system_prompt = """You are a helpful weather assistant. You have access to weather tools that can:

1. get_weather(city) - Get the current temperature for any city
2. set_weather(city, temp) - Set/update temperature data for cities  
3. add(a, b) - Perform basic arithmetic operations

When users ask about weather, use the get_weather tool to retrieve temperatures.
If users want to update weather data, use the set_weather tool.
Always be helpful and provide clear, friendly responses about weather information.

Example responses:
- "The temperature in Berlin is 20.0°C"
- "I've updated the temperature in Paris to 25.0°C"
- "The sum of 5 + 3 is 8"
"""
        
        # Create and run the chat assistant
        assistant = TerminalChatAssistant(mcp_tools, system_prompt, chat_interface, client)
        
        # Start the chat loop
        assistant.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up: stop the MCP server
        print("🧹 Stopping MCP server...")
        mcp_client.stop_server()

if __name__ == "__main__":
    main()
