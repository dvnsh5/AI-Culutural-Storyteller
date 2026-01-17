"""
KathaChitra - Cultural Storytelling Platform

Main FastAPI application.
Uses Gemini for story generation.
Audio (TTS) and Video (FFmpeg) services remain unchanged.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from config import config
from services.gemini_service import gemini_service
from services.audio_service import audio_service
from services.video_service import video_service
from utils.file_handler import temp_file_handler, cleanup_temp_files


# ============================================================================
# Request / Response Models
# ============================================================================

class GenerateRequest(BaseModel):
    culture: str = Field(..., description="Cultural region")
    language: str = Field(..., description="Output language")
    theme: str = Field(..., description="Story theme")
    generate_textual: bool = Field(default=True)
    generate_video: bool = Field(default=False)


class GenerateResponse(BaseModel):
    title: str
    culture: str
    language: str
    story_text: str
    moral: Optional[str] = None
    story_image: Optional[str] = None
    video_image: Optional[str] = None


class VideoGenerateRequest(BaseModel):
    title: str
    culture: str
    language: str
    story_text: str
    video_image: Optional[str] = None
    moral: Optional[str] = None
    enable_captions: bool = Field(default=False)
    voice_style: str = Field(default="storyteller")


class HealthResponse(BaseModel):
    status: str
    version: str
    gemini_configured: bool
    supported_cultures: list
    supported_languages: list
    story_themes: list


# ============================================================================
# Lifespan / Cleanup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_temp_files()
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    cleanup_temp_files()


async def periodic_cleanup():
    while True:
        await asyncio.sleep(300)
        cleanup_temp_files()


# ============================================================================
# App Initialization
# ============================================================================

app = FastAPI(
    title="KathaChitra API",
    description="Cultural Storytelling Platform (Gemini-powered)",
    version="2.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    config_status = config.validate()

    return HealthResponse(
        status="healthy" if config_status["valid"] else "degraded",
        version="2.2.0",
        gemini_configured=config_status["gemini_configured"],
        supported_cultures=config.SUPPORTED_CULTURES,
        supported_languages=config.SUPPORTED_LANGUAGES,
        story_themes=config.STORY_THEMES
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):

    print("=== /generate called ===")
    print("Payload:", request)

    if not gemini_service.is_configured():
        print("Gemini NOT configured")
        raise HTTPException(status_code=503, detail="Gemini service not configured")

    print("Gemini configured")

    story_data = await gemini_service.generate_story(
        culture=request.culture,
        language=request.language,
        theme=request.theme
    )

    print("Story generated successfully")
    print("Story keys:", story_data.keys())
    story_image = None
    video_image = None

    

    return GenerateResponse(
        title=story_data["title"],
        culture=request.culture,
        language=request.language,
        story_text=story_data["story_text"],
        moral=story_data.get("moral"),
        story_image=story_image,
        video_image=video_image
    )

    '''except Exception as e:
        print(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail="Story generation failed")
'''

@app.post("/generate-video", tags=["Generation"])
async def generate_video(
    request: VideoGenerateRequest,
    background_tasks: BackgroundTasks
):
    if not request.story_text:
        raise HTTPException(status_code=400, detail="Story text required")


    session_dir = temp_file_handler.create_session_dir()

    try:
        print("Generating narration...")
        audio_path = await audio_service.generate_full_narration(
            story_text=request.story_text,
            language=request.language,
            session_dir=session_dir,
            voice_style=request.voice_style
        )

        print("Creating video...")
        video_path = await video_service.create_story_video(
            image_base64=request.video_image,
            audio_path=audio_path,
            story_text=request.story_text,
            title=request.title,
            session_dir=session_dir,
            enable_captions=request.enable_captions
        )

        if not video_path or not video_path.exists():
            raise HTTPException(status_code=500, detail="Failed to create video")

        def iterfile():
            with open(video_path, "rb") as f:
                yield from f

        background_tasks.add_task(temp_file_handler.cleanup_session, session_dir)

        safe_title = "".join(
            c for c in request.title if c.isascii() and (c.isalnum() or c in " -_")
        )[:50] or "cultural_story"

        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}_story.mp4"'
            }
        )

    except HTTPException:
        temp_file_handler.cleanup_session(session_dir)
        raise
    except Exception as e:
        temp_file_handler.cleanup_session(session_dir)
        print(f"Video error: {e}")
        raise HTTPException(status_code=500, detail="Video generation failed")


@app.get("/cultures", tags=["Configuration"])
async def get_cultures():
    return {"cultures": config.SUPPORTED_CULTURES}


@app.get("/languages", tags=["Configuration"])
async def get_languages():
    return {"languages": config.SUPPORTED_LANGUAGES}


@app.get("/themes", tags=["Configuration"])
async def get_themes():
    return {"themes": config.STORY_THEMES}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": str(exc) if config.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
