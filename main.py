import os
import re
import json
import sys
from dotenv import load_dotenv
from claude_agent import ClaudeAgent
from tools.python_repl import execute_python
from tools.file_operations import make_edit_files

def create_file(filename: str, content: str) -> str:
    """A simplified file creator tool."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if os.path.exists(filename):
            return f"Successfully created {filename} with {len(content)} characters"
        else:
            return f"Error: File creation reported success but {filename} doesn't exist"
    except Exception as e:
        return f"Error creating file: {str(e)}"

def debug_tool(command: str) -> str:
    """A simple diagnostic tool for debugging."""
    if command == "list_files":
        files = os.listdir(".")
        return f"Files in current directory: {files}"
    elif command == "get_cwd":
        return f"Current working directory: {os.getcwd()}"
    elif command == "get_env":
        return f"Environment variables: {dict(os.environ)}"
    elif command == "get_permissions":
        try:
            return f"Can write to current dir: {os.access('.', os.W_OK)}"
        except Exception as e:
            return f"Error checking permissions: {str(e)}"
    elif command.startswith("check_file:"):
        filename = command.split(":", 1)[1]
        try:
            exists = os.path.exists(filename)
            readable = os.access(filename, os.R_OK) if exists else False
            writable = os.access(filename, os.W_OK) if exists else False
            return f"File {filename}: exists={exists}, readable={readable}, writable={writable}"
        except Exception as e:
            return f"Error checking file {filename}: {str(e)}"
    else:
        return f"Unknown debug command: {command}"

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
    
    # Add a simplified file creator tool
    agent.register_tool(
        name="create_file",
        description="Create a file with the given content (simpler alternative to file_operations)",
        parameters={
            "filename": {"type": "string", "description": "Name of the file to create"},
            "content": {"type": "string", "description": "Content to write to the file"}
        },
        handler=create_file
    )
    
    agent.register_tool(
        name="debug",
        description="Debug tool to diagnose system issues",
        parameters={"command": {"type": "string", "description": "Debug command to run"}},
        handler=debug_tool
    )

    # Print some startup diagnostic info
    print(f"Starting with working directory: {os.getcwd()}")
    print(f"Can write to current directory: {os.access('.', os.W_OK)}")

    history = []
    print("Claude Agent with Python REPL and File Operations initialized. Type 'exit' to quit.")
    print("-" * 50)

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        
        # Get the response from Claude - tool execution happens inside the agent
        response = agent.chat(user_input, history)
        
        # Extract tool calls from the response for display purposes only
        tool_calls = agent._extract_tool_calls(response)
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            if tool_name == "python_repl":
                python_code = tool_call.get("parameters", {}).get("code", "")
                print("\n" + "-" * 20 + " PYTHON CODE EXECUTED " + "-" * 20)
                print(python_code)
                print("-" * 60)
            elif tool_name == "file_operations":
                action = tool_call.get("parameters", {}).get("action", "")
                file_path = tool_call.get("parameters", {}).get("file_path", "")
                print(f"\n{'-' * 20} FILE OPERATION: {action.upper()} {file_path} {'-' * 20}")
            elif tool_name == "create_file":
                filename = tool_call.get("parameters", {}).get("filename", "")
                print(f"\n{'-' * 20} CREATED FILE: {filename} {'-' * 20}")
            elif tool_name == "debug":
                command = tool_call.get("parameters", {}).get("command", "")
                print(f"\n{'-' * 20} DEBUG: {command} {'-' * 20}")
        
        print("\nClaude:", response)
        print("-" * 50)
        
        # Add the interaction to history
        history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ])

if __name__ == "__main__":
    main()
