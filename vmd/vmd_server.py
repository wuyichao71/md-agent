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

mcp = FastMCP("VMD")

_proc: subprocess.Popen | None = None
_queue: queue.Queue[str] = queue.Queue()
_SENTINEL = "---VMD-MCP-DONE---"


def _vmd_argv(*extra_args: str) -> list[str]:
    """Build argv for launching VMD.

    VMD_CMD in .env can be a bare executable or a full invocation, e.g.:
        VMD_CMD=vmd
        VMD_CMD=C:\\Program Files\\University of Illinois\\VMD\\vmd.exe
        VMD_CMD=conda run -n vmd vmd
    """
    cmd = os.environ.get("VMD_CMD", "vmd")
    return shlex.split(cmd) + list(extra_args)


def _reader(proc: subprocess.Popen, q: queue.Queue) -> None:
    """Background thread: drain proc.stdout into q line by line."""
    for raw in proc.stdout:
        q.put(raw.decode().rstrip("\n"))


def _send(command: str, timeout: float = 15.0) -> str:
    """Write one Tcl command to VMD stdin and collect output until the sentinel."""
    global _proc
    if _proc is None or _proc.poll() is not None:
        return "Error: VMD is not running. Use open_vmd() first."
    # flush stdout explicitly so the sentinel is pushed through the pipe immediately
    _proc.stdin.write(f"{command}\nputs \"{_SENTINEL}\"\nflush stdout\n".encode())
    _proc.stdin.flush()
    lines = []
    while True:
        try:
            line = _queue.get(timeout=timeout)
        except queue.Empty:
            return f"Error: timed out after {timeout}s waiting for VMD response."
        if line == _SENTINEL:
            break
        lines.append(line)
    return "\n".join(lines).strip() or "OK"


@mcp.tool()
def open_vmd() -> str:
    """Launch VMD as a subprocess with stdin/stdout pipes for remote control."""
    global _proc, _queue
    if _proc is not None and _proc.poll() is None:
        return "VMD is already running."
    argv = _vmd_argv("-dispdev", "text")
    _proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    _queue = queue.Queue()
    threading.Thread(target=_reader, args=(_proc, _queue), daemon=True).start()
    time.sleep(3)
    return f"VMD launched (cmd: {argv})"


@mcp.tool()
def run_vmd_command(command: str) -> str:
    """Run a VMD Tcl command via stdin pipe.

    Args:
        command: A valid VMD Tcl command string.

    Common commands:
        mol new /path/to/file.pdb    — load a molecule
        mol list                      — list loaded molecules
        mol delete all                — delete all molecules
        display resetview             — reset camera
        rotate x by 45               — rotate the scene
        render snapshot out.tga       — save a screenshot (TGA format)
        animate goto 0                — jump to first trajectory frame
        molinfo top get numframes     — get the number of loaded frames
    """
    return _send(command)


if __name__ == "__main__":
    mcp.run()
