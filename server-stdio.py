#!/usr/bin/env python3
"""MCP Server for TickTick - Stdio mode wrapper.

This module provides backward compatibility for Docker-based stdio deployments.
For native installations, use the `ticktick-mcp` command instead.

Usage:
    Docker:  python server-stdio.py
    Native:  ticktick-mcp
"""

from ticktick.mcp.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
