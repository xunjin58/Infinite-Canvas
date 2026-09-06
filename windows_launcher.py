"""PyInstaller entry point for the Windows one-file desktop application."""
import threading
import time
import urllib.request
import webbrowser

import main


def open_browser_when_ready() -> None:
    url = "http://127.0.0.1:3000/"
    for _ in range(80):
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                webbrowser.open(url)
                return
        except Exception:
            time.sleep(0.25)


if __name__ == "__main__":
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    main.run_server()
