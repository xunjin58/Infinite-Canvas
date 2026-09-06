import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main
import windows_launcher


class TrayControllerTests(unittest.TestCase):
    def test_open_page_waits_until_server_is_ready(self):
        open_browser = Mock()
        controller = windows_launcher.TrayController(open_browser=open_browser)

        self.assertFalse(controller.open_page())
        open_browser.assert_not_called()

        controller.server_ready.set()
        self.assertTrue(controller.open_page())
        open_browser.assert_called_once_with(windows_launcher.APP_URL)

    def test_ready_probe_opens_browser_and_marks_server_ready(self):
        open_browser = Mock()
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        controller = windows_launcher.TrayController(
            urlopen=Mock(return_value=response),
            open_browser=open_browser,
            sleep=Mock(),
        )

        self.assertTrue(controller.wait_for_server_and_open())
        self.assertTrue(controller.server_ready.is_set())
        open_browser.assert_called_once_with(windows_launcher.APP_URL)

    def test_exit_requests_shutdown_and_stops_tray_icon(self):
        controller = windows_launcher.TrayController()
        icon = Mock()

        controller.exit_application(icon)

        self.assertTrue(controller.shutdown_requested.is_set())
        icon.stop.assert_called_once_with()


class ServerShutdownTests(unittest.TestCase):
    def test_run_server_honors_shutdown_event(self):
        shutdown_event = threading.Event()
        server_started = threading.Event()

        def server_run():
            server_started.set()
            shutdown_event.wait(timeout=1)

        server = SimpleNamespace(should_exit=False, run=server_run)
        with patch("uvicorn.Config"), patch("uvicorn.Server", return_value=server):
            thread = threading.Thread(target=main.run_server, kwargs={"shutdown_event": shutdown_event})
            thread.start()
            self.assertTrue(server_started.wait(timeout=1))
            shutdown_event.set()
            thread.join(timeout=1)

        self.assertFalse(thread.is_alive())
        self.assertTrue(server.should_exit)
