"""
KathaChitra Services Package

Contains all AI service integrations:
- Groq: Text generation and story creation
- Image: Pollinations.ai image generation
- Audio: Text-to-speech narration (edge-tts/gTTS)
- Video: FFmpeg video composition
"""

from .gemini_service import GeminiService, gemini_service

from .audio_service import AudioService, audio_service
from .video_service import VideoService, video_service

__all__ = [
    "GeminiService", "gemini_service",
    "AudioService", "audio_service",
    "VideoService", "video_service"
]
