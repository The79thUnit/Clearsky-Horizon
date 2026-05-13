export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <p className="footer-line">
          <strong>79th Unit OSINT</strong> &nbsp;|&nbsp; Facts First. Question Everything.
        </p>
        <p className="footer-line">
          Built on CLEARSKY methodology. Not medical advice. Not affiliated with WHO,
          CDC, ECDC, or PAHO.
        </p>
        <p className="footer-line">
          UK GDPR Art 6: legitimate interests (public-health information). No PII
          processed.
        </p>
        <nav className="footer-links" aria-label="Footer">
          <a href="/about">About</a>
          <span aria-hidden="true">·</span>
          <a href="/contact">Contact</a>
          <span aria-hidden="true">·</span>
          <a href="/methodology">Methodology</a>
          <span aria-hidden="true">·</span>
          <a href="/editorial-standards">Editorial standards</a>
          <span aria-hidden="true">·</span>
          <a href="/corrections">Corrections</a>
          <span aria-hidden="true">·</span>
          <a href="/terms-of-service">Terms of Service</a>
          <span aria-hidden="true">·</span>
          <a href="/privacy">Privacy</a>
          <span aria-hidden="true">·</span>
          <a href="/sources">Sources</a>
          <span aria-hidden="true">·</span>
          <a href="/api/openapi.json">API</a>
        </nav>
      </div>
    </footer>
  )
}
