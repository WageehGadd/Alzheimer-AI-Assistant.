import os


APP_NAME: str = os.getenv("APP_NAME", "Alzheimer Assistant Backend")
APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")

# Voice/TTS Configuration
TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge")  # Options: "edge", "openai", "elevenlabs"
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
OPENAI_TTS_VOICE: str = os.getenv("OPENAI_TTS_VOICE", "shimmer")  # Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
TTS_AUTO_FALLBACK: bool = os.getenv("TTS_AUTO_FALLBACK", "true").lower() == "true"

