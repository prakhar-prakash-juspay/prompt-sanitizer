import { useEffect, useState } from 'react'
import { fetchSummary, Summary } from '../api'

export function Stats() {
  const [stats, setStats] = useState<Summary | null>(null)

  useEffect(() => {
    fetchSummary().then(setStats)
  }, [])

  if (!stats) return <div>Loading...</div>

  return (
    <div style={{ display: 'flex', gap: 24, padding: '16px 0' }}>
      <div style={{ background: '#1e293b', padding: 16, borderRadius: 8, minWidth: 140 }}>
        <div style={{ fontSize: 24, fontWeight: 'bold' }}>{stats.total_requests}</div>
        <div style={{ color: '#94a3b8', fontSize: 14 }}>Total Requests</div>
      </div>
      <div style={{ background: '#1e293b', padding: 16, borderRadius: 8, minWidth: 140 }}>
        <div style={{ fontSize: 24, fontWeight: 'bold', color: '#f87171' }}>{stats.total_redactions}</div>
        <div style={{ color: '#94a3b8', fontSize: 14 }}>Total Redactions</div>
      </div>
      {Object.entries(stats.redactions_by_type).map(([type, count]) => (
        <div key={type} style={{ background: '#1e293b', padding: 16, borderRadius: 8, minWidth: 140 }}>
          <div style={{ fontSize: 24, fontWeight: 'bold' }}>{count}</div>
          <div style={{ color: '#94a3b8', fontSize: 14 }}>{type}</div>
        </div>
      ))}
    </div>
  )
}
