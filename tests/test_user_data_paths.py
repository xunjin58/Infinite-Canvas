import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class UserDataPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.user_data = self.root / "user-data"
        self.legacy = self.root / "legacy-project"
        self.legacy.mkdir()
        self.user_data.mkdir()
        self.patches = [
            patch.object(main, "USER_DATA_DIR", str(self.user_data)),
            patch.object(main, "DATA_DIR", str(self.user_data / "data")),
            patch.object(main, "ASSETS_DIR", str(self.user_data / "assets")),
            patch.object(main, "OUTPUT_DIR", str(self.user_data / "output")),
            patch.object(main, "OUTPUT_INPUT_DIR", str(self.user_data / "assets" / "input")),
            patch.object(main, "OUTPUT_OUTPUT_DIR", str(self.user_data / "assets" / "output")),
            patch.object(main, "ASSET_LIBRARY_DIR", str(self.user_data / "assets" / "library")),
            patch.object(main, "LOCAL_UPLOAD_DIR", str(self.user_data / "assets" / "uploads")),
            patch.object(main, "CONVERSATION_DIR", str(self.user_data / "data" / "conversations")),
            patch.object(main, "CANVAS_DIR", str(self.user_data / "data" / "canvases")),
            patch.object(main, "MEDIA_PREVIEW_DIR", str(self.user_data / "data" / "media_previews")),
            patch.object(main, "USER_WORKFLOW_DIR", str(self.user_data / "workflows")),
            patch.object(main, "API_ENV_FILE", str(self.user_data / "API" / ".env")),
            patch.object(main, "STATIC_RUNNINGHUB_API_PROVIDERS_FILE", str(self.user_data / "data" / "runninghub_static_provider.json")),
        ]
        for item in self.patches:
            item.start()
        main.ensure_user_data_layout()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_override_selects_explicit_user_data_root(self):
        with patch.dict(os.environ, {"INFINITE_CANVAS_DATA_DIR": str(self.root / "override")}, clear=False):
            self.assertEqual(main.default_user_data_dir(), os.path.abspath(str(self.root / "override")))

    def test_import_copies_legacy_data_without_modifying_source(self):
        (self.legacy / "data" / "canvases").mkdir(parents=True)
        (self.legacy / "data" / "canvases" / "canvas.json").write_text("{}", encoding="utf-8")
        (self.legacy / "assets" / "output").mkdir(parents=True)
        (self.legacy / "assets" / "output" / "result.png").write_bytes(b"image")
        (self.legacy / "API").mkdir()
        (self.legacy / "API" / ".env").write_text("TOKEN=old\n", encoding="utf-8")
        (self.legacy / "static" / "runninghub").mkdir(parents=True)
        (self.legacy / "static" / "runninghub" / "api_providers.json").write_text("[]", encoding="utf-8")
        (self.user_data / "history.json").write_text("[\"current\"]", encoding="utf-8")

        result = main.import_legacy_user_data(str(self.legacy))

        self.assertTrue(result["ok"])
        self.assertEqual(
            (self.user_data / "data" / "canvases" / "canvas.json").read_text(encoding="utf-8"),
            "{}",
        )
        self.assertEqual((self.user_data / "API" / ".env").read_text(encoding="utf-8"), "TOKEN=old\n")
        self.assertEqual((self.user_data / "data" / "runninghub_static_provider.json").read_text(encoding="utf-8"), "[]")
        self.assertTrue((self.legacy / "assets" / "output" / "result.png").exists())
        self.assertTrue(Path(result["backup_dir"]).joinpath("history.json").exists())

    def test_builtin_workflows_stay_in_resource_directory(self):
        self.assertEqual(
            main.workflow_path_from_name("Z-Image.json"),
            str(Path(main.RESOURCE_WORKFLOW_DIR, "Z-Image.json").resolve()),
        )

    def test_custom_workflows_use_user_directory(self):
        self.assertEqual(
            main.workflow_path_from_name("custom/demo.json"),
            os.path.abspath(str(self.user_data / "workflows" / "custom" / "demo.json")),
        )

    def test_windowed_package_disables_uvicorn_default_logging(self):
        with patch("uvicorn.run") as run, patch.object(main, "RUNNING_FROZEN", True):
            main.run_server()
        self.assertIsNone(run.call_args.kwargs["log_config"])
        self.assertFalse(run.call_args.kwargs["access_log"])

    def test_missing_stderr_disables_uvicorn_default_logging(self):
        with patch("uvicorn.run") as run, patch.object(main, "RUNNING_FROZEN", False), patch.object(main.sys, "stderr", None):
            main.run_server()
        self.assertIsNone(run.call_args.kwargs["log_config"])
        self.assertFalse(run.call_args.kwargs["access_log"])
