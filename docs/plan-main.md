# AI Avatar Agent — Implementation Plan

## Context

Build a multimodal AI agent — a restaurant guide for Almaty that accepts text/image/audio, responds with text + talking avatar video, uses MCP servers for real data (2GIS, Chocolife), wrapped in Gradio. Scored out of 100 points. Budget: ~$15-20.

**Pipeline:** User Input → ASR → LLM (tool calling) → TTS (cloned voice) → Avatar Video → Gradio Output

---

## Dependency Graph

```
Phase 1 (scaffold)
  └→ Phase 2 (MCP servers)
       └→ Phase 3 (LLM agent + vision + critic skill)
            ├→ Phase 4 (ASR) — adds audio input
            ├→ Phase 5 (TTS) — adds audio output
            │    └→ Phase 6 (Avatar) — needs TTS audio URL
            └→ Phase 7 (Gradio + README + demo)
```

## Points by Phase

| Phase | Description | Points | Cumulative |
|-------|-------------|--------|------------|
| 1 | Scaffold + Config | 0 | 0 |
| 2 | MCP Servers (2GIS + Chocolife) | 25 | 25 |
| 3 | LLM + Tools + Memory + Vision + Critic | 35 | 60 |
| 4 | ASR (Whisper) | 0* | 60 |
| 5 | Voice Clone + TTS | 10 | 70 |
| 6 | Avatar Video | 20 | 90 |
| 7 | Gradio + README + Demo | 10 | 100 |

\* ASR has no dedicated points but is required for full pipeline.

---

## Phase 1: Project Scaffold + Config

**Goal:** Directory structure, config system, env vars, mock toggle.

### Files to create

- `config.py` — centralized config from env vars
- `.env.example` — template with all keys
- `agent/__init__.py`, `agent/llm.py`, `agent/tools.py`, `agent/pipeline.py` — placeholders
- `mcp_servers/__init__.py`, `mcp_servers/twogis/__init__.py`, `mcp_servers/chocolife/__init__.py`, `mcp_servers/abr_group/__init__.py`
- `voice/__init__.py`, `voice/clone.py`, `voice/tts.py` — placeholders
- `avatar/__init__.py`, `avatar/generate.py` — placeholder
- `assets/` — directory for demo video
- Delete `main.py` (placeholder from `uv init`)

### .gitignore addition

Add `.cache/` to `.gitignore` — cached scraping data must not be committed.

### config.py design

```python
import os
from dotenv import load_dotenv

load_dotenv()

USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # cheapest for text + tool calling + vision
ASR_MODEL = os.getenv("ASR_MODEL", "gpt-5.4-mini")  # better transcription quality
VISION_DETAIL = os.getenv("VISION_DETAIL", "low")  # cost optimization

VOICE_ID = os.getenv("VOICE_ID", "")
VOICE_SAMPLE_PATH = os.getenv("VOICE_SAMPLE_PATH", "voice/my_voice_sample.wav")
AVATAR_PHOTO_URL = os.getenv("AVATAR_PHOTO_URL", "")

CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
MAX_RESPONSE_CHARS = int(os.getenv("MAX_RESPONSE_CHARS", "500"))  # ~30s speech
```

### .env.example

```
USE_MOCKS=true
OPENAI_API_KEY=sk-...
FAL_KEY=...
VOICE_ID=
VOICE_SAMPLE_PATH=voice/my_voice_sample.wav
AVATAR_PHOTO_URL=
LLM_MODEL=gpt-4o-mini
ASR_MODEL=gpt-5.4-mini
VISION_DETAIL=low
```

### Dependencies

```bash
uv add python-dotenv
```

### Verification

```bash
uv run python -c "from config import USE_MOCKS; print(f'Mocks: {USE_MOCKS}')"
```

---

## Phase 2: MCP Servers (2GIS + Chocolife)

**Goal:** Two functional MCP servers as separate processes. Each uses Playwright for scraping with JSON file cache.

### Dependencies

```bash
uv add "mcp[cli]" playwright
uv run playwright install chromium
```

