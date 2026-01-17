"""
KathaChitra Groq Service

Handles text generation using Groq API with LLaMA/Mixtral models.
- Generate culturally accurate stories with high randomization
- Create simplified image prompts (under 50 words)
- Two image prompts: story illustration + video background
"""

import json
import re
import random
import time
from typing import Dict, Optional
from groq import Groq

from config import config


class GroqService:
    """
    Text and reasoning engine using Groq API.
    Generates varied stories and concise image prompts.
    """
    
    # Random story starters for variety
    STORY_ANGLES = [
        "a young protagonist discovering",
        "an elderly sage teaching",
        "a brave warrior facing",
        "a clever trickster outwitting",
        "a devoted lover seeking",
        "a curious child learning",
        "a humble farmer encountering",
        "a princess challenging",
        "a wandering musician finding",
        "a skilled craftsman creating"
    ]
    
    def __init__(self):
        """Initialize Groq client with API key."""
        self.client = None
        if config.GROQ_API_KEY:
            self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
        self.fallback_model = config.GROQ_FALLBACK_MODEL
    
    def _get_random_seed(self) -> str:
        """Generate a unique seed for story variety."""
        timestamp = int(time.time() * 1000)
        random_part = random.randint(1000, 9999)
        return f"{timestamp}_{random_part}"
    
    def _get_random_angle(self) -> str:
        """Get a random story angle for variety."""
        return random.choice(self.STORY_ANGLES)
    
    async def generate_simple_story(
        self, 
        culture: str, 
        language: str, 
        theme: str
    ) -> Dict:
        """
        Generate a culturally authentic story with two image prompts.
        Uses randomization to ensure variety in outputs.
        
        Returns:
            Dictionary with title, story_text, moral, story_image_prompt, video_image_prompt
        """
        if not self.client:
            raise ValueError("Groq API key not configured")
        
        seed = self._get_random_seed()
        angle = self._get_random_angle()
        
        system_prompt = self._get_story_system_prompt(culture, language)
        user_prompt = self._get_story_user_prompt(culture, language, theme, seed, angle)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.9,  # Higher for more variety
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            story_data = json.loads(content)
            
            story_text = story_data.get("story_text", "")
            if len(story_text) < 100:
                raise ValueError("Story text too short")
            
            return {
                "title": story_data.get("title", "Untitled Story"),
                "story_text": story_text,
                "moral": story_data.get("moral"),
                "story_image_prompt": story_data.get("story_image_prompt", ""),
                "video_image_prompt": story_data.get("video_image_prompt", "")
            }
            
        except Exception as e:
            print(f"Primary generation failed: {e}, trying fallback...")
            return await self._generate_story_fallback(culture, language, theme)
    
    async def _generate_story_fallback(
        self,
        culture: str,
        language: str,
        theme: str
    ) -> Dict:
        """Fallback story generation with simpler prompt."""
        if not self.client:
            raise ValueError("Groq API key not configured")
        
        seed = self._get_random_seed()
        
        prompt = f"""Generate a unique {theme} story from {culture} culture in {language}.
Story seed: {seed}

OUTPUT (JSON only):
{{
    "title": "Title in {language}",
    "story_text": "Story in {language}, 400-600 words",
    "moral": "Moral in {language}",
    "story_image_prompt": "Under 50 words: main character, action, {culture} setting",
    "video_image_prompt": "Under 50 words: atmospheric {culture} landscape, no characters"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.fallback_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                story_data = json.loads(json_match.group())
                return {
                    "title": story_data.get("title", "Untitled Story"),
                    "story_text": story_data.get("story_text", ""),
                    "moral": story_data.get("moral"),
                    "story_image_prompt": story_data.get("story_image_prompt", ""),
                    "video_image_prompt": story_data.get("video_image_prompt", "")
                }
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
        
        raise Exception("Story generation failed")
    
    def _get_story_system_prompt(self, culture: str, language: str) -> str:
        """System prompt focusing on variety and cultural authenticity."""
        
        lang_note = ""
        if language.lower() != 'english':
            lang_note = f"Write title, story_text, and moral in proper {language}."
        
        return f"""You are a creative storyteller specializing in {culture} traditions.

RULES:
- Create UNIQUE stories each time (never repeat plots)
- Use authentic {culture} names, settings, and customs
- {lang_note}
- Image prompts must be in English, under 50 words each
- Image prompts should be simple and focused"""
    
    def _get_story_user_prompt(
        self, culture: str, language: str, theme: str, seed: str, angle: str
    ) -> str:
        """User prompt with randomization elements."""
        
        return f"""Create a {theme} story from {culture} culture.

UNIQUE STORY SEED: {seed}
STORY ANGLE: Focus on {angle}

OUTPUT FORMAT (JSON only):
{{
    "title": "Creative title in {language}",
    "story_text": "Complete story in {language} (400-600 words)",
    "moral": "Lesson in {language}",
    "story_image_prompt": "Simple prompt under 50 words: main character with key action in {culture} setting, digital art",
    "video_image_prompt": "Simple prompt under 50 words: scenic {culture} landscape or temple, atmospheric, no people"
}}

IMPORTANT:
- story_image_prompt: Show the protagonist in a key story moment
- video_image_prompt: Atmospheric background scene (no characters)
- Both prompts in English, simple and focused"""
    
    async def generate_image_prompt_from_story(
        self,
        story_text: str,
        culture: str
    ) -> str:
        """Generate a simple image prompt from story text."""
        if not self.client:
            return f"{culture} cultural scene, traditional art"
        
        prompt = f"""Create a simple image prompt (under 50 words) for this story.
Focus on: main character, key action, {culture} setting.

Story excerpt: {story_text[:800]}

OUTPUT (JSON):
{{"image_prompt": "your prompt here"}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            return data.get("image_prompt", f"{culture} cultural illustration")
            
        except Exception:
            return f"{culture} cultural scene, traditional style"
    
    def is_configured(self) -> bool:
        """Check if Groq service is properly configured."""
        return self.client is not None


# Singleton instance
groq_service = GroqService()
