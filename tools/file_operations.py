import os
import pathlib
from typing import Dict, Optional, List, Union, Any

def ensure_safe_path(file_path: str, base_dir: str) -> str:
    """Ensure the path is within the base directory for security."""
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.abspath(os.path.join(base_dir, file_path.lstrip('/')))
    if not abs_path.startswith(abs_base):
        raise ValueError(f"Path {file_path} attempts to access files outside the base directory")
    return abs_path

def read_file(file_path: str, base_dir: str = "/home/manogya/Desktop/Projects/kraken") -> str:
    """Read the contents of a file."""
    safe_path = ensure_safe_path(file_path, base_dir)
    try:
        with open(safe_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(file_path: str, content: str, base_dir: str = "/home/manogya/Desktop/Projects/kraken") -> str:
    """Write content to a file, creating directories as needed."""
    safe_path = ensure_safe_path(file_path, base_dir)
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

def apply_diff(file_path: str, diff: List[Dict[str, Any]], base_dir: str = "/home/manogya/Desktop/Projects/kraken") -> str:
    """Apply a diff to a file.
    
    diff format: [
        {"op": "replace", "start": 10, "end": 20, "content": "new content"},
        {"op": "insert", "position": 5, "content": "inserted content"},
        {"op": "delete", "start": 30, "end": 40}
    ]
    """
    safe_path = ensure_safe_path(file_path, base_dir)
    
    try:
        # Read the original file
        if not os.path.exists(safe_path):
            return f"Error: File '{file_path}' not found."
        
        with open(safe_path, 'r') as f:
            content = f.read()
        
        # Apply diffs in reverse order (to avoid position shifts)
        sorted_diff = sorted(diff, key=lambda d: d.get("start", d.get("position", 0)), reverse=True)
        
        for change in sorted_diff:
            op = change.get("op")
            
            if op == "replace":
                start = change.get("start", 0)
                end = change.get("end", start)
                new_content = change.get("content", "")
                content = content[:start] + new_content + content[end:]
            
            elif op == "insert":
                position = change.get("position", 0)
                new_content = change.get("content", "")
                content = content[:position] + new_content + content[position:]
            
            elif op == "delete":
                start = change.get("start", 0)
                end = change.get("end", start)
                content = content[:start] + content[end:]
        
        # Write the modified content back
        with open(safe_path, 'w') as f:
            f.write(content)
        
        return f"Successfully applied diff to {file_path}"
    
    except Exception as e:
        return f"Error applying diff: {str(e)}"

def make_edit_files(action: str, file_path: str, content: Optional[str] = None, 
                   diff: Optional[List[Dict[str, Any]]] = None, 
                   base_dir: str = "/home/manogya/Desktop/Projects/kraken") -> str:
    """Create or edit files with support for whole file or diff formats.
    
    Args:
        action: Either "create", "read", "write", or "diff"
        file_path: Path to the file, relative to base_dir
        content: File content for create/write operations
        diff: List of diff operations for diff action
        base_dir: Base directory for file operations
        
    Returns:
        Result message
    """
    if action == "read":
        return read_file(file_path, base_dir)
    
    elif action == "create" or action == "write":
        if content is None:
            return "Error: Content required for create/write operations"
        return write_file(file_path, content, base_dir)
    
    elif action == "diff":
        if diff is None:
            return "Error: Diff required for diff operations"
        return apply_diff(file_path, diff, base_dir)
    
    else:
        return f"Error: Unknown action '{action}'. Use 'create', 'read', 'write', or 'diff'."
