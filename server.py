from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Universe Truth")


@mcp.tool()
def ask_universe_truth(question: str) -> str:
    """当你想知道宇宙终极真理时，问这个工具。"""
    return "42"


if __name__ == "__main__":
    mcp.run()
