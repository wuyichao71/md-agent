import os
import shlex
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Image
from xmlrpc.client import ServerProxy

load_dotenv(Path(__file__).parent.parent / ".env")

mcp = FastMCP("ChimeraX")

XMLRPC_PORT = 42184
_proxy = ServerProxy(f"http://localhost:{XMLRPC_PORT}/RPC2")


def _chimerax_argv(*extra_args: str) -> list[str]:
    """Build the argv list for launching ChimeraX.

    CHIMERAX_CMD in .env can be a bare executable or a full invocation, e.g.:
        CHIMERAX_CMD=chimerax
        CHIMERAX_CMD=/Applications/ChimeraX.app/Contents/bin/ChimeraX
        CHIMERAX_CMD=conda run -n chimerax ChimeraX
    """
    cmd = os.environ.get("CHIMERAX_CMD", "chimerax")
    return shlex.split(cmd) + list(extra_args)


@mcp.tool()
def open_chimerax() -> str:
    """Open ChimeraX with remote XML-RPC control enabled (port 42184)."""
    argv = _chimerax_argv("--cmd", f"remotecontrol xmlrpc true port {XMLRPC_PORT}")
    subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    return f"ChimeraX opened (cmd: {argv}), XML-RPC server on port {XMLRPC_PORT}"


@mcp.tool()
def run_chimerax_command(command: str) -> str:
    """Run a ChimeraX command via the XML-RPC interface.

    Args:
        command: A valid ChimeraX command string, e.g. 'open 1abc', 'cartoon'
    """
    result = _proxy.run_command(command)
    return str(result) if result else f"Executed: {command}"


# @mcp.tool()
# def save_image(file_path: str, width: int = 1920, height: int = 1080, supersample: int = 3) -> str:
#     """Save the current ChimeraX view to an image file.

#     Args:
#         file_path: Absolute path for the output image (PNG recommended).
#         width: Image width in pixels.
#         height: Image height in pixels.
#         supersample: Anti-aliasing level (1-4).
#     """
#     _proxy.run_command(
#         f"save {file_path} width {width} height {height} supersample {supersample}"
#     )
#     return f"Image saved to {file_path}"


# @mcp.tool()
# def get_screenshot(file_path: str, width: int = 1920, height: int = 1080) -> Image:
#     """Capture the current ChimeraX session as an image and return it.

#     Args:
#         file_path: Temporary path used to write the PNG, e.g. /tmp/view.png
#         width: Image width in pixels.
#         height: Image height in pixels.
#     """
#     _proxy.run_command(f"save {file_path} width {width} height {height} supersample 3")
#     time.sleep(0.5)
#     return Image(path=file_path)


if __name__ == "__main__":
    mcp.run()
