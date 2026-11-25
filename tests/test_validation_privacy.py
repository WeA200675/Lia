import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app


class ValidationPrivacyTests(unittest.TestCase):
    def test_invalid_requests_do_not_echo_input(self):
        marker = "private-conversation-marker"
        headers = {"Authorization": "Bearer test"}
        with patch.dict(os.environ, {"LIA_API_TOKEN": "test"}, clear=True):
            with TestClient(app) as client:
                for payload in (
                    {"user_id": "test", "text_input": {"private": marker}},
                    {"user_id": "test", "text_input": "x" * 4001 + marker},
                    {"user_id": "test", "text_input": "hello",
                     "history": [{"role": "system", "content": marker}]},
                ):
                    with self.subTest(payload_type=type(payload["text_input"])):
                        response = client.post("/api/chat", json=payload, headers=headers)
                        self.assertEqual(response.status_code, 422)
                        self.assertEqual(response.json(), {"detail": "Ungültige Anfrage"})
                        self.assertNotIn(marker, response.text)
                response = client.post("/api/chat", content='{"' + marker,
                                       headers={**headers, "Content-Type": "application/json"})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn(marker, response.text)
