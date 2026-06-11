import os
import shlex
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Image
from xmlrpc.client import ServerProxy

load_dotenv(Path(__file__).parent.parent / ".env")

mcp = FastMCP("PyMOL")

XMLRPC_PORT = 9123
_proxy = ServerProxy(f"http://localhost:{XMLRPC_PORT}/RPC2")


def _pymol_argv(*extra_args: str) -> list[str]:
    """Build the argv list for launching PyMOL.

    PYMOL_CMD in .env can be a bare executable or a full invocation, e.g.:
        PYMOL_CMD=pymol
        PYMOL_CMD=/opt/conda/bin/pymol
        PYMOL_CMD=conda run -n work pymol
    """
    cmd = os.environ.get("PYMOL_CMD", "pymol")
    return shlex.split(cmd) + list(extra_args)


@mcp.tool()
def open_pymol() -> str:
    """Open PyMOL with the built-in XML-RPC server enabled (port 9123)."""
    argv = _pymol_argv("-R")
    subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    return f"PyMOL opened (cmd: {argv}), XML-RPC server on port {XMLRPC_PORT}"


@mcp.tool()
def run_pymol_command(command: str) -> str:
    """Run a PyMOL command via the XML-RPC interface.

    Args:
        command: A valid PyMOL command string, e.g. 'fetch 1abc', 'show cartoon'
    """
    _proxy.do(command)
    return f"Executed: {command}"


# @mcp.tool()
# def save_image(file_path: str, ray: bool = False, dpi: int = 150) -> str:
#     """Save the current PyMOL view to a PNG file.

#     Args:
#         file_path: Absolute path for the output PNG file.
#         ray: Whether to ray-trace before saving (slower but higher quality).
#         dpi: Image resolution in DPI.
#     """
#     _proxy.do("zoom")
#     if ray:
#         _proxy.do("ray")
#     _proxy.do(f"png {file_path}, dpi={dpi}")
#     time.sleep(1)
#     return f"Image saved to {file_path}"


# @mcp.tool()
# def get_screenshot(file_path: str, ray: bool = False) -> Image:
#     """Capture the current PyMOL session as an image and return it.

#     Args:
#         file_path: Temporary path used to write the PNG, e.g. /tmp/view.png
#         ray: Whether to ray-trace before capturing.
#     """
#     _proxy.do("zoom")
#     if ray:
#         _proxy.do("ray")
#     _proxy.do(f"png {file_path}, dpi=150")
#     time.sleep(1)
#     return Image(path=file_path)


if __name__ == "__main__":
    mcp.run()
