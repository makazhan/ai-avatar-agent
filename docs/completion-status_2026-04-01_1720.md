# Project Completion Status

**Date:** 2026-04-01
**Branch:** main
**Last commit:** 3e4907a — FEAT: added MCP servers
**Note:** Phase 3 (LLM Agent) changes are uncommitted in the working tree.

---

## Overview Table

| Category | Done | Partial | Not started | Total | % |
|----------|------|---------|-------------|-------|---|
| Phase 1: Scaffold + Config | 5 | 0 | 0 | 5 | 100% |
| Phase 2: MCP Servers | 8 | 0 | 0 | 8 | 100% |
| Phase 3: LLM Agent + Vision + Critic | 8 | 0 | 0 | 8 | 100% |
| Phase 4: ASR (Whisper) | 0 | 0 | 2 | 2 | 0% |
| Phase 5: Voice Clone + TTS | 0 | 0 | 4 | 4 | 0% |
| Phase 6: Avatar Video | 0 | 0 | 3 | 3 | 0% |
| Phase 7: Gradio + Pipeline + README | 0 | 0 | 5 | 5 | 0% |
| **Total** | **21** | **0** | **14** | **35** | **60%** |

**Percentage formula**: (done + partial * 0.5) / total * 100

---

## Phase 1: Scaffold + Config

### Directory structure — DONE

**Status:** Done

- All required directories exist: `agent/`, `mcp_servers/`, `voice/`, `avatar/`, `assets/`
- `__init__.py` files present in all packages
- `main.py` deleted as specified

### config.py — DONE

**Status:** Done

- `config.py:1-31` — All env vars: `USE_MOCKS`, `OPENAI_API_KEY`, `FAL_KEY`, `LLM_MODEL`, `ASR_MODEL`, `VISION_DETAIL`, `VOICE_ID`, `VOICE_SAMPLE_PATH`, `AVATAR_PHOTO_URL`, `CACHE_DIR`, `CACHE_TTL_HOURS`, `MAX_RESPONSE_CHARS`

### .env.example — DONE

**Status:** Done

- Template with all required keys, no real secrets

### .gitignore — DONE

**Status:** Done

- Includes `.cache/`, `.env`, standard Python entries

### Dependencies (Phase 1) — DONE

**Status:** Done

- `python-dotenv>=1.2.2` in `pyproject.toml`

---

## Phase 2: MCP Servers (25 pts)

### 2GIS MCP server — DONE

**Status:** Done

- `mcp_servers/twogis/server.py` (169 lines) — `search_restaurants(query, location)` tool
- Playwright scraping with headless browser, antibot measures, 5s wait
- Returns: name, address, rating, cuisine, price_range, working_hours, phone
- Mock mode: 5 realistic restaurant entries in Russian

### Chocolife MCP server — DONE

**Status:** Done

- `mcp_servers/chocolife/server.py` (155 lines) — `search_deals(category, city)` tool
- Playwright scraping with locale="ru-RU"
- Returns: title, restaurant_name, original_price, discount_price, discount_percent, description, url
- Mock mode: 4 realistic deal entries

### ABR Group MCP server (bonus) — DONE

**Status:** Done

- `mcp_servers/abr_group/server.py` (215 lines) — `get_abr_restaurants(name)` tool
- Multi-stage scraping: listing page then detail pages
- Returns: name, cuisine, city, addresses, menu_url, booking_url, phones, working_hours, menu_highlights, average_check
- Mock mode: 5 ABR Group restaurants

### Cache system — DONE

**Status:** Done

- `mcp_servers/cache_utils.py` (36 lines) — `get_cached()`, `set_cache()` with MD5 key hashing
- 24h TTL from `CACHE_TTL_HOURS` env var
- Per-server cache directories: `.cache/twogis/`, `.cache/chocolife/`, `.cache/abr_group/`

### MCP READMEs — DONE

**Status:** Done

- `mcp_servers/twogis/README.md`, `mcp_servers/chocolife/README.md`, `mcp_servers/abr_group/README.md` all present with tool documentation

### MCP smoke tests — DONE

**Status:** Done

- `tests/smoke_mcp.py` (120 lines) — tests all three servers individually via stdio_client

