import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class ApiProviderModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.providers_file = root / "data" / "api_providers.json"
        self.providers_file.parent.mkdir(parents=True)
        self.env_file = root / "API" / ".env"
        self.patches = [
            patch.object(main, "API_PROVIDERS_FILE", str(self.providers_file)),
            patch.object(main, "API_ENV_FILE", str(self.env_file)),
        ]
        for item in self.patches:
            item.start()
        self.environment = patch.dict(os.environ, {}, clear=False)
        self.environment.start()
        os.environ.pop("API_SETTINGS_ADVANCED", None)
        os.environ.pop(main.provider_key_env(main.CUSTOMER_API_PROVIDER_ID), None)

    def tearDown(self):
        self.environment.stop()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_customer_mode_only_exposes_fixed_provider(self):
        response = asyncio.run(main.api_providers())
        self.assertEqual(response["mode"], "simple")
        providers = response["providers"]

        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]["id"], "custom-api")
        self.assertEqual(providers[0]["base_url"], "https://mid.aiturn.top")
        self.assertEqual(providers[0]["image_models"], ["gpt-image-2"])
        self.assertEqual(providers[0]["chat_models"], ["gpt-5.6-terra"])
        self.assertEqual(providers[0]["video_models"], [])

        config = asyncio.run(main.ai_config())
        self.assertEqual(config["api_settings_mode"], "simple")
        self.assertEqual(config["image_models"], ["gpt-image-2"])
        self.assertEqual(config["chat_models"], ["gpt-5.6-terra"])
        self.assertEqual(config["video_models"], [])

    def test_customer_mode_falls_back_to_fixed_provider_and_rejects_exact_legacy_id(self):
        self.assertEqual(main.get_api_provider("modelscope")["id"], "custom-api")
        os.environ[main.provider_key_env(main.CUSTOMER_API_PROVIDER_ID)] = "test-key"
        chat_base, _, chat_model = main.resolve_chat_provider("modelscope", "", "")
        self.assertEqual(chat_base, "https://mid.aiturn.top/v1")
        self.assertEqual(chat_model, "gpt-5.6-terra")
        with self.assertRaises(main.HTTPException) as error:
            main.get_api_provider_exact("runninghub")
        self.assertEqual(error.exception.status_code, 400)

    def test_customer_mode_disables_modelscope_only_routes(self):
        with self.assertRaises(main.HTTPException) as error:
            asyncio.run(main.get_global_token())
        self.assertEqual(error.exception.status_code, 404)

        with self.assertRaises(main.HTTPException) as error:
            asyncio.run(main.generate_cloud(None))
        self.assertEqual(error.exception.status_code, 404)

    def test_customer_key_save_keeps_advanced_configuration_file(self):
        legacy = [{
            "id": "aihub",
            "name": "aihub",
            "base_url": "https://aihub.example/v1",
            "protocol": "openai",
            "image_models": ["legacy-image"],
            "chat_models": ["legacy-chat"],
            "video_models": [],
        }]
        original = json.dumps(legacy, ensure_ascii=False)
        self.providers_file.write_text(original, encoding="utf-8")

        result = asyncio.run(main.save_providers([
            main.ApiProviderPayload(id="custom-api", api_key="test-secret-key")
        ]))

        self.assertEqual(self.providers_file.read_text(encoding="utf-8"), original)
        self.assertTrue(result["providers"][0]["has_key"])
        self.assertEqual(result["providers"][0]["key_preview"], "••••••••-key")
        self.assertEqual(main.provider_env_key_value("custom-api"), "test-secret-key")

    def test_customer_mode_rejects_fixed_configuration_changes(self):
        payload = main.ApiProviderPayload(
            id="custom-api",
            base_url="https://other.example/v1",
        )

        with self.assertRaises(main.HTTPException) as error:
            asyncio.run(main.save_providers([payload]))

        self.assertEqual(error.exception.status_code, 400)

    def test_advanced_mode_retains_multi_provider_runtime(self):
        self.providers_file.write_text(json.dumps([{
            "id": "aihub",
            "name": "aihub",
            "base_url": "https://aihub.example/v1",
            "protocol": "openai",
            "image_models": ["legacy-image"],
            "chat_models": ["legacy-chat"],
            "video_models": [],
        }]), encoding="utf-8")

        with patch.dict(os.environ, {"API_SETTINGS_ADVANCED": "1"}, clear=False):
            providers = main.runtime_api_providers()

        self.assertTrue(any(provider["id"] == "aihub" for provider in providers))
