import StatsHero from './StatsHero'
import IncidentBanner from './IncidentBanner'
import WorldMap from './WorldMap'
import Timeline from './Timeline'
import ClusterStrip from './ClusterStrip'
import EventTimeline from './EventTimeline'

/**
 * HORIZON home screen.
 *
 * Layout (top to bottom):
 *   1. Stats hero — authoritative case numbers (WHO/CDC/PAHO) + ingestion telemetry
 *   2. Incident banner — active outbreaks (e.g. MV Hondius) with confirmed counts,
 *      vessel context, per-country breakdown
 *   3. World map (country pins)
 *   4. Dot timeline (serotype-coloured)
 *   5. Event chronology (deduped, authority-first)
 *   6. Cluster strip
 */
export default function HomeView() {
  return (
    <div className="home-view">
      <StatsHero />
      <IncidentBanner />
      <WorldMap />
      <Timeline />
      <EventTimeline />
      <ClusterStrip />
    </div>
  )
}
