"""Comprehensive Automated Test Suite for VideoFlow Media Downloader.
"""
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from yt_downloader import (
    get_video_info,
    get_playlist_info,
    download_video,
    sanitize_filename,
    estimate_file_size,
    friendly_error_message,
    format_duration,
    format_bytes,
)

TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
BATCH_URLS = "https://www.youtube.com/watch?v=jNQXAC9IVRw\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ"

results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "details": []
}

def log_test(name: str, passed: bool, message: str = "", is_warning: bool = False):
    results["total"] += 1
    if passed:
        results["passed"] += 1
        status = "PASSED"
    elif is_warning:
        results["warnings"] += 1
        status = "WARNING"
    else:
        results["failed"] += 1
        status = "FAILED"
    results["details"].append({"name": name, "status": status, "message": message})
    clean_msg = message.encode("ascii", "ignore").decode("ascii")
    print(f"[{status}] {name}: {clean_msg}")

print("==================================================")
print("RUNNING VIDEOFLOW AUTOMATED TEST SUITE")
print("==================================================\n")

# TEST 1: App Modules Import & Syntax
try:
    import app
    import yt_downloader
    log_test("Module Imports", True, "app and yt_downloader imported without errors")
except Exception as e:
    log_test("Module Imports", False, str(e))

# TEST 2: Sanitize Filename Edge Cases
try:
    test_str = 'Amazing: Nature / Documentary? * " < > | Special!'
    clean = sanitize_filename(test_str)
    assert ":" not in clean and "/" not in clean and "*" not in clean and "<" not in clean
    log_test("Filename Sanitization", True, f"Sanitized '{test_str}' -> '{clean}'")
except Exception as e:
    log_test("Filename Sanitization", False, str(e))

# TEST 3: File Size Estimation Helper
try:
    est_4k = estimate_file_size(2160, 120)
    est_1080 = estimate_file_size(1080, 120)
    assert "MB" in est_4k or "GB" in est_4k
    log_test("File Size Estimation", True, f"1080p 2min -> {est_1080}, 4K 2min -> {est_4k}")
except Exception as e:
    log_test("File Size Estimation", False, str(e))

# TEST 4: Friendly Error Translation
try:
    err1 = friendly_error_message(Exception("Private video: This video is private"))
    assert "Media Unavailable" in err1
    err2 = friendly_error_message(Exception("HTTP Error 429: Too Many Requests"))
    assert "Rate Limited" in err2
    log_test("Error Translation", True, f"Translated technical errors into friendly UI strings")
except Exception as e:
    log_test("Error Translation", False, str(e))

# TEST 5: Single Video Metadata Analysis (Public Domain / Sample URL)
info = None
start_t = time.time()
try:
    info = get_video_info(TEST_URL)
    analysis_t = time.time() - start_t
    assert info["title"] == "Me at the zoo"
    assert info["channel"] == "jawed"
    assert info["duration"] == 19
    assert len(info["quality_options"]) == 9
    log_test("Single Video Analysis", True, f"Analyzed in {analysis_t:.2f}s | Title: '{info['title']}' | Formats: {len(info['quality_options'])} options")
except Exception as e:
    log_test("Single Video Analysis", False, str(e))

# TEST 6: Complete Video Download Workflow (Original Quality)
start_t = time.time()
try:
    res_orig = download_video(TEST_URL, quality_id="original", filename_template="test_{title}_{quality}")
    dl_t = time.time() - start_t
    assert os.path.exists(res_orig["file_path"])
    assert res_orig["file_size"] > 100000  # > 100KB
    log_test("Original Quality Download", True, f"Downloaded in {dl_t:.2f}s | Size: {res_orig['file_size_str']} | File: {res_orig['filename']}")
except Exception as e:
    log_test("Original Quality Download", False, str(e))

# TEST 7: Audio Extraction Workflow (MP3 Audio)
start_t = time.time()
try:
    res_audio = download_video(TEST_URL, quality_id="mp3", filename_template="test_{title}_audio")
    dl_t = time.time() - start_t
    assert os.path.exists(res_audio["file_path"])
    assert res_audio["file_path"].endswith(".mp3")
    assert res_audio["file_size"] > 10000
    log_test("Audio Extraction (MP3)", True, f"Extracted MP3 in {dl_t:.2f}s | Size: {res_audio['file_size_str']} | File: {res_audio['filename']}")
except Exception as e:
    log_test("Audio Extraction (MP3)", False, str(e))

# TEST 8: Invalid / Malformed URL Error Handling
try:
    try:
        get_video_info("https://invalid-url-domain-xyz.com/fake")
        log_test("Invalid URL Handling", False, "Failed to catch invalid URL exception")
    except RuntimeError as e:
        log_test("Invalid URL Handling", True, f"Caught invalid URL with user-friendly string: '{str(e)[:60]}...'")
except Exception as e:
    log_test("Invalid URL Handling", False, str(e))

# TEST 9: Empty URL Validation
try:
    try:
        get_video_info("")
        log_test("Empty URL Handling", False, "Failed to catch empty URL")
    except ValueError:
        log_test("Empty URL Handling", True, "Empty URL properly rejected with ValueError")
except Exception as e:
    log_test("Empty URL Handling", False, str(e))

# TEST 10: Multi-URL Batch Parsing
try:
    p_info = get_playlist_info(BATCH_URLS)
    assert p_info["video_count"] == 2
    assert len(p_info["videos"]) == 2
    log_test("Multi-URL Batch Parsing", True, f"Parsed batch list | {p_info['video_count']} videos found")
except Exception as e:
    log_test("Multi-URL Batch Parsing", False, str(e))

print("\n==================================================")
print(f"TEST SUMMARY: Total: {results['total']} | Passed: {results['passed']} | Failed: {results['failed']} | Warnings: {results['warnings']}")
print("==================================================")
