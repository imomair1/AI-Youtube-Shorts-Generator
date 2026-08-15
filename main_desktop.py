"""FuseGrab — Standalone Native Windows PC Desktop Software Application.

Launches native desktop app window using pywebview and Edge WebView2 backend.
"""
import os
import sys
import webview

from desktop_backend import FuseGrabApi


def main():
    api = FuseGrabApi()
    gui_file = os.path.join(os.path.dirname(__file__), "fusegrab_gui.html")
    
    window = webview.create_window(
        title="Vidora",
        url=gui_file,
        js_api=api,
        width=1280,
        height=820,
        resizable=True,
        min_size=(960, 600),
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