### Mock strategy — DONE

**Status:** Done

- All servers return hardcoded data when `USE_MOCKS=true`, no Playwright launched

### Scraping cache (cost optimization) — DONE

**Status:** Done

- JSON file cache with 24h TTL implemented across all servers

---

## Phase 3: LLM Agent + Vision + Critic (35 pts)

### MCPToolManager — DONE

**Status:** Done

- `agent/tools.py` (64 lines) — connects to MCP subprocesses, converts tool schemas to OpenAI format, routes tool calls
- `connect_server()`, `call_tool()`, `get_openai_tools()`, `cleanup()`
- Guard for empty `result.content` in `call_tool()`

### RestaurantAgent with tool calling loop — DONE

**Status:** Done

- `agent/llm.py` (126 lines) — `RestaurantAgent` class with `chat(user_text, image_url)` method
- Tool calling loop: sends messages + tools to API, executes tool_calls, loops until final text
- Parallel tool execution via `asyncio.gather()`

### Conversation memory — DONE

**Status:** Done

- `agent/llm.py:54` — `self.history: list[dict]` maintains full conversation across turns
- Verified by smoke test: follow-up questions use prior context

### Vision input — DONE

**Status:** Done

- `agent/llm.py:62-65` — `image_url` content block with `detail: VISION_DETAIL` (default "low")
- LLM processes food/menu/interior photos directly

### Restaurant Critic skill — DONE

**Status:** Done

- `agent/llm.py:27` — `ANALYZE_PHOTO_TOOL` constant, registered as OpenAI function tool
- `agent/llm.py:101-126` — `_analyze_restaurant_photo(image_url)` sends image + CRITIC_PROMPT to vision model
- Returns structured JSON: `{level, status, description, confidence}`
- LLM auto-selects this tool when user asks to evaluate a restaurant photo

### Cost optimizations (model routing, detail:low, response cap) — DONE

**Status:** Done

- Model routing: `gpt-4o-mini` for LLM, `gpt-5.4-mini` for ASR (config.py)
- Vision: `detail: "low"` in all image_url blocks (llm.py:65)
- Response cap: 500 chars in system prompt (llm.py:11)

### Agent smoke tests — DONE

**Status:** Done

- `tests/smoke_agent.py` (79 lines) — 3 tests: text query (tool calling), follow-up (memory), deals query (chocolife)

### openai dependency — DONE

**Status:** Done

- `openai>=2.30.0` in pyproject.toml, requirements.txt synced

---

## Phase 4: ASR (Whisper) (0 pts, but required)

### transcribe_audio() function — NOT STARTED

**Status:** Not started

- `agent/pipeline.py` is empty (0 lines)
- Missing: `transcribe_audio(audio_path)` with OpenAI Whisper API
- Missing: mock mode returning hardcoded Russian query

### ASR integration test — NOT STARTED

**Status:** Not started

- No test for audio transcription

---

## Phase 5: Voice Clone + TTS (10 pts)

### voice/clone.py — NOT STARTED

**Status:** Not started

- File exists but is empty (0 lines)
- Missing: fal_client.subscribe("fal-ai/minimax/voice-clone") implementation

### voice/tts.py — NOT STARTED

**Status:** Not started

- File exists but is empty (0 lines)
- Missing: `generate_speech(text)` returning audio URL

### Voice sample — NOT STARTED

**Status:** Not started

- `voice/my_voice_sample.wav` does not exist
- Required: 10+ second clean audio recording

### fal-client dependency — NOT STARTED

**Status:** Not started

- Not in pyproject.toml — needs `uv add fal-client`

---

## Phase 6: Avatar Video (20 pts)

### avatar/generate.py — NOT STARTED

**Status:** Not started

- File exists but is empty (0 lines)
- Missing: `generate_avatar_video(audio_url)` with fal_client.subscribe("fal-ai/creatify/aurora")

### Avatar photo — NOT STARTED

**Status:** Not started

- `avatar/my_photo.jpg` does not exist
- Required: frontal portrait, 512x512+, good lighting, neutral background

### AVATAR_PHOTO_URL config — NOT STARTED

**Status:** Not started

- Config var exists in config.py but no photo uploaded to set the URL

---

