import json
from collections import Counter
from pathlib import Path
from typing import Any


class AuditReader:
    def __init__(self, log_path: Path):
        self._log_path = log_path

    def _read_all(self) -> list[dict[str, Any]]:
        if not self._log_path.exists():
            return []
        entries = []
        with open(self._log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def list_entries(
        self,
        provider: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        entries = self._read_all()

        if provider:
            entries = [e for e in entries if e.get("provider") == provider]

        entries.reverse()

        if limit:
            entries = entries[:limit]

        return entries

    def get_entry(self, request_id: str) -> dict[str, Any] | None:
        for entry in self._read_all():
            if entry.get("request_id") == request_id:
                return entry
        return None

    def summary(self) -> dict[str, Any]:
        entries = self._read_all()
        redaction_types: Counter[str] = Counter()

        total_redactions = 0
        for entry in entries:
            for r in entry.get("redactions", []):
                redaction_types[r["type"]] += 1
                total_redactions += 1

        return {
            "total_requests": len(entries),
            "total_redactions": total_redactions,
            "redactions_by_type": dict(redaction_types),
        }
