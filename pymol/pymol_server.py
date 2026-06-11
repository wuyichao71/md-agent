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

mcp = FastMCP("PyMOL")

_proc: subprocess.Popen | None = None
_queue: queue.Queue[str] = queue.Queue()
_SENTINEL = "---PYMOL-MCP-DONE---"


def _pymol_argv(*extra_args: str) -> list[str]:
    """Build argv for launching PyMOL.

    PYMOL_CMD in .env can be a bare executable or a full invocation, e.g.:
        PYMOL_CMD=pymol
        PYMOL_CMD=C:\\ProgramData\\Anaconda3\\envs\\pymol\\Scripts\\pymol.exe
        PYMOL_CMD=conda run -n work pymol
    """
    cmd = os.environ.get("PYMOL_CMD", "pymol")
    return shlex.split(cmd) + list(extra_args)


def _reader(proc: subprocess.Popen, q: queue.Queue) -> None:
    """Background thread: drain proc.stdout into q line by line."""
    for raw in proc.stdout:
        q.put(raw.decode().rstrip("\n"))


def _send(command: str, timeout: float = 15.0) -> str:
    """Write one command to PyMOL stdin and collect output until the sentinel."""
    global _proc
    if _proc is None or _proc.poll() is not None:
        return "Error: PyMOL is not running. Use open_pymol() first."
    # flush=True ensures the sentinel line is pushed through the pipe immediately
    _proc.stdin.write(f"{command}\nprint('{_SENTINEL}', flush=True)\n".encode())
    _proc.stdin.flush()
    lines = []
    while True:
        try:
            line = _queue.get(timeout=timeout)
        except queue.Empty:
            return f"Error: timed out after {timeout}s waiting for PyMOL response."
        if line == _SENTINEL:
            break
        lines.append(line)
    return "\n".join(lines).strip() or "OK"


@mcp.tool()
def open_pymol() -> str:
    """Launch PyMOL as a subprocess with stdin/stdout pipes for remote control."""
    global _proc, _queue
    if _proc is not None and _proc.poll() is None:
        return "PyMOL is already running."
    argv = _pymol_argv("-Q")
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
    time.sleep(3)
    return f"PyMOL launched (cmd: {argv})"


@mcp.tool()
def run_pymol_command(command: str) -> str:
    """Run a PyMOL command via stdin pipe.

    Args:
        command: A valid PyMOL command string, e.g. 'fetch 1abc', 'show cartoon'
    """
    return _send(command)


if __name__ == "__main__":
    mcp.run()
