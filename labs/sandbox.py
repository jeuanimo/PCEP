"""Code execution sandbox for PCEP Prep Coach coding labs.

Security model
--------------
The sandbox uses two layers of defence:

  Layer 1 — AST validation (before execution)
    Rejects code that contains imports, dunder attribute access,
    forbidden builtins, or any use of ``type()``/``object`` which
    can be used to climb the class hierarchy.

  Layer 2 — Subprocess isolation (during execution)
    Runs the code in a forked child process with:
      • CPU time limit  (5 s)  — kills infinite loops
      • Memory limit    (64 MB) — kills memory bombs
      • Restricted builtins namespace — no file system, no network,
        no import machinery

Production upgrade path
-----------------------
Replace ``run_user_code()`` with a call to an isolated container:
  • Docker: ``docker run --rm --network none --memory 64m --cpus 0.5``
  • nsjail / firejail for Linux namespace isolation
  • External API: Piston (https://github.com/engineer-man/piston) or Judge0
"""
from __future__ import annotations

import ast
import contextlib
import io
import multiprocessing
import resource

# Builtins that are safe for PCEP-level exercises.
# Anything not in this dict is unavailable inside submitted code.
_SAFE_BUILTINS: dict = {
    # I/O
    "print":    print,
    "input":    None,       # replaced with fake_input at runtime
    # Numeric
    "abs":      abs,
    "divmod":   divmod,
    "max":      max,
    "min":      min,
    "pow":      pow,
    "round":    round,
    "sum":      sum,
    # Type constructors
    "bool":     bool,
    "complex":  complex,
    "float":    float,
    "int":      int,
    "str":      str,
    # Collections
    "dict":     dict,
    "frozenset":frozenset,
    "list":     list,
    "set":      set,
    "tuple":    tuple,
    # Iteration helpers
    "enumerate":enumerate,
    "filter":   filter,
    "map":      map,
    "range":    range,
    "reversed": reversed,
    "sorted":   sorted,
    "zip":      zip,
    # Introspection (read-only, safe subset)
    "isinstance": isinstance,
    "len":        len,
    "repr":       repr,
    # Constants
    "True":  True,
    "False": False,
    "None":  None,
    # Exception types students may need to catch/raise
    "ValueError":    ValueError,
    "TypeError":     TypeError,
    "IndexError":    IndexError,
    "KeyError":      KeyError,
    "ZeroDivisionError": ZeroDivisionError,
    "StopIteration": StopIteration,
    "Exception":     Exception,
}

# Builtins that are always forbidden (belt-and-suspenders on top of the AST check)
_FORBIDDEN_BUILTINS: frozenset[str] = frozenset({
    "exec", "eval", "compile", "__import__",
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr",
    "open", "breakpoint", "exit", "quit",
    "type", "object", "super",  # class hierarchy climbers
    "memoryview", "bytearray", "bytes",
})

# AST node types that are always blocked regardless of context
_FORBIDDEN_AST_CALLS: frozenset[str] = _FORBIDDEN_BUILTINS | frozenset({
    "chr", "ord",  # can be chained to build forbidden strings
})


def _validate_ast_node(node: ast.AST) -> str | None:
    """Return an error string for a forbidden AST node, otherwise None."""
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "Forbidden: import statements are not allowed"

    if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
        return f"Forbidden: access to '{node.attr}' is not allowed"

    if isinstance(node, ast.Name) and node.id.startswith("__"):
        return f"Forbidden: use of '{node.id}' is not allowed"

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_AST_CALLS:
            return f"Forbidden: '{node.func.id}()' is not allowed"

    return None


def validate(code: str) -> str | None:
    """Parse ``code`` with the AST and return an error string, or None if safe.

    Checks (in order):
      1. Import statements (``import x``, ``from x import y``)
      2. Dunder attribute access (``obj.__class__``, ``obj.__dict__``)
      3. Dunder name usage (``__builtins__``, ``__import__``)
      4. Forbidden builtin calls (exec, eval, open, type, …)
      5. ``type()`` or ``object`` anywhere — prevents class hierarchy escape

    SyntaxErrors are *not* caught here so the subprocess can surface them
    with a proper traceback message.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # Let the subprocess report SyntaxError naturally

    for node in ast.walk(tree):
        error = _validate_ast_node(node)
        if error:
            return error

    return None


def _worker(code: str, test_input: str, result_queue: multiprocessing.Queue) -> None:
    """Child-process target: apply resource limits, then exec the code."""
    # Layer 2: OS-level resource limits applied *inside* the child process
    # so they only affect this process, not the Django server.
    try:
        # 64 MB address space
        resource.setrlimit(resource.RLIMIT_AS, (64 * 1024 * 1024, 64 * 1024 * 1024))
        # 5 CPU-seconds (kills infinite loops even if the wall-clock timeout fires late)
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        # No new files
        resource.setrlimit(resource.RLIMIT_NOFILE, (0, 0))
    except ValueError:
        # Some limits can't be tightened on certain OS configurations; that's OK —
        # the wall-clock timeout in run_user_code() still protects the server.
        pass

    # Build the fake input() that reads from the challenge's test_input lines
    input_lines = iter(test_input.strip().splitlines() if test_input.strip() else [])

    def fake_input(prompt=""):
        try:
            return next(input_lines)
        except StopIteration:
            return ""

    builtins = {**_SAFE_BUILTINS, "input": fake_input}
    stdout_buf = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_buf):
            exec(code, {"__builtins__": builtins})  # noqa: S102
        result_queue.put(("ok", stdout_buf.getvalue()))
    except Exception as exc:
        result_queue.put(("error", f"{type(exc).__name__}: {exc}"))


def run_user_code(code: str, test_input: str, timeout: int = 10) -> str:
    """Run ``code`` safely and return its stdout as a string.

    Return value format:
      • Normal output  → the raw stdout string (may be empty)
      • Any error      → a string starting with ``"Error: "``

    The function is intentionally I/O-only: it takes strings in, returns
    a string out, and has no Django dependencies so it can be tested in
    isolation or swapped for a remote sandbox call.
    """
    # Layer 1: static analysis before we ever fork
    validation_error = validate(code)
    if validation_error:
        return f"Error: {validation_error}"

    # Spawn a child process; use a Queue instead of Manager().dict() —
    # Queue doesn't require a background Manager server process.
    result_queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    proc = multiprocessing.Process(
        target=_worker,
        args=(code, test_input, result_queue),
        daemon=True,
    )
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=2)
        if proc.is_alive():
            proc.kill()
        return f"Error: Code timed out (max {timeout} seconds)"

    if not result_queue.empty():
        status, payload = result_queue.get_nowait()
        if status == "error":
            return f"Error: {payload}"
        return payload

    # Process exited without writing to the queue (OOM kill, etc.)
    return "Error: Execution failed (process terminated unexpectedly)"
