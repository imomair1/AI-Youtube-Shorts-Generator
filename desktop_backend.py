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
        "concurrency": 2,
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
        self.load_history()

    def load_history(self):
        """Load history list from disk."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.downloads = json.load(f)
            except Exception:
                self.downloads = []

    def save_history(self):
        """Save history list to disk."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.downloads, f, indent=2)
        except Exception as e:
            print("Failed to save history:", e)

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
        ffmpeg_loc = _get_ffmpeg_path()
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
                    }
                    added_items.append(item)
            except Exception as e:
                # Add item with error if single
                item_id = f"item_err_{int(time.time()*1000)}"
                item = {
                    "id": item_id,
                    "title": target_url,
                    "channel": "Error",
                    "url": target_url,
                    "quality": self.settings.get("default_quality", "1080p"),
                    "status": "Failed",
                    "progress": 0,
                    "speed": "",
                    "eta": "",
                    "file_path": "",
                    "playlist_name": "",
                    "date": datetime.now().strftime("%Y/%m/%d"),
                    "selected": True,
                }
                added_items.append(item)

        # Prepend added items to downloads list
        self.downloads = added_items + self.downloads
        self.save_history()
        return {"success": True, "count": len(added_items), "items": added_items}

    def start_download(self, item_id: str):
        """Start downloading a queued or paused item in background thread."""
        item = next((x for x in self.downloads if x["id"] == item_id), None)
        if not item or item["status"] in ("Downloading", "Processing"):
            return

        self.pause_flags[item_id] = False
        t = threading.Thread(target=self._download_worker, args=(item,), daemon=True)
        self.active_threads[item_id] = t
        t.start()

    def start_all_queued(self):
        """Start downloading all queued items."""
        for item in self.downloads:
            if item["status"] == "Queued" and item.get("selected", True):
                self.start_download(item["id"])

    def pause_download(self, item_id: str):
        """Flag download thread to pause."""
        self.pause_flags[item_id] = True
        item = next((x for x in self.downloads if x["id"] == item_id), None)
        if item and item["status"] == "Downloading":
            item["status"] = "Paused"
            self.save_history()

    def toggle_pause_all(self):
        """Pause or resume selected items."""
        has_active = any(x["status"] == "Downloading" for x in self.downloads)
        for item in self.downloads:
            if item.get("selected", True):
                if has_active:
                    if item["status"] == "Downloading":
                        self.pause_download(item["id"])
                else:
                    if item["status"] in ("Queued", "Paused", "Failed"):
                        self.start_download(item["id"])

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
        """Background thread executing yt-dlp download."""
        item_id = item["id"]
        item["status"] = "Downloading"
        item["progress"] = 0
        
        out_dir = self.settings.get("download_dir", os.path.join(os.path.expanduser("~"), "Downloads"))
        os.makedirs(out_dir, exist_ok=True)
        ffmpeg_loc = _get_ffmpeg_path()

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
                ydl_format = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
            except ValueError:
                ydl_format = "bestvideo+bestaudio/best"
            postprocessors = []

        # Download thumbnail option
        if self.settings.get("download_thumbnails", False):
            postprocessors.append({"key": "FFmpegMetadata"})

        outtmpl = os.path.join(out_dir, "%(title)s [%(height)sp].%(ext)s") if quality_id != "mp3" else os.path.join(out_dir, "%(title)s.%(ext)s")

        ydl_opts = {
            "format": ydl_format,
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "progress_hooks": [_progress_hook],
            "quiet": True,
            "no_warnings": True,
            "writethumbnail": self.settings.get("download_thumbnails", False),
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
