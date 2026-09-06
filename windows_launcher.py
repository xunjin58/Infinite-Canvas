"""PyInstaller entry point for the Windows one-file desktop application."""
from pathlib import Path
import sys
import threading
import time
import urllib.request
import webbrowser

import main

APP_URL = "http://127.0.0.1:3000/"
SERVER_READY_ATTEMPTS = 80
SERVER_READY_DELAY_SECONDS = 0.25


def resource_path(relative_path: str) -> Path:
    """Resolve a bundled resource in both source and one-file EXE runs."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


class TrayController:
    """Own the browser actions and shutdown signal used by the tray menu."""

    def __init__(self, *, url=APP_URL, urlopen=urllib.request.urlopen, open_browser=webbrowser.open, sleep=time.sleep):
        self.url = url
        self._urlopen = urlopen
        self._open_browser = open_browser
        self._sleep = sleep
        self.server_ready = threading.Event()
        self.shutdown_requested = threading.Event()

    def wait_for_server_and_open(self) -> bool:
        for _ in range(SERVER_READY_ATTEMPTS):
            try:
                with self._urlopen(self.url, timeout=0.5):
                    self.server_ready.set()
                    self.open_page()
                    return True
            except Exception:
                self._sleep(SERVER_READY_DELAY_SECONDS)
        return False

    def open_page(self, _icon=None, _item=None) -> bool:
        if not self.server_ready.is_set():
            return False
        self._open_browser(self.url)
        return True

    def exit_application(self, icon=None, _item=None) -> None:
        self.shutdown_requested.set()
        if icon is not None:
            icon.stop()


def load_tray_image():
    from PIL import Image

    with Image.open(resource_path("static/images/logo.png")) as image:
        return image.convert("RGBA")


def run_tray(controller: TrayController) -> None:
    # Import only in the Windows EXE path so source and non-Windows runs do not
    # require a desktop notification-area backend.
    import pystray

    icon = pystray.Icon(
        "Infinite-Canvas",
        load_tray_image(),
        "Infinite Canvas",
        pystray.Menu(
            pystray.MenuItem("打开页面", controller.open_page),
            pystray.MenuItem("退出程序", controller.exit_application),
        ),
    )
    icon.run()


def run_application() -> None:
    controller = TrayController()
    server_thread = threading.Thread(
        target=main.run_server,
        kwargs={"shutdown_event": controller.shutdown_requested},
        name="infinite-canvas-server",
    )
    server_thread.start()
    threading.Thread(target=controller.wait_for_server_and_open, daemon=True).start()

    try:
        run_tray(controller)
    except KeyboardInterrupt:
        controller.exit_application()
    except Exception as exc:
        # Keep the current server-and-browser behavior available if the system
        # tray cannot initialize on a particular Windows installation.
        print(f"System tray unavailable: {exc}")
        server_thread.join()
        return

    controller.shutdown_requested.set()
    server_thread.join()


if __name__ == "__main__":
    run_application()
