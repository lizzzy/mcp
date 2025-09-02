import logging, sys
from fastmcp import FastMCP

# 把日志写到 stderr，避免污染 stdout（JSON-RPC）
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool
def hello(name: str) -> str:
    """Say hello to someone"""
    return f"Hello, {name}! 👋"

if __name__ == "__main__":
    mcp.run()
