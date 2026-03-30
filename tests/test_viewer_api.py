import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from aegis.viewer.api import create_viewer_router
from aegis.audit.reader import AuditReader
from aegis.detection.allowlist import Allowlist


@pytest.fixture
def viewer_app(tmp_audit_log, tmp_allowlist_file):
    entries = [
        {"timestamp": "2026-03-30T10:00:00Z", "request_id": "req_001", "provider": "anthropic", "endpoint": "/v1/messages", "request_body": {"messages": [{"content": "[REDACTED:AWS_KEY:a1b2c3]"}]}, "response_body": {"content": [{"text": "ok"}]}, "redactions": [{"type": "AWS_KEY", "placeholder": "[REDACTED:AWS_KEY:a1b2c3]", "original": "AKIA1234"}]},
        {"timestamp": "2026-03-30T10:01:00Z", "request_id": "req_002", "provider": "openai", "endpoint": "/v1/chat/completions", "request_body": {}, "response_body": {}, "redactions": []},
    ]
    with open(tmp_audit_log, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    app = FastAPI()
    reader = AuditReader(tmp_audit_log)
    allowlist = Allowlist(tmp_allowlist_file)
    router = create_viewer_router(reader, allowlist)
    app.include_router(router)
    return app


@pytest.fixture
def client(viewer_app):
    return TestClient(viewer_app)


class TestViewerAPI:
    def test_list_entries(self, client):
        resp = client.get("/api/entries")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["request_id"] == "req_002"

    def test_list_entries_filter_provider(self, client):
        resp = client.get("/api/entries?provider=anthropic")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["provider"] == "anthropic"

    def test_get_entry_by_id(self, client):
        resp = client.get("/api/entries/req_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "anthropic"
        assert "request_body" in data
        assert "response_body" in data

    def test_get_entry_not_found(self, client):
        resp = client.get("/api/entries/req_999")
        assert resp.status_code == 404

    def test_summary(self, client):
        resp = client.get("/api/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_requests"] == 2
        assert data["total_redactions"] == 1

    def test_reveal_original(self, client):
        resp = client.get("/api/entries/req_001/reveal/[REDACTED:AWS_KEY:a1b2c3]")
        assert resp.status_code == 200
        data = resp.json()
        assert data["original"] == "AKIA1234"

    def test_add_to_allowlist(self, client):
        resp = client.post("/api/allowlist", json={"value": "AKIA1234", "reason": "test key"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "added"