### Files to create

- `mcp_servers/twogis/server.py`
- `mcp_servers/twogis/README.md`
- `mcp_servers/chocolife/server.py`
- `mcp_servers/chocolife/README.md`

### mcp_servers/twogis/server.py

```python
from mcp.server.fastmcp import FastMCP
import json, os, hashlib, time
from pathlib import Path

mcp = FastMCP("twogis")
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"

CACHE_DIR = Path(".cache/twogis")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 86400  # 24h

def _get_cached(key: str) -> list[dict] | None:
    path = CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data["timestamp"] < CACHE_TTL:
            return data["results"]
    return None

def _set_cache(key: str, results: list[dict]):
    path = CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"
    path.write_text(json.dumps({"timestamp": time.time(), "results": results}, ensure_ascii=False), encoding="utf-8")

@mcp.tool()
async def search_restaurants(query: str, location: str = "Алматы") -> list[dict]:
    """Search restaurants in Almaty via 2GIS.
    Returns list with: name, address, rating, cuisine, price_range, working_hours, phone."""
    cache_key = f"{query}:{location}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if USE_MOCKS:
        return [
            {"name": "Del Papa", "address": "пр. Достык, 85", "rating": 4.5,
             "cuisine": "итальянская", "price_range": "$$", "working_hours": "10:00-23:00", "phone": "+7 727 111-22-33"},
            {"name": "Бочка", "address": "ул. Кабанбай батыра, 42", "rating": 4.3,
             "cuisine": "европейская", "price_range": "$$", "working_hours": "11:00-00:00", "phone": "+7 727 222-33-44"},
            {"name": "Kishlak", "address": "ул. Тулебаева, 78", "rating": 4.6,
             "cuisine": "узбекская", "price_range": "$", "working_hours": "09:00-22:00", "phone": "+7 727 333-44-55"},
        ]

    from playwright.async_api import async_playwright
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        search_url = f"https://2gis.kz/almaty/search/{query}"
        await page.goto(search_url, wait_until="networkidle", timeout=30000)
        # Parse restaurant cards from DOM — inspect 2GIS live to find selectors
        # Extract: name, address, rating, cuisine, hours, phone
        # Limit to 5-10 results
        await browser.close()

    _set_cache(cache_key, results)
    return results

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### mcp_servers/chocolife/server.py

Same cache structure as 2GIS. Scrapes `https://chocolife.me/restorany-kafe-i-bary/` (verify URL at implementation time).

```python
from mcp.server.fastmcp import FastMCP
import json, os, hashlib, time
from pathlib import Path

mcp = FastMCP("chocolife")
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"

CACHE_DIR = Path(".cache/chocolife")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 86400

# ... same _get_cached / _set_cache helpers as 2GIS ...

@mcp.tool()
async def search_deals(category: str = "рестораны", city: str = "Алматы") -> list[dict]:
    """Search restaurant deals on Chocolife.
    Returns list with: title, restaurant_name, original_price, discount_price, discount_percent, description, url."""
    cache_key = f"{category}:{city}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if USE_MOCKS:
        return [
            {"title": "Ужин на двоих в Del Papa", "restaurant_name": "Del Papa",
             "original_price": 15000, "discount_price": 9000, "discount_percent": 40,
             "description": "Два основных блюда + десерт + напитки",
             "url": "https://chocolife.me/almaty/deal/12345"},
            {"title": "Бизнес-ланч в Бочке", "restaurant_name": "Бочка",
             "original_price": 5000, "discount_price": 3500, "discount_percent": 30,
             "description": "Салат + суп + горячее + напиток",
             "url": "https://chocolife.me/almaty/deal/67890"},
        ]

    from playwright.async_api import async_playwright
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://chocolife.me/restorany-kafe-i-bary/", wait_until="networkidle", timeout=30000)
        # Parse deal cards from DOM — inspect Chocolife live to find selectors
        # Extract: title, restaurant_name, original_price, discount_price, discount_percent, description, url
        await browser.close()

    _set_cache(cache_key, results)
    return results

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Mock strategy

When `USE_MOCKS=true`, return hardcoded sample data (3-5 realistic entries in Russian) without launching Playwright.

### Verification

Test each server standalone via MCP client:

```python
# test_mcp.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    params = StdioServerParameters(command="uv", args=["run", "python", "mcp_servers/twogis/server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])
            result = await session.call_tool("search_restaurants", {"query": "итальянский ресторан"})
            print("Result:", result)

