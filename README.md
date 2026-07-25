# AI YouTube Shorts Generator (Fully Local & FOSS)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20(qwen2.5%3A7b)-orange.svg)](https://ollama.com)
[![Speech-to-Text](https://img.shields.io/badge/STT-faster--whisper-blueviolet.svg)](https://github.com/SYSTRAN/faster-whisper)

**The 100% Free, Open-Source & Fully Local alternative to Opus Clip, Vidyo.ai, Klap, SubMagic, and 2short.ai.**

Maintained by **[@imomair1](https://github.com/imomair1)**.

Drop in any long-form YouTube video URL or local file path and generate viral-ready 9:16 vertical Shorts completely on your local machine — **zero paid APIs, zero subscriptions, zero credit caps, and no cloud data uploads**.

---

## 🚀 Key Highlights

- 🟢 **100% Local & Free**: Runs default offline mode powered by **Ollama (`qwen2.5:7b`)**, **`faster-whisper`**, **`yt-dlp`**, and **OpenCV face reframing**.
- 🧠 **Smart Local LLM Virality Analysis**: Uses local LLMs to evaluate transcript hooks, emotional peaks, opinions, revelations, and story arcs.
- 🎯 **Face-Aware Vertical Reframing**: Tracks speakers in the frame using OpenCV motion smoothing and clips vertically for 9:16 (TikTok, Reels, Shorts) or 1:1 format.
- ⚡ **Offline Disk Caching**: Caches downloaded source videos and Whisper `.srt` transcripts in `./output/` so re-runs complete in seconds.
- 💻 **CLI & Python API**: Run from PowerShell/Terminal or import directly into Python applications.

---

## 📊 Why Use This Local Generator?

| Feature | This Repository (`imomair1/AI-Youtube-Shorts-Generator`) | Opus Clip / Vidyo.ai / Klap |
|---|---|---|
| **Cost** | 100% Free & Open Source | $20–$300/month |
| **Privacy & Security** | 100% Offline / Local | Uploads your videos to cloud servers |
| **Clip Limits** | Unlimited | Capped monthly minutes |
| **LLM Provider** | **Ollama (`qwen2.5:7b`)** / OpenAI / Gemini | Proprietary / Hidden |
| **Speech-to-Text** | Local `faster-whisper` | Cloud transcription |
| **Reframing** | Local OpenCV + FFmpeg | Cloud processing |

---

## 🛠️ Quick Start (Local Setup)

### 1. Prerequisites
- **Python**: 3.10 or higher
- **FFmpeg**: Installed and on system PATH
- **Ollama**: Installed from [ollama.com](https://ollama.com) with the `qwen2.5:7b` model:
  ```bash
  ollama pull qwen2.5:7b
  ```

### 2. Installation

```bash
# 1. Clone your private repository
git clone https://github.com/imomair1/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator

# 2. Create virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 3. Install local dependencies
pip install -r requirements-local.txt

# 4. Copy environment configuration
cp .env.example .env
```

---

## 📖 Usage

### Generate Shorts from YouTube Video
```bash
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --num-clips 1
```

### Generate Shorts from Local Video File
```bash
python main.py "C:\path\to\your\video.mp4" --num-clips 3
```

### Advanced CLI Arguments
```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" \
    --mode local \
    --num-clips 3 \
    --aspect-ratio 9:16 \
    --format 720 \
    --output-json result.json
```

| Flag | Default | Description |
|------|---------|-------------|
| `--mode` | `local` | `local` (100% offline via Ollama + Whisper + OpenCV) or `api` |
| `--num-clips` | `3` | Number of short highlight clips to generate |
| `--aspect-ratio` | `9:16` | Aspect ratio (`9:16` vertical or `1:1` square) |
| `--format` | `720` | YouTube download resolution (`720` or `1080`) |
| `--output-json` | — | Path to dump JSON metadata output |

---

## 📁 Project Structure

```
AI-Youtube-Shorts-Generator/
├── main.py                       # CLI entry point (defaults to --mode local)
├── requirements-local.txt        # Local dependencies (ollama, faster-whisper, opencv)
├── .env.example                  # Default local configuration template
├── SETUP_LOCAL.md                # Step-by-step local installation guide
└── shorts_generator/
    ├── config.py                 # Configuration loader (Ollama defaults)
    ├── pipeline.py               # Main pipeline dispatcher
    ├── highlights.py             # Virality ranking prompt logic
    └── local/                    # 100% Local offline modules
        ├── downloader.py         # yt-dlp video downloader & caching
        ├── transcriber.py        # faster-whisper speech-to-text
        ├── llm.py                # Ollama local LLM integration
        └── clipper.py            # OpenCV reframing & FFmpeg cutter
```

---

## 🤝 Author & License

Developed and maintained by **[@imomair1](https://github.com/imomair1)**.

Licensed under the [MIT License](LICENSE).
