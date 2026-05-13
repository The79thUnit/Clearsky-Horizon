import ExportPanel from './ExportPanel'

export default function Methodology() {
  return (
    <article className="methodology">
      <h2>Methodology</h2>

      <section>
        <h3>Source qualification</h3>
        <p>
          Every record carries a complete source provenance trail. No competitor
          tracker implements this. The model has four layers.
        </p>
        <ol>
          <li>
            <strong>ICD 206 Source Reference Citation</strong> on every record. US
            Office of the Director of National Intelligence, 2023.
          </li>
          <li>
            <strong>NATO Admiralty Scale (STANAG 2511)</strong>. Reliability A
            (completely reliable) through F (cannot be judged). Credibility 1 (confirmed
            by other sources) through 6 (cannot be judged).
          </li>
          <li>
            <strong>Dual confidence</strong>:
            <ul>
              <li>
                <em>pipeline_confidence</em>: auto, bounded 0 to 0.99. Computed from
                NATO base + corroboration boost (+0.02 per source, cap +0.10) - recency
                decay (-0.001 per day after 7-day grace, cap -0.05).
              </li>
              <li>
                <em>analyst_confidence</em>: human-set by an analyst after review.
                Nullable until reviewed. Displayed separately so readers can see what
                automation said versus what a human decided.
              </li>
            </ul>
          </li>
          <li>
            <strong>Berkeley Protocol chain-of-custody</strong>: SHA-256 hash of raw
            payload + UTC capture timestamp + raw URL + parser version. UN/UC Berkeley
            Human Rights Center, 2022.
          </li>
        </ol>
      </section>

      <section>
        <h3>UK GDPR Art 6 lawful basis</h3>
        <p>Legitimate interests, Article 6(1)(f). The three-part test:</p>
        <ul>
          <li>
            <strong>Purpose:</strong> public-health surveillance and outbreak awareness.
          </li>
          <li>
            <strong>Necessity:</strong> aggregating already-published surveillance data
            is the least intrusive way to provide a unified view across jurisdictions.
          </li>
          <li>
            <strong>Balance:</strong> only data already published by health authorities
            or under press freedom is ingested. No patient names. No re-identification
            attempts. No PII processed.
          </li>
        </ul>
      </section>

      <section>
        <h3>Not medical advice</h3>
        <p>
          HORIZON is informational only. For diagnosis or clinical care, contact a
          qualified clinician.
        </p>
        <p>
          HORIZON is not affiliated with WHO, CDC, ECDC, PAHO, or any national health
          authority. Source attribution is for transparency; it does not imply endorsement
          by the cited bodies.
        </p>
      </section>

      <section>
        <h3>Source inventory</h3>
        <p>
          Sources are organised across 7 tiers, from Tier 1 (official health
          authorities such as WHO, CDC, ECDC, PAHO) to Tier 7 (derivative
          trackers, cross-reference only). See the Sources tab for the current
          enabled inventory and per-source status, freshness, latency and
          ingestion count.
        </p>
      </section>

      <ExportPanel />
    </article>
  )
}
