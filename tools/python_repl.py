import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

def execute_python(code: str) -> str:
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    result = None

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            local_vars = {}
            exec(code, {"__builtins__": __builtins__}, local_vars)
            result = local_vars.get("result")
    except Exception:
        stderr_capture.write(traceback.format_exc())

    stdout_output = stdout_capture.getvalue()
    stderr_output = stderr_capture.getvalue()
    parts = []
    if stdout_output:
        parts.append(f"STDOUT:\n{stdout_output}")
    if stderr_output:
        parts.append(f"STDERR:\n{stderr_output}")
    if result is not None:
        parts.append(f"RESULT:\n{repr(result)}")
    return "\n\n".join(parts) or "Code executed with no output."