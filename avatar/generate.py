import asyncio

import fal_client

from config import AVATAR_PHOTO_PATH, MOCK_VIDEO

_cached_photo_url: str | None = None


async def _get_photo_url() -> str:
    """Upload avatar photo once and cache the URL."""
    global _cached_photo_url
    if _cached_photo_url is None:
        _cached_photo_url = await asyncio.to_thread(
            fal_client.upload_file, AVATAR_PHOTO_PATH
        )
    return _cached_photo_url


async def generate_avatar_video(audio_url: str) -> str:
    """Generate talking-head video from avatar photo + TTS audio. Returns video URL."""
    if MOCK_VIDEO:
        return "https://example.com/mock_video.mp4"

    photo_url = await _get_photo_url()

    result = await asyncio.to_thread(
        lambda: fal_client.subscribe("fal-ai/creatify/aurora", arguments={
            "image_url": photo_url,
            "audio_url": audio_url,
            "prompt": (
                "4K studio interview, medium close-up. "
                "Soft key-light, light-grey backdrop. "
                "Presenter faces lens, steady eye-contact. Ultra-sharp."
            ),
            "guidance_scale": 1,
            "audio_guidance_scale": 2,
            "resolution": "720p",
        })
    )
    return result["video"]["url"]
