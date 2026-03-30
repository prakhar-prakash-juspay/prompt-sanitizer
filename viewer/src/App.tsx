import { useState } from 'react'
import { AuditEntry } from './api'
import { Timeline } from './components/Timeline'
import { RequestDetail } from './components/RequestDetail'
import { Stats } from './components/Stats'

export default function App() {
  const [selected, setSelected] = useState<AuditEntry | null>(null)

  return (
    <div>
      <div style={{ background: '#1e293b', padding: '12px 20px', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 18, fontWeight: 'bold' }}>Aegis</span>
        <span style={{ color: '#64748b', fontSize: 14 }}>Log Viewer</span>
      </div>
      <div style={{ padding: '0 20px' }}>
        <Stats />
      </div>
      <div style={{ display: 'flex' }}>
        <Timeline onSelect={setSelected} selectedId={selected?.request_id ?? null} />
        {selected ? (
          <RequestDetail entry={selected} />
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
            Select a request to view details
          </div>
        )}
      </div>
    </div>
  )
}
