import os
from dotenv import load_dotenv

load_dotenv()

# Mode flags — USE_MOCKS controls all components globally;
# per-component overrides allow testing expensive parts separately.
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
MOCK_TTS = os.getenv("MOCK_TTS", str(USE_MOCKS)).lower() == "true"
MOCK_VIDEO = os.getenv("MOCK_VIDEO", str(USE_MOCKS)).lower() == "true"
MOCK_ASR = os.getenv("MOCK_ASR", str(USE_MOCKS)).lower() == "true"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

# LLM settings
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
ASR_MODEL = os.getenv("ASR_MODEL", "gpt-4o-mini-transcribe")
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
