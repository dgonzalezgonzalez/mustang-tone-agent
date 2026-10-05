"""Interoperability smoke test: two transports, actual initialized MCP client sessions."""

import asyncio
import sys
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mustang.config import token


async def exercise(read, write, transport):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("get_capabilities", {})
        assert not result.isError
        assert len(tools.tools) >= 15
        print(f"{transport}: {len(tools.tools)} tools; capability call passed")


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mustang.cli", "mcp"],
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    async with stdio_client(params) as (read, write):
        await exercise(read, write, "stdio")
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token()}"}) as client:
        async with streamable_http_client("http://127.0.0.1:8765/mcp", http_client=client) as streams:
            await exercise(streams[0], streams[1], "Streamable HTTP")


if __name__ == "__main__":
    asyncio.run(main())
