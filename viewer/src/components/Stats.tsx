import { AuditEntry } from '../api'

interface Props {
  entries: AuditEntry[]
}

const TYPE_COLORS: Record<string, string> = {
  EMAIL_ADDRESS: '#f472b6',
  PHONE_NUMBER: '#c084fc',
  PHONE_INTL: '#c084fc',
  CREDIT_CARD: '#fb923c',
  US_SSN: '#fb923c',
  IP_ADDRESS: '#38bdf8',
  PERSON: '#4ade80',
  LOCATION: '#2dd4bf',
  AWS_KEY: '#f87171',
  GENERIC_SECRET: '#f87171',
  GENERIC_TOKEN: '#f87171',
  PREFIXED_API_KEY: '#f87171',
  PASSWORD_IN_PROSE: '#fbbf24',
  PRIVATE_KEY: '#f87171',
  JWT: '#f87171',
  CONNECTION_STRING: '#f87171',
}

export function Stats({ entries }: Props) {
  const totalRedactions = entries.reduce((sum, e) => sum + e.redactions.length, 0)
  const byType: Record<string, number> = {}
  for (const e of entries) {
    for (const r of e.redactions) {
      byType[r.type] = (byType[r.type] || 0) + 1
    }
  }

  const cleanCount = entries.filter(e => e.redactions.length === 0).length
  const redactedCount = entries.filter(e => e.redactions.length > 0).length

  return (
    <div style={{
      display: 'flex', gap: 10, padding: '12px 24px',
      borderBottom: '1px solid #1e293b', overflowX: 'auto',
    }}>
      <StatCard label="Requests" value={entries.length} color="#e2e8f0" />
      <StatCard label="Redacted" value={totalRedactions} color="#f87171" />
      <StatCard label="Clean" value={cleanCount} color="#4ade80" />
      <StatCard label="Flagged" value={redactedCount} color="#fbbf24" />
      <div style={{ width: 1, background: '#334155', margin: '0 6px' }} />
      {Object.entries(byType).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
        <StatPill key={type} label={type} count={count} color={TYPE_COLORS[type] || '#94a3b8'} />
      ))}
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{
      background: '#1e293b', padding: '10px 16px', borderRadius: 8, minWidth: 80,
      border: '1px solid #334155',
    }}>
      <div style={{ fontSize: 20, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>{value}</div>
      <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>{label}</div>
    </div>
  )
}

function StatPill({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      background: '#1e293b', padding: '6px 12px', borderRadius: 20,
      border: '1px solid #334155', whiteSpace: 'nowrap',
    }}>
      <span style={{
        width: 8, height: 8, borderRadius: '50%', background: color,
        display: 'inline-block', flexShrink: 0,
      }} />
      <span style={{ fontSize: 12, color: '#94a3b8' }}>{label.replace(/_/g, ' ')}</span>
      <span style={{ fontSize: 12, fontWeight: 600, color }}>{count}</span>
    </div>
  )
}
