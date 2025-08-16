#!/usr/bin/env python3

import os
import asyncio
import json
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        return
        
    openai_client = OpenAI()
    
    # Connect to MCP server using official SDK
    server_params = StdioServerParameters(
        command="python", 
        args=["0a-agents/weather_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            print("✅ Connected to MCP server")

            # Get available tools
            tools_result = await session.list_tools()
            tools = tools_result.tools
            print(f"✅ Found {len(tools)} tools: {[tool.name for tool in tools]}")

            # Convert tools to OpenAI format
            openai_tools = []
            for tool in tools:
                # Extract schema - handle both dict and Pydantic model
                schema = tool.inputSchema
                if hasattr(schema, 'model_dump'):
                    schema = schema.model_dump()
                
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": schema
                    }
                }
                openai_tools.append(openai_tool)

            # Chat loop
            messages = [{
                "role": "system", 
                "content": "You are a helpful weather assistant. Use the available tools to help users with weather information and basic calculations."
            }]

            print("\n🌤️  Weather Assistant Ready!")
            print("Type 'quit' to exit\n")

            while True:
                try:
                    # Get user input
                    user_input = input("You: ").strip()
                    if user_input.lower() == 'quit':
                        break

                    messages.append({"role": "user", "content": user_input})

                    # Call OpenAI
                    response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto"
                    )

                    message = response.choices[0].message
                    messages.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": message.tool_calls
                    })

                    # Handle tool calls
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            # Parse arguments
                            arguments = json.loads(tool_call.function.arguments)
                            
                            # Call MCP tool directly
                            result = await session.call_tool(tool_call.function.name, arguments)
                            
                            # Extract result content
                            result_content = ""
                            if result.content:
                                for content in result.content:
                                    if hasattr(content, 'text'):
                                        result_content += content.text
                                    else:
                                        result_content += str(content)

                            print(f"🔧 {tool_call.function.name}({arguments}) → {result_content}")

                            # Add tool result to conversation
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result_content
                            })

                        # Get final response from OpenAI
                        final_response = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages
                        )
                        
                        final_message = final_response.choices[0].message
                        messages.append(final_message.model_dump())
                        print(f"Assistant: {final_message.content}")
                    else:
                        # No tool calls, just display the response
                        if message.content:
                            print(f"Assistant: {message.content}")

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")

    print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())