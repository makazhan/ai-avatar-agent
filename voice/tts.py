import asyncio

import fal_client

from config import VOICE_ID, MOCK_TTS


async def generate_speech(text: str) -> str:
    """Generate speech from text using cloned voice. Returns audio URL."""
    if MOCK_TTS:
        return "https://example.com/mock_audio.mp3"

    args = {"text": text, "language_boost": "Russian"}
    if VOICE_ID:
        args["voice_setting"] = {"voice_id": VOICE_ID}
    result = await asyncio.to_thread(
        lambda: fal_client.subscribe("fal-ai/minimax/speech-02-hd", arguments=args)
    )
    return result["audio"]["url"]
