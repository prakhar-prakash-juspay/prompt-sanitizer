from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ProviderConfig:
    upstream: str


@dataclass
class CustomPattern:
    name: str
    pattern: str


@dataclass
class DetectionConfig:
    secrets: bool = True
    pii: bool = True
    infra: bool = True
    custom_patterns: list[CustomPattern] = field(default_factory=list)


@dataclass
class LoggingConfig:
    audit_file: str = "~/.aegis/audit.log"
    log_original_values: bool = True
    store_request_body: bool = True
    store_response_body: bool = True


@dataclass
class AegisConfig:
    port: int = 8443
    viewer_port: int = 8444
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @property
    def audit_file_path(self) -> Path:
        return Path(self.logging.audit_file).expanduser()


def default_config() -> AegisConfig:
    return AegisConfig(
        providers={
            "anthropic": ProviderConfig(upstream="https://api.anthropic.com"),
            "openai": ProviderConfig(upstream="https://api.openai.com"),
        }
    )


def load_config(path: Path) -> AegisConfig:
    if not path.exists():
        return default_config()

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not raw:
        return default_config()

    providers = {}
    for name, prov in raw.get("providers", {}).items():
        providers[name] = ProviderConfig(upstream=prov["upstream"])

    det_raw = raw.get("detection", {})
    custom_patterns = [
        CustomPattern(name=p["name"], pattern=p["pattern"])
        for p in det_raw.get("custom_patterns", [])
    ]
    detection = DetectionConfig(
        secrets=det_raw.get("secrets", True),
        pii=det_raw.get("pii", True),
        infra=det_raw.get("infra", True),
        custom_patterns=custom_patterns,
    )

    log_raw = raw.get("logging", {})
    logging_config = LoggingConfig(
        audit_file=log_raw.get("audit_file", "~/.aegis/audit.log"),
        log_original_values=log_raw.get("log_original_values", True),
        store_request_body=log_raw.get("store_request_body", True),
        store_response_body=log_raw.get("store_response_body", True),
    )

    return AegisConfig(
        port=raw.get("port", 8443),
        viewer_port=raw.get("viewer_port", 8444),
        providers=providers,
        detection=detection,
        logging=logging_config,
    )
