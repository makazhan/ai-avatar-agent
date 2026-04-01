"""Smoke test for MCP servers — runs with USE_MOCKS=false to verify real scraping.

Usage:
    uv run python tests/smoke_mcp.py              # test all
    uv run python tests/smoke_mcp.py twogis        # test 2GIS only
    uv run python tests/smoke_mcp.py chocolife     # test Chocolife only
    uv run python tests/smoke_mcp.py abr_group     # test ABR Group only
"""

import asyncio
import json
import os
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ENV = {**os.environ, "USE_MOCKS": "false", "PYTHONUTF8": "1"}

SERVERS = {
    "twogis": {
        "script": "mcp_servers/twogis/server.py",
        "tool": "search_restaurants",
        "args": {"query": "итальянский ресторан"},
        "display": lambda item: (
            f"{item.get('name', '?')} | {item.get('address', '')} | rating: {item.get('rating', '')}"
        ),
    },
    "chocolife": {
        "script": "mcp_servers/chocolife/server.py",
        "tool": "search_deals",
        "args": {"category": "рестораны"},
        "display": lambda item: (
            f"{item.get('title', '?')} | {item.get('restaurant_name', '')} | -{item.get('discount_percent', '')}%"
        ),
    },
    "abr_group": {
        "script": "mcp_servers/abr_group/server.py",
        "tool": "get_abr_restaurants",
        "args": {"name": "Del Papa"},
        "display": lambda item: (
            f"{item.get('name', '?')} | {item.get('cuisine', '')[:60]} | check: {item.get('average_check', '')}"
        ),
    },
}


def log(msg: str):
    print(f"  [{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _parse_mcp_result(result) -> list[dict]:
    """MCP serializes list[dict] as separate content blocks. Collect them all."""
    data = []
    for block in result.content:
        try:
            parsed = json.loads(block.text)
        except json.JSONDecodeError:
            log(f"WARNING: non-JSON content block: {block.text[:100]}")
            continue
        if isinstance(parsed, list):
            data.extend(parsed)
        else:
            data.append(parsed)
    return data


async def run_server_test(name: str, cfg: dict):
    print(f"=== {name}: {cfg['tool']} ===")
    params = StdioServerParameters(
        command="uv",
        args=["run", "python", cfg["script"]],
        env=ENV,
    )
    log("starting MCP subprocess...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            log("initializing session...")
            await session.initialize()
            log("listing tools...")
            tools = await session.list_tools()
            log(f"tools: {[t.name for t in tools.tools]}")
            log(f"calling {cfg['tool']}({cfg['args']})...")
            t0 = time.time()
            result = await session.call_tool(cfg["tool"], cfg["args"])
            log(f"got response in {time.time() - t0:.1f}s")
            data = _parse_mcp_result(result)
            print(f"  Got {len(data)} results")
            for item in data[:3]:
                print(f"    - {cfg['display'](item)}")
            assert isinstance(data, list) and len(data) >= 1, (
                f"No results returned from {name}"
            )
            print("  PASS\n")


async def main():
    t_start = time.time()
    targets = sys.argv[1:] or list(SERVERS.keys())
    failed = []
    for target in targets:
        if target not in SERVERS:
            print(f"Unknown target: {target}")
            sys.exit(1)
        try:
            await run_server_test(target, SERVERS[target])
        except Exception as e:
            print(f"  FAIL: {e}\n")
            failed.append(target)

    elapsed = time.time() - t_start
    if failed:
        print(f"Failed: {', '.join(failed)} ({elapsed:.1f}s)")
        sys.exit(1)
    print(f"All smoke tests passed. ({elapsed:.1f}s)")


if __name__ == "__main__":
    asyncio.run(main())
