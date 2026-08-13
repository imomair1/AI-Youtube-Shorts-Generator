"""Streamlit YouTube Video Downloader Web Application.

Features:
- Download YouTube videos in Original/Best Quality (4K, 2K, 1080p 60fps) or selected resolution.
- Audio extraction (MP3 / M4A).
- Real-time progress status.
- Direct browser download delivery.
"""
import os
import time
from pathlib import Path
import streamlit as st

from yt_downloader import get_video_info, download_video, format_bytes

# Page Configuration
st.set_page_config(
    page_title="YouTube Video Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS for Premium Design Aesthetics
CUSTOM_CSS = """
<style>
    /* Dark Slate Theme Customizations */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Header Card */
    .header-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin-bottom: 28px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
    }

    /* Video Preview Card */
    .preview-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 20px;
        margin-top: 20px;
        margin-bottom: 24px;
    }
    
    .badge {
        display: inline-block;
        background-color: #334155;
        color: #e2e8f0;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        margin-right: 8px;
        margin-top: 6px;
    }
    
    .badge-accent {
        background-color: #0369a1;
        color: #e0f2fe;
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        padding: 12px 16px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }

    /* Download Button */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 14px 24px !important;
        border-radius: 10px !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
    }
    
    /* Download Delivery Button */
    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 14px 24px !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Hide Streamlit Footer & Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header Section
st.markdown(
    """
    <div class="header-box">
        <div class="header-title">⚡ YouTube Video Downloader</div>
        <div class="header-subtitle">Download YouTube videos in Original Quality (4K, 1080p, 720p) or MP3 audio — 100% Free & Unlimited</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Session state initialization
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "download_result" not in st.session_state:
    st.session_state.download_result = None

# Input Section
video_url = st.text_input(
    "Enter YouTube Video Link:",
    placeholder="https://www.youtube.com/watch?v=...",
    key="url_input",
)

col1, col2 = st.columns([3, 1])

with col1:
    fetch_clicked = st.button("🔍 Fetch Video Details")

if fetch_clicked or (video_url and st.session_state.video_info is None):
    if video_url.strip():
        with st.spinner("Fetching video details & available formats..."):
            try:
                info = get_video_info(video_url.strip())
                st.session_state.video_info = info
                st.session_state.download_result = None
            except Exception as e:
                st.error(f"❌ Failed to fetch video details: {str(e)}")
                st.session_state.video_info = None
    else:
        st.warning("Please enter a valid YouTube URL.")

# Video Info & Quality Selection Preview Card
if st.session_state.video_info:
    info = st.session_state.video_info
    
    st.markdown("<div class=\"preview-card\">", unsafe_allow_html=True)
    pcol1, pcol2 = st.columns([1, 2])
    
    with pcol1:
        if info.get("thumbnail"):
            st.image(info["thumbnail"], use_container_width=True)
            
    with pcol2:
        st.markdown(f"### {info['title']}")
        st.markdown(
            f"""
            <span class="badge badge-accent">📺 {info['channel']}</span>
            <span class="badge">⏱️ {info['duration_str']}</span>
            <span class="badge">👁️ {info['view_count']:,} views</span>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Quality Selection Form
    st.markdown("### ⚙️ Select Quality Choice:")
    
    quality_options = info["quality_options"]
    quality_labels = [q["label"] for q in quality_options]
    
    selected_label = st.selectbox(
        "Quality Format:",
        options=quality_labels,
        index=0,
        help="Select 'Original / Best Quality' to download maximum resolution available (4K/1080p).",
    )
    
    # Find matching quality choice object
    selected_quality = next((q for q in quality_options if q["label"] == selected_label), quality_options[0])
    
    st.write("") # spacing
    download_clicked = st.button("🚀 Start Download")

    if download_clicked:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def _update_progress(d):
            if d.get("status") == "downloading":
                pct = int(d.get("percent", 0))
                progress_bar.progress(min(100, max(0, pct)))
                status_text.markdown(
                    f"**Downloading... {pct}%** ({d.get('speed_str', '')} • ETA: {d.get('eta_str', '')})"
                )
            elif d.get("status") == "processing":
                progress_bar.progress(100)
                status_text.markdown("⏳ **Processing & merging streams with FFmpeg...**")

        with st.spinner("Downloading video..."):
            try:
                res = download_video(
                    video_url=info["url"],
                    quality_id=selected_quality["id"],
                    progress_callback=_update_progress,
                )
                st.session_state.download_result = res
                status_text.success("✅ Download & processing complete!")
            except Exception as e:
                st.error(f"❌ Download failed: {str(e)}")

# Download Completion & Direct File Delivery Button
if st.session_state.download_result:
    res = st.session_state.download_result
    file_path = res["file_path"]
    
    if os.path.exists(file_path):
        st.markdown("---")
        st.success(f"🎉 **Ready!** {res['filename']} ({res['file_size_str']})")
        
        # Read file binary for in-browser download
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        mime_type = "audio/mp3" if file_path.endswith(".mp3") else "video/mp4"
        
        st.download_button(
            label=f"💾 Click to Save File to Your Device ({res['file_size_str']})",
            data=file_bytes,
            file_name=res["filename"],
            mime=mime_type,
        )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
    "Maintained by <a href='https://github.com/imomair1' style='color: #818cf8;'>@imomair1</a> • Private Application"
    "</div>",
    unsafe_allow_html=True,
)
