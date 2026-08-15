"""FuseGrab Desktop Backend API Bridge.

Interacts with pywebview frontend JS API to manage YouTube video downloads,
playlist extraction, settings persistence, and system folder access.
"""
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yt_dlp

# Auto-inject venv\Scripts to system PATH so FFmpeg is always found
_CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
_VENV_SCRIPTS = os.path.join(_CURRENT_DIR, "venv", "Scripts")
if os.path.exists(_VENV_SCRIPTS) and _VENV_SCRIPTS not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _VENV_SCRIPTS + os.pathsep + os.environ.get("PATH", "")

from shorts_generator.config import LOCAL_OUTPUT_DIR
from yt_downloader import _get_ffmpeg_path, format_bytes, sanitize_filename


SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".fusegrab_settings.json")
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".fusegrab_history.json")


def load_settings() -> Dict:
    """Load settings from JSON file or return defaults."""
    default_settings = {
        "download_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
        "default_quality": "1080p",
        "download_thumbnails": False,
        "concurrency": 1,  # Strict 1-by-1 sequential download queue by default
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_settings.update(data)
        except Exception:
            pass
    return default_settings


def save_settings_to_file(settings: Dict):
    """Save settings dictionary to JSON file."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print("Failed to save settings:", e)


class FuseGrabApi:
    def __init__(self):
        self.settings = load_settings()
        self.downloads: List[Dict] = []
        self.active_threads: Dict[str, threading.Thread] = {}
        self.pause_flags: Dict[str, bool] = {}
        self.is_running = True
        self.load_history()
        
        # Start sequential background queue manager loop
        self.queue_thread = threading.Thread(target=self._queue_manager_loop, daemon=True)
        self.queue_thread.start()

    def load_history(self):
        """Load history list from disk and reset any interrupted/failed items to Queued."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.downloads = json.load(f)
                    for item in self.downloads:
                        if item.get("status") in ("Downloading", "Processing", "Failed"):
                            item["status"] = "Queued"
                            item["progress"] = 0
            except Exception:
                self.downloads = []

    def save_history(self):
        """Save history list to disk."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.downloads, f, indent=2)
        except Exception as e:
            print("Failed to save history:", e)

    def _queue_manager_loop(self):
        """Sequential queue manager: processes items 1-by-1 in order (top to bottom)."""
        while self.is_running:
            time.sleep(1.0)
            
            # Count currently active downloading items
            active_count = sum(1 for d in self.downloads if d.get("status") in ("Downloading", "Processing"))
            
            max_conc = int(self.settings.get("concurrency", 1))
            if max_conc < 1:
                max_conc = 1
                
            if active_count < max_conc:
                # Pick the first queued item in array order (top to bottom as displayed in UI)
                queued_item = None
                for item in self.downloads:
                    if item.get("status") == "Queued" and item.get("selected", True):
                        queued_item = item
                        break
                        
                if queued_item:
                    self.start_download(queued_item["id"])

    def get_settings(self) -> Dict:
        """Expose current settings to UI."""
        return self.settings

    def update_settings(self, settings_json: str) -> Dict:
        """Update settings from UI."""
        try:
            new_s = json.loads(settings_json)
            self.settings.update(new_s)
            save_settings_to_file(self.settings)
            return {"success": True, "settings": self.settings}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def select_folder(self) -> str:
        """Open native folder picker using tkinter or fallback."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            folder = filedialog.askdirectory(initialdir=self.settings.get("download_dir"))
            root.destroy()
            if folder:
                return folder
        except Exception:
            pass
        return self.settings.get("download_dir")

    def get_downloads(self) -> List[Dict]:
        """Return list of download items."""
        return self.downloads

    def parse_urls(self, url_text: str) -> Dict:
        """Parse YouTube URLs or playlists and return metadata entries."""
        if not url_text or not url_text.strip():
            return {"success": False, "error": "Please enter a valid YouTube URL."}

        raw_urls = [u.strip() for u in url_text.strip().splitlines() if u.strip()]
        ffmpeg_loc = _get_ffmpeg_path() or _VENV_SCRIPTS
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
        }
        if ffmpeg_loc:
            ydl_opts["ffmpeg_location"] = ffmpeg_loc

        added_items = []
        for target_url in raw_urls:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_url, download=False)
                    
                if "entries" in info and info["entries"]:
                    playlist_title = info.get("title", "Playlist")
                    for idx, entry in enumerate(info["entries"], 1):
                        if not entry:
                            continue
                        v_id = entry.get("id", str(time.time()))
                        item_id = f"item_{v_id}_{idx}"
                        v_url = entry.get("url") or f"https://www.youtube.com/watch?v={v_id}"
                        item = {
                            "id": item_id,
                            "title": entry.get("title", f"Video #{idx}"),
                            "channel": entry.get("uploader") or entry.get("channel") or playlist_title,
                            "url": v_url,
                            "quality": self.settings.get("default_quality", "1080p"),
                            "status": "Queued",
                            "progress": 0,
                            "speed": "",
                            "eta": "",
                            "file_path": "",
                            "playlist_name": playlist_title,
                            "date": datetime.now().strftime("%Y/%m/%d"),
                            "selected": True,
                            "error_msg": "",
                        }
                        added_items.append(item)
                else:
                    v_id = info.get("id", str(int(time.time()*1000)))
                    item_id = f"item_{v_id}"
                    item = {
                        "id": item_id,
                        "title": info.get("title", "YouTube Video"),
                        "channel": info.get("uploader") or info.get("channel") or "YouTube Channel",
                        "url": target_url,
                        "quality": self.settings.get("default_quality", "1080p"),
                        "status": "Queued",
                        "progress": 0,
                        "speed": "",
                        "eta": "",
                        "file_path": "",
                        "playlist_name": "",
                        "date": datetime.now().strftime("%Y/%m/%d"),
                        "selected": True,
                        "error_msg": "",
                    }
                    added_items.append(item)
            except Exception as e:
                item_id = f"item_err_{int(time.time()*1000)}"
                item = {
                    "id": item_id,
                    "title": target_url,
                    "channel": "Error",
                    "url": target_url,
                    "quality": self.settings.get("default_quality", "1080p"),
                    "status": "Queued",
                    "progress": 0,
                    "speed": "",
                    "eta": "",
                    "file_path": "",
                    "playlist_name": "",
                    "date": datetime.now().strftime("%Y/%m/%d"),
                    "selected": True,
                    "error_msg": str(e),
                }
                added_items.append(item)

        # Place added items at top of list in sequential order (item 1 at top)
        self.downloads = added_items + self.downloads
        self.save_history()
        return {"success": True, "count": len(added_items), "items": added_items}

    def start_download(self, item_id: str):
        """Start downloading a specific item in background thread if concurrency limit allows."""
        active_count = sum(1 for d in self.downloads if d.get("status") in ("Downloading", "Processing"))
        max_conc = int(self.settings.get("concurrency", 1))
        if max_conc < 1:
            max_conc = 1

        if active_count >= max_conc:
            return  # Strict queue guard: Queue manager will trigger when active slot frees up

        item = next((x for x in self.downloads if x["id"] == item_id), None)
        if not item or item["status"] in ("Downloading", "Processing"):
            return

        self.pause_flags[item_id] = False
        t = threading.Thread(target=self._download_worker, args=(item,), daemon=True)
        self.active_threads[item_id] = t
        t.start()

    def start_all_queued(self):
        """Ensure queue manager is active."""
        pass

    def retry_item(self, item_id: str):
        """Re-queue a failed or paused item for download."""
        item = next((x for x in self.downloads if x["id"] == item_id), None)
        if item:
            item["status"] = "Queued"
            item["progress"] = 0
            item["error_msg"] = ""
            self.save_history()

    def pause_download(self, item_id: str):
        """Flag download thread to pause."""
        self.pause_flags[item_id] = True
        item = next((x for x in self.downloads if x["id"] == item_id), None)
        if item and item["status"] == "Downloading":
            item["status"] = "Paused"
            self.save_history()

    def toggle_pause_all(self):
        """Pause active download or resume queued items."""
        has_active = any(x["status"] == "Downloading" for x in self.downloads)
        if has_active:
            for item in self.downloads:
                if item["status"] == "Downloading":
                    self.pause_download(item["id"])
        else:
            for item in self.downloads:
                if item["status"] in ("Paused", "Failed") and item.get("selected", True):
                    item["status"] = "Queued"
                    item["progress"] = 0
            self.save_history()

    def delete_selected(self):
        """Delete selected items from download list."""
        self.downloads = [x for x in self.downloads if not x.get("selected", False)]
        self.save_history()
        return {"success": True, "count": len(self.downloads)}

    def delete_item(self, item_id: str):
        """Delete single item by ID."""
        self.downloads = [x for x in self.downloads if x["id"] != item_id]
        self.save_history()

    def update_item_quality(self, item_id: str, quality: str):
        """Update quality setting for specific item."""
        item = next((x for x in self.downloads if x["id"] == item_id), None)
        if item:
            item["quality"] = quality
            self.save_history()

    def _download_worker(self, item: Dict):
        """Background thread executing yt-dlp download with robust network retries and auto-resume."""
        item_id = item["id"]
        item["status"] = "Downloading"
        item["progress"] = 0
        item["error_msg"] = ""
        
        out_dir = self.settings.get("download_dir", os.path.join(os.path.expanduser("~"), "Downloads"))
        os.makedirs(out_dir, exist_ok=True)
        ffmpeg_loc = _get_ffmpeg_path() or _VENV_SCRIPTS

        def _progress_hook(d):
            if self.pause_flags.get(item_id, False):
                raise RuntimeError("PAUSED")

            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed") or 0
                eta = d.get("eta") or 0
                percent = (downloaded / total * 100.0) if total > 0 else 0.0

                item["status"] = "Downloading"
                item["progress"] = min(99.0, max(0.0, percent))
                item["speed"] = f"{format_bytes(speed)}/s" if speed else ""
                item["eta"] = f"{eta}s" if eta else ""
            elif status == "finished":
                item["status"] = "Processing"
                item["progress"] = 99.0

        quality_id = item.get("quality", "1080p")
        if quality_id == "mp3":
            ydl_format = "bestaudio/best"
            postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}]
        elif quality_id == "m4a":
            ydl_format = "bestaudio[ext=m4a]/bestaudio/best"
            postprocessors = []
        elif quality_id in ("original", "Original / Best"):
            ydl_format = "bestvideo+bestaudio/best"
            postprocessors = []
        else:
            try:
                h = int(quality_id.replace("p", ""))
                # Flexible format string with automatic fallback if height stream is restricted
                ydl_format = f"bestvideo[height<={h}]+bestaudio/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
            except ValueError:
                ydl_format = "bestvideo+bestaudio/best"
            postprocessors = []

        if self.settings.get("download_thumbnails", False):
            postprocessors.append({"key": "FFmpegMetadata"})

        outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")

        ydl_opts = {
            "format": ydl_format,
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "progress_hooks": [_progress_hook],
            "quiet": True,
            "no_warnings": True,
            "writethumbnail": self.settings.get("download_thumbnails", False),
            "retries": 10,                # Auto-retry network glitches 10 times
            "fragment_retries": 10,       # Auto-retry video chunk fragments
            "continuedl": True,           # Auto-resume partial .part downloads
            "socket_timeout": 30,         # 30s socket timeout
        }
        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors
        if ffmpeg_loc:
            ydl_opts["ffmpeg_location"] = ffmpeg_loc

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item["url"], download=True)
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

            item["status"] = "Finished"
            item["progress"] = 100.0
            item["file_path"] = str(Path(filename).resolve())
            item["date"] = datetime.now().strftime("%Y/%m/%d")
            self.save_history()
        except Exception as e:
            if "PAUSED" in str(e):
                item["status"] = "Paused"
            else:
                item["status"] = "Failed"
                item["error_msg"] = str(e)
            self.save_history()

    def open_file_folder(self, item_id: str):
        """Open the downloaded file or directory in Windows File Explorer."""
        item = next((x for x in self.downloads if x["id"] == item_id), None)
        if item and item.get("file_path") and os.path.exists(item["file_path"]):
            subprocess.run(f'explorer /select,"{item["file_path"]}"', shell=True)
        else:
            download_dir = self.settings.get("download_dir", os.path.join(os.path.expanduser("~"), "Downloads"))
            os.makedirs(download_dir, exist_ok=True)
            subprocess.run(f'explorer "{download_dir}"', shell=True)
