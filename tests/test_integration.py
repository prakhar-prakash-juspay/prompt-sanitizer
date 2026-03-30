import json
import pytest
from unittest.mock import AsyncMock, patch
from httpx import Response
from fastapi.testclient import TestClient

from aegis.config import AegisConfig, ProviderConfig, DetectionConfig, LoggingConfig
from aegis.proxy.app import create_app


@pytest.fixture
def full_app(tmp_audit_log, tmp_aegis_dir):
    allowlist_path = tmp_aegis_dir / "allowlist.yaml"
    allowlist_path.write_text("allowed: []\n")

    config = AegisConfig(
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
    return create_app(config, allowlist_path=allowlist_path)


@pytest.fixture
def client(full_app):
    return TestClient(full_app)


class TestEndToEnd:
    def test_secrets_redacted_pii_redacted_audit_written(self, client, tmp_audit_log):
        """Full flow: request with secrets + PII -> redacted -> forwarded -> logged."""
        mock_response = Response(
            200,
            json={"content": [{"text": "I see some credentials and an email."}]},
            headers={"content-type": "application/json"},
        )
        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            resp = client.post(
                "/anthropic/v1/messages",
                json={
                    "messages": [{
                        "role": "user",
                        "content": "My AWS key is AKIAIOSFODNN7EXAMPLE and my email is john.doe@example.com. DB is at postgresql://admin:secret@prod-db.internal:5432/myapp"
                    }]
                },
                headers={"Authorization": "Bearer sk-ant-test123", "Content-Type": "application/json"},
            )

        # 1. Response came back successfully
        assert resp.status_code == 200

        # 2. Upstream request had secrets redacted
        sent_request = mock_send.call_args[0][0]
        sent_body_str = sent_request.content.decode()
        assert "AKIAIOSFODNN7EXAMPLE" not in sent_body_str
        assert "john.doe@example.com" not in sent_body_str
        assert "postgresql://admin:secret@prod-db.internal:5432/myapp" not in sent_body_str
        assert "[REDACTED:" in sent_body_str

        # 3. Auth header was forwarded as-is
        assert sent_request.headers["authorization"] == "Bearer sk-ant-test123"

        # 4. Audit log was written
        log_lines = tmp_audit_log.read_text().strip().split("\n")
        assert len(log_lines) == 1
        audit = json.loads(log_lines[0])
        assert audit["provider"] == "anthropic"
        assert len(audit["redactions"]) >= 2
        redaction_types = {r["type"] for r in audit["redactions"]}
        assert "AWS_KEY" in redaction_types

        # 5. Original values stored in audit for lookup
        originals = {r["original"] for r in audit["redactions"]}
        assert "AKIAIOSFODNN7EXAMPLE" in originals

    def test_clean_request_passes_through(self, client, tmp_audit_log):
        """Request with no sensitive data passes through untouched."""
        mock_response = Response(
            200,
            json={"content": [{"text": "Hello!"}]},
            headers={"content-type": "application/json"},
        )
        with patch("aegis.proxy.router.httpx.AsyncClient.send", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            resp = client.post(
                "/anthropic/v1/messages",
                json={"messages": [{"role": "user", "content": "What is 2+2?"}]},
                headers={"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
            )

        assert resp.status_code == 200
        sent_body = json.loads(mock_send.call_args[0][0].content)
        assert sent_body["messages"][0]["content"] == "What is 2+2?"

        audit = json.loads(tmp_audit_log.read_text().strip())
        assert len(audit["redactions"]) == 0

    def test_health_endpoint(self, client):
        # Note: health endpoint needs to exist on the app
        # This test verifies the proxy app returns something for health
        resp = client.get("/health")
        # If health endpoint exists, should be 200
        # If not, this will flag it as needing to be added
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
