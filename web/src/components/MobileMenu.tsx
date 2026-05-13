import { useEffect } from 'react'
import LiveIndicator from './LiveIndicator'

interface Tab {
  id: string
  label: string
}

interface Props {
  tabs: Tab[]
  view: string
  setView: (id: never) => void
  onClose: () => void
}

export default function MobileMenu({ tabs, view, setView, onClose }: Props) {
  // Lock body scroll while menu is open
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [])

  // Escape to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="mobile-menu-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Navigation menu"
    >
      <div className="mobile-menu" onClick={(e) => e.stopPropagation()}>
        <header className="mobile-menu-head">
          <span className="mobile-menu-brand">
            <span className="accent">HORIZON</span>
          </span>
          <button
            className="mobile-menu-close"
            onClick={onClose}
            type="button"
            aria-label="Close menu"
          >
            ×
          </button>
        </header>
        <nav className="mobile-menu-nav" aria-label="Main">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`mobile-menu-item${view === t.id ? ' active' : ''}`}
              onClick={() => {
                setView(t.id as never)
                onClose()
              }}
              type="button"
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="mobile-menu-meta">
          <LiveIndicator />
          <p className="mobile-menu-footnote">
            <strong>79th Unit OSINT</strong> &middot; Facts First. Question Everything.
          </p>
          <p className="mobile-menu-footnote">
            UK GDPR Art 6: legitimate interests (public-health information). No PII.
          </p>
        </div>
      </div>
    </div>
  )
}
