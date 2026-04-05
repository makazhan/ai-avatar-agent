"""One-time voice cloning script.

Usage:
    FAL_KEY=... uv run python voice/clone.py

Uploads voice/my_voice_sample.wav to fal.ai, clones the voice,
and prints the VOICE_ID to add to .env.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fal_client
from config import VOICE_SAMPLE_PATH


def clone_voice(audio_path: str) -> str:
    print(f"Uploading {audio_path}...")
    audio_url = fal_client.upload_file(audio_path)
    print(f"Uploaded: {audio_url}")

    print("Cloning voice...")
    result = fal_client.subscribe("fal-ai/minimax/voice-clone", arguments={
        "audio_url": audio_url,
        "preview_text": "Привет! Я ваш персональный ресторанный гид по Алматы.",
        "language": "Russian",
    })
    print(f"API response: {result}")
    voice_id = result.get("custom_voice_id") or result.get("voice_id")
    if not voice_id:
        print(f"Error: could not find voice_id in response")
        sys.exit(1)
    print(f"\nDone! Add to .env:\nVOICE_ID={voice_id}")
    return voice_id


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else VOICE_SAMPLE_PATH
    if not os.path.exists(path):
        print(f"Error: audio file not found: {path}")
        sys.exit(1)
    clone_voice(path)
