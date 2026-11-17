"""Locate an actual FFmpeg binary; never download tools during preflight."""
import os,shutil
from pathlib import Path

def ffmpeg_command():
    configured=os.getenv('STUDIO_FFMPEG')
    if configured:return shutil.which(configured)
    system=shutil.which('ffmpeg')
    if system:return system
    try:
        import imageio_ffmpeg
        candidate=imageio_ffmpeg.get_ffmpeg_exe()
        if Path(candidate).is_file() and os.access(candidate,os.X_OK):return candidate
    except (ImportError,RuntimeError):pass
    # Existing repo-local dependency installation used by prior actual renders.
    root=Path(__file__).resolve().parents[1]
    for candidate in sorted((root/'.local-motion/imageio_ffmpeg/binaries').glob('ffmpeg-*')):
        if candidate.is_file() and os.access(candidate,os.X_OK):return str(candidate)
    return None
