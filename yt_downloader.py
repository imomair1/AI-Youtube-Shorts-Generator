"""YouTube Video Downloader Engine powered by yt-dlp & FFmpeg.

Extracts video metadata and formats, and downloads videos in Original/Best quality
or selected resolutions (4K, 2K, 1080p, 720p, 480p, 360p, MP3/M4A Audio).
"""
import os
import shutil
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional
import yt_dlp

from shorts_generator.config import LOCAL_OUTPUT_DIR


def _get_ffmpeg_path() -> Optional[str]:
    """Find local ffmpeg binary path dynamically."""
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin and os.path.exists(ffmpeg_bin):
        return os.path.dirname(ffmpeg_bin)
    
    venv_ffmpeg = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "ffmpeg.exe")
    if os.path.exists(venv_ffmpeg):
        return os.path.dirname(venv_ffmpeg)
    
    return None


def format_duration(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_bytes(size: float) -> str:
    """Format byte size into human readable string."""
    if not size:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def get_video_info(video_url: str) -> Dict:
    """Fetch video metadata and available quality formats without downloading.
    
    Returns:
        dict with keys: title, thumbnail, duration, duration_str, channel, view_count, quality_options
    """
    ffmpeg_loc = _get_ffmpeg_path()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        
    duration_sec = info.get("duration", 0) or 0
    
    # Always present full suite of resolution & audio quality options
    quality_options = [
        {"id": "original", "label": "⭐ Original / Best Quality (Max Resolution)", "height": 99999, "type": "video"},
        {"id": "2160p", "label": "🖥️ 4K Ultra HD (2160p)", "height": 2160, "type": "video"},
        {"id": "1440p", "label": "🖥️ 2K Quad HD (1440p)", "height": 1440, "type": "video"},
        {"id": "1080p", "label": "📺 1080p Full HD", "height": 1080, "type": "video"},
        {"id": "720p",  "label": "📺 720p HD", "height": 720, "type": "video"},
        {"id": "480p",  "label": "📱 480p SD", "height": 480, "type": "video"},
        {"id": "360p",  "label": "📱 360p Low", "height": 360, "type": "video"},
        {"id": "mp3",   "label": "🎵 Audio Only (MP3 320kbps)", "height": 0, "type": "audio"},
        {"id": "m4a",   "label": "🎵 Audio Only (M4A Original)", "height": 0, "type": "audio"},
    ]

    return {
        "id": info.get("id", ""),
        "title": info.get("title", "Untitled Video"),
        "thumbnail": info.get("thumbnail") or info.get("thumbnails", [{}])[-1].get("url", ""),
        "duration": duration_sec,
        "duration_str": format_duration(duration_sec),
        "channel": info.get("uploader") or info.get("channel") or "Unknown Channel",
        "view_count": info.get("view_count", 0),
        "url": video_url,
        "quality_options": quality_options,
    }


def download_video(
    video_url: str,
    quality_id: str,
    progress_callback: Optional[Callable[[Dict], None]] = None,
    out_dir: Optional[str] = None,
) -> Dict:
    """Download video with specified quality choice.
    
    Args:
        video_url: YouTube URL
        quality_id: 'original', '2160p', '1440p', '1080p', '720p', '480p', '360p', 'mp3', 'm4a'
        progress_callback: callback function receiving status dict
        out_dir: destination directory
    
    Returns:
        dict: { 'file_path': str, 'filename': str, 'file_size': int, 'title': str }
    """
    out_dir = out_dir or LOCAL_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    ffmpeg_loc = _get_ffmpeg_path()
    
    stream_state = {"current_file": "", "stream_count": 0}
    
    # Progress hook wrapper handling multi-stream video & audio progress
    def _progress_hook(d):
        if not progress_callback:
            return
        status = d.get("status")
        if status == "downloading":
            fn = d.get("filename", "")
            if fn and fn != stream_state["current_file"]:
                if stream_state["current_file"]:
                    stream_state["stream_count"] += 1
                stream_state["current_file"] = fn
            
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0
            percent = (downloaded / total * 100.0) if total > 0 else 0.0
            
            if quality_id in ("mp3", "m4a"):
                stream_label = "Downloading Audio"
            elif stream_state["stream_count"] == 0:
                stream_label = "Downloading Video Stream"
            else:
                stream_label = "Downloading Audio Stream"
            
            progress_callback({
                "status": "downloading",
                "percent": min(100.0, max(0.0, percent)),
                "stream_label": stream_label,
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "speed_str": f"{format_bytes(speed)}/s" if speed else "",
                "eta_str": f"{eta}s" if eta else "",
                "filename": os.path.basename(fn),
            })
        elif status == "finished":
            progress_callback({
                "status": "processing",
                "percent": 100.0,
                "stream_label": "Merging with FFmpeg",
                "message": "Processing & merging streams with FFmpeg...",
            })

    # Select yt-dlp format string & postprocessors based on quality_id
    if quality_id == "mp3":
        ydl_format = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]
        outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
    elif quality_id == "m4a":
        ydl_format = "bestaudio[ext=m4a]/bestaudio/best"
        postprocessors = []
        outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
    elif quality_id == "original":
        ydl_format = "bestvideo+bestaudio/best"
        postprocessors = []
        outtmpl = os.path.join(out_dir, "%(title)s [%(height)sp].%(ext)s")
    else:
        # e.g., '1080p' -> height 1080
        try:
            h = int(quality_id.replace("p", ""))
            ydl_format = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        except ValueError:
            ydl_format = "bestvideo+bestaudio/best"
        postprocessors = []
        outtmpl = os.path.join(out_dir, "%(title)s [%(height)sp].%(ext)s")

    ydl_opts = {
        "format": ydl_format,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "progress_hooks": [_progress_hook],
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    if postprocessors:
        ydl_opts["postprocessors"] = postprocessors
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info)
        
        # Postprocessing might change output extension (e.g., .webm -> .mp4 or .mp3)
        if quality_id == "mp3":
            stem, _ = os.path.splitext(filename)
            filename = stem + ".mp3"
        elif not os.path.exists(filename):
            stem, _ = os.path.splitext(filename)
            for ext in (".mp4", ".mkv", ".webm", ".m4a"):
                if os.path.exists(stem + ext):
                    filename = stem + ext
                    break

    file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
    return {
        "file_path": str(Path(filename).resolve()),
        "filename": os.path.basename(filename),
        "file_size": file_size,
        "file_size_str": format_bytes(file_size),
        "title": info.get("title", "Downloaded File"),
    }
