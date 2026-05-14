import { useEffect, useState } from 'react'
import { useTick } from '../hooks/useLiveTick'

function relativeAge(tickIso: string, now: number): string {
  if (!tickIso) return 'no signal'
  const ms = now - new Date(tickIso).getTime()
  const sec = Math.max(0, Math.floor(ms / 1000))
  if (sec < 60) return `${sec}s ago`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  return `${Math.floor(min / 60)}h ago`
}

/** Pulses every second when connected, shows "down" when disconnected. */
export default function LiveIndicator() {
  const tick = useTick()
  const [now, setNow] = useState(Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className={`live-indicator ${tick.connected ? 'connected' : 'disconnected'}`}>
      <span className="live-dot" aria-hidden="true" />
      {tick.connected ? (
        <>
          <span className="live-text">LIVE</span>
          <span className="live-sub">{tick.ts ? `updated ${relativeAge(tick.ts, now)}` : 'syncing...'}</span>
        </>
      ) : (
        <>
          <span className="live-text">RECONNECTING</span>
          <span className="live-sub">stream offline</span>
        </>
      )}
    </div>
  )
}
