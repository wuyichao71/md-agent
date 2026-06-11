import os
import queue
import shlex
import subprocess
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).parent.parent / ".env")

mcp = FastMCP("ChimeraX")

_proc: subprocess.Popen | None = None
_queue: queue.Queue[str] = queue.Queue()
_SENTINEL = "---CHIMERAX-MCP-DONE---"


def _chimerax_argv(*extra_args: str) -> list[str]:
    """Build argv for launching ChimeraX.

    CHIMERAX_CMD in .env can be a bare executable or a full invocation, e.g.:
        CHIMERAX_CMD=chimerax
        CHIMERAX_CMD=C:\\Program Files\\ChimeraX\\bin\\ChimeraX.exe
        CHIMERAX_CMD=conda run -n chimerax ChimeraX
    """
    cmd = os.environ.get("CHIMERAX_CMD", "chimerax")
    return shlex.split(cmd) + list(extra_args)


def _reader(proc: subprocess.Popen, q: queue.Queue) -> None:
    """Background thread: drain proc.stdout into q line by line."""
    for raw in proc.stdout:
        q.put(raw.decode().rstrip("\n"))


def _send(command: str, timeout: float = 15.0) -> str:
    """Write one command to ChimeraX stdin and collect output until the sentinel."""
    global _proc
    if _proc is None or _proc.poll() is not None:
        return "Error: ChimeraX is not running. Use open_chimerax() first."
    # Use ChimeraX's Python escape to print the sentinel with immediate flush
    _proc.stdin.write(f"{command}\npython print('{_SENTINEL}', flush=True)\n".encode())
    _proc.stdin.flush()
    lines = []
    while True:
        try:
            line = _queue.get(timeout=timeout)
        except queue.Empty:
            return f"Error: timed out after {timeout}s waiting for ChimeraX response."
        if line == _SENTINEL:
            break
        lines.append(line)
    return "\n".join(lines).strip() or "OK"


@mcp.tool()
def open_chimerax() -> str:
    """Launch ChimeraX as a subprocess with stdin/stdout pipes for remote control."""
    global _proc, _queue
    if _proc is not None and _proc.poll() is None:
        return "ChimeraX is already running."
    argv = _chimerax_argv("--nogui")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    _proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    _queue = queue.Queue()
    threading.Thread(target=_reader, args=(_proc, _queue), daemon=True).start()
    time.sleep(4)
    return f"ChimeraX launched (cmd: {argv})"


@mcp.tool()
def run_chimerax_command(command: str) -> str:
    """Run a ChimeraX command via stdin pipe.

    Args:
        command: A valid ChimeraX command string, e.g. 'open 1abc', 'cartoon'
    """
    return _send(command)


if __name__ == "__main__":
    mcp.run()
