import { useState } from 'react'
import { AuditEntry } from '../api'
import { RedactionBadge } from './RedactionBadge'

interface Props {
  entry: AuditEntry
}

const TYPE_LABELS: Record<string, { label: string; icon: string }> = {
  EMAIL_ADDRESS: { label: 'Email Addresses', icon: '&#9993;' },
  PHONE_NUMBER: { label: 'Phone Numbers', icon: '&#128222;' },
  PHONE_INTL: { label: 'Phone Numbers (Intl)', icon: '&#128222;' },
  CREDIT_CARD: { label: 'Credit Cards', icon: '&#128179;' },
  US_SSN: { label: 'SSNs', icon: '&#128196;' },
  IP_ADDRESS: { label: 'IP Addresses', icon: '&#127760;' },
  PERSON: { label: 'Person Names', icon: '&#128100;' },
  LOCATION: { label: 'Locations', icon: '&#128205;' },
  AWS_KEY: { label: 'AWS Keys', icon: '&#128273;' },
  GENERIC_SECRET: { label: 'Secrets', icon: '&#128274;' },
  GENERIC_TOKEN: { label: 'Tokens', icon: '&#128274;' },
  PREFIXED_API_KEY: { label: 'API Keys', icon: '&#128273;' },
  PASSWORD_IN_PROSE: { label: 'Passwords', icon: '&#128274;' },
  PRIVATE_KEY: { label: 'Private Keys', icon: '&#128273;' },
  JWT: { label: 'JWTs', icon: '&#128273;' },
  CONNECTION_STRING: { label: 'Connection Strings', icon: '&#128279;' },
}

function groupRedactions(redactions: AuditEntry['redactions']) {
  const groups: Record<string, AuditEntry['redactions']> = {}
  for (const r of redactions) {
    if (!groups[r.type]) groups[r.type] = []
    groups[r.type].push(r)
  }
  return groups
}

function highlightRedactions(text: string, requestId: string): (string | JSX.Element)[] {
  const pattern = /\[REDACTED:[A-Z_]+:[a-f0-9]+\]/g
  const parts: (string | JSX.Element)[] = []
  let lastIndex = 0
  let keyCounter = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    parts.push(
      <RedactionBadge key={`r-${keyCounter++}`} placeholder={match[0]} requestId={requestId} inline />
    )
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }
  return parts
}

export function RequestDetail({ entry }: Props) {
  const [tab, setTab] = useState<'request' | 'response'>('request')
  const requestStr = JSON.stringify(entry.request_body, null, 2)
  const responseStr = JSON.stringify(entry.response_body, null, 2)
  const groups = groupRedactions(entry.redactions)

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '14px 20px', borderBottom: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{
              fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
              color: entry.provider === 'anthropic' ? '#38bdf8' : '#4ade80',
              letterSpacing: '0.05em',
            }}>{entry.provider}</span>
            <span style={{ fontSize: 13, color: '#94a3b8', marginLeft: 10, fontFamily: 'monospace' }}>
              {entry.endpoint}
            </span>
          </div>
          <span style={{ fontSize: 11, color: '#475569', fontFamily: 'monospace' }}>{entry.request_id}</span>
        </div>
        <div style={{ fontSize: 11, color: '#475569', marginTop: 4 }}>
          {new Date(entry.timestamp).toLocaleString()}
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Redactions panel */}
        {entry.redactions.length > 0 && (
          <div style={{
            width: 280, borderRight: '1px solid #1e293b', overflow: 'auto',
            padding: '12px 14px', flexShrink: 0,
          }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#f87171', marginBottom: 10 }}>
              Redactions ({entry.redactions.length})
            </div>
            {Object.entries(groups).map(([type, items]) => {
              const meta = TYPE_LABELS[type] || { label: type, icon: '&#128308;' }
              return (
                <div key={type} style={{ marginBottom: 12 }}>
                  <div style={{
                    fontSize: 11, fontWeight: 600, color: '#94a3b8',
                    marginBottom: 5, display: 'flex', alignItems: 'center', gap: 5,
                  }}>
                    <span dangerouslySetInnerHTML={{ __html: meta.icon }} />
                    {meta.label}
                    <span style={{
                      background: '#334155', padding: '0 6px', borderRadius: 10,
                      fontSize: 10, color: '#e2e8f0', marginLeft: 'auto',
                    }}>{items.length}</span>
                  </div>
                  {items.map((r, i) => (
                    <div key={i} style={{ marginBottom: 3 }}>
                      <RedactionBadge placeholder={r.placeholder} requestId={entry.request_id} />
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        )}

        {/* Request/Response body */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #1e293b' }}>
            {(['request', 'response'] as const).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                style={{
                  padding: '8px 20px', fontSize: 13, cursor: 'pointer',
                  background: 'transparent', border: 'none',
                  color: tab === t ? (t === 'request' ? '#38bdf8' : '#4ade80') : '#64748b',
                  borderBottom: tab === t ? `2px solid ${t === 'request' ? '#38bdf8' : '#4ade80'}` : '2px solid transparent',
                  fontWeight: tab === t ? 600 : 400,
                  textTransform: 'capitalize',
                }}
              >{t === 'request' ? 'Request (scrubbed)' : 'Response'}</button>
            ))}
          </div>
          <pre style={{
            flex: 1, margin: 0, padding: 16, overflow: 'auto',
            fontSize: 12, lineHeight: 1.6, fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            background: '#0c1222',
          }}>
            {tab === 'request'
              ? highlightRedactions(requestStr, entry.request_id)
              : responseStr
            }
          </pre>
        </div>
      </div>
    </div>
  )
}
