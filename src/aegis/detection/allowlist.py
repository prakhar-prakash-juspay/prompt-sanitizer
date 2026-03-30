import re
from pathlib import Path

import yaml


class Allowlist:
    def __init__(self, path: Path):
        self._path = path
        self._values: set[str] = set()
        self._patterns: list[re.Pattern] = []
        self._raw_entries: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._raw_entries = []
            return

        with open(self._path) as f:
            data = yaml.safe_load(f) or {}

        self._raw_entries = data.get("allowed", [])
        for entry in self._raw_entries:
            if "value" in entry:
                self._values.add(entry["value"])
            elif "pattern" in entry:
                self._patterns.append(re.compile(entry["pattern"]))

    def is_allowed(self, value: str) -> bool:
        if value in self._values:
            return True
        return any(p.fullmatch(value) for p in self._patterns)

    def add_value(self, value: str, reason: str = "") -> None:
        self._values.add(value)
        self._raw_entries.append({"value": value, "reason": reason})
        self._save()

    def _save(self) -> None:
        data = {"allowed": self._raw_entries}
        with open(self._path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