asyncio.run(test())
```

### Cost optimization (bonus pts — implement here)

- **Scraping cache is mandatory in this phase.** Use `_get_cached`/`_set_cache` with 24h TTL JSON files. The cache code shown above in `server.py` is not optional — it earns bonus points.

### Risks

- 2GIS uses heavy JS rendering — set 30s timeouts, `wait_until="networkidle"`
- Chocolife may change DOM — cache aggressively
- Add `asyncio.sleep(2)` between requests to avoid rate limiting

### ABR Group MCP (bonus — not separately scored, but strengthens MCP criterion)

Lower priority — implement only after core phases work. Outline:

```python
# mcp_servers/abr_group/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("abr_group")

@mcp.tool()
async def get_restaurant_info(name: str) -> dict:
    """Get info about ABR Group restaurants (Бочка, Del Papa, etc.).
    Returns: name, address, menu_highlights, average_check, booking_url."""
    # Scrape ABR Group restaurant websites
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Phase 3: LLM Agent (Tool Calling + Memory + Vision + Restaurant Critic)

**Goal:** LLM brain connecting to MCP servers, auto-selecting tools, maintaining conversation history, processing images, and exposing restaurant critic skill.

### Dependencies

```bash
uv add openai
```

### Files to create

- `agent/tools.py` — MCP client manager + custom tool definitions
- `agent/llm.py` — LLM with tool calling loop, memory, vision, restaurant critic

