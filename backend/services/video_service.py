"""
KathaChitra Video Service

Handles video generation using FFmpeg.
Creates story videos with:
- Image background (with optional Ken Burns effect)
- Emotional audio narration
- Optional caption overlay
- Downloadable MP4 format
"""

import asyncio
import base64
import subprocess
import textwrap
from pathlib import Path
from typing import Optional
from io import BytesIO

from config import config


class VideoService:
    """
    Video composition engine.
    Creates narrated story videos with optional captions.
    """
    
    def __init__(self):
        """Initialize video service."""
        self.fps = 24
        self.video_size = (config.IMAGE_WIDTH, config.IMAGE_HEIGHT)
    
    async def create_story_video(
        self,
        image_base64: str,
        audio_path: Optional[Path],
        story_text: str,
        title: str,
        session_dir: Path,
        enable_captions: bool = False
    ) -> Optional[Path]:
        """
        Create a story video with image, audio, and optional captions.
        
        Args:
            image_base64: Base64 encoded background image
            audio_path: Path to narration audio file
            story_text: Story text for captions
            title: Story title
            session_dir: Directory for temporary files
            enable_captions: Whether to overlay caption text
            
        Returns:
            Path to generated video file or None
        """
        try:
            # Save image to file
            image_path = session_dir / "story_image.png"
            self._save_base64_image(image_base64, image_path)
            
            if not image_path.exists():
                print("Failed to save story image")
                return None
            
            # Determine video duration from audio
            if audio_path and audio_path.exists():
                duration = await self._get_audio_duration(audio_path)
                if duration is None or duration < 5:
                    duration = 30
                duration += 2  # Padding
            else:
                duration = 30
            
            print(f"Creating video: {duration:.1f}s, captions={enable_captions}")
            
            # Create subtitle file if captions enabled
            subtitle_path = None
            if enable_captions and story_text:
                subtitle_path = await self._create_subtitle_file(
                    story_text, duration, session_dir
                )
            
            # Create video
            output_path = session_dir / "story_video.mp4"
            
            success = await self._create_video_ffmpeg(
                image_path=image_path,
                audio_path=audio_path,
                subtitle_path=subtitle_path,
                output_path=output_path,
                duration=duration
            )
            
            if success and output_path.exists():
                print(f"Video created: {output_path.stat().st_size} bytes")
                return output_path
            
            return None
            
        except Exception as e:
            print(f"Video creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _create_subtitle_file(
        self,
        story_text: str,
        duration: float,
        session_dir: Path
    ) -> Optional[Path]:
        """Create an SRT subtitle file from story text with better timing."""
        try:
            subtitle_path = session_dir / "captions.srt"
            
            # Split text into sentences first for natural pausing
            import re
            sentences = re.split(r'(?<=[.!?])\s+', story_text)
            
            # Create caption segments (aim for ~6-8 words per caption for readability)
            segments = []
            for sentence in sentences:
                words = sentence.split()
                # Break long sentences into smaller chunks
                for i in range(0, len(words), 8):
                    chunk_words = words[i:i + 8]
                    if chunk_words:
                        segments.append(" ".join(chunk_words))
            
            if len(segments) == 0:
                return None
            
            # Calculate timing based on reading speed (~150 words per minute)
            # This makes captions sync better with narration
            total_words = len(story_text.split())
            words_per_second = 2.5  # ~150 words per minute = 2.5 words/sec
            
            # Calculate time per segment based on word count
            segment_times = []
            current_time = 0.5  # Small delay at start
            
            for segment in segments:
                word_count = len(segment.split())
                # Duration based on word count, minimum 1.5 seconds
                segment_duration = max(word_count / words_per_second, 1.5)
                segment_times.append((current_time, current_time + segment_duration))
                current_time += segment_duration + 0.2  # Small gap between segments
            
            # Scale timing to fit within video duration if needed
            if segment_times and segment_times[-1][1] > duration - 1:
                scale = (duration - 1) / segment_times[-1][1]
                segment_times = [(s * scale, e * scale) for s, e in segment_times]
            
            # Write SRT file
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                for i, (segment, (start_time, end_time)) in enumerate(zip(segments, segment_times)):
                    start_str = self._format_srt_time(start_time)
                    end_str = self._format_srt_time(end_time)
                    
                    # Wrap long lines
                    wrapped = textwrap.fill(segment, width=45)
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{wrapped}\n\n")
            
            print(f"Created subtitles: {len(segments)} segments, synced to {duration:.1f}s")
            return subtitle_path
            
        except Exception as e:
            print(f"Subtitle creation failed: {e}")
            return None
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _save_base64_image(self, image_base64: str, output_path: Path) -> bool:
        """Save base64 image to file."""
        try:
            from PIL import Image
            
            image_data = base64.b64decode(image_base64)
            img = Image.open(BytesIO(image_data))
            
            if img.size != self.video_size:
                img = img.resize(self.video_size, Image.Resampling.LANCZOS)
            
            img.save(str(output_path), 'PNG')
            return True
            
        except Exception as e:
            print(f"Failed to save image: {e}")
            return False
    
    async def _get_audio_duration(self, audio_path: Path) -> Optional[float]:
        """Get duration of audio file in seconds."""
        try:
            import imageio_ffmpeg
            
            ffprobe_exe = imageio_ffmpeg.get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
            
            cmd = [
                ffprobe_exe,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_path)
            ]
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True)
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
                
        except Exception as e:
            print(f"Could not get audio duration: {e}")
        
        # Fallback: estimate from file size
        try:
            size = audio_path.stat().st_size
            return size / 16000
        except:
            pass
        
        return None
    
    async def _create_video_ffmpeg(
        self,
        image_path: Path,
        audio_path: Optional[Path],
        subtitle_path: Optional[Path],
        output_path: Path,
        duration: float
    ) -> bool:
        """Create video using FFmpeg with optional captions."""
        try:
            import imageio_ffmpeg
            
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # Build filter chain
            filters = []
            
            # Scale and pad for consistent size
            filters.append(f"scale={self.video_size[0]}:{self.video_size[1]}:force_original_aspect_ratio=decrease")
            filters.append(f"pad={self.video_size[0]}:{self.video_size[1]}:(ow-iw)/2:(oh-ih)/2")
            
            # Subtle zoom effect
            filters.append(f"zoompan=z='min(zoom+0.0003,1.08)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.video_size[0]}x{self.video_size[1]}:fps={self.fps}")
            
            # Add captions if subtitle file exists
            if subtitle_path and subtitle_path.exists():
                # Escape path for FFmpeg
                sub_path_escaped = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
                filters.append(f"subtitles='{sub_path_escaped}':force_style='FontSize=22,FontName=DejaVu Sans,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Shadow=1,MarginV=40'")
            
            filter_chain = ",".join(filters)
            
            # Build command
            if audio_path and audio_path.exists():
                cmd = [
                    ffmpeg_exe,
                    '-y',
                    '-loop', '1',
                    '-i', str(image_path),
                    '-i', str(audio_path),
                    '-c:v', 'libx264',
                    '-tune', 'stillimage',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-pix_fmt', 'yuv420p',
                    '-vf', filter_chain,
                    '-shortest',
                    '-movflags', '+faststart',
                    str(output_path)
                ]
            else:
                cmd = [
                    ffmpeg_exe,
                    '-y',
                    '-loop', '1',
                    '-i', str(image_path),
                    '-c:v', 'libx264',
                    '-tune', 'stillimage',
                    '-pix_fmt', 'yuv420p',
                    '-t', str(duration),
                    '-vf', filter_chain,
                    '-movflags', '+faststart',
                    str(output_path)
                ]
            
            print(f"Running FFmpeg (captions={subtitle_path is not None})...")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            )
            
            if result.returncode == 0 and output_path.exists():
                return True
            else:
                print(f"FFmpeg error: {result.stderr[:500] if result.stderr else 'Unknown'}")
                # Try without captions if that was the issue
                if subtitle_path:
                    print("Retrying without captions...")
                    return await self._create_video_ffmpeg(
                        image_path, audio_path, None, output_path, duration
                    )
                return await self._create_simple_video(
                    image_path, audio_path, output_path, duration
                )
                
        except Exception as e:
            print(f"FFmpeg video creation failed: {e}")
            return False
    
    async def _create_simple_video(
        self,
        image_path: Path,
        audio_path: Optional[Path],
        output_path: Path,
        duration: float
    ) -> bool:
        """Create simple video without effects (fallback)."""
        try:
            import imageio_ffmpeg
            
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            if audio_path and audio_path.exists():
                cmd = [
                    ffmpeg_exe,
                    '-y',
                    '-loop', '1',
                    '-i', str(image_path),
                    '-i', str(audio_path),
                    '-c:v', 'libx264',
                    '-tune', 'stillimage',
                    '-c:a', 'aac',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',
                    '-movflags', '+faststart',
                    str(output_path)
                ]
            else:
                cmd = [
                    ffmpeg_exe,
                    '-y',
                    '-loop', '1',
                    '-i', str(image_path),
                    '-c:v', 'libx264',
                    '-tune', 'stillimage',
                    '-pix_fmt', 'yuv420p',
                    '-t', str(duration),
                    '-movflags', '+faststart',
                    str(output_path)
                ]
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            )
            
            return result.returncode == 0 and output_path.exists()
                
        except Exception as e:
            print(f"Simple video creation failed: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if video generation is available."""
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe() is not None
        except ImportError:
            return False


# Singleton instance
video_service = VideoService()
