"""
KathaChitra Audio Service

Handles text-to-speech narration generation.
Supports multiple TTS engines with language fallbacks.
Generates emotional, expressive narration for story videos.
"""

import asyncio
from pathlib import Path
from typing import Optional, List

from config import config


class AudioService:
    """
    Audio narration engine for story videos.
    Uses edge-tts or gTTS for multilingual support with emotional expression.
    """
    
    # Language code mapping for TTS engines
    LANGUAGE_CODES = {
        # Indian languages
        'english': 'en',
        'hindi': 'hi',
        'bengali': 'bn',
        'tamil': 'ta',
        'telugu': 'te',
        'kannada': 'kn',
        'punjabi': 'pa',
        # European languages
        'spanish': 'es',
        'french': 'fr',
        'german': 'de',
        'italian': 'it',
        'portuguese': 'pt',
        'dutch': 'nl',
        'russian': 'ru'
    }
    
    # Edge TTS voice mapping for emotional narration
    # Using expressive neural voices where available
    EDGE_TTS_VOICES = {
        # Indian languages
        'en': 'en-IN-NeerjaNeural',      # Indian English, warm
        'hi': 'hi-IN-SwaraNeural',        # Expressive Hindi
        'bn': 'bn-IN-TanishaaNeural',     # Natural Bengali
        'ta': 'ta-IN-PallaviNeural',      # Natural Tamil
        'te': 'te-IN-ShrutiNeural',       # Natural Telugu
        'kn': 'kn-IN-SapnaNeural',        # Natural Kannada
        'pa': 'pa-IN-OjasNeural',         # Natural Punjabi (male voice available)
        # European languages
        'es': 'es-ES-ElviraNeural',       # Warm Spanish
        'fr': 'fr-FR-DeniseNeural',       # Expressive French
        'de': 'de-DE-KatjaNeural',        # Clear German
        'it': 'it-IT-ElsaNeural',         # Natural Italian
        'pt': 'pt-BR-FranciscaNeural',    # Warm Portuguese
        'nl': 'nl-NL-ColetteNeural',      # Clear Dutch
        'ru': 'ru-RU-SvetlanaNeural'      # Expressive Russian
    }
    
    def __init__(self):
        """Initialize audio service."""
        self.use_edge_tts = self._check_edge_tts()
        self.use_gtts = self._check_gtts()
    
    def _check_edge_tts(self) -> bool:
        """Check if edge-tts is available."""
        try:
            import edge_tts
            return True
        except ImportError:
            return False
    
    def _check_gtts(self) -> bool:
        """Check if gTTS is available."""
        try:
            from gtts import gTTS
            return True
        except ImportError:
            return False
    
    def _get_language_code(self, language: str) -> str:
        """Convert language name to TTS language code."""
        return self.LANGUAGE_CODES.get(language.lower(), 'en')
    
    def _get_edge_voice(self, lang_code: str) -> str:
        """Get edge-tts voice for language."""
        return self.EDGE_TTS_VOICES.get(lang_code, 'en-US-AriaNeural')
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text for TTS to avoid encoding issues.
        Removes problematic Unicode characters that cause latin-1 errors.
        """
        import re
        
        # Replace common problematic characters
        replacements = {
            '\u2018': "'",    # Left single quote
            '\u2019': "'",    # Right single quote
            '\u201c': '"',    # Left double quote
            '\u201d': '"',    # Right double quote
            '\u2013': '-',    # En dash
            '\u2014': '-',    # Em dash
            '\u2026': '...',  # Ellipsis
            '\u00a0': ' ',    # Non-breaking space
            '\u00ad': '',     # Soft hyphen
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove any remaining non-ASCII characters for problematic languages
        # Keep letters and basic punctuation
        text = re.sub(r'[^\x00-\x7F]+', lambda m: m.group().encode('utf-8', errors='ignore').decode('utf-8', errors='ignore') if any(ord(c) > 127 for c in m.group()) else m.group(), text)
        
        return text
    
    async def generate_full_narration(
        self,
        story_text: str,
        language: str,
        session_dir: Path,
        voice_style: str = 'storyteller'
    ) -> Optional[Path]:
        """
        Generate a complete audio narration for the entire story.
        
        Args:
            story_text: Complete story text to narrate
            language: Language for narration
            session_dir: Directory to save audio file
            voice_style: Voice style (friendly, professional, storyteller, gentle, energetic)
            
        Returns:
            Path to generated audio file or None on failure
        """
        output_path = session_dir / "story_narration.mp3"
        
        # Try edge-tts first (better quality and expression)
        if self.use_edge_tts:
            success = await self._generate_audio_edge_tts(
                story_text, language, output_path, voice_style
            )
            if success:
                return output_path
        
        # Fallback to gTTS (does not support voice styles)
        if self.use_gtts:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._generate_audio_gtts,
                story_text,
                language,
                output_path
            )
            if success:
                return output_path
        
        print("No TTS engine available")
        return None
    
    async def _generate_audio_edge_tts(
        self,
        text: str,
        language: str,
        output_path: Path,
        voice_style: str = 'storyteller'
    ) -> bool:
        """
        Generate audio using edge-tts (Microsoft neural voices).
        These voices have better emotional expression.
        """
        try:
            import edge_tts
            
            lang_code = self._get_language_code(language)
            voice = self._get_edge_voice(lang_code)
            
            # Voice style adjustments (rate and pitch)
            # Styles: friendly, professional, storyteller, gentle, energetic
            style_settings = {
                'friendly': {'rate': '+5%', 'pitch': '+5Hz'},
                'professional': {'rate': '-5%', 'pitch': '-3Hz'},
                'storyteller': {'rate': '-10%', 'pitch': '+0Hz'},  # Slower, natural
                'gentle': {'rate': '-15%', 'pitch': '-5Hz'},  # Calm and slow
                'energetic': {'rate': '+15%', 'pitch': '+8Hz'}  # Fast and excited
            }
            
            settings = style_settings.get(voice_style, style_settings['storyteller'])
            
            print(f"Generating narration with {voice} (style={voice_style})...")
            
            # Sanitize text to avoid encoding issues
            sanitized_text = self._sanitize_text(text)
            
            # Create communication object with the voice and style
            communicate = edge_tts.Communicate(
                sanitized_text,
                voice,
                rate=settings['rate'],
                pitch=settings['pitch']
            )
            
            # Save the audio
            await communicate.save(str(output_path))
            
            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"Narration saved: {output_path.stat().st_size} bytes")
                return True
            return False
            
        except Exception as e:
            print(f"Edge TTS failed: {e}")
            return False
    
    def _generate_audio_gtts(
        self,
        text: str,
        language: str,
        output_path: Path
    ) -> bool:
        """
        Generate audio using gTTS (Google TTS).
        Fallback option with good language support.
        """
        try:
            from gtts import gTTS
            
            lang_code = self._get_language_code(language)
            
            # gTTS uses slightly different codes for some languages
            gtts_lang = lang_code
            if lang_code == 'zh-CN':
                gtts_lang = 'zh-cn'
            
            print(f"Generating narration with gTTS ({gtts_lang})...")
            
            # Sanitize text to avoid encoding issues
            sanitized_text = self._sanitize_text(text)
            
            tts = gTTS(text=sanitized_text, lang=gtts_lang, slow=False)
            tts.save(str(output_path))
            
            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"Narration saved: {output_path.stat().st_size} bytes")
                return True
            return False
            
        except Exception as e:
            print(f"gTTS failed: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if any TTS engine is available."""
        return self.use_edge_tts or self.use_gtts
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.LANGUAGE_CODES.keys())


# Singleton instance
audio_service = AudioService()
