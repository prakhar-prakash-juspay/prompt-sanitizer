import json
import pytest
from aegis.audit.reader import AuditReader


class TestAuditReader:
    @pytest.fixture
    def reader_with_data(self, tmp_audit_log):
        entries = [
            {"timestamp": "2026-03-30T10:00:00Z", "request_id": "req_001", "provider": "anthropic", "endpoint": "/v1/messages", "request_body": {}, "response_body": {}, "redactions": [{"type": "AWS_KEY", "placeholder": "[REDACTED:AWS_KEY:a1b2c3]", "original": "AKIA..."}]},
            {"timestamp": "2026-03-30T10:01:00Z", "request_id": "req_002", "provider": "openai", "endpoint": "/v1/chat/completions", "request_body": {}, "response_body": {}, "redactions": []},
            {"timestamp": "2026-03-30T10:02:00Z", "request_id": "req_003", "provider": "anthropic", "endpoint": "/v1/messages", "request_body": {}, "response_body": {}, "redactions": [{"type": "EMAIL_ADDRESS", "placeholder": "[REDACTED:EMAIL:d4e5f6]", "original": "john@example.com"}]},
        ]
        with open(tmp_audit_log, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        return AuditReader(tmp_audit_log)

    def test_list_all_entries(self, reader_with_data):
        entries = reader_with_data.list_entries()
        assert len(entries) == 3

    def test_list_entries_reverse_chronological(self, reader_with_data):
        entries = reader_with_data.list_entries()
        assert entries[0]["request_id"] == "req_003"
        assert entries[2]["request_id"] == "req_001"

    def test_filter_by_provider(self, reader_with_data):
        entries = reader_with_data.list_entries(provider="anthropic")
        assert len(entries) == 2
        assert all(e["provider"] == "anthropic" for e in entries)

    def test_get_entry_by_id(self, reader_with_data):
        entry = reader_with_data.get_entry("req_002")
        assert entry is not None
        assert entry["provider"] == "openai"

    def test_get_entry_missing_returns_none(self, reader_with_data):
        entry = reader_with_data.get_entry("req_999")
        assert entry is None

    def test_summary_stats(self, reader_with_data):
        stats = reader_with_data.summary()
        assert stats["total_requests"] == 3
        assert stats["total_redactions"] == 2
        assert stats["redactions_by_type"]["AWS_KEY"] == 1
        assert stats["redactions_by_type"]["EMAIL_ADDRESS"] == 1

    def test_empty_log(self, tmp_audit_log):
        tmp_audit_log.write_text("")
        reader = AuditReader(tmp_audit_log)
        assert reader.list_entries() == []
        assert reader.summary()["total_requests"] == 0
