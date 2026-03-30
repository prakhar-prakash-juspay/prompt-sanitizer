import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response
from fastapi.testclient import TestClient

from aegis.config import AegisConfig, ProviderConfig, DetectionConfig, LoggingConfig
from aegis.proxy.app import create_app


@pytest.fixture
def config(tmp_audit_log, tmp_empty_allowlist):
    return AegisConfig(
        port=8443,
        viewer_port=8444,
        providers={
            "anthropic": ProviderConfig(upstream="https://api.anthropic.com"),
            "openai": ProviderConfig(upstream="https://api.openai.com"),
        },
        detection=DetectionConfig(secrets=True, pii=True),
        logging=LoggingConfig(
            audit_file=str(tmp_audit_log),
            log_original_values=True,
            store_request_body=True,
            store_response_body=True,
        ),
    )


@pytest.fixture
def app(config, tmp_empty_allowlist):
    return create_app(config, allowlist_path=tmp_empty_allowlist)


@pytest.fixture
def client(app):
    return TestClient(app)


class TestProxyRouter:
    def test_unknown_provider_returns_404(self, client):
        resp = client.post("/unknown/v1/messages", json={"messages": []})
        assert resp.status_code == 404

    def test_proxies_request_to_upstream(self, client):
        mock_response = Response(
            200,
            json={"content": [{"text": "Hello"}]},
            headers={"content-type": "application/json"},
        )
        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response):
            resp = client.post(
                "/anthropic/v1/messages",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
            )
            assert resp.status_code == 200
            assert resp.json()["content"][0]["text"] == "Hello"

    def test_redacts_secrets_in_request(self, client, tmp_audit_log):
        mock_response = Response(
            200,
            json={"content": [{"text": "noted"}]},
            headers={"content-type": "application/json"},
        )
        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            resp = client.post(
                "/anthropic/v1/messages",
                json={"messages": [{"role": "user", "content": "My key is AKIAIOSFODNN7EXAMPLE"}]},
                headers={"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
            )
            assert resp.status_code == 200
            sent_request = mock_send.call_args[0][0]
            sent_body = json.loads(sent_request.content)
            assert "AKIAIOSFODNN7EXAMPLE" not in json.dumps(sent_body)
            assert "[REDACTED:AWS_KEY:" in json.dumps(sent_body)

    def test_audit_log_written(self, client, tmp_audit_log):
        mock_response = Response(
            200,
            json={"content": [{"text": "ok"}]},
            headers={"content-type": "application/json"},
        )
        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response):
            client.post(
                "/anthropic/v1/messages",
                json={"messages": [{"role": "user", "content": "hello"}]},
                headers={"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
            )
        log_content = tmp_audit_log.read_text().strip()
        assert len(log_content) > 0
        entry = json.loads(log_content)
        assert entry["provider"] == "anthropic"

    def test_forwards_auth_header(self, client):
        mock_response = Response(
            200,
            json={"content": [{"text": "ok"}]},
            headers={"content-type": "application/json"},
        )
        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            client.post(
                "/anthropic/v1/messages",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={"Authorization": "Bearer sk-test-key-123", "Content-Type": "application/json"},
            )
            sent_request = mock_send.call_args[0][0]
            assert sent_request.headers["authorization"] == "Bearer sk-test-key-123"
