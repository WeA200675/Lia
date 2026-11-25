import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from openai import OpenAIError
from main import app, CHAT_SLOTS


class ProviderTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {
            "LIA_API_TOKEN": "test",
            "OPENAI_BASE_URL": "http://127.0.0.1:11434/v1",
            "LIA_MODEL": "test-model",
        }, clear=True)
        env.start()
        self.addCleanup(env.stop)
        provider = patch("main.OpenAI")
        self.factory = provider.start()
        self.addCleanup(provider.stop)
        self.create = self.factory.return_value.__enter__.return_value.chat.completions.create
        self.create.return_value = SimpleNamespace(choices=[
            SimpleNamespace(message=SimpleNamespace(content="Hallo!"))
        ])
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def chat(self):
        return self.client.post("/api/chat", headers={"Authorization": "Bearer test"},
                                json={"user_id": "test", "text_input": "Hallo"})

    def test_success_and_provider_configuration(self):
        response = self.chat()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "Hallo!"})
        self.factory.assert_called_once_with(
            api_key="local", base_url="http://127.0.0.1:11434/v1",
            timeout=15.0, max_retries=0)
        self.assertEqual(self.create.call_args.kwargs["model"], "test-model")
        self.assertEqual(self.create.call_args.kwargs["messages"][-1],
                         {"role": "user", "content": "Hallo"})

    def test_saturation_rejects_without_provider_call(self):
        acquired = 0
        try:
            for _ in range(4):
                self.assertTrue(CHAT_SLOTS.acquire(blocking=False))
                acquired += 1
            response = self.chat()
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["Retry-After"], "2")
            self.factory.assert_not_called()
        finally:
            for _ in range(acquired):
                CHAT_SLOTS.release()
        self.assertEqual(self.chat().status_code, 200)

    def test_provider_error_is_sanitized_and_slots_released(self):
        self.create.side_effect = OpenAIError("private provider detail")
        for _ in range(5):
            response = self.chat()
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private provider detail", response.text)
        self.create.side_effect = None
        self.assertEqual(self.chat().status_code, 200)

    def test_empty_response_releases_slots(self):
        self.create.return_value = SimpleNamespace(choices=[])
        for _ in range(5):
            self.assertEqual(self.chat().status_code, 502)
        self.create.return_value = SimpleNamespace(choices=[
            SimpleNamespace(message=SimpleNamespace(content="Recovered"))
        ])
        self.assertEqual(self.chat().status_code, 200)
