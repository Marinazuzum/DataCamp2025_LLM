import json
import os

class TerminalChatInterface:
    def input(self):
        question = input("You: ")
        return question
    
    def display(self, message):
        print(f"Assistant: {message}")

    def display_function_call(self, function_name, arguments, result):
        print(f"\n🔧 Function Call: {function_name}")
        print(f"📥 Input: {json.dumps(arguments, indent=2)}")
        print(f"📤 Output: {result}")
        print("-" * 40)

    def display_response(self, content):
        if content:
            print(f"\nAssistant: {content}")

class TerminalChatAssistant:
    def __init__(self, tools, system_prompt, chat_interface, client):
        self.tools = tools
        self.system_prompt = system_prompt
        self.chat_interface = chat_interface
        self.client = client
    
    def call_openai(self, messages):
        """Call OpenAI API with proper formatting"""
        tools_list = self.tools.get_tools()
        
        return self.client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            tools=tools_list if tools_list else None,
            tool_choice="auto" if tools_list else None
        )

    def run(self):
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        print("\n" + "="*50)
        print("🌤️  Weather Assistant Started!")
        print("="*50)
        print("Available commands:")
        print("• Ask about weather in any city")
        print("• Set temperature for cities") 
        print("• Basic math operations")
        print("• Type 'stop' to exit")
        print("="*50)

        # Chat loop
        while True:
            try:
                question = self.chat_interface.input()
                if question.strip().lower() == 'stop':  
                    self.chat_interface.display("Chat ended. Goodbye! 👋")
                    break

                # Add user message
                messages.append({"role": "user", "content": question})

                while True:  # Tool calling loop
                    try:
                        response = self.call_openai(messages)
                        message = response.choices[0].message
                        
                        # Add assistant message to conversation
                        messages.append({
                            "role": "assistant",
                            "content": message.content,
                            "tool_calls": message.tool_calls
                        })

                        # Display assistant response if there's content
                        if message.content:
                            self.chat_interface.display_response(message.content)

                        # Handle tool calls
                        if message.tool_calls:
                            for tool_call in message.tool_calls:
                                function_name = tool_call.function.name
                                try:
                                    arguments = json.loads(tool_call.function.arguments)
                                except json.JSONDecodeError:
                                    arguments = {}
                                
                                # Call the tool using MCP
                                try:
                                    result = self.tools.mcp_client.call_tool(function_name, arguments)
                                    result_str = json.dumps(result, indent=2)
                                    
                                    # Display the function call
                                    self.chat_interface.display_function_call(
                                        function_name, arguments, result_str
                                    )
                                    
                                    # Add tool result to messages
                                    messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": result_str
                                    })
                                    
                                except Exception as e:
                                    error_msg = f"Error calling tool {function_name}: {str(e)}"
                                    print(f"❌ Tool error: {error_msg}")
                                    
                                    messages.append({
                                        "role": "tool", 
                                        "tool_call_id": tool_call.id,
                                        "content": error_msg
                                    })
                        else:
                            # No tool calls, break the loop
                            break
                            
                    except Exception as e:
                        print(f"❌ API Error: {str(e)}")
                        break
                        
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                continue
