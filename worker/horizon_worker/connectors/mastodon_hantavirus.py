"""Mastodon #hantavirus hashtag RSS connector.

mastodon.social is the largest Fediverse instance (~1.2M users). The
public hashtag RSS endpoint requires no authentication and exposes a
standard RSS 2.0 feed of all public posts tagged #hantavirus across
federated instances that mastodon.social follows.

Value to HORIZON:
  * Epidemiologists and public-health professionals post findings on
    Mastodon 1-4h before mainstream media picks them up (the public
    health community largely migrated from Twitter/X after the 2023 API
    closure). Real-time corroboration from practitioners.
  * Posts from @CDCgov.social, @WHO.social, virologists, and
    MV Hondius passenger/observer accounts surface rapidly.
  * Mastodon posts that include links (news articles, preprints) get
    ingested here first; the linked article is later ingested when the
    relevant source connector picks it up, generating a cross-source link.

Verified 2026-05-13: mastodon.social/tags/hantavirus.rss returns 200,
35KB of real posts including fresh MV Hondius coverage minutes old.

NATO rating: C3 (possibly unverified source, possibly true). Social media.
Individual posts require corroboration from authoritative sources before
analyst-confidence can be set.
"""

from __future__ import annotations

from typing import ClassVar

from .mastodon_base import MastodonRSSBase


class MastodonHantavirusConnector(MastodonRSSBase):
    SOURCE_CODE: ClassVar[str] = "mastodon-hantavirus"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://mastodon.social/tags/hantavirus.rss"
    # All items are already pre-filtered by hashtag; no keyword filter needed.
    # But we keep keywords as a safety net in case the feed ever returns
    # off-topic items from the federated timeline.
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes",
        "orthohantavirus",
        "sin nombre",
        "puumala",
        "hontaan",
        "hondius",
        "cruise ship",
    ]
