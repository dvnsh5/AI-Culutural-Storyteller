"""
KathaChitra Configuration Module

Handles environment variables and application settings.
Uses Gemini as the AI backend.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """Application configuration loaded from environment variables."""

    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")

    # Server Settings
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8000'))
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'

    # Temporary File Settings
    TEMP_DIR: str = '/tmp/kathachitra'
    MAX_TEMP_FILE_AGE: int = 300  # 5 minutes

    # Image / Video Settings
    IMAGE_WIDTH: int = 1024
    IMAGE_HEIGHT: int = 576  # 16:9 aspect ratio

    # Supported Cultures and Languages
    SUPPORTED_CULTURES: list = [
        'Bengali', 'Hindi', 'Tamil', 'Japanese', 'Chinese',
        'Korean', 'African', 'Norse', 'Greek', 'Egyptian',
        'Celtic', 'Native American', 'Mayan', 'Persian', 'Arabic',
        'Russian', 'Irish', 'Scottish', 'Vietnamese', 'Thai'
    ]

    SUPPORTED_LANGUAGES: list = [
        'English', 'Hindi', 'Bengali', 'Tamil', 'Telugu', 'Kannada', 'Punjabi',
        'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Dutch', 'Russian'
    ]

    STORY_THEMES: list = [
        'myth', 'folklore', 'legend', 'moral tale',
        'creation story', 'hero journey', 'love story',
        'wisdom tale', 'trickster tale', 'nature spirit'
    ]

    @classmethod
    def validate(cls) -> dict:
        """Validate configuration and return status."""
        issues = []

        if not cls.GEMINI_API_KEY:
            issues.append('GEMINI_API_KEY not set')
        if not cls.HF_API_KEY:
            issues.append("HF_API_KEY not set")


        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'gemini_configured': bool(cls.GEMINI_API_KEY)
        }


# Singleton config instance
config = Config()
