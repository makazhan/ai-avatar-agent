# Project Instructions

## AI Avatar Agent — Almaty Restaurant Assistant

Multimodal AI agent that takes text/image/audio input, answers with text + talking avatar video, uses MCP servers for real data (2GIS, Chocolife, ABR Group), wrapped in Gradio.

## Package Management

- **Always use `uv` for installing packages**, even if a document or example uses `pip`. Convert `pip install <pkg>` to `uv add <pkg>`.
- After adding or removing packages, sync to `requirements.txt` so it stays usable with plain pip:
  ```bash
  uv export --no-hashes --frozen > requirements.txt
  ```
- To run scripts, use `uv run <script>` instead of activating the venv manually.

## Project Structure (mandatory)

```
project05/
├── README.md
├── requirements.txt
├── .env.example               # Template only, NO real keys
├── app.py                     # Main Gradio file
├── agent/
│   ├── llm.py                 # LLM + tool calling logic
│   ├── tools.py               # Tool definitions for LLM
│   └── pipeline.py            # Orchestrator: ASR → LLM → TTS → Avatar
├── mcp_servers/
│   ├── twogis/
│   │   ├── server.py          # MCP server for 2GIS
│   │   └── README.md
│   ├── chocolife/
│   │   ├── server.py          # MCP server for Chocolife
│   │   └── README.md
│   └── abr_group/             # (bonus)
│       ├── server.py
│       └── README.md
├── voice/
│   ├── clone.py               # Voice cloning script
│   ├── tts.py                 # TTS generation
│   └── my_voice_sample.wav    # Audio sample (10+ sec)
├── avatar/
│   ├── generate.py            # Video generation via Creatify Aurora
│   └── my_photo.jpg           # Avatar photo (512x512+, frontal)
├── assets/
│   └── demo.mp4               # Project demo video
└── config.py                  # Configuration (models, params)
```

## Hard Requirements

### MCP Servers
- **Minimum 2 MCP servers** required: 2GIS + Chocolife. ABR Group is bonus.
- MCP server is a **separate process** connected via MCP protocol (stdio/SSE) — NOT a regular function import.
- Use **Playwright** (the Python library) inside custom MCP servers for browser-based scraping.
- LLM must call MCP tools **automatically via function calling** — never hardcode responses.
- Each MCP server directory must have its own README.

### LLM + Tool Calling
- LLM must support tool calling (GPT-4o-mini, GPT-4o, Gemini Flash, Claude Sonnet, etc.).
- LLM must **automatically choose** which tool to call based on user query.
- Agent must maintain **conversation history within session** (memory).
- If user sends an image (food photo / interior), LLM must process it via vision.

### Custom Skill — Restaurant Critic
- `analyze_restaurant_photo(image_url)` — registered as a tool, called automatically by LLM when a restaurant photo is received.
- Returns: `level` (fastfood/casual/mid-range/fine dining), `status` (family/romantic/business/youth), `description`, `confidence`.

### Voice Clone + TTS
- Must clone the **student's own voice** (real voice, not library preset).
- Audio sample: minimum 10 seconds, clean sound.
- Recommended: MiniMax via fal.ai (`fal-ai/minimax/voice-clone`, `fal-ai/minimax/speech-02-hd`).

### Avatar Video
- Generate video from student photo + TTS audio.
- Recommended: Creatify Aurora via fal.ai (`fal-ai/creatify/aurora`).
- Photo requirements: frontal portrait, eye contact, min 512x512px, good lighting, neutral background, no glasses/hands near face.
- Keep agent response to 15-30 seconds of speech (controls video length/cost).

### Gradio Frontend
- Accepts: text, image, audio input.
- Outputs: text response + avatar video.

## API Keys & Budget

- Total budget: ~$15-20.
- Store keys in `.env`, provide `.env.example` with placeholder values.
- **Never commit `.env` with real keys.**
- Services: fal.ai (~$10), OpenAI (~$5) or Google AI (free tier).

## Development Order (CRITICAL)

Follow this order strictly — **test video avatar LAST** because each generation costs real money:

1. MCP servers (2GIS, Chocolife) — verify tools are called and data returns
2. LLM + Tool Calling — verify agent forms correct responses from data
3. ASR (Whisper) — verify voice transcription
4. TTS + Voice Clone — verify audio generation with cloned voice
5. Avatar Video — **only after all 4 steps above work stably**

Use mocks for expensive components (TTS, video) during development until full integration.

## Cost Optimization (bonus +10 pts — built into phases, NOT a separate task)

These are not a separate phase. They must be implemented inline at the relevant stages:

- **Phase 2 (MCP Servers):** Cache all scraping results to JSON files with a 24h TTL. Never re-scrape the same query within the TTL window.
- **Phase 3 + 4 (LLM + ASR):** Model routing — use `gpt-4o-mini` (`LLM_MODEL`) for LLM (text + vision + tool calling), use `gpt-5.4-mini` (`ASR_MODEL`) for ASR (better transcription quality). Different models for different pipeline stages = demonstrable routing. Always pass `detail: "low"` in `image_url` content blocks to minimize vision token cost.
- **Phase 3 (LLM Agent):** Cap response length via system prompt (`MAX_RESPONSE_CHARS=500`) to keep TTS and video generation short and cheap.
- **Phase 5 (TTS):** Keep text under 500 chars (~15-30s speech) to minimize per-character TTS cost.

## Code Quality

- No hardcoded answers — LLM must actually call MCP tools and receive data.
- Add reasonable delays between web scraping requests (2GIS/Chocolife may block).
- Cache scraping results to reduce API calls.

## README Requirements

README.md must include all of the following sections:
1. Project description (2-3 sentences)
2. Architecture diagram (pipeline schema)
3. Which models were used and why
4. Step-by-step launch instructions (install deps, configure .env, start MCP servers, start app)
5. Screenshots / GIFs of working interface
6. Cost breakdown (how much spent on APIs)
7. What would be improved with more time
