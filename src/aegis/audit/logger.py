import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AuditEntry:
    provider: str
    endpoint: str
    request_body: dict[str, Any]
    response_body: dict[str, Any]
    redactions: list[dict[str, str]]


class AuditLogger:
    def __init__(self, log_path: Path):
        self._log_path = log_path

    def log(self, entry: AuditEntry) -> str:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "provider": entry.provider,
            "endpoint": entry.endpoint,
            "request_body": entry.request_body,
            "response_body": entry.response_body,
            "redactions": entry.redactions,
        }

        with open(self._log_path, "a") as f:
            f.write(json.dumps(record) + "\n")

        return request_id
