"""Reddit search-feed connector. NATO E4 (unreliable, doubtful).

Reddit's 2024 API-access policy walled off the `*.json` endpoints
(`/search.json`, `/r/Subreddit.json`) behind OAuth + paid API tier; our
unauthenticated requests hit HTTP 403. However the legacy Atom-feed
endpoints (`*.rss`) remain publicly accessible with generous rate-limits
(verified 2026-05-13: `x-ratelimit-remaining: 99` on a 100/window quota).

This connector uses Reddit's site-wide search Atom feed:
    https://www.reddit.com/search.rss?q=...&sort=new&limit=50

Verified 2026-05-13 content sample:
  * "[World] - Where Are the Passengers of the Hantavirus-Hit Cruise Ship
    Now? | NY Times" (2026-05-13, r/AutoNewspaper)
  * "Italy Says Suspected Hantavirus Case Is Negative, Easing Worries"
    (2026-05-13, r/RWATimes)
  * Three brand-new hantavirus subreddits: r/HantaVirus26,
    r/hantavirusoutbreak, r/hantavirus

NATO rating intentionally low (E4 — unreliable / doubtful) because the
content is user-submitted. Reddit signal is most useful as an
"early-warning radar" — surfacing news articles + community chatter
that arrives faster than authoritative bulletins. The extraction pipeline
treats Reddit-sourced records as analyst-review-required (cluster-tie
score must still be STRONG before any auto-application to the ontology).
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class RedditConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "reddit"
    # 0.2.0: switched from /search.json (HTTP 403 since the 2024 Reddit
    # API policy change) to /search.rss (publicly accessible Atom feed,
    # 100 requests/window rate-limit). Same query, same result set,
    # different transport. Bumps PARSER_VERSION to invalidate cached
    # parses against the JSON-pipeline output.
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = (
        "https://www.reddit.com/search.rss"
        "?q=hantavirus+OR+%22Andes+virus%22+OR+%22Sin+Nombre%22+OR+%22MV+Hondius%22"
        "&sort=new&limit=50"
    )
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes virus",
        "andv",
        "sin nombre",
        "puumala",
        "hantaan",
        "seoul virus",
        "orthohantavirus",
        # MV Hondius specific so cruise-ship news with no virus keyword
        # in the title still surfaces.
        "hondius",
        "cruise ship",
        "oceanwide",
    ]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        # Reddit requires a stable, identifying User-Agent. The /u/79thunit
        # reference is purely descriptive — there's no account auth on this
        # endpoint, just polite identification per Reddit's TOS.
        "user-agent": "HORIZON/0.2 by /u/79thunit (research; +https://hantavirus.software)",
    }
