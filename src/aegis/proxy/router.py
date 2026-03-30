import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

from aegis.audit.logger import AuditLogger, AuditEntry
from aegis.config import AegisConfig
from aegis.detection.allowlist import Allowlist
from aegis.detection.engine import DetectionEngine
from aegis.redaction.redactor import Redactor


class ProxyRouter:
    def __init__(self, config: AegisConfig, allowlist: Allowlist):
        self.config = config
        self.engine = DetectionEngine(config=config.detection, allowlist=allowlist)
        self.redactor = Redactor()
        self.audit_logger = AuditLogger(config.audit_file_path)
        self.router = APIRouter()
        self.router.add_api_route(
            "/{provider}/{path:path}",
            self.proxy_request,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )

    def _redact_string(self, text: str, all_redactions: list[dict]) -> str:
        detections = self.engine.detect(text)
        if not detections:
            return text
        result = self.redactor.redact(text, detections)
        for placeholder, info in result.redaction_map.items():
            all_redactions.append({
                "type": info["type"],
                "placeholder": placeholder,
                "original": info["original"],
            })
        return result.redacted_text

    def _redact_message_content(self, content: Any, all_redactions: list[dict]) -> Any:
        """Redact within message content only (string or content blocks)."""
        if isinstance(content, str):
            return self._redact_string(content, all_redactions)
        elif isinstance(content, list):
            # Content blocks: [{"type": "text", "text": "..."}, ...]
            result = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text" and "text" in block:
                    result.append({**block, "text": self._redact_string(block["text"], all_redactions)})
                else:
                    result.append(block)
            return result
        return content

    def _redact_body(self, body: dict[str, Any]) -> tuple[dict[str, Any], list[dict]]:
        all_redactions: list[dict] = []
        redacted = dict(body)

        # Only redact within messages content — leave tool definitions,
        # model names, and other structural fields untouched
        if "messages" in redacted:
            new_messages = []
            for msg in redacted["messages"]:
                if isinstance(msg, dict) and "content" in msg:
                    new_msg = dict(msg)
                    new_msg["content"] = self._redact_message_content(msg["content"], all_redactions)
                    new_messages.append(new_msg)
                else:
                    new_messages.append(msg)
            redacted["messages"] = new_messages

        # Also redact system prompt if present
        if "system" in redacted:
            if isinstance(redacted["system"], str):
                redacted["system"] = self._redact_string(redacted["system"], all_redactions)
            elif isinstance(redacted["system"], list):
                redacted["system"] = self._redact_message_content(redacted["system"], all_redactions)

        return redacted, all_redactions

    async def proxy_request(self, provider: str, path: str, request: Request) -> Response:
        if provider not in self.config.providers:
            return Response(
                content=json.dumps({"error": f"Unknown provider: {provider}"}),
                status_code=404,
                media_type="application/json",
            )

        upstream = self.config.providers[provider].upstream
        target_url = f"{upstream}/{path}"
        # Preserve query parameters
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"

        # Read and redact request body
        raw_body = await request.body()
        redactions = []
        is_streaming = False
        if raw_body:
            body_json = json.loads(raw_body)
            is_streaming = body_json.get("stream", False)
            redacted_body, redactions = self._redact_body(body_json)
            send_body = json.dumps(redacted_body).encode()
        else:
            body_json = {}
            redacted_body = {}
            send_body = raw_body

        # Build headers
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)

        upstream_request = httpx.Request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=send_body,
        )

        if is_streaming:
            return await self._handle_streaming(
                upstream_request, provider, path, redacted_body, redactions,
            )
        else:
            return await self._handle_non_streaming(
                upstream_request, provider, path, redacted_body, redactions,
            )

    async def _handle_non_streaming(
        self,
        upstream_request: httpx.Request,
        provider: str,
        path: str,
        redacted_body: dict,
        redactions: list[dict],
    ) -> Response:
        async with httpx.AsyncClient() as client:
            upstream_response = await client.send(upstream_request)

        response_body = {}
        try:
            response_body = upstream_response.json()
        except Exception:
            pass

        self._log_audit(provider, path, redacted_body, response_body, redactions)

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type", "application/json"),
        )

    async def _handle_streaming(
        self,
        upstream_request: httpx.Request,
        provider: str,
        path: str,
        redacted_body: dict,
        redactions: list[dict],
    ) -> StreamingResponse:
        client = httpx.AsyncClient()
        upstream_response = await client.send(upstream_request, stream=True)

        collected_chunks: list[bytes] = []

        async def stream_generator():
            try:
                async for chunk in upstream_response.aiter_bytes():
                    collected_chunks.append(chunk)
                    yield chunk
            finally:
                await upstream_response.aclose()
                await client.aclose()
                full_response = b"".join(collected_chunks).decode(errors="replace")
                self._log_audit(provider, path, redacted_body, {"_streamed": full_response}, redactions)

        return StreamingResponse(
            stream_generator(),
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type", "text/event-stream"),
        )

    def _log_audit(
        self,
        provider: str,
        path: str,
        redacted_body: dict,
        response_body: dict,
        redactions: list[dict],
    ) -> None:
        entry = AuditEntry(
            provider=provider,
            endpoint=f"/{path}",
            request_body=redacted_body if self.config.logging.store_request_body else {},
            response_body=response_body if self.config.logging.store_response_body else {},
            redactions=redactions,
        )
        self.audit_logger.log(entry)
