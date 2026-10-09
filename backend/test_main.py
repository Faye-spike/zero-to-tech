"""接口测试使用内存中的模型响应，不联网、不消耗 API 额度。"""

import json
import os
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from openai import OpenAI

import main


class AnalyzeAPITests(unittest.TestCase):
    def setUp(self):
        self.api = TestClient(main.app)

    def tearDown(self):
        self.api.close()

    def post_with_model(self, payload, *, status=200):
        def handle(request):
            if status != 200:
                return httpx.Response(status, json={"error": {"message": "upstream error"}})
            body = json.loads(request.content)
            self.assertEqual(body["response_format"], {"type": "json_object"})
            self.assertEqual(json.loads(body["messages"][1]["content"])["text"], "今天真开心")
            return httpx.Response(200, json={
                "id": "test-completion",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [{
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": json.dumps(payload)},
                }],
            })

        client = OpenAI(
            api_key="test-only-key",
            http_client=httpx.Client(transport=httpx.MockTransport(handle)),
            max_retries=0,
        )
        with patch("main.create_client", return_value=(client, "test-model", {})):
            return self.api.post("/api/analyze", json={"text": "今天真开心"})

    def test_real_parser_and_score_conversion(self):
        response = self.post_with_model({
            "label": "positive", "score": 75,
            "reason": "作者表达了开心。", "evidence": ["开心"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "text": "今天真开心", "score": 0.75, "label": "positive",
            "reason": "作者表达了开心。", "evidence": ["开心"],
            "pinyin": "jīn tiān zhēn kāi xīn",
        })

    def test_zero_and_unknown_scores(self):
        for label, score in [("negative", 0), ("uncertain", None)]:
            with self.subTest(label=label):
                response = self.post_with_model({
                    "label": label, "score": score, "reason": "测试", "evidence": [],
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["score"], score)

    def test_empty_input_does_not_call_model(self):
        with patch("main.create_client") as factory:
            response = self.api.post("/api/analyze", json={"text": "  "})
        self.assertEqual(response.status_code, 400)
        factory.assert_not_called()

    def test_missing_key_is_actionable(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "deepseek"}, clear=True):
            response = self.api.post("/api/analyze", json={"text": "今天真开心"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("DEEPSEEK_API_KEY", response.json()["detail"])

    def test_invalid_evidence_or_score_is_rejected(self):
        for score, evidence in [(75, ["不存在的原文"]), (25, ["开心"])]:
            with self.subTest(score=score):
                response = self.post_with_model({
                    "label": "positive", "score": score,
                    "reason": "测试", "evidence": evidence,
                })
                self.assertEqual(response.status_code, 502)

    def test_provider_errors_do_not_expose_upstream_body(self):
        for status, expected in [(401, 502), (429, 503), (500, 502)]:
            with self.subTest(status=status):
                response = self.post_with_model({}, status=status)
                self.assertEqual(response.status_code, expected)
                self.assertNotIn("upstream error", response.text)

    def test_timeout(self):
        def timeout(request):
            raise httpx.ReadTimeout("upstream timeout", request=request)

        client = OpenAI(
            api_key="test-only-key", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(timeout)),
        )
        with patch("main.create_client", return_value=(client, "test-model", {})):
            response = self.api.post("/api/analyze", json={"text": "今天真开心"})
        self.assertEqual(response.status_code, 504)

    def test_profile_still_works_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.api.get("/api/profile")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
