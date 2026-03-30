import json
import pytest
from pathlib import Path
from aegis.audit.logger import AuditLogger, AuditEntry


class TestAuditLogger:
    @pytest.fixture
    def logger(self, tmp_audit_log):
        return AuditLogger(tmp_audit_log)

    def test_writes_json_lines(self, logger, tmp_audit_log):
        entry = AuditEntry(
            provider="anthropic",
            endpoint="/v1/messages",
            request_body={"messages": [{"role": "user", "content": "hello"}]},
            response_body={"content": [{"text": "hi"}]},
            redactions=[
                {"type": "AWS_KEY", "placeholder": "[REDACTED:AWS_KEY:a1b2c3]", "original": "AKIA...", "location": "messages[0].content"}
            ],
        )
        logger.log(entry)

        lines = tmp_audit_log.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["provider"] == "anthropic"
        assert data["endpoint"] == "/v1/messages"
        assert len(data["redactions"]) == 1

    def test_includes_timestamp_and_request_id(self, logger, tmp_audit_log):
        entry = AuditEntry(
            provider="openai",
            endpoint="/v1/chat/completions",
            request_body={},
            response_body={},
            redactions=[],
        )
        logger.log(entry)

        data = json.loads(tmp_audit_log.read_text().strip())
        assert "timestamp" in data
        assert "request_id" in data
        assert data["request_id"].startswith("req_")

    def test_appends_multiple_entries(self, logger, tmp_audit_log):
        for i in range(3):
            entry = AuditEntry(
                provider="anthropic",
                endpoint="/v1/messages",
                request_body={"i": i},
                response_body={},
                redactions=[],
            )
            logger.log(entry)

        lines = tmp_audit_log.read_text().strip().split("\n")
        assert len(lines) == 3

    def test_stores_request_and_response_body(self, logger, tmp_audit_log):
        req = {"messages": [{"role": "user", "content": "[REDACTED:EMAIL:abc123]"}]}
        resp = {"content": [{"text": "I see a redacted email"}]}
        entry = AuditEntry(
            provider="anthropic",
            endpoint="/v1/messages",
            request_body=req,
            response_body=resp,
            redactions=[],
        )
        logger.log(entry)

        data = json.loads(tmp_audit_log.read_text().strip())
        assert data["request_body"] == req
        assert data["response_body"] == resp
