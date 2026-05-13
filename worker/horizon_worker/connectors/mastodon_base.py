"""Shared base for Mastodon hashtag RSS connectors.

Mastodon's RSS feeds leave <title> empty (some instances put the account
name, most put nothing). The post content lives in <description> as HTML.
This base overrides `parse` from RSSConnectorBase to synthesise a title
from the first 140 characters of the stripped description text.
"""

from __future__ import annotations

import dataclasses
import re

from .rss_base import RSSConnectorBase
from .types import ParsedItem


def _mastodon_title(summary: str | None) -> str:
    """Extract a human-readable title from Mastodon post HTML."""
    if not summary:
        return "[Mastodon post]"
    # strip_html already removed tags; summary is plain text at this point
    text = re.sub(r'\s+', ' ', summary).strip()
    if len(text) <= 140:
        return text
    # Truncate at word boundary
    truncated = text[:137]
    last_space = truncated.rfind(' ')
    if last_space > 80:
        truncated = truncated[:last_space]
    return truncated + "..."


class MastodonRSSBase(RSSConnectorBase):
    """RSSConnectorBase subclass that fills blank titles from post content."""

    def parse(self, raw: bytes) -> list[ParsedItem]:
        items = super().parse(raw)
        fixed: list[ParsedItem] = []
        for item in items:
            if not item.title and item.summary:
                title = _mastodon_title(item.summary)
                # ParsedItem is a frozen dataclass — use replace() for the fix
                item = dataclasses.replace(item, title=title)
            fixed.append(item)
        return fixed