## Phase 7: Gradio + Pipeline + README (10 pts)

### agent/pipeline.py (Pipeline orchestrator) — NOT STARTED

**Status:** Not started

- File exists but is empty (0 lines)
- Missing: `Pipeline` class with `initialize()`, `process(text, image_path, audio_path)`
- Missing: `_encode_image_to_data_url()` helper

### app.py (Gradio frontend) — NOT STARTED

**Status:** Not started

- File does not exist
- Missing: gr.Blocks interface with text/image/audio inputs and chatbot + video outputs

### README.md — NOT STARTED

**Status:** Not started

- File exists but is empty
- Missing all 7 required sections: description, architecture, models, launch instructions, screenshots, cost breakdown, improvements

### Demo video — NOT STARTED

**Status:** Not started

- `assets/demo.mp4` does not exist
- Required: 2-3 minute recording showing all features

### Final requirements.txt sync — NOT STARTED

**Status:** Not started

- Current requirements.txt is synced for Phases 1-3 only
- Will need re-sync after adding fal-client and gradio

---

## Functionality beyond requirements

- **ABR Group MCP server** (`mcp_servers/abr_group/server.py`) — bonus server not separately scored but strengthens the MCP criterion. Includes multi-stage scraping of restaurant detail pages.
- **Shared cache utilities** (`mcp_servers/cache_utils.py`) — extracted common cache logic to avoid duplication across servers.
- **Parallel tool execution** (`agent/llm.py:83-86`) — uses `asyncio.gather()` for concurrent tool calls, not required by plan but improves latency.
- **Agent smoke test** (`tests/smoke_agent.py`) — verifies end-to-end agent behavior with MCP tools.

---

## Progress bars (visual summary)

```
Phase 1: Scaffold     ██████████  100%  (all files, config, deps)
Phase 2: MCP Servers  ██████████  100%  (3 servers + cache + tests)
Phase 3: LLM Agent    ██████████  100%  (tools + memory + vision + critic)
Phase 4: ASR          ░░░░░░░░░░    0%  (pipeline.py empty)
Phase 5: Voice/TTS    ░░░░░░░░░░    0%  (clone.py, tts.py empty, no sample)
Phase 6: Avatar       ░░░░░░░░░░    0%  (generate.py empty, no photo)
Phase 7: Gradio/Demo  ░░░░░░░░░░    0%  (no app.py, no README, no demo)
──────────────────────────────────────
Overall               ██████░░░░   60%
```

---

## Points assessment

| Phase | Max pts | Earned | Notes |
|-------|---------|--------|-------|
| 2: MCP Servers | 25 | **25** | 3 servers, cache, mocks, READMEs |
| 3: LLM + Tools + Memory + Vision + Critic | 35 | **35** | All implemented and tested |
| 5: Voice Clone + TTS | 10 | 0 | Not started |
| 6: Avatar Video | 20 | 0 | Not started |
| 7: Gradio + README + Demo | 10 | 0 | Not started |
| Bonus: Cost Optimization | 10 | **~8** | Cache, model routing, detail:low, response cap all implemented; not yet demonstrable in full pipeline |
| **Total** | **100+10** | **~68** | |

---

## Remaining work (prioritized)

### Priority 1 — Pipeline + Gradio (unblocks demo)
- Implement `agent/pipeline.py` with `transcribe_audio()`, `Pipeline` class, `_encode_image_to_data_url()`
- Create `app.py` with Gradio gr.Blocks interface
- Add `gradio` dependency

### Priority 2 — Voice + TTS (10 pts)
- `uv add fal-client`
- Implement `voice/clone.py` and `voice/tts.py`
- Record and upload `voice/my_voice_sample.wav` (10+ sec)
- Run clone script once to get VOICE_ID

### Priority 3 — Avatar (20 pts)
- Implement `avatar/generate.py`
- Upload frontal portrait to `avatar/my_photo.jpg` and set AVATAR_PHOTO_URL
- Test with real TTS audio (budget: 3-5 generations max)

### Priority 4 — README + Demo (required for submission)
- Write `README.md` with all 7 sections
- Record `assets/demo.mp4` (2-3 min) showing all features
- Final `uv export --no-hashes --frozen > requirements.txt`
