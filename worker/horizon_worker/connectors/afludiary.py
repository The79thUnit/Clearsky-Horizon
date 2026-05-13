"""Avian Flu Diary (afludiary.blogspot.com) connector.

Mike Coston's outbreak blog — running since 2006, gold-standard
English-language outbreak aggregator. Despite the name, Avian Flu Diary
covers the full zoonotic disease portfolio: avian + swine influenza,
MERS-CoV, hantavirus, Crimean-Congo HF, Nipah, Lassa, monkeypox,
Marburg, etc. Editorial style is commentary-on-primary-sources, often
posting WHO DON / CDC HAN / ECDC summaries with context within hours
of release.

Verified 2026-05-13: feed returns Atom XML with 25 recent items
from afludiary.blogspot.com/feeds/posts/default.

NATO rating: B3 (usually reliable, possibly true). Individual posts
are secondary commentary not primary surveillance; signal is value-add
context rather than authoritative numbers. The extraction pipeline's
cluster-tie-score gate already prevents auto-application without a
primary corroborating source.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class AvianFluDiaryConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "avian-flu-diary"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://afludiary.blogspot.com/feeds/posts/default"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "sin nombre",
        "snv",
        "puumala",
        "puuv",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "dobrava",
        "dobv",
        "orthohantavirus",
        "rodent-borne",
        # MV Hondius specific so cruise-ship coverage surfaces even when
        # the post title doesn't lead with a virus keyword.
        "hondius",
        "oceanwide",
        "cruise ship",
    ]
