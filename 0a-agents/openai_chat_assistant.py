import json
from IPython.display import display, HTML
import markdown

def shorten(text, max_length=50):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

class ChatInterface:
    def input(self):
        question = input("You: ")
        return question
    
    def display(self, message):
        print(message)

    def display_function_call(self, function_name, arguments, result):
        call_html = f"""
            <details>
            <summary>Function call: <tt>{function_name}({shorten(str(arguments))})</tt></summary>
            <div>
                <b>Call</b>
                <pre>{function_name}({json.dumps(arguments, indent=2)})</pre>
            </div>
            <div>
                <b>Output</b>
                <pre>{result}</pre>
            </div>
            </details>
        """
        display(HTML(call_html))

    def display_response(self, content):
        response_html = markdown.markdown(content)
        html = f"""
            <div>
                <div><b>Assistant:</b></div>
                <div>{response_html}</div>
            </div>
        """
        display(HTML(response_html))

class OpenAIChatAssistant:
    def __init__(self, tools, system_prompt, chat_interface, client):
        self.tools = tools
        self.system_prompt = system_prompt
        self.chat_interface = chat_interface
        self.client = client
    
    def call_openai(self, messages):
        """Call OpenAI API with proper formatting"""
        tools_list = self.tools.get_tools()
        
        # Debug: print the tools format
        if tools_list:
            print(f"DEBUG: Sending {len(tools_list)} tools to OpenAI")
            for i, tool in enumerate(tools_list[:1]):  # Just print first tool
                print(f"DEBUG: Tool {i}: {json.dumps(tool, indent=2)}")
        
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

        # Chat loop
        while True:
            question = self.chat_interface.input()
            if question.strip().lower() == 'stop':  
                self.chat_interface.display("Chat ended.")
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
                                self.chat_interface.display(f"Tool error: {error_msg}")
                                
                                messages.append({
                                    "role": "tool", 
                                    "tool_call_id": tool_call.id,
                                    "content": error_msg
                                })
                    else:
                        # No tool calls, break the loop
                        break
                        
                except Exception as e:
                    self.chat_interface.display(f"API Error: {str(e)}")
                    break