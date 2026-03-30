import { AuditEntry } from '../api'

interface Props {
  entries: AuditEntry[]
  onSelect: (entry: AuditEntry) => void
  selectedId: string | null
  filter: string
  onFilterChange: (filter: string) => void
}

export function Timeline({ entries, onSelect, selectedId, filter, onFilterChange }: Props) {
  return (
    <div style={{
      borderRight: '1px solid #1e293b', width: 340, flexShrink: 0,
      display: 'flex', flexDirection: 'column', height: '100%',
    }}>
      <div style={{ padding: 10, borderBottom: '1px solid #1e293b' }}>
        <select
          value={filter}
          onChange={e => onFilterChange(e.target.value)}
          style={{
            background: '#1e293b', color: '#e2e8f0',
            border: '1px solid #334155', padding: '7px 10px',
            borderRadius: 6, width: '100%', fontSize: 13,
          }}
        >
          <option value="">All Providers</option>
          <option value="anthropic">Anthropic</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      <div style={{ overflow: 'auto', flex: 1 }}>
        {entries.map(entry => {
          const isSelected = entry.request_id === selectedId
          const hasRedactions = entry.redactions.length > 0
          const time = new Date(entry.timestamp).toLocaleTimeString()
          const date = new Date(entry.timestamp).toLocaleDateString()

          return (
            <div
              key={entry.request_id}
              onClick={() => onSelect(entry)}
              style={{
                padding: '10px 14px',
                borderBottom: '1px solid #1e293b',
                cursor: 'pointer',
                background: isSelected ? '#1e293b' : 'transparent',
                borderLeft: isSelected ? '3px solid #f87171' : '3px solid transparent',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = '#1e293b50' }}
              onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{
                  fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                  color: entry.provider === 'anthropic' ? '#38bdf8' : '#4ade80',
                  letterSpacing: '0.05em',
                }}>{entry.provider}</span>
                <span style={{ fontSize: 11, color: '#475569' }}>{time}</span>
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 3, fontFamily: 'monospace' }}>
                {entry.endpoint}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 5 }}>
                <span style={{ fontSize: 10, color: '#475569' }}>{date}</span>
                {hasRedactions ? (
                  <span style={{
                    fontSize: 11, color: '#fecaca', background: '#991b1b',
                    padding: '1px 8px', borderRadius: 10, fontWeight: 500,
                  }}>{entry.redactions.length} redacted</span>
                ) : (
                  <span style={{
                    fontSize: 11, color: '#bbf7d0', background: '#14532d',
                    padding: '1px 8px', borderRadius: 10,
                  }}>clean</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
