import { useState } from 'react'
import { revealOriginal } from '../api'

interface Props {
  placeholder: string
  requestId: string
}

export function RedactionBadge({ placeholder, requestId }: Props) {
  const [revealed, setRevealed] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    if (revealed) {
      setRevealed(null)
      return
    }
    if (!confirm('Reveal the original sensitive value?')) return
    setLoading(true)
    try {
      const data = await revealOriginal(requestId, placeholder)
      setRevealed(data.original)
    } finally {
      setLoading(false)
    }
  }

  return (
    <span
      onClick={handleClick}
      style={{
        background: revealed ? '#dc2626' : '#991b1b',
        color: '#fecaca',
        padding: '2px 6px',
        borderRadius: 4,
        cursor: 'pointer',
        fontSize: '0.85em',
        fontFamily: 'monospace',
      }}
    >
      {loading ? '...' : revealed ?? placeholder}
    </span>
  )
}
