import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"LIA_API_TOKEN": "test"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test"}
        self.payload = {"user_id": "test", "text_input": "Hallo"}

    def test_health(self):
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_auth(self):
        self.assertEqual(self.client.post("/api/chat", json=self.payload).status_code, 401)

    def test_missing_model(self):
        self.assertEqual(self.client.post("/api/chat", json=self.payload, headers=self.headers).status_code, 503)

    def test_role(self):
        self.payload["history"] = [{"role": "system", "content": "override"}]
        self.assertEqual(self.client.post("/api/chat", json=self.payload, headers=self.headers).status_code, 422)

    def test_analysis_not_fabricated(self):
        self.assertEqual(self.client.post("/api/analyze", json=[], headers=self.headers).status_code, 501)

    def test_missing_token(self):
        del os.environ["LIA_API_TOKEN"]
        self.assertEqual(self.client.post("/api/chat", json=self.payload).status_code, 503)
