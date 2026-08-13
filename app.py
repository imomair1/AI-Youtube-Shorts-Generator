"""VideoFlow — Premium Media Manager & Video Downloader Web App.

Built with Streamlit, yt-dlp & FFmpeg.
Features:
- Modern Charcoal/Black Dark UI with Sidebar Navigation
- Single & Batch/Playlist Downloads
- Quality Selection Panel with File Size Estimations
- Smart Filename System
- Download History & Queue Management
- 100% Local Privacy Notice
"""
import os
import time
from pathlib import Path
import streamlit as st

from yt_downloader import (
    get_video_info,
    get_playlist_info,
    download_video,
    format_bytes,
    format_duration,
    sanitize_filename,
)

# Page Config
st.set_page_config(
    page_title="VideoFlow — Media Downloader",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Dark CSS System
CUSTOM_CSS = """
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #090d16;
        color: #f1f5f9;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    
    .sidebar-brand {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #6366f1, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 24px;
        padding-left: 8px;
    }

    /* Container Cards */
    .flow-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    
    .hero-box {
        text-align: center;
        padding: 32px 20px 24px 20px;
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid #1e293b;
        border-radius: 20px;
        margin-bottom: 28px;
    }

    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: -0.8px;
        margin-bottom: 8px;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 400;
    }

    /* Badges & Metrics */
    .vf-badge {
        display: inline-block;
        background-color: #1e293b;
        color: #cbd5e1;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 8px;
        margin-right: 8px;
        margin-top: 6px;
        border: 1px solid #334155;
    }
    
    .vf-badge-indigo {
        background-color: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border-color: rgba(99, 102, 241, 0.3);
    }

    .vf-badge-emerald {
        background-color: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border-color: rgba(16, 185, 129, 0.3);
    }

    /* Form & Input Enhancements */
    .stTextInput > div > div > input {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        font-size: 1.05rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
    }

    .action-btn > button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
    }

    .action-btn > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(99, 102, 241, 0.45) !important;
    }

    .download-btn > button {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        font-size: 1.15rem !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.35) !important;
    }
    
    .stDownloadButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 14px 28px !important;
        width: 100%;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
    }

    /* Privacy Banner */
    .privacy-banner {
        background-color: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #6ee7b7;
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 0.95rem;
        margin-top: 16px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session State Initialization
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "playlist_info" not in st.session_state:
    st.session_state.playlist_info = None
if "download_history" not in st.session_state:
    st.session_state.download_history = []
if "active_downloads" not in st.session_state:
    st.session_state.active_downloads = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "out_dir": "output",
        "filename_tmpl": "{title} - {channel} [{quality}]",
        "concurrency": 2,
        "theme": "Dark Charcoal",
    }

# Sidebar Navigation
st.sidebar.markdown('<div class="sidebar-brand">◉ VideoFlow</div>', unsafe_allow_html=True)

nav_page = st.sidebar.radio(
    "Navigation Menu",
    options=[
        "➕ New Download",
        "📋 Batch & Playlist",
        "⬇️ Downloads & Queue",
        "📜 History",
        "⚙️ Settings",
        "ℹ️ Help / About",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='color: #64748b; font-size: 0.8rem; padding-left: 4px;'>
        🔒 <b>100% Local & Private</b><br>
        Your downloads stay on your device.
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# PAGE 1: ➕ NEW DOWNLOAD (Single URL)
# ==============================================================================
if nav_page == "➕ New Download":
    st.markdown(
        """
        <div class="hero-box">
            <div class="hero-title">Download your media</div>
            <div class="hero-subtitle">Fast, simple and organized • Original quality 4K & MP3 extraction</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # URL Input Box
    url_input = st.text_input(
        "Paste Video URL:",
        placeholder="https://www.youtube.com/watch?v=...",
        key="single_url_field",
    )

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        analyze_clicked = st.button("🔍 Analyze URL")
        st.markdown('</div>', unsafe_allow_html=True)

    if analyze_clicked or (url_input and st.session_state.video_info is None):
        if url_input.strip():
            with st.spinner("Analyzing media options..."):
                try:
                    info = get_video_info(url_input.strip())
                    st.session_state.video_info = info
                except Exception as e:
                    st.error(str(e))
                    st.session_state.video_info = None

    # Video Information Preview Card
    if st.session_state.video_info:
        info = st.session_state.video_info
        
        st.markdown('<div class="flow-card">', unsafe_allow_html=True)
        vcol1, vcol2 = st.columns([1, 2])
        
        with vcol1:
            if info.get("thumbnail"):
                st.image(info["thumbnail"], use_container_width=True)
                
        with vcol2:
            st.markdown(f"### {info['title']}")
            st.markdown(
                f"""
                <span class="vf-badge vf-badge-indigo">📺 {info['channel']}</span>
                <span class="vf-badge vf-badge-emerald">⏱️ {info['duration_str']}</span>
                <span class="vf-badge">📅 {info['upload_date']}</span>
                <span class="vf-badge">👁️ {info['view_count']:,} views</span>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Quality Selection Panel
        st.markdown("### ⚙️ Quality & Format Selection Panel")
        
        quality_options = info["quality_options"]
        
        # Display Choice Cards in Radio Selector
        choice_labels = [f"{q['label']} ({q['est_size']})" for q in quality_options]
        
        selected_choice = st.radio(
            "Available Formats:",
            options=choice_labels,
            index=0,
            help="Select 'Original / Best Quality' for maximum 4K/1080p stream resolution.",
        )
        
        selected_quality = next(
            (q for q, label in zip(quality_options, choice_labels) if label == selected_choice),
            quality_options[0],
        )

        st.write("") # spacing
        st.markdown('<div class="download-btn">', unsafe_allow_html=True)
        start_download = st.button("🚀 Download Media Now")
        st.markdown('</div>', unsafe_allow_html=True)

        if start_download:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def _progress_cb(d):
                if d.get("status") == "downloading":
                    pct = int(d.get("percent", 0))
                    progress_bar.progress(min(100, max(0, pct)))
                    stage = d.get("stream_label", "Downloading")
                    status_text.markdown(
                        f"**{stage}... {pct}%** ({d.get('speed_str', '')} • ETA: {d.get('eta_str', '')})"
                    )
                elif d.get("status") == "processing":
                    progress_bar.progress(100)
                    status_text.markdown("⏳ **Merging video & audio streams with FFmpeg...**")

            with st.spinner("Downloading media..."):
                try:
                    res = download_video(
                        video_url=info["url"],
                        quality_id=selected_quality["id"],
                        filename_template=st.session_state.settings["filename_tmpl"],
                        progress_callback=_progress_cb,
                        out_dir=st.session_state.settings["out_dir"],
                    )
                    status_text.success(f"✅ Download Completed! Saved: `{res['filename']}` ({res['file_size_str']})")
                    
                    # Add to History
                    st.session_state.download_history.insert(0, res)
                    
                    # File Delivery Button
                    if os.path.exists(res["file_path"]):
                        st.markdown("---")
                        with open(res["file_path"], "rb") as f:
                            file_bytes = f.read()
                        mime_type = "audio/mp3" if res["file_path"].endswith(".mp3") else "video/mp4"
                        st.download_button(
                            label=f"💾 Save {res['filename']} to Your Device ({res['file_size_str']})",
                            data=file_bytes,
                            file_name=res["filename"],
                            mime=mime_type,
                        )
                except Exception as e:
                    st.error(str(e))


# ==============================================================================
# PAGE 2: 📋 BATCH & PLAYLIST
# ==============================================================================
elif nav_page == "📋 Batch & Playlist":
    st.markdown("## 📋 Batch & Playlist Downloader")
    st.markdown("Download entire YouTube playlists or multiple video URLs at once.")
    
    playlist_url = st.text_input(
        "Enter Playlist or Multi-Video Link:",
        placeholder="https://www.youtube.com/playlist?list=...",
    )
    
    if st.button("🔍 Parse Playlist"):
        if playlist_url.strip():
            with st.spinner("Parsing playlist videos..."):
                try:
                    p_info = get_playlist_info(playlist_url.strip())
                    st.session_state.playlist_info = p_info
                except Exception as e:
                    st.error(str(e))
        else:
            st.warning("Please enter a playlist URL.")

    if st.session_state.playlist_info:
        p_info = st.session_state.playlist_info
        st.markdown(f"### 📺 {p_info['title']} ({p_info['video_count']} videos found)")
        
        # Select All Checkbox
        select_all = st.checkbox("☑ Select All Videos", value=True)
        
        selected_videos = []
        for v in p_info["videos"]:
            checked = st.checkbox(
                f"#{v['idx']} {v['title']} ({v['duration_str']}) — {v['channel']}",
                value=select_all,
                key=f"p_vid_{v['idx']}",
            )
            if checked:
                selected_videos.append(v)

        st.markdown(f"**{len(selected_videos)} videos selected for download.**")
        
        b_quality = st.selectbox(
            "Batch Download Quality:",
            options=["⭐ Original / Best Quality", "📺 1080p Full HD", "📺 720p HD", "🎵 MP3 Audio Only"],
            index=0,
        )
        
        if st.button("🚀 Download Selected Videos"):
            q_id = "original" if "Original" in b_quality else ("1080p" if "1080p" in b_quality else ("720p" if "720p" in b_quality else "mp3"))
            
            b_bar = st.progress(0)
            b_status = st.empty()
            
            total_vids = len(selected_videos)
            for i, vid in enumerate(selected_videos, 1):
                b_status.markdown(f"**Downloading video {i}/{total_vids}:** `{vid['title']}`")
                try:
                    res = download_video(
                        video_url=vid["url"],
                        quality_id=q_id,
                        filename_template=st.session_state.settings["filename_tmpl"],
                        out_dir=st.session_state.settings["out_dir"],
                    )
                    st.session_state.download_history.insert(0, res)
                except Exception as e:
                    st.error(f"Failed to download #{vid['idx']}: {e}")
                b_bar.progress(int(i / total_vids * 100))
                
            b_status.success(f"🎉 Batch Download Complete! {total_vids} videos processed.")


# ==============================================================================
# PAGE 3: ⬇️ DOWNLOADS & QUEUE
# ==============================================================================
elif nav_page == "⬇️ Downloads & Queue":
    st.markdown("## ⬇️ Active Downloads & Queue")
    
    if not st.session_state.download_history:
        st.info("No downloads currently in queue. Go to '➕ New Download' to start a media download!")
    else:
        st.markdown(f"### Recent Queue ({len(st.session_state.download_history)} items)")
        for item in st.session_state.download_history[:5]:
            st.markdown('<div class="flow-card">', unsafe_allow_html=True)
            st.markdown(f"#### ✅ {item['filename']}")
            st.markdown(
                f"""
                <span class="vf-badge vf-badge-emerald">Size: {item['file_size_str']}</span>
                <span class="vf-badge vf-badge-indigo">Quality: {item['quality']}</span>
                <span class="vf-badge">Downloaded: {item['timestamp']}</span>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# PAGE 4: 📜 HISTORY
# ==============================================================================
elif nav_page == "📜 History":
    st.markdown("## 📜 Download History")
    
    hcol1, hcol2 = st.columns([3, 1])
    with hcol2:
        if st.button("🗑️ Clear History"):
            st.session_state.download_history = []
            st.rerun()

    if not st.session_state.download_history:
        st.info("No download history recorded yet.")
    else:
        for idx, item in enumerate(st.session_state.download_history, 1):
            st.markdown('<div class="flow-card">', unsafe_allow_html=True)
            st.markdown(f"### #{idx} {item['title']}")
            st.markdown(
                f"""
                <span class="vf-badge vf-badge-indigo">📁 File: {item['filename']}</span>
                <span class="vf-badge vf-badge-emerald">📦 Size: {item['file_size_str']}</span>
                <span class="vf-badge">🕒 {item['timestamp']}</span>
                """,
                unsafe_allow_html=True,
            )
            
            if os.path.exists(item["file_path"]):
                st.write("")
                with open(item["file_path"], "rb") as f:
                    f_bytes = f.read()
                mime = "audio/mp3" if item["file_path"].endswith(".mp3") else "video/mp4"
                st.download_button(
                    label=f"💾 Save {item['filename']} ({item['file_size_str']})",
                    data=f_bytes,
                    file_name=item["filename"],
                    mime=mime,
                    key=f"hist_save_{idx}",
                )
            st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# PAGE 5: ⚙️ SETTINGS
# ==============================================================================
elif nav_page == "⚙️ Settings":
    st.markdown("## ⚙️ VideoFlow Settings")
    
    out_folder = st.text_input(
        "Download Location Folder:",
        value=st.session_state.settings["out_dir"],
        help="Local folder where downloads are saved on disk.",
    )
    
    fn_tmpl = st.text_input(
        "Smart Filename Template:",
        value=st.session_state.settings["filename_tmpl"],
        help="Template parameters: {title}, {channel}, {quality}",
    )
    
    conc = st.slider(
        "Max Simultaneous Downloads:",
        min_value=1,
        max_value=5,
        value=st.session_state.settings["concurrency"],
    )

    if st.button("💾 Save Settings"):
        st.session_state.settings["out_dir"] = out_folder
        st.session_state.settings["filename_tmpl"] = fn_tmpl
        st.session_state.settings["concurrency"] = conc
        st.success("Settings saved successfully!")


# ==============================================================================
# PAGE 6: ℹ️ HELP / ABOUT
# ==============================================================================
elif nav_page == "ℹ️ Help / About":
    st.markdown("## ℹ️ About VideoFlow")
    
    st.markdown(
        """
        <div class="privacy-banner">
            🔒 <b>Privacy Commitment: Your downloads stay on your device.</b><br>
            VideoFlow processes all media directly on your local machine using yt-dlp and FFmpeg.
            Zero telemetry, zero external tracking, and zero cloud uploads.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### Supported Features
        - **Original / Best Quality Downloads**: Fetches 4K, 2K, 1080p 60fps streams and merges audio seamlessly.
        - **MP3 / M4A Audio Extraction**: Lossless 320kbps audio conversion.
        - **Playlist & Batch Downloads**: Process entire playlists with individual video selection.
        - **Smart Filename Formatting**: Auto-sanitized template outputs (`{title} - {channel} [{quality}]`).

        ### Legal Guidance
        Please ensure you only download media that you have lawful authorization or copyright permissions to download.
        
        Developed & Maintained by **[@imomair1](https://github.com/imomair1)**.
        """
    )
