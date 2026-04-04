import os
from dotenv import load_dotenv

load_dotenv()

# Mode flags
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")

# LLM settings
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
ASR_MODEL = os.getenv("ASR_MODEL", "gpt-5.4-mini")
VISION_DETAIL = os.getenv("VISION_DETAIL", "low")

# Voice settings
VOICE_ID = os.getenv("VOICE_ID", "")
VOICE_SAMPLE_PATH = os.getenv("VOICE_SAMPLE_PATH", "voice/my_voice_sample.wav")

# Avatar settings
AVATAR_PHOTO_PATH = os.getenv("AVATAR_PHOTO_PATH", "avatar/my_photo.jpg")

# Cache
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

# Response length
MAX_RESPONSE_CHARS = int(os.getenv("MAX_RESPONSE_CHARS", "500"))
