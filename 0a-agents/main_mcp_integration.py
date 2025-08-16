#!/usr/bin/env python3

import os
from openai import OpenAI
from openai_chat_assistant import OpenAIChatAssistant, ChatInterface
from simple_mcp_client import SimpleMCPClient, SimpleMCPTools

def main():
    # Initialize MCP client with the weather server command
    mcp_client = SimpleMCPClient(["python", "0a-agents/weather_server.py"])
    
    try:
        # Start the MCP server
        print("Starting MCP weather server...")
        mcp_client.start_server()
        
        # Initialize the MCP connection
        print("Initializing MCP connection...")
        mcp_client.initialize()
        
        # Create MCP tools wrapper
        mcp_tools = SimpleMCPTools(mcp_client)
        
        # Verify tools are available
        print("DEBUG: About to get available tools...")
        try:
            available_tools = mcp_tools.get_tools()
            print(f"DEBUG: Got {len(available_tools)} tools successfully")
            print(f"Available tools: {[tool.get('function', {}).get('name', 'UNKNOWN') for tool in available_tools]}")
        except Exception as e:
            print(f"ERROR: Failed to get tools: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Define the system prompt for the weather assistant
        system_prompt = """
You are a helpful weather assistant. You have access to weather tools that can:
1. Get the current temperature for any city
2. Set/update temperature data for cities
3. Perform basic arithmetic operations

When users ask about weather, use the get_weather tool to retrieve temperatures.
If users want to update weather data, use the set_weather tool.
Always be helpful and provide clear responses about weather information.
"""
        
        # Create chat interface and OpenAI client
        chat_interface = ChatInterface()
        
        # Initialize OpenAI client (make sure you have OPENAI_API_KEY set)
        if not os.getenv("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY environment variable not set!")
            print("Please set it with: export OPENAI_API_KEY='your-api-key'")
            return
            
        client = OpenAI()
        
        # Create and run the chat assistant
        assistant = OpenAIChatAssistant(mcp_tools, system_prompt, chat_interface, client)
        
        print("\nWeather Assistant is ready! Available commands:")
        print("- Ask about weather in any city")
        print("- Set weather data for cities")
        print("- Type 'stop' to end the conversation")
        print("\nExamples:")
        print("- 'What's the weather in Berlin?'")
        print("- 'Set the temperature in Paris to 25 degrees'")
        print("-" * 50)
        
        # Start the chat loop
        print("DEBUG: Starting chat loop...")
        try:
            assistant.run()
        except Exception as e:
            print(f"ERROR: Failed in chat loop: {e}")
            import traceback
            traceback.print_exc()
            raise
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up: stop the MCP server
        print("Stopping MCP server...")
        mcp_client.stop_server()

if __name__ == "__main__":
    main()