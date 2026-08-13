# ⚡ YouTube Video Downloader (Streamlit Web App)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Web%20UI-Streamlit-ff4b4b.svg)](https://streamlit.io)
[![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-red.svg)](https://github.com/yt-dlp/yt-dlp)

**A Private, Premium YouTube Video Downloader Web Application built with Streamlit.**

Maintained by **[@imomair1](https://github.com/imomair1)**.

Paste any long-form YouTube video URL and download it in **Original / Best Quality (4K, 2K, 1080p 60fps)** or your choice of resolution (720p, 480p, 360p, or MP3/M4A Audio) — directly in your browser with zero subscription fees, no credit caps, and no watermark.

---

## 🚀 Features

- ⭐ **Original / Best Quality Download**: Automatically fetches the highest resolution video & audio streams available (4K, 1440p, 1080p) and merges them using local FFmpeg.
- 🎯 **Flexible Quality Choices**:
  - 🖥️ **Original / Best Quality (Max Resolution)**
  - 🖥️ **4K Ultra HD (2160p)**
  - 🖥️ **2K Quad HD (1440p)**
  - 📺 **1080p Full HD**
  - 📺 **720p HD**
  - 📱 **480p SD / 360p Low**
  - 🎵 **Audio Only (MP3 320kbps / M4A)**
- 🎨 **Modern Streamlit Interface (`app.py`)**: Sleek dark mode UI with interactive video info preview (thumbnail, title, duration, views).
- 💾 **Direct In-Browser File Delivery**: Click to download the file directly to your computer.
- 🔒 **Private & Secure**: Private repository and self-hostable.

---

## 🛠️ Quick Start (Local Setup)

### 1. Prerequisites
- **Python**: 3.10 or higher
- **FFmpeg**: Installed on system PATH

### 2. Installation

```bash
# Clone private repository
git clone https://github.com/imomair1/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
source venv/bin/activate      # Linux / macOS

# Install dependencies
pip install -r requirements-local.txt
```

### 3. Launch Streamlit Web App

```bash
streamlit run app.py
```

The web application will open automatically at `http://localhost:8501`.

---

## 📁 Project Structure

```
AI-Youtube-Shorts-Generator/
├── app.py                        # Streamlit Web Application Interface
├── yt_downloader.py              # Core YouTube extraction & download engine
├── main.py                       # CLI entry point for shorts pipeline
├── requirements-local.txt        # Local dependencies
├── README.md                     # Documentation
└── output/                       # Destination folder for downloaded files
```

---

## 🔒 Copyright & Proprietary Rights

Copyright © 2026 **[@imomair1](https://github.com/imomair1)**. All rights reserved. Private and proprietary software.
