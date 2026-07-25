# 🚀 Local Setup Guide — AI YouTube Shorts Generator

Run the entire pipeline **100% locally** with zero paid APIs.

---

## Prerequisites

| Tool | Purpose | Min Version |
|---|---|---|
| **Python** | Runtime | 3.10+ |
| **ffmpeg** | Video cutting & audio muxing | 4.0+ |
| **Ollama** | Local LLM (highlight detection) | 0.1.0+ |
| **Git** | Clone the repo | Any |

### Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **RAM** | 8 GB | 16 GB |
| **Disk** | 10 GB free (models + temp video) | 20 GB |
| **GPU** | Not required (CPU works) | NVIDIA GPU speeds up Whisper |

---

## Step-by-Step Installation

### 1. Install Ollama

**Windows:**
Download from [https://ollama.com/download](https://ollama.com/download) and run the installer.

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

After installing, verify:
```bash
ollama --version
```

### 2. Pull the LLM Model

```bash
ollama pull qwen2.5:7b
```

This downloads ~4.7 GB. Wait for it to complete.

> **Alternative models** (if you have more RAM/VRAM):
> - `llama3.1:8b` — Meta's Llama 3.1 (4.7 GB)
> - `mistral:7b` — Mistral 7B (4.1 GB)
> - `gemma2:9b` — Google's Gemma 2 (5.4 GB)
> - `qwen2.5:14b` — Higher quality, needs 16 GB RAM (8.7 GB)

### 3. Install ffmpeg

**Windows:**
```powershell
# Using winget (recommended):
winget install Gyan.FFmpeg

# Or using chocolatey:
choco install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

Verify:
```bash
ffmpeg -version
```

### 4. Clone the Repository

```bash
git clone https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator
```

### 5. Create a Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 6. Install Python Dependencies

```bash
pip install -r requirements-local.txt
```

### 7. Configure Environment

```bash
# Copy the example config
cp .env.example .env
```

The defaults work out of the box — no API keys needed! The `.env` file uses:
- `LLM_PROVIDER=ollama` (fully local)
- `OLLAMA_MODEL=qwen2.5:7b`
- `LOCAL_WHISPER_MODEL=base` (auto-downloads on first run)

> **Optional:** Edit `.env` to change the Whisper model size:
> - `tiny` — Fastest, lowest accuracy (~75 MB)
> - `base` — Default, good balance (~150 MB)
> - `small` — Better accuracy (~500 MB)
> - `medium` — High accuracy (~1.5 GB)
> - `large-v3` — Best accuracy (~3 GB, needs 8+ GB RAM)

---

## Running the Project

### 1. Start Ollama (if not running)

```bash
ollama serve
```

> On Windows, Ollama typically auto-starts as a background service after installation.

### 2. Generate Shorts

```bash
# Basic usage — generates 3 shorts from a YouTube video
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Customize number of clips
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --num-clips 5

# Use a local video file instead of YouTube
python main.py "path/to/your/video.mp4"

# Change output resolution
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --format 1080

# Square output (for Instagram)
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --aspect-ratio 1:1

# Save full results as JSON
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-json results.json

# Force English transcription
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --language en
```

### 3. Output

Generated shorts are saved in the `output/` directory:
```
output/
  source_VIDEO_ID.mp4    # Downloaded source video (cached)
  source_VIDEO_ID.srt    # Transcript cache (cached)
  short_01.mp4           # Generated short #1
  short_02.mp4           # Generated short #2
  short_03.mp4           # Generated short #3
```

---

## What Happens Under the Hood

```
YouTube URL
  │
  ├─ 1. DOWNLOAD ─────── yt-dlp downloads the video to output/
  │
  ├─ 2. TRANSCRIBE ────── faster-whisper runs speech-to-text locally
  │                        (auto-downloads model on first run)
  │
  ├─ 3. HIGHLIGHT ─────── Ollama (qwen2.5:7b) analyzes transcript
  │    DETECTION           for viral-worthy moments using virality
  │                        criteria prompts
  │
  └─ 4. CROP & RENDER ─── ffmpeg cuts subclips, OpenCV does face-
                           tracking vertical crop
```

**Every step runs on your machine. No data leaves your network.**

---

## Troubleshooting

### "Cannot connect to Ollama"
```
RuntimeError: Cannot connect to Ollama at http://localhost:11434
```
**Fix:** Start the Ollama server:
```bash
ollama serve
```

### "Ollama model not found"
```
RuntimeError: Ollama model 'qwen2.5:7b' not found
```
**Fix:** Pull the model:
```bash
ollama pull qwen2.5:7b
```

### "ffmpeg not found"
```
FileNotFoundError: [WinError 2] The system cannot find the file specified
```
**Fix:** Install ffmpeg and ensure it's on your PATH. After installing, restart your terminal.

### "yt-dlp errors / video unavailable"
```
yt_dlp.utils.DownloadError: ...
```
**Fix:** Update yt-dlp (YouTube frequently changes their API):
```bash
pip install -U yt-dlp
```

### "Whisper produced no segments"
The video may have no detectable speech, or the audio format is unsupported.
**Fix:** Try forcing the language: `--language en`

### "Highlight generator produced invalid output"
The LLM failed to produce valid JSON.
**Fix:** Try a stronger model:
```bash
ollama pull llama3.1:8b
# Then edit .env: OLLAMA_MODEL=llama3.1:8b
```

### Slow performance
- **Whisper is slow:** Use `LOCAL_WHISPER_MODEL=tiny` in `.env` for faster (less accurate) transcription
- **LLM is slow:** This is normal for CPU inference on 7B models. A GPU significantly speeds this up
- **Video processing is slow:** Use `--format 480` for faster downloads and processing

### Out of memory
- Use a smaller Whisper model: `LOCAL_WHISPER_MODEL=tiny`
- Use a smaller LLM: `ollama pull qwen2.5:3b` and set `OLLAMA_MODEL=qwen2.5:3b`
- Close other applications to free RAM

---

## Configuration Reference

| Environment Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama`, `openai`, or `gemini` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama model name |
| `LOCAL_WHISPER_MODEL` | `base` | faster-whisper model size |
| `LOCAL_WHISPER_DEVICE` | `auto` | `auto`, `cpu`, or `cuda` |
| `LOCAL_OUTPUT_DIR` | `output` | Where to save generated shorts |
| `LOCAL_WHISPER_VAD_FILTER` | `false` | Enable Voice Activity Detection |
| `OPENAI_API_KEY` | *(empty)* | Only if `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | Only if `LLM_PROVIDER=openai` |
| `GEMINI_API_KEY` | *(empty)* | Only if `LLM_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Only if `LLM_PROVIDER=gemini` |
| `MUAPI_API_KEY` | *(empty)* | Only for `--mode api` |

---

## Verification Checklist

- [ ] Python 3.10+ installed (`python --version`)
- [ ] ffmpeg installed (`ffmpeg -version`)
- [ ] Ollama installed and running (`ollama --version`)
- [ ] Model pulled (`ollama list` shows `qwen2.5:7b`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements-local.txt`)
- [ ] `.env` file created from `.env.example`
- [ ] Test run succeeds: `python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --num-clips 1`
- [ ] Output file exists in `output/short_01.mp4`
- [ ] Video plays correctly and is vertically cropped
