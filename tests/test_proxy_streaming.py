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


class TestStreamingProxy:
    def test_streaming_request_returns_sse(self, client):
        async def mock_stream():
            chunks = [
                b'data: {"type":"content_block_delta","delta":{"text":"Hello"}}\n\n',
                b'data: {"type":"content_block_delta","delta":{"text":" world"}}\n\n',
                b'data: [DONE]\n\n',
            ]
            for chunk in chunks:
                yield chunk

        mock_response = Response(
            200,
            headers={"content-type": "text/event-stream"},
        )
        mock_response.stream = MagicMock()
        mock_response.stream.aiter_bytes = mock_stream
        mock_response.aclose = AsyncMock()

        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response):
            resp = client.post(
                "/anthropic/v1/messages",
                json={"messages": [{"role": "user", "content": "hi"}], "stream": True},
                headers={"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
            )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_streaming_redacts_request_body(self, client, tmp_audit_log):
        async def mock_stream():
            yield b'data: {"type":"content_block_delta","delta":{"text":"ok"}}\n\n'
            yield b'data: [DONE]\n\n'

        mock_response = Response(
            200,
            headers={"content-type": "text/event-stream"},
        )
        mock_response.stream = MagicMock()
        mock_response.stream.aiter_bytes = mock_stream
        mock_response.aclose = AsyncMock()

        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            resp = client.post(
                "/anthropic/v1/messages",
                json={"messages": [{"role": "user", "content": "Key AKIAIOSFODNN7EXAMPLE"}], "stream": True},
                headers={"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
            )
            sent_request = mock_send.call_args[0][0]
            sent_body = json.loads(sent_request.content)
            assert "AKIAIOSFODNN7EXAMPLE" not in json.dumps(sent_body)
