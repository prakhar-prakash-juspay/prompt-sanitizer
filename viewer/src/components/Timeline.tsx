import { useEffect, useState } from 'react'
import { fetchEntries, AuditEntry } from '../api'

interface Props {
  onSelect: (entry: AuditEntry) => void
  selectedId: string | null
}

export function Timeline({ onSelect, selectedId }: Props) {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [filter, setFilter] = useState<string>('')

  useEffect(() => {
    fetchEntries(filter || undefined).then(setEntries)
  }, [filter])

  return (
    <div style={{ borderRight: '1px solid #334155', minWidth: 320, height: '100vh', overflow: 'auto' }}>
      <div style={{ padding: 12, borderBottom: '1px solid #334155' }}>
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          style={{ background: '#1e293b', color: '#e2e8f0', border: '1px solid #475569', padding: '6px 10px', borderRadius: 4, width: '100%' }}
        >
          <option value="">All Providers</option>
          <option value="anthropic">Anthropic</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      {entries.map(entry => (
        <div
          key={entry.request_id}
          onClick={() => onSelect(entry)}
          style={{
            padding: 12,
            borderBottom: '1px solid #1e293b',
            cursor: 'pointer',
            background: entry.request_id === selectedId ? '#1e293b' : 'transparent',
          }}
        >
          <div style={{ fontSize: 12, color: '#64748b' }}>{entry.timestamp}</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ fontWeight: 500 }}>{entry.provider}</span>
            {entry.redactions.length > 0 && (
              <span style={{ color: '#f87171', fontSize: 13 }}>{entry.redactions.length} redacted</span>
            )}
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>{entry.endpoint}</div>
        </div>
      ))}
    </div>
  )
}
