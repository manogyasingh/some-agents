import os
import re
import json
from dotenv import load_dotenv
from claude_agent import ClaudeAgent
from tools.python_repl import execute_python
from tools.file_operations import make_edit_files

def extract_tool_calls(text):
    tool_pattern = r"```tool\n(.*?)```"
    matches = re.findall(tool_pattern, text, re.DOTALL)
    tool_calls = []
    for match in matches:
        try:
            tool_calls.append(json.loads(match.strip()))
        except json.JSONDecodeError:
            pass
    return tool_calls

def main():
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found")
        return

    agent = ClaudeAgent(api_key)
    agent.register_tool(
        name="python_repl",
        description="Execute Python code",
        parameters={"code": {"type": "string", "description": "Python code"}},
        handler=execute_python
    )
    
    agent.register_tool(
        name="file_operations",
        description="Create and edit files in both whole file and diff formats",
        parameters={
            "action": {"type": "string", "description": "Action to perform: 'create', 'read', 'write', or 'diff'"},
            "file_path": {"type": "string", "description": "Path to the file, relative to the project directory"},
            "content": {"type": "string", "description": "File content for create/write operations (optional)"},
            "diff": {"type": "array", "description": "List of diff operations (optional)", "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["replace", "insert", "delete"]},
                    "start": {"type": "integer", "description": "Start position for replace/delete operations"},
                    "end": {"type": "integer", "description": "End position for replace/delete operations"},
                    "position": {"type": "integer", "description": "Position for insert operations"},
                    "content": {"type": "string", "description": "Content for replace/insert operations"}
                }
            }}
        },
        handler=make_edit_files
    )

    history = []
    print("Claude Agent with Python REPL initialized. Type 'exit' to quit.")
    print("-" * 50)

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        
        # Get the initial response from Claude
        response = agent.chat(user_input, history)
        
        # Extract any tool calls from the response
        tool_calls = extract_tool_calls(response)
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            if tool_name == "python_repl":
                python_code = tool_call.get("parameters", {}).get("code", "")
                print("\n" + "-" * 20 + " EXECUTING PYTHON CODE " + "-" * 20)
                print(python_code)
                print("-" * 60)
            elif tool_name == "file_operations":
                action = tool_call.get("parameters", {}).get("action", "")
                file_path = tool_call.get("parameters", {}).get("file_path", "")
                print(f"\n{'-' * 20} FILE OPERATION: {action.upper()} {file_path} {'-' * 20}")
        
        print("\nClaude:", response)
        print("-" * 50)
        history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ])

if __name__ == "__main__":
    main()
