"""VideoFlow Media Engine powered by yt-dlp & FFmpeg.

Supports video/playlist metadata extraction, smart filename templates,
quality selection with size estimation, and multi-stream progress reporting.
"""
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
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


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent filesystem errors across OSes."""
    if not filename:
        return "download"
    # Remove invalid characters: / \ : * ? " < > |
    clean = re.sub(r'[\\/*?:"<>|]', "", filename)
    clean = clean.strip().strip(".")
    return clean or "download"


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
    if not size or size <= 0:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def estimate_file_size(height: int, duration_sec: float) -> str:
    """Estimate approximate file size based on resolution and duration."""
    if not duration_sec or duration_sec <= 0:
        return "Est. ~"
    
    # Approx bitrates in Mbps
    bitrate_mbps = {
        2160: 25.0,  # 4K
        1440: 12.0,  # 2K
        1080: 5.0,   # Full HD
        720: 2.5,    # HD
        480: 1.2,    # SD
        360: 0.6,    # Low
        0: 0.3,      # MP3/Audio
    }
    
    mbps = bitrate_mbps.get(height, 4.0)
    est_bytes = (mbps * 1000000 / 8) * duration_sec
    return f"~{format_bytes(est_bytes)}"


def friendly_error_message(e: Exception) -> str:
    """Translate technical raw exception into user-friendly error string."""
    msg = str(e)
    if "Private video" in msg or "is private" in msg:
        return "🔒 Media Unavailable: This video is private or restricted by the creator."
    if "Video unavailable" in msg or "has been removed" in msg:
        return "⚠️ Media Unavailable: This video has been removed or is unavailable in your region."
    if "HTTP Error 429" in msg or "Too Many Requests" in msg:
        return "⌛ Rate Limited: YouTube is temporarily limiting requests. Please wait a moment and try again."
    if "IncompleteRead" in msg or "Connection reset" in msg or "timed out" in msg:
        return "🌐 Connection Problem: Check your internet connection and try again."
    return f"❌ Download Error: {msg}"


def get_video_info(video_url: str) -> Dict:
    """Fetch video metadata and quality choices without downloading.
    
    Returns:
        dict with metadata & quality_options list
    """
    ffmpeg_loc = _get_ffmpeg_path()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
    except Exception as e:
        raise RuntimeError(friendly_error_message(e)) from e
        
    duration_sec = info.get("duration", 0) or 0
    upload_date = info.get("upload_date", "")
    if upload_date and len(upload_date) == 8:
        date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    else:
        date_str = "N/A"
        
    # Quality Choices with File Size Estimations
    quality_options = [
        {
            "id": "original",
            "label": "⭐ Original / Best Quality (Max Resolution)",
            "height": 99999,
            "badge": "Max",
            "est_size": estimate_file_size(1080, duration_sec),
            "type": "video",
        },
        {
            "id": "2160p",
            "label": "🖥️ 4K Ultra HD (2160p)",
            "height": 2160,
            "badge": "4K",
            "est_size": estimate_file_size(2160, duration_sec),
            "type": "video",
        },
        {
            "id": "1440p",
            "label": "🖥️ 2K Quad HD (1440p)",
            "height": 1440,
            "badge": "2K",
            "est_size": estimate_file_size(1440, duration_sec),
            "type": "video",
        },
        {
            "id": "1080p",
            "label": "📺 1080p Full HD",
            "height": 1080,
            "badge": "FHD",
            "est_size": estimate_file_size(1080, duration_sec),
            "type": "video",
        },
        {
            "id": "720p",
            "label": "📺 720p HD",
            "height": 720,
            "badge": "HD",
            "est_size": estimate_file_size(720, duration_sec),
            "type": "video",
        },
        {
            "id": "480p",
            "label": "📱 480p SD",
            "height": 480,
            "badge": "SD",
            "est_size": estimate_file_size(480, duration_sec),
            "type": "video",
        },
        {
            "id": "360p",
            "label": "📱 360p Low",
            "height": 360,
            "badge": "Low",
            "est_size": estimate_file_size(360, duration_sec),
            "type": "video",
        },
        {
            "id": "mp3",
            "label": "🎵 Audio Only (MP3 320kbps)",
            "height": 0,
            "badge": "MP3",
            "est_size": estimate_file_size(0, duration_sec),
            "type": "audio",
        },
        {
            "id": "m4a",
            "label": "🎵 Audio Only (M4A Original)",
            "height": 0,
            "badge": "M4A",
            "est_size": estimate_file_size(0, duration_sec),
            "type": "audio",
        },
    ]

    return {
        "id": info.get("id", ""),
        "title": info.get("title", "Untitled Video"),
        "thumbnail": info.get("thumbnail") or info.get("thumbnails", [{}])[-1].get("url", ""),
        "duration": duration_sec,
        "duration_str": format_duration(duration_sec),
        "channel": info.get("uploader") or info.get("channel") or "Unknown Channel",
        "view_count": info.get("view_count", 0),
        "upload_date": date_str,
        "url": video_url,
        "quality_options": quality_options,
    }


def get_playlist_info(playlist_url: str) -> Dict:
    """Fetch videos inside a playlist or batch URL list.
    
    Returns:
        dict: { 'title': str, 'video_count': int, 'videos': list }
    """
    ffmpeg_loc = _get_ffmpeg_path()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
    }
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
    except Exception as e:
        raise RuntimeError(friendly_error_message(e)) from e

    entries = info.get("entries", [])
    videos = []
    for idx, entry in enumerate(entries, 1):
        if not entry:
            continue
        v_url = entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
        videos.append({
            "idx": idx,
            "id": entry.get("id", ""),
            "title": entry.get("title", f"Video #{idx}"),
            "url": v_url,
            "duration_str": format_duration(entry.get("duration", 0)),
            "channel": entry.get("uploader") or entry.get("channel") or "Unknown",
        })

    return {
        "title": info.get("title", "YouTube Playlist"),
        "video_count": len(videos),
        "videos": videos,
    }


def download_video(
    video_url: str,
    quality_id: str,
    filename_template: str = "{title} - {channel} [{quality}]",
    progress_callback: Optional[Callable[[Dict], None]] = None,
    out_dir: Optional[str] = None,
) -> Dict:
    """Download video with custom quality & filename template.
    
    Returns:
        dict: { 'file_path': str, 'filename': str, 'file_size': int, 'file_size_str': str, 'title': str }
    """
    out_dir = out_dir or LOCAL_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    ffmpeg_loc = _get_ffmpeg_path()
    
    stream_state = {"current_file": "", "stream_count": 0}
    
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
                "speed_str": f"{format_bytes(speed)}/s" if speed else "0 B/s",
                "eta_str": f"{eta}s" if eta else "0s",
                "filename": os.path.basename(fn),
            })
        elif status == "finished":
            progress_callback({
                "status": "processing",
                "percent": 100.0,
                "stream_label": "Merging with FFmpeg",
                "message": "Processing & merging video/audio streams with FFmpeg...",
            })

    # Output template formatting
    quality_tag = quality_id if quality_id != "original" else "Best"
    formatted_tmpl = filename_template.replace("{quality}", quality_tag)
    formatted_tmpl = formatted_tmpl.replace("{title}", "%(title)s").replace("{channel}", "%(uploader)s")
    outtmpl = os.path.join(out_dir, f"{formatted_tmpl}.%(ext)s")

    # Select yt-dlp format string & postprocessors
    if quality_id == "mp3":
        ydl_format = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]
    elif quality_id == "m4a":
        ydl_format = "bestaudio[ext=m4a]/bestaudio/best"
        postprocessors = []
    elif quality_id == "original":
        ydl_format = "bestvideo+bestaudio/best"
        postprocessors = []
    else:
        try:
            h = int(quality_id.replace("p", ""))
            ydl_format = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        except ValueError:
            ydl_format = "bestvideo+bestaudio/best"
        postprocessors = []

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
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
            "quality": quality_tag,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        raise RuntimeError(friendly_error_message(e)) from e
