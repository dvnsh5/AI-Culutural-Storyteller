"""
Gemini Service for KathaChitra

- Uses a verified Gemini model available to the API key
- Safely extracts JSON from Gemini responses
- Handles non-JSON / verbose outputs gracefully
"""

import json
import re
import google.generativeai as genai
from config import config

# Configure Gemini with API key
genai.configure(api_key=config.GEMINI_API_KEY)


class GeminiService:
    def __init__(self):
        # ✅ VERIFIED from your ListModels output
        self.model = genai.GenerativeModel("models/gemini-flash-latest")

    def _extract_json(self, text: str) -> dict:
        """
        Safely extract a JSON object from Gemini output.
        Handles extra text, markdown, or explanations.
        """
        if not text:
            raise ValueError("Empty response from Gemini")

        # Find first JSON object in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError(f"No JSON found in Gemini output:\n{text}")

        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON extracted: {e}")

    async def generate_story(self, culture: str, language: str, theme: str) -> dict:
        """
        Generate a culturally grounded story and image prompts.
        Returns a dictionary with:
        - title
        - story_text
        - moral
        - story_image_prompt
        - video_image_prompt
        """

        prompt = f"""
Create a culturally authentic {theme} story.

Rules:
- Culture: {culture}
- Language: {language}
- Length: 400–600 words
- Include a moral
- Image prompts must be under 40 words
- DO NOT include markdown
- DO NOT include explanations
- OUTPUT ONLY VALID JSON

JSON format:
{{
  "title": "Story title",
  "story_text": "Full story text",
  "moral": "Moral of the story",
  "story_image_prompt": "Visual description for main story image",
  "video_image_prompt": "Visual description for background video image"
}}
"""

        response = self.model.generate_content(prompt)

        # ✅ Correct way to read Gemini output
        try:
            raw_text = response.candidates[0].content.parts[0].text.strip()
        except (IndexError, AttributeError) as e:
            raise ValueError(f"Unexpected Gemini response structure: {e}")

        data = self._extract_json(raw_text)

        # ✅ Validate required keys
        required_keys = [
            "title",
            "story_text",
            "story_image_prompt",
            "video_image_prompt",
        ]

        for key in required_keys:
            if key not in data or not data[key]:
                raise ValueError(f"Missing required field in Gemini output: {key}")

        return data

    def is_configured(self) -> bool:
        """Check if Gemini API key is available."""
        return bool(config.GEMINI_API_KEY)


# Singleton instance
gemini_service = GeminiService()