### agent/tools.py — MCPToolManager

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPToolManager:
    """Connects to MCP server subprocesses, lists their tools,
    converts schemas to OpenAI format, routes tool calls."""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._tool_to_server: dict[str, str] = {}
        self._openai_tools: list[dict] = []
        self._cleanup_tasks: list[tuple] = []  # (session_cm, client_cm)

    async def connect_server(self, name: str, command: str, args: list[str]):
        """Start MCP server subprocess, register its tools."""
        params = StdioServerParameters(command=command, args=args)
        # Manually enter async context managers — keep alive for session duration
        client_cm = stdio_client(params)
        read, write = await client_cm.__aenter__()
        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._sessions[name] = session
        self._cleanup_tasks.append((session_cm, client_cm))

        # List tools & convert to OpenAI format
        tools = await session.list_tools()
        for tool in tools.tools:
            self._tool_to_server[tool.name] = name
            self._openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema  # JSON Schema → direct mapping
                }
            })

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Route tool call to correct MCP server."""
        server_name = self._tool_to_server[tool_name]
        session = self._sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        return result.content[0].text

    def get_openai_tools(self) -> list[dict]:
        """Return all MCP tools + custom tools in OpenAI format."""
        custom_tools = [{
            "type": "function",
            "function": {
                "name": "analyze_restaurant_photo",
                "description": "Analyze the restaurant photo that the user just sent to determine establishment level, status, and atmosphere. Call this when the user asks to evaluate/rate a restaurant based on its photo.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }]
        return self._openai_tools + custom_tools

    async def cleanup(self):
        """Shut down all MCP server subprocesses."""
        for session_cm, client_cm in self._cleanup_tasks:
            await session_cm.__aexit__(None, None, None)
            await client_cm.__aexit__(None, None, None)
```

Key detail: MCP tool `inputSchema` maps directly to OpenAI function `parameters` (both are JSON Schema). The `stdio_client` context manager owns the subprocess — exiting it kills the server. We manually `__aenter__`/`__aexit__` to control the lifecycle.

### agent/llm.py — RestaurantAgent

```python
class RestaurantAgent:
    def __init__(self, tool_manager: MCPToolManager):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.tool_manager = tool_manager
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    async def chat(self, user_text: str, image_url: str | None = None) -> str:
        self._current_image_url = image_url  # store for tool access
        # Build user message (text + optional image_url with detail=low)
        # gpt-4o-mini handles both text and vision (detail=low keeps cost down)
        # Tool calling loop:
        #   1. Send messages + tools to LLM (with selected model)
        #   2. If response has tool_calls → execute each, append results, loop
        #      Special case: analyze_restaurant_photo → call _analyze_restaurant_photo
        #      using self._current_image_url (NOT a tool argument — the LLM can't pass it)
        #   3. If response has content → return text

    async def _analyze_restaurant_photo(self) -> str:
        """Custom skill: send stored image to vision model with critic prompt.
        Uses self._current_image_url (set by chat() before tool loop).
        Returns JSON: {level, status, description, confidence}"""
```

### System prompt

```
Ты — персональный ассистент-проводник по ресторанам Алматы.
Помогаешь найти рестораны, кафе, бары, узнать о скидках и акциях.
Отвечай на русском. Используй инструменты для поиска реальных данных.
Держи ответы краткими — не более 500 символов (15-30 секунд речи).

Если пользователь отправляет фото еды — опиши блюдо и предложи подходящие рестораны.
Если пользователь просит оценить ресторан по фото (интерьер, вывеска, зал) —
используй инструмент analyze_restaurant_photo для структурированной оценки.
```

### Vision vs. Restaurant Critic — two separate scored items

**Vision Input (10 pts):** User sends ANY image (food, menu, interior). The LLM receives it directly via `image_url` content block and incorporates what it sees into its text response. No tool call — the LLM just "looks" at the image. Example: food photo → "This looks like plov, I can recommend uzbek restaurants nearby..."

**Restaurant Critic Skill (5 pts):** User sends a restaurant exterior/interior photo AND asks to evaluate it. The LLM calls the `analyze_restaurant_photo` tool → gets structured JSON `{level, status, description, confidence}` → uses that in the answer. This must be a registered tool that the LLM calls automatically via function calling.

Both paths involve vision, but only the critic path uses the tool. The system prompt guides the LLM to distinguish between the two cases.

### Cost optimization (bonus pts — implement here)

- **Model routing:** `gpt-4o-mini` (`LLM_MODEL`) for LLM (text + vision + tool calling), `gpt-5.4-mini` (`ASR_MODEL`) for ASR. Different models for different tasks = model routing.
- **`detail: low`:** Always pass `{"detail": config.VISION_DETAIL}` (default `"low"`) in image_url content blocks.
- **Response length cap:** System prompt must enforce `MAX_RESPONSE_CHARS` limit (~500 chars / 15-30s speech).

### Mock strategy

MCP servers return mock data (Phase 2 handles this). LLM itself is cheap (~$0.15/1M input tokens) — no mock needed for it. Vision uses `detail: low` for cost savings.

### Verification

```python
# test_agent.py
import asyncio
from agent.tools import MCPToolManager
from agent.llm import RestaurantAgent

async def main():
    manager = MCPToolManager()
    await manager.connect_server("twogis", "uv", ["run", "python", "mcp_servers/twogis/server.py"])
    await manager.connect_server("chocolife", "uv", ["run", "python", "mcp_servers/chocolife/server.py"])

    agent = RestaurantAgent(manager)

    # Test 1: text → triggers MCP tool
    print(await agent.chat("Где поужинать в центре Алматы, итальянская кухня?"))

    # Test 2: follow-up → tests memory
    print(await agent.chat("А какие там цены?"))

    # Test 3: image → triggers restaurant critic
    print(await agent.chat("Что скажешь об этом ресторане?", image_url="https://example.com/restaurant.jpg"))

asyncio.run(main())
```

### Key architecture decisions

- **Tool call loop:** LLM may chain multiple tools. Loop until LLM returns text (no more tool_calls).
- **MCP client lifecycle:** Keep subprocess connections alive for session duration. The `stdio_client` context manager owns the subprocess.
- **Memory:** Simple `list[dict]` of messages. Per-session, no cross-session persistence needed.

---

## Phase 4: ASR (Whisper)

**Goal:** Accept audio input, transcribe to text via OpenAI Whisper API.

### Dependencies

None new — `openai` already installed.

### Files to modify

- `agent/pipeline.py` — add `transcribe_audio()` function

```python
from config import ASR_MODEL, USE_MOCKS

async def transcribe_audio(audio_path: str) -> str:
    if USE_MOCKS:
        return "Где лучшие рестораны в центре Алматы?"

    with open(audio_path, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model=ASR_MODEL, file=f, language="ru"
        )
    return transcript.text
```

### Mock strategy

Return a hardcoded Russian query string when `USE_MOCKS=true`.

### Verification

```bash
# With mock:
USE_MOCKS=true uv run python -c "
import asyncio
from agent.pipeline import transcribe_audio
print(asyncio.run(transcribe_audio('test.wav')))
"

# With real audio file:
USE_MOCKS=false uv run python -c "
import asyncio
from agent.pipeline import transcribe_audio
print(asyncio.run(transcribe_audio('path/to/real_audio.wav')))
"
```

---

## Phase 5: Voice Clone + TTS (fal.ai MiniMax)

**Goal:** Clone student's voice (one-time), then generate TTS audio from LLM responses.

### Dependencies

```bash
uv add fal-client
```

### Files to create

#### voice/clone.py — one-time script

```python
import fal_client, os

def clone_voice(audio_url: str) -> str:
    result = fal_client.subscribe("fal-ai/minimax/voice-clone", arguments={
        "audio_url": audio_url,
        "preview_text": "Привет! Я ваш персональный ресторанный гид по Алматы.",
        "language": "Russian"
    })
    voice_id = result["voice_id"]
    print(f"Add to .env: VOICE_ID={voice_id}")
    return voice_id

if __name__ == "__main__":
    audio_url = os.getenv("VOICE_SAMPLE_URL", "")
    if not audio_url:
        audio_url = fal_client.upload_file(os.getenv("VOICE_SAMPLE_PATH", "voice/my_voice_sample.wav"))
    clone_voice(audio_url)
```

#### voice/tts.py

```python
import fal_client
from config import VOICE_ID, USE_MOCKS

async def generate_speech(text: str) -> str:
    """Returns audio URL."""
    if USE_MOCKS:
        return "https://example.com/mock_audio.mp3"

    import asyncio
    result = await asyncio.to_thread(
        lambda: fal_client.subscribe("fal-ai/minimax/speech-02-hd", arguments={
            "text": text, "voice_id": VOICE_ID, "language": "Russian"
        })
    )
    return result["audio"]["url"]
```

### Mock strategy

`generate_speech()` returns placeholder URL when mocked. Clone script is never mocked (run once manually, costs ~$0.50).

### Verification

```bash
# Clone (run once, ~$0.50):
FAL_KEY=... uv run python voice/clone.py

# TTS mock:
USE_MOCKS=true uv run python -c "
import asyncio; from voice.tts import generate_speech
print(asyncio.run(generate_speech('Тест')))
"

# TTS real (few cents):
USE_MOCKS=false VOICE_ID=... FAL_KEY=... uv run python -c "
import asyncio; from voice.tts import generate_speech
print(asyncio.run(generate_speech('Рекомендую ресторан Del Papa.')))
"
```

---

## Phase 6: Avatar Video Generation (fal.ai Creatify Aurora)

**Goal:** Generate talking-head video from student photo + TTS audio. **Test LAST — each generation costs real money.**

### Files to create

#### avatar/generate.py

```python
import fal_client
from config import AVATAR_PHOTO_URL, USE_MOCKS

async def generate_avatar_video(audio_url: str, prompt: str = None) -> str:
    """Returns video URL."""
    if USE_MOCKS:
        return "https://example.com/mock_video.mp4"

    if prompt is None:
        prompt = ("4K studio interview, medium close-up. "
                  "Soft key-light, light-grey backdrop. "
                  "Presenter faces lens, steady eye-contact. Ultra-sharp.")

    import asyncio
    result = await asyncio.to_thread(
        lambda: fal_client.subscribe("fal-ai/creatify/aurora", arguments={
            "image_url": AVATAR_PHOTO_URL,
            "audio_url": audio_url,
            "prompt": prompt,
            "guidance_scale": 1,
            "audio_guidance_scale": 2,
            "resolution": "720p"
        })
    )
    return result["video"]["url"]
```

### Mock strategy

Return placeholder URL. Optionally place a short sample `.mp4` in `assets/` for Gradio preview testing.

### Verification

```bash
# Mock:
USE_MOCKS=true uv run python -c "
import asyncio; from avatar.generate import generate_avatar_video
print(asyncio.run(generate_avatar_video('https://example.com/audio.mp3')))
"

# Real (ONLY after everything else works, costs ~$1-2 per generation):
USE_MOCKS=false FAL_KEY=... AVATAR_PHOTO_URL=... uv run python -c "
import asyncio; from avatar.generate import generate_avatar_video
print(asyncio.run(generate_avatar_video('https://real-tts-audio.mp3')))
"
```

### Budget note

Keep responses under 500 chars (~15-30s speech). Test at most 3-5 times total. Save budget for final demo.

---

## Phase 7: Gradio Frontend + Pipeline Orchestration + README

**Goal:** Wire everything together, build full pipeline orchestrator, write README, record demo.

### Dependencies

```bash
uv add gradio
uv export --no-hashes --frozen > requirements.txt
```

### Files to create/complete

#### agent/pipeline.py — full orchestrator

```python
import base64, mimetypes

def _encode_image_to_data_url(path: str) -> str:
    """Convert local image file to base64 data URL for OpenAI vision."""
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"

class Pipeline:
    def __init__(self):
        self.tool_manager = MCPToolManager()
        self.agent = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        await self.tool_manager.connect_server("twogis", "uv", ["run", "python", "mcp_servers/twogis/server.py"])
        await self.tool_manager.connect_server("chocolife", "uv", ["run", "python", "mcp_servers/chocolife/server.py"])
        self.agent = RestaurantAgent(self.tool_manager)
        self._initialized = True

    async def process(self, text=None, image_path=None, audio_path=None) -> tuple[str, str | None]:
        """ASR → LLM → TTS → Avatar. Returns (text_response, video_url)."""
        await self.initialize()

        if audio_path and not text:
            text = await transcribe_audio(audio_path)

        image_url = _encode_image_to_data_url(image_path) if image_path else None
        response_text = await self.agent.chat(text or "", image_url=image_url)
        audio_url = await generate_speech(response_text)
        video_url = await generate_avatar_video(audio_url)

        return response_text, video_url
```

#### app.py — Gradio frontend

Use `gr.Blocks` with separate output components for reliable text + video display.
`gr.ChatInterface` with `type="messages"` has uncertain support for inline video —
`gr.Blocks` gives full control.

```python
import gradio as gr
from agent.pipeline import Pipeline

pipeline = Pipeline()

async def respond(text, image, audio, chat_history):
    """Handle multimodal input, return updated chat + video."""
    response_text, video_url = await pipeline.process(
        text=text or None,
        image_path=image or None,
        audio_path=audio or None
    )

    chat_history = chat_history or []
    if text:
        chat_history.append({"role": "user", "content": text})
    if image:
        chat_history.append({"role": "user", "content": f"[Uploaded image: {image}]"})
    if audio:
        chat_history.append({"role": "user", "content": f"[Uploaded audio: {audio}]"})
    chat_history.append({"role": "assistant", "content": response_text})

    # Return video only when it's a real URL (not mock placeholder)
    video_out = video_url if (video_url and "example.com" not in video_url) else None

    return chat_history, video_out, "", None, None  # clear inputs after submit

with gr.Blocks(title="AI Ресторанный Гид Алматы") as demo:
    gr.Markdown("# AI Ресторанный Гид Алматы\nМультимодальный ассистент с аватаром. Текст, голос или фото.")

    chatbot = gr.Chatbot(type="messages", label="Диалог")
    video_output = gr.Video(label="Аватар-ответ")

    with gr.Row():
        text_input = gr.Textbox(placeholder="Спросите о ресторанах Алматы...", label="Текст", scale=3)
        image_input = gr.Image(type="filepath", label="Фото", scale=1)
        audio_input = gr.Audio(type="filepath", label="Аудио", scale=1)

    submit_btn = gr.Button("Отправить")
    submit_btn.click(
        respond,
        inputs=[text_input, image_input, audio_input, chatbot],
        outputs=[chatbot, video_output, text_input, image_input, audio_input]
    )

if __name__ == "__main__":
    demo.launch()
```

#### README.md

Must include all 7 required sections:
1. Project description (2-3 sentences)
2. Architecture diagram (ASCII/Mermaid pipeline)
3. Models used and why (GPT-4o-mini for LLM, GPT-5.4-mini for ASR, MiniMax for TTS, Creatify Aurora for avatar)
4. Step-by-step launch: install deps, configure `.env`, start MCP servers, run `app.py`
5. Screenshots/GIFs of working interface
6. Cost breakdown (actual API spend)
7. What would improve with more time

#### Demo video (2-3 minutes) — must demonstrate all scored features:

1. **Text query** → agent searches restaurants via MCP → responds with text + avatar video (MCP 25pts + Avatar 20pts)
2. **Voice query** → ASR transcribes → same pipeline → avatar video (Voice Clone + TTS 10pts)
3. **Image input (food photo)** → LLM describes dish, recommends restaurants (Vision 10pts)
4. **Image input (restaurant photo)** → LLM calls `analyze_restaurant_photo` tool → structured analysis (Critic 5pts)
5. **Follow-up question** → agent uses prior context to answer (Memory, part of 20pts)

### Verification

```bash
# Full integration with mocks:
USE_MOCKS=true uv run python app.py
# → Opens at http://localhost:7860
# Test: type query → text response
# Test: upload image → critic analysis
# Test: upload audio → transcription + response

# Final demo (USE_MOCKS=false) — all real APIs
```

---

## All Dependencies (install order)

```bash
uv add python-dotenv                  # Phase 1
uv add "mcp[cli]" playwright          # Phase 2
uv run playwright install chromium    # Phase 2
uv add openai                         # Phase 3
uv add fal-client                     # Phase 5
uv add gradio                         # Phase 7
uv export --no-hashes --frozen > requirements.txt
```

## Budget Estimate

| Component | Cost |
|-----------|------|
| GPT-4o-mini (LLM + vision, dev + demo) | ~$2-3 |
| GPT-5.4-mini (ASR) | ~$0.50 |
| Voice Clone (1 clone) | ~$0.50 |
| MiniMax TTS (dev + demo) | ~$1-2 |
| Creatify Aurora (3-5 gens) | ~$5-10 |
| **Total** | **~$10-16** |

## Cost Optimization (bonus +10 pts — NOT a separate phase)

These are design decisions baked into the code at specific phases. They must be implemented inline, not as a follow-up:

| Technique | Where | Implementation |
|-----------|-------|----------------|
| **Scraping cache** | Phase 2 — MCP servers | JSON file cache with 24h TTL (`_get_cached`/`_set_cache` helpers). Never re-scrape the same query within TTL. |
| **Model routing** | Phase 3 + 4 | `gpt-4o-mini` for LLM (cheap text + vision + tool calling), `gpt-5.4-mini` for ASR (better transcription). Different models for different pipeline stages. |
| **`detail: low`** | Phase 3 — `agent/llm.py` | Always pass `{"detail": VISION_DETAIL}` (default `"low"`) in `image_url` content blocks to minimize vision tokens. Configured via `config.VISION_DETAIL`. |
| **Response length cap** | Phase 3 — system prompt | System prompt enforces `MAX_RESPONSE_CHARS=500` (~15-30s speech). Keeps TTS and video generation short and cheap. |
