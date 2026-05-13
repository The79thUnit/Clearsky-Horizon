"""Mastodon #MVHondius hashtag RSS connector.

Vessel-specific feed for the MV Hondius hantavirus cluster. The
#MVHondius hashtag is actively used on Mastodon by journalists,
epidemiologists, MV Hondius passengers, and public health accounts
publishing real-time updates on the outbreak. This is the highest-
signal social-media feed for the current cluster.

As of 2026-05-13, mastodon.social/tags/MVHondius.rss is the largest
of the three hantavirus-adjacent hashtag feeds (42 KB, more posts than
#hantavirus or #orthohantavirus).

Separate connector from mastodon-hantavirus because:
  * Different population of posts (vessel-specific context vs. general
    hantavirus epidemiology). The two feeds do overlap (many posts use
    both hashtags) but the cross-source dedup in ingest.py links them
    via content_topic_hash rather than duplicating events.
  * Can be independently enabled/disabled as the cluster becomes
    less active over time.

NATO rating: C3 (social media, possibly unverified).
"""

from __future__ import annotations

from typing import ClassVar

from .mastodon_base import MastodonRSSBase


class MastodonHondiusConnector(MastodonRSSBase):
    SOURCE_CODE: ClassVar[str] = "mastodon-hondius"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://mastodon.social/tags/MVHondius.rss"
    # All items already hashtag-filtered by mastodon; full pass-through.
    KEYWORDS: ClassVar[list[str]] = [
        "hondius",
        "hantavirus",
        "hanta",
        "andes",
        "cruise",
        "oceanwide",
        "passenger",
        "quarantine",
    ]
