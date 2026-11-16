"""Locate a real FFmpeg binary; never download tools during preflight.

Isolated from the three-channel system: this package reads `ACCOUNTS_FFMPEG`,
never `STUDIO_FFMPEG`.
"""
import os
import shutil
from pathlib import Path


def ffmpeg_command():
    """Return an executable FFmpeg path, or None. Never raises."""
    configured = os.getenv('ACCOUNTS_FFMPEG')
    if configured:
        found = shutil.which(configured)
        if found:
            return found
        # An operator may point straight at a binary rather than a PATH name.
        if Path(configured).is_file() and os.access(configured, os.X_OK):
            return configured
    system = shutil.which('ffmpeg')
    if system:
        return system
    try:
        import imageio_ffmpeg
        candidate = imageio_ffmpeg.get_ffmpeg_exe()
        if Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    except (ImportError, RuntimeError):
        pass
    # Virtual-env style installs used by earlier actual renders in this repo.
    root = Path(__file__).resolve().parents[1]
    for pattern in ('.local-motion/imageio_ffmpeg/binaries/ffmpeg-*',
                    '.venv/lib/*/site-packages/imageio_ffmpeg/binaries/ffmpeg-*'):
        for candidate in sorted(root.glob(pattern)):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return None
