import { AuditEntry } from '../api'
import { RedactionBadge } from './RedactionBadge'

interface Props {
  entry: AuditEntry
}

function highlightRedactions(text: string, entry: AuditEntry): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = []
  let remaining = text
  let keyCounter = 0
  for (const r of entry.redactions) {
    const idx = remaining.indexOf(r.placeholder)
    if (idx === -1) continue
    parts.push(remaining.slice(0, idx))
    parts.push(
      <RedactionBadge key={`${r.placeholder}-${keyCounter++}`} placeholder={r.placeholder} requestId={entry.request_id} />
    )
    remaining = remaining.slice(idx + r.placeholder.length)
  }
  parts.push(remaining)
  return parts
}

export function RequestDetail({ entry }: Props) {
  const requestStr = JSON.stringify(entry.request_body, null, 2)
  const responseStr = JSON.stringify(entry.response_body, null, 2)

  return (
    <div style={{ flex: 1, padding: 20, overflow: 'auto', height: '100vh' }}>
      <h2 style={{ fontSize: 16, marginBottom: 8 }}>
        {entry.request_id} — {entry.provider} {entry.endpoint}
      </h2>
      <div style={{ fontSize: 12, color: '#64748b', marginBottom: 16 }}>{entry.timestamp}</div>

      {entry.redactions.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 14, color: '#f87171', marginBottom: 8 }}>Redactions ({entry.redactions.length})</h3>
          {entry.redactions.map((r, i) => (
            <div key={i} style={{ fontSize: 13, marginBottom: 4 }}>
              <span style={{ color: '#94a3b8' }}>{r.type}:</span>{' '}
              <RedactionBadge placeholder={r.placeholder} requestId={entry.request_id} />
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <h3 style={{ fontSize: 14, marginBottom: 8, color: '#38bdf8' }}>Request (scrubbed)</h3>
          <pre style={{ background: '#1e293b', padding: 12, borderRadius: 8, fontSize: 12, overflow: 'auto', maxHeight: '60vh', whiteSpace: 'pre-wrap' }}>
            {highlightRedactions(requestStr, entry)}
          </pre>
        </div>
        <div>
          <h3 style={{ fontSize: 14, marginBottom: 8, color: '#4ade80' }}>Response</h3>
          <pre style={{ background: '#1e293b', padding: 12, borderRadius: 8, fontSize: 12, overflow: 'auto', maxHeight: '60vh', whiteSpace: 'pre-wrap' }}>
            {responseStr}
          </pre>
        </div>
      </div>
    </div>
  )
}
