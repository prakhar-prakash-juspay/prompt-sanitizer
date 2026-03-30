# prompt-sanitizer

A local reverse proxy that redacts secrets and PII from agentic coding tool requests to LLM APIs.

In the agentic coding era (Claude Code, GitHub Copilot, Codex), AI agents routinely read files containing API keys, credentials, and personal data. This sensitive information flows into prompts sent to cloud LLM APIs where it can be logged, cached, or trained on. **prompt-sanitizer** sits between your coding agents and LLM APIs, automatically detecting and redacting sensitive data before it leaves your machine.

## How It Works

```
Agent (Claude Code, Copilot, Codex)
    |
    v
prompt-sanitizer (localhost:8443)
    |-- Detect secrets + PII in message content
    |-- Replace with [REDACTED:TYPE:hash] placeholders
    |-- Log redaction audit trail
    |-- Forward scrubbed request to real API
    |
    v
LLM API (api.anthropic.com, api.openai.com)
    |
    v
Response returned as-is to agent
```

## What It Detects

**Secrets:** AWS keys, JWTs, GitHub/Stripe/Twilio/Slack tokens, private keys, database connection strings, generic API keys, high-entropy strings

**PII:** Email addresses, phone numbers, credit card numbers, SSNs, IP addresses, physical addresses, person names

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
prompt-sanitizer setup
prompt-sanitizer start
```

`prompt-sanitizer setup` automatically:
- Creates `~/.prompt-sanitizer/` with default config and allowlist
- Adds `ANTHROPIC_BASE_URL` and `OPENAI_BASE_URL` env vars to your shell profile
- Detects installed agents (Claude Code, Codex, VS Code/Copilot)

Open a new terminal and your agents will route through the proxy automatically.

## CLI

```bash
prompt-sanitizer setup              # one-time auto-configuration
prompt-sanitizer start              # start the proxy
prompt-sanitizer stop               # stop the proxy
prompt-sanitizer status             # check if proxy is running
prompt-sanitizer log                # view recent audit entries
prompt-sanitizer log --summary      # redaction stats by type
prompt-sanitizer log --web          # open log viewer in browser
prompt-sanitizer allow <value>      # allowlist a false positive
prompt-sanitizer config             # edit config
prompt-sanitizer install            # auto-start on boot (systemd/launchd)
```

## Log Viewer

A built-in web dashboard at `http://localhost:8444` with:
- Timeline of all proxied requests
- Side-by-side request/response viewer with syntax highlighting
- Clickable redaction badges that reveal original values
- Redaction statistics and filtering
- One-click allowlisting for false positives

## Configuration

Config lives at `~/.prompt-sanitizer/config.yaml`:

```yaml
port: 8443
viewer_port: 8444

providers:
  anthropic:
    upstream: https://api.anthropic.com
  openai:
    upstream: https://api.openai.com

detection:
  secrets: true
  pii: true
  custom_patterns:
    - name: internal_project_id
      pattern: "PROJ-[A-Z0-9]{8}"
```

## Allowlist

False positives can be managed via CLI or the log viewer UI:

```bash
prompt-sanitizer allow "sha256:abc123" --reason "Docker image digest"
```

Allowlist at `~/.prompt-sanitizer/allowlist.yaml`:

```yaml
allowed:
  - value: "sha256:abc123"
    reason: "Docker image digest"
  - pattern: "TEST_.*"
    reason: "Test fixture values"
```

## Tech Stack

- **Python** + **FastAPI** — async reverse proxy with streaming SSE support
- **detect-secrets** patterns — regex-based secret detection
- **Presidio** (Microsoft) + **spaCy** — NER-based PII detection
- **React** + **Vite** — log viewer SPA

## License

MIT
