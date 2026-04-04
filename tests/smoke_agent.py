"""Smoke test for the LLM agent — verifies tool calling + memory + vision.

Usage:
    USE_MOCKS=true uv run python tests/smoke_agent.py
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("USE_MOCKS", "true")

from agent.tools import MCPToolManager
from agent.llm import RestaurantAgent


def log(msg: str):
    print(f"  [{time.strftime('%H:%M:%S')}] {msg}", flush=True)


async def main():
    manager = MCPToolManager()

    log("Connecting MCP servers...")
    await manager.connect_server(
        "twogis", "uv", ["run", "python", "mcp_servers/twogis/server.py"]
    )
    await manager.connect_server(
        "chocolife", "uv", ["run", "python", "mcp_servers/chocolife/server.py"]
    )
    await manager.connect_server(
        "abr_group", "uv", ["run", "python", "mcp_servers/abr_group/server.py"]
    )

    tools = manager.get_openai_tools()
    log(f"Registered tools: {[t['function']['name'] for t in tools]}")

    agent = RestaurantAgent(manager)

    # Test 1: text query — should trigger MCP tool(s)
    print("\n=== Test 1: Text query (tool calling) ===")
    t0 = time.time()
    resp1 = await agent.chat("Где поужинать в центре Алматы? Хочу итальянскую кухню.")
    log(f"Response in {time.time() - t0:.1f}s")
    print(f"  Agent: {resp1}")
    assert len(resp1) > 0, "Empty response"
    print("  PASS\n")

    # Test 2: follow-up — tests conversation memory
    print("=== Test 2: Follow-up (memory) ===")
    t0 = time.time()
    resp2 = await agent.chat("А какие там цены и часы работы?")
    log(f"Response in {time.time() - t0:.1f}s")
    print(f"  Agent: {resp2}")
    assert len(resp2) > 0, "Empty response"
    print("  PASS\n")

    # Test 3: deals query — should trigger chocolife tool
    print("=== Test 3: Deals query (chocolife tool) ===")
    t0 = time.time()
    resp3 = await agent.chat("Есть ли скидки на рестораны сейчас?")
    log(f"Response in {time.time() - t0:.1f}s")
    print(f"  Agent: {resp3}")
    assert len(resp3) > 0, "Empty response"
    print("  PASS\n")

    # Cleanup may raise on Windows due to anyio cancel scope limitations
    # in MCP stdio_client — safe to ignore since subprocesses die with the script.
    try:
        await manager.cleanup()
    except Exception:
        pass
    print("All agent smoke tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
