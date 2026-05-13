import { useEffect, useState } from 'react'
import CaseList from './components/CaseList'
import SourceQualityTable from './components/SourceQualityTable'
import Methodology from './components/Methodology'
import Resources from './components/Resources'
import Footer from './components/Footer'
import HomeView from './components/HomeView'
import LiveIndicator from './components/LiveIndicator'
import MobileMenu from './components/MobileMenu'
import { LiveTickProvider } from './hooks/useLiveTick'

type View = 'home' | 'reports' | 'sources' | 'resources' | 'methodology'

const TABS: { id: View; label: string }[] = [
  { id: 'home', label: 'Home' },
  { id: 'reports', label: 'Reports' },
  { id: 'sources', label: 'Sources' },
  { id: 'resources', label: 'Resources' },
  { id: 'methodology', label: 'Methodology' },
]

const TITLES: Record<View, string> = {
  home: 'HORIZON - Live Hantavirus Outbreak Tracker',
  reports: 'Reports - HORIZON Hantavirus Surveillance',
  sources: 'Sources - HORIZON Hantavirus Surveillance',
  resources: 'Resources - HORIZON Hantavirus Surveillance',
  methodology: 'Methodology - HORIZON Hantavirus Surveillance',
}

export default function App() {
  const [view, setView] = useState<View>('home')
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    document.title = TITLES[view]
    if (view !== 'home') {
      window.history.replaceState(null, '', `#${view}`)
    } else if (window.location.hash) {
      window.history.replaceState(null, '', '/')
    }
  }, [view])

  // Boot from URL hash on first load (deep-link support). Also handle legacy
  // 'cases' hash by redirecting to the renamed 'reports' route.
  useEffect(() => {
    const hash = window.location.hash.slice(1)
    if (hash === 'cases') {
      setView('reports')
      return
    }
    if (
      hash &&
      (['reports', 'sources', 'resources', 'methodology'] as View[]).includes(hash as View)
    ) {
      setView(hash as View)
    }
  }, [])

  return (
    <LiveTickProvider>
      <div className="app">
        <header className="header">
          <div className="brand">
            <h1>
              <span className="accent">HORIZON</span>
            </h1>
            <p className="tagline">Hantavirus surveillance. Audit-grade source provenance.</p>
          </div>
          <div className="header-right">
            <LiveIndicator />
            <nav className="nav" aria-label="Primary">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setView(t.id)}
                  className={view === t.id ? 'active' : ''}
                  type="button"
                >
                  {t.label}
                </button>
              ))}
            </nav>
            <button
              className="hamburger"
              onClick={() => setMenuOpen(true)}
              type="button"
              aria-label="Open menu"
              aria-expanded={menuOpen}
              aria-controls="mobile-menu"
            >
              <span aria-hidden="true" />
              <span aria-hidden="true" />
              <span aria-hidden="true" />
            </button>
          </div>
        </header>

        <main className="main">
          {view === 'home' && <HomeView />}
          {view === 'reports' && <CaseList />}
          {view === 'sources' && <SourceQualityTable />}
          {view === 'resources' && <Resources />}
          {view === 'methodology' && <Methodology />}
        </main>

        <Footer />

        {menuOpen && (
          <MobileMenu
            tabs={TABS}
            view={view}
            setView={(id) => setView(id as View)}
            onClose={() => setMenuOpen(false)}
          />
        )}
      </div>
    </LiveTickProvider>
  )
}
