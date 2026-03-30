import { useState, useEffect } from 'react'
import { AuditEntry, fetchEntries } from './api'
import { Timeline } from './components/Timeline'
import { RequestDetail } from './components/RequestDetail'
import { Stats } from './components/Stats'

export default function App() {
  const [selected, setSelected] = useState<AuditEntry | null>(null)
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [filter, setFilter] = useState<string>('')

  useEffect(() => {
    fetchEntries(filter || undefined).then(setEntries)
  }, [filter])

  const refresh = () => {
    fetchEntries(filter || undefined).then(setEntries)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        padding: '14px 24px',
        borderBottom: '1px solid #334155',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #f87171 0%, #ef4444 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 'bold',
          }}>PS</div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, letterSpacing: '-0.01em' }}>Prompt Sanitizer</div>
            <div style={{ fontSize: 11, color: '#64748b' }}>LLM Request Audit Log</div>
          </div>
        </div>
        <button
          onClick={refresh}
          style={{
            background: '#334155', color: '#e2e8f0', border: 'none',
            padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
          }}
        >Refresh</button>
      </div>

      {/* Stats */}
      <Stats entries={entries} />

      {/* Main content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Timeline
          entries={entries}
          onSelect={setSelected}
          selectedId={selected?.request_id ?? null}
          filter={filter}
          onFilterChange={setFilter}
        />
        {selected ? (
          <RequestDetail entry={selected} />
        ) : (
          <div style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#475569', flexDirection: 'column', gap: 8,
          }}>
            <div style={{ fontSize: 40, opacity: 0.3 }}>&#128274;</div>
            <div style={{ fontSize: 14 }}>Select a request to inspect</div>
          </div>
        )}
      </div>
    </div>
  )
}
