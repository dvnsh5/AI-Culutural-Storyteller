"""
KathaChitra Pydantic Schemas

Defines request and response models for API validation.
These schemas ensure type safety and automatic documentation.

Simplified for the new Groq + Pollinations architecture.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(default="2.0.0", description="API version")
    groq_configured: bool = Field(..., description="Groq API key status")
    pollinations_configured: bool = Field(..., description="Pollinations API key status")
    supported_cultures: List[str] = Field(..., description="Available cultures")
    supported_languages: List[str] = Field(..., description="Available languages")
    story_themes: List[str] = Field(..., description="Available themes")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional details")


# Legacy models kept for backwards compatibility
# These are no longer used in the main API but may be imported elsewhere

class ImagePrompt(BaseModel):
    """Structured image prompt (legacy, kept for compatibility)."""
    scene_number: int = Field(default=1, description="Scene number")
    scene_text: str = Field(default="", description="Scene description")
    subject: str = Field(default="", description="Main subject")
    environment: str = Field(default="", description="Setting")
    clothing: str = Field(default="", description="Clothing details")
    cultural_details: str = Field(default="", description="Cultural elements")
    art_style: str = Field(default="", description="Art style")
    lighting_mood: str = Field(default="", description="Mood")
    
    def to_prompt_string(self) -> str:
        """Convert to text prompt."""
        return f"{self.subject}, {self.environment}, {self.clothing}, {self.cultural_details}"


class StoryRequest(BaseModel):
    """Request model for story generation (legacy)."""
    culture: str = Field(..., description="Cultural region")
    language: str = Field(..., description="Output language")
    theme: str = Field(..., description="Story theme")


class StoryResponse(BaseModel):
    """Response model for generated story (legacy)."""
    title: str = Field(..., description="Story title")
    culture: str = Field(..., description="Cultural context")
    language: str = Field(..., description="Language")
    story_text: str = Field(..., description="Complete story")
    scenes: List[str] = Field(default=[], description="Scene descriptions")
    image_prompts: List[ImagePrompt] = Field(default=[], description="Image prompts")
    moral: Optional[str] = Field(None, description="Moral of the story")


class ImageRequest(BaseModel):
    """Request model for image generation (legacy)."""
    prompts: List[ImagePrompt] = Field(..., description="Image prompts")


class ImageResponse(BaseModel):
    """Response model for generated images (legacy)."""
    images: List[str] = Field(..., description="Base64 encoded images")
    scene_numbers: List[int] = Field(default=[], description="Scene numbers")


class VideoRequest(BaseModel):
    """Request model for video generation (legacy)."""
    story: StoryResponse = Field(..., description="Story data")


class VideoResponse(BaseModel):
    """Response model for video generation (legacy)."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Status message")
    duration: Optional[float] = Field(None, description="Video duration")
