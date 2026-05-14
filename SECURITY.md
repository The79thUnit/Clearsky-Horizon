# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.3.x (current) | Yes |
| < 0.3.0 | No |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities by email to **security@79thunit.co.uk**.

Include:

- Description of the vulnerability and its potential impact
- Steps to reproduce or proof-of-concept
- Affected component (API, worker, nginx config, database schema, frontend)
- Your name / handle for credit (optional — anonymous reports accepted)

We operate a **90-day coordinated disclosure** policy:

1. We acknowledge receipt within 48 hours.
2. We aim to assess severity and reproduce the issue within 7 days.
3. A fix is targeted within 30 days for critical issues, 90 days for others.
4. We credit researchers by name and handle in the release notes unless
   anonymity is requested.
5. We will not pursue legal action against good-faith researchers who stay
   within the scope below.

## Scope

**In scope:**

- The public API at `https://hantavirus.software/api/v1/*`
- Authentication / authorisation gaps
- Data integrity issues (manipulation of confidence scores, source ratings,
  case counts, or chain-of-custody hashes)
- Server-side injection (SQL, command, template)
- Information disclosure (credentials, internal paths, PII)
- The nginx reverse proxy configuration

**Out of scope:**

- Theoretical vulnerabilities without proof of impact
- Social engineering attacks
- Denial-of-service / volumetric attacks
- Issues affecting only third-party services (WHO, CDC, ECDC, etc.)
- Scanner output without analyst narrative

## Data integrity reports

If you believe HORIZON is displaying inaccurate case data or incorrect
source attributions, use the **Data Correction** issue template on GitHub.
This is not a security issue but is treated with the same urgency.
