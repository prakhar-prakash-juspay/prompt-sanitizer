import { useState } from 'react'
import { revealOriginal } from '../api'

interface Props {
  placeholder: string
  requestId: string
  inline?: boolean
}

const TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  EMAIL_ADDRESS: { bg: '#831843', text: '#fbcfe8' },
  PHONE_NUMBER: { bg: '#581c87', text: '#e9d5ff' },
  PHONE_INTL: { bg: '#581c87', text: '#e9d5ff' },
  CREDIT_CARD: { bg: '#7c2d12', text: '#fed7aa' },
  US_SSN: { bg: '#7c2d12', text: '#fed7aa' },
  IP_ADDRESS: { bg: '#0c4a6e', text: '#bae6fd' },
  PERSON: { bg: '#14532d', text: '#bbf7d0' },
  LOCATION: { bg: '#134e4a', text: '#99f6e4' },
  AWS_KEY: { bg: '#7f1d1d', text: '#fecaca' },
  GENERIC_SECRET: { bg: '#7f1d1d', text: '#fecaca' },
  GENERIC_TOKEN: { bg: '#7f1d1d', text: '#fecaca' },
  PREFIXED_API_KEY: { bg: '#7f1d1d', text: '#fecaca' },
  PASSWORD_IN_PROSE: { bg: '#713f12', text: '#fef08a' },
  PRIVATE_KEY: { bg: '#7f1d1d', text: '#fecaca' },
  JWT: { bg: '#7f1d1d', text: '#fecaca' },
  CONNECTION_STRING: { bg: '#7f1d1d', text: '#fecaca' },
}

function getType(placeholder: string): string {
  const match = placeholder.match(/\[REDACTED:([A-Z_]+):/)
  return match ? match[1] : ''
}

export function RedactionBadge({ placeholder, requestId, inline }: Props) {
  const [revealed, setRevealed] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const type = getType(placeholder)
  const colors = TYPE_COLORS[type] || { bg: '#374151', text: '#d1d5db' }

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
        background: revealed ? '#dc2626' : colors.bg,
        color: revealed ? '#fff' : colors.text,
        padding: inline ? '1px 5px' : '2px 8px',
        borderRadius: 4,
        cursor: 'pointer',
        fontSize: inline ? '0.8em' : '0.85em',
        fontFamily: 'monospace',
        border: `1px solid ${revealed ? '#ef4444' : colors.text}20`,
        transition: 'all 0.15s',
      }}
    >
      {loading ? '...' : revealed ?? placeholder}
    </span>
  )
}
