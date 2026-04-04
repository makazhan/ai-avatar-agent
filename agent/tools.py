from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolManager:
    """Connects to MCP server subprocesses, lists their tools,
    converts schemas to OpenAI format, routes tool calls."""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._tool_to_server: dict[str, str] = {}
        self._openai_tools: list[dict] = []
        self._cleanup_tasks: list[tuple] = []

    async def connect_server(self, name: str, command: str, args: list[str]):
        """Start MCP server subprocess, register its tools."""
        params = StdioServerParameters(command=command, args=args)
        client_cm = stdio_client(params)
        read, write = await client_cm.__aenter__()
        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._sessions[name] = session
        self._cleanup_tasks.append((session_cm, client_cm))

        tools = await session.list_tools()
        for tool in tools.tools:
            self._tool_to_server[tool.name] = name
            self._openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            })

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Route tool call to correct MCP server."""
        server_name = self._tool_to_server[tool_name]
        session = self._sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        if not result.content:
            return "No results returned."
        return result.content[0].text

    def get_openai_tools(self) -> list[dict]:
        """Return MCP tools in OpenAI format."""
        return list(self._openai_tools)

    async def cleanup(self):
        """Shut down all MCP server subprocesses."""
        for session_cm, _client_cm in self._cleanup_tasks:
            try:
                await session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            # Skip client_cm.__aexit__ — anyio cancel scope raises
            # RuntimeError on Windows when exited from a different task.
            # Subprocesses are cleaned up when the event loop exits.
        self._sessions.clear()
        self._tool_to_server.clear()
        self._cleanup_tasks.clear()
