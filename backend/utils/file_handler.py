"""
KathaChitra Temporary File Handler

Manages temporary files for stateless operation.
All files are automatically cleaned up after use.
"""

import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager

from config import config


class TempFileHandler:
    """
    Handles temporary file creation and cleanup.
    Ensures stateless operation by removing all files after use.
    """
    
    def __init__(self):
        """Initialize temp file handler with base directory."""
        self.base_dir = Path(config.TEMP_DIR)
        self._ensure_base_dir()
    
    def _ensure_base_dir(self):
        """Create base temp directory if it doesn't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session_dir(self) -> Path:
        """
        Create a unique session directory for a request.
        Returns the path to the session directory.
        """
        session_id = str(uuid.uuid4())
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def get_temp_file_path(self, session_dir: Path, filename: str) -> Path:
        """Get a path for a temporary file within a session directory."""
        return session_dir / filename
    
    def save_temp_file(self, session_dir: Path, filename: str, data: bytes) -> Path:
        """
        Save data to a temporary file.
        Returns the file path.
        """
        file_path = self.get_temp_file_path(session_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(data)
        return file_path
    
    def cleanup_session(self, session_dir: Path):
        """
        Remove a session directory and all its contents.
        Called after request is complete.
        """
        try:
            if session_dir.exists():
                shutil.rmtree(session_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup session directory: {e}")
    
    def cleanup_old_files(self, max_age_seconds: int = None):
        """
        Remove old temporary files that exceed max age.
        Safety mechanism for orphaned files.
        """
        if max_age_seconds is None:
            max_age_seconds = config.MAX_TEMP_FILE_AGE
        
        current_time = time.time()
        
        try:
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    # Check directory age by modification time
                    mtime = item.stat().st_mtime
                    if current_time - mtime > max_age_seconds:
                        shutil.rmtree(item)
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")
    
    @contextmanager
    def session(self):
        """
        Context manager for automatic session cleanup.
        
        Usage:
            with file_handler.session() as session_dir:
                # Use session_dir for temp files
                # Automatically cleaned up after
        """
        session_dir = self.create_session_dir()
        try:
            yield session_dir
        finally:
            self.cleanup_session(session_dir)


def cleanup_temp_files():
    """
    Global cleanup function.
    Called periodically to remove orphaned temp files.
    """
    handler = TempFileHandler()
    handler.cleanup_old_files()


# Singleton instance
temp_file_handler = TempFileHandler()
