const BASE = '/api'

export interface AuditEntry {
  timestamp: string
  request_id: string
  provider: string
  endpoint: string
  request_body: Record<string, unknown>
  response_body: Record<string, unknown>
  redactions: Array<{
    type: string
    placeholder: string
    original: string
  }>
}

export interface Summary {
  total_requests: number
  total_redactions: number
  redactions_by_type: Record<string, number>
}

export async function fetchEntries(provider?: string): Promise<AuditEntry[]> {
  const params = provider ? `?provider=${provider}` : ''
  const resp = await fetch(`${BASE}/entries${params}`)
  return resp.json()
}

export async function fetchEntry(requestId: string): Promise<AuditEntry> {
  const resp = await fetch(`${BASE}/entries/${requestId}`)
  return resp.json()
}

export async function fetchSummary(): Promise<Summary> {
  const resp = await fetch(`${BASE}/summary`)
  return resp.json()
}

export async function revealOriginal(requestId: string, placeholder: string): Promise<{ original: string }> {
  const resp = await fetch(`${BASE}/entries/${requestId}/reveal/${encodeURIComponent(placeholder)}`)
  return resp.json()
}

export async function addToAllowlist(value: string, reason: string): Promise<void> {
  await fetch(`${BASE}/allowlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value, reason }),
  })
}
