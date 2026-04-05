import base64
import mimetypes

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, ASR_MODEL, MOCK_ASR

_asr_client: AsyncOpenAI | None = None


def _get_asr_client() -> AsyncOpenAI:
    global _asr_client
    if _asr_client is None:
        _asr_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _asr_client
from agent.tools import MCPToolManager
from agent.llm import RestaurantAgent
from voice.tts import generate_speech
from avatar.generate import generate_avatar_video


async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file to text via OpenAI Whisper."""
    if MOCK_ASR:
        return "Где лучшие рестораны в центре Алматы?"

    client = _get_asr_client()
    with open(audio_path, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model=ASR_MODEL, file=f, language="ru"
        )
    return transcript.text


def _encode_image_to_data_url(path: str) -> str:
    """Convert local image file to base64 data URL for OpenAI vision."""
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


class Pipeline:
    def __init__(self):
        self.tool_manager = MCPToolManager()
        self.agent: RestaurantAgent | None = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        await self.tool_manager.connect_server(
            "twogis", "uv", ["run", "python", "mcp_servers/twogis/server.py"]
        )
        await self.tool_manager.connect_server(
            "chocolife", "uv", ["run", "python", "mcp_servers/chocolife/server.py"]
        )
        await self.tool_manager.connect_server(
            "abr_group", "uv", ["run", "python", "mcp_servers/abr_group/server.py"]
        )
        self.agent = RestaurantAgent(self.tool_manager)
        self._initialized = True

    async def process(
        self,
        text: str | None = None,
        image_path: str | None = None,
        audio_path: str | None = None,
    ) -> tuple[str, str | None, str | None]:
        """Full pipeline: ASR -> LLM -> TTS -> Avatar. Returns (text_response, video_url, asr_text)."""
        await self.initialize()

        asr_text = None
        if audio_path and not text:
            asr_text = await transcribe_audio(audio_path)
            text = asr_text

        image_url = _encode_image_to_data_url(image_path) if image_path else None
        response_text = await self.agent.chat(text or "", image_url=image_url)

        audio_url = await generate_speech(response_text)
        video_url = await generate_avatar_video(audio_url)

        return response_text, video_url, asr_text
