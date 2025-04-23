import os
import sys
import pathlib
from typing import Dict, Optional, List, Union, Any

def ensure_safe_path(file_path: str, base_dir: str) -> str:
    if os.path.isabs(file_path):
        abs_path = file_path
    else:
        abs_path = os.path.abspath(os.path.join(base_dir, file_path))
    abs_base = os.path.abspath(base_dir)
    if not abs_path.startswith(abs_base):
        raise ValueError(f"Path {file_path} attempts to access files outside the base directory")
    return abs_path

def read_file(file_path: str, base_dir: Optional[str] = None) -> str:
    if base_dir is None:
        base_dir = os.getcwd()
    safe_path = ensure_safe_path(file_path, base_dir)
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"

def write_file(file_path: str, content: str, base_dir: Optional[str] = None) -> str:
    if base_dir is None:
        base_dir = os.getcwd()
    try:
        safe_path = ensure_safe_path(file_path, base_dir)
        directory = os.path.dirname(safe_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        if os.path.exists(safe_path):
            with open(safe_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            if len(written_content) == len(content):
                return f"Successfully wrote {len(content)} characters to {file_path}"
            else:
                return f"Warning: File was created but content length mismatch. Expected: {len(content)}, Actual: {len(written_content)}"
        else:
            return f"Error: Failed to create file {file_path}"
    except Exception as e:
        return f"Error writing to file {file_path}: {str(e)}"

def apply_diff(file_path: str, diff: List[Dict[str, Any]], base_dir: Optional[str] = None) -> str:
    if base_dir is None:
        base_dir = os.getcwd()
    safe_path = ensure_safe_path(file_path, base_dir)
    try:
        if not os.path.exists(safe_path):
            return f"Error: File '{file_path}' not found."
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        sorted_diff = sorted(diff, key=lambda d: d.get("start", d.get("position", 0)), reverse=True)
        for change in sorted_diff:
            op = change.get("op")
            if op == "replace":
                start = change.get("start", 0)
                end = change.get("end", start)
                content = content[:start] + change.get("content", "") + content[end:]
            elif op == "insert":
                position = change.get("position", 0)
                content = content[:position] + change.get("content", "") + content[position:]
            elif op == "delete":
                start = change.get("start", 0)
                end = change.get("end", start)
                content = content[:start] + content[end:]
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully applied diff to {file_path}"
    except Exception as e:
        return f"Error applying diff to {file_path}: {str(e)}"

def make_edit_files(action: str, file_path: str, content: Optional[str] = None, diff: Optional[List[Dict[str, Any]]] = None, base_dir: Optional[str] = None) -> str:
    if base_dir is None:
        base_dir = os.getcwd()
    if not file_path:
        return "Error: file_path cannot be empty"
    if action == "read":
        return read_file(file_path, base_dir)
    elif action in ("create", "write"):
        if content is None:
            return "Error: Content required for create/write operations"
        return write_file(file_path, content, base_dir)
    elif action == "diff":
        if diff is None:
            return "Error: Diff required for diff operations"
        return apply_diff(file_path, diff, base_dir)
    return f"Error: Unknown action '{action}'. Use 'create', 'read', 'write', or 'diff'."
