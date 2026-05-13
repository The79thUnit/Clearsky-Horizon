import { createContext, createElement, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { API_BASE } from '../api'

export interface LiveTick {
  ts: string  // ISO8601, '' until first tick arrives
  connected: boolean
}

const DEFAULT_TICK: LiveTick = { ts: '', connected: false }

const LiveTickContext = createContext<LiveTick>(DEFAULT_TICK)

/** Subscribe to /api/v1/stream/events. Reconnects on error every 5s. */
function useEventSourceTick(): LiveTick {
  const [tick, setTick] = useState<LiveTick>(DEFAULT_TICK)

  useEffect(() => {
    const url = `${API_BASE}/api/v1/stream/events`
    let es: EventSource | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null

    const connect = () => {
      es = new EventSource(url)
      es.onopen = () => setTick((t) => ({ ...t, connected: true }))
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as { type?: string; ts?: string }
          if (data.type === 'tick' && data.ts) {
            setTick({ ts: data.ts, connected: true })
          }
        } catch {
          // ignore malformed payloads
        }
      }
      es.onerror = () => {
        setTick((t) => ({ ...t, connected: false }))
        es?.close()
        es = null
        reconnectTimer = setTimeout(connect, 5000)
      }
    }
    connect()

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer)
      es?.close()
    }
  }, [])

  return tick
}

/** Wrap your app in <LiveTickProvider>; descendants use useTick() to subscribe. */
export function LiveTickProvider({ children }: { children: ReactNode }) {
  const tick = useEventSourceTick()
  return createElement(LiveTickContext.Provider, { value: tick }, children)
}

/** Read the live tick. Returns DEFAULT_TICK if not inside a provider. */
export function useTick(): LiveTick {
  return useContext(LiveTickContext)
}
