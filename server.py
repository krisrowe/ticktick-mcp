"""MCP Server for TickTick - Docker compatibility wrapper.

This module provides backward compatibility for Docker-based deployments.
For native installations, use the `ticktick-mcp` command instead.

Usage:
    HTTP mode (Docker):  uvicorn server:mcp_app --host 0.0.0.0 --port 8000
    Stdio mode (Docker): python server.py --stdio
    Native (preferred):  ticktick-mcp --stdio
"""

import sys

# Import from the package
from ticktick.mcp.server import mcp, mcp_app

__all__ = ["mcp", "mcp_app"]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        mcp.run(transport="stdio")
