"""Shared text-extraction helpers used by every connector.

Each connector calls these to derive country / region / serotype from titles
and summaries. Phase 2 starter heuristics; Phase 3 will replace with a real
geocoder (GeoNames or Nominatim) and a serotype classifier.
"""

from __future__ import annotations

import hashlib
import html
import re
from datetime import date, datetime

# Strip HTML tags + unescape entities. Google News + many RSS feeds shove
# anchor tags + <font> markup into the summary; we want plain text only.
_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def strip_html(s: str | None) -> str:
    """Remove all HTML tags + unescape entities + collapse whitespace."""
    if not s:
        return ""
    no_tags = _HTML_TAG.sub(" ", s)
    decoded = html.unescape(no_tags)
    return _WHITESPACE.sub(" ", decoded).strip()


# --- Content hashing for cross-source dedup ---------------------------------
# A "topic hash" is a lossy hash of the normalised title. Two articles with
# the same topic hash within a recent window are the SAME news event reported
# by different sources — we link them as corroborating sources of one record,
# not separate cases.

# Stopwords that should NOT count toward topic identity.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "for",
        "to",
        "in",
        "on",
        "at",
        "by",
        "with",
        "from",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "but",
        "if",
        "then",
        "after",
        "before",
        "more",
        "most",
        "all",
        "any",
        "some",
        "no",
        "not",
        "new",
        "old",
        "first",
        "second",
        "third",
        "now",
        "us",
        "uk",  # too generic
        "says",
        "said",
        "say",
        "tests",
        "test",
        "tested",
        "case",
        "cases",
        "video",
        "live",
        "latest",
        "update",
        "updates",
        "news",
        "report",
        "reports",
        "what",
        "who",
        "how",
        "why",
        "where",
        "when",
        "amid",
        "could",
        "should",
        "will",
        "would",
        "may",
        "might",
        "must",
    }
)
_PUNCT = re.compile(r"[^\w\s]")


def title_topic_tokens(title: str) -> list[str]:
    """Normalise a title to its content tokens for similarity comparison."""
    if not title:
        return []
    lowered = title.lower()
    no_punct = _PUNCT.sub(" ", lowered)
    tokens = no_punct.split()
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]


def topic_hash(title: str) -> str:
    """64-bit hex hash of the sorted, deduplicated content tokens of a title.

    Two articles with the same topic hash were saying the same thing.
    Used as a dedup key over a recent time window (e.g., 7 days).
    """
    tokens = sorted(set(title_topic_tokens(title)))
    if not tokens:
        return ""
    joined = " ".join(tokens)
    return hashlib.blake2s(joined.encode("utf-8"), digest_size=8).hexdigest()


# Heuristic case-count + death-count extraction. Surfaced as a CLAIM that
# an analyst reviews, NEVER treated as authoritative on its own.
_NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "hundred": 100,
}
_CASE_PHRASES = (
    r"cases?\s+confirmed",
    r"confirmed\s+cases?",
    r"cases?\s+of\s+hantavirus",
    r"cases?\s+have\s+been\s+confirmed",
    r"positive\s+tests?",
    r"test(?:ed)?\s+positive",
    r"infected",
)
_DEATH_PHRASES = (
    r"deaths?",
    r"died",
    r"fatalit(?:ies|y)",
    r"killed",
)


def _extract_count_near(text: str, phrases: tuple[str, ...]) -> int | None:
    """Find a number (digit or word) within 5 tokens of any phrase. Best match."""
    if not text:
        return None
    lower = text.lower()
    best: int | None = None
    for phrase in phrases:
        pattern = re.compile(
            r"(?:(\d+)|(" + "|".join(_NUMBER_WORDS) + r"))\s+(?:\w+\s+){0,5}?" + phrase,
            re.IGNORECASE,
        )
        for m in pattern.finditer(lower):
            digit, word = m.group(1), m.group(2)
            value: int | None = None
            if digit:
                try:
                    value = int(digit)
                except ValueError:
                    continue
            elif word:
                value = _NUMBER_WORDS.get(word)
            if value is not None and (best is None or value > best):
                best = value
    return best


def extract_case_count_claim(text: str) -> int | None:
    """Heuristic. Surfaces as a CLAIM; analyst reviews before promotion."""
    return _extract_count_near(text, _CASE_PHRASES)


def extract_death_count_claim(text: str) -> int | None:
    return _extract_count_near(text, _DEATH_PHRASES)


def parse_date_safe(s: str, *fmts: str) -> date | None:
    """Try each format string; return the first match, else None.

    We discard the time portion so the lack of timezone is harmless. Single
    point of `noqa: DTZ007` for the whole codebase.
    """
    if not s:
        return None
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()  # noqa: DTZ007
        except (TypeError, ValueError):
            continue
    return None


# Country name -> ISO 3166-1 alpha-2. Longest-first matching avoids the
# 'us' / 'united states' collision.
_COUNTRY_MAP: dict[str, str] = {
    "argentina": "AR",
    "chile": "CL",
    "brazil": "BR",
    "uruguay": "UY",
    "paraguay": "PY",
    "bolivia": "BO",
    "peru": "PE",
    "ecuador": "EC",
    "panama": "PA",
    "colombia": "CO",
    "venezuela": "VE",
    "united states": "US",
    "usa": "US",
    "u.s.": "US",
    "us": "US",
    "canada": "CA",
    "mexico": "MX",
    "germany": "DE",
    "finland": "FI",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "iceland": "IS",
    "france": "FR",
    "spain": "ES",
    "italy": "IT",
    "russia": "RU",
    "china": "CN",
    "south korea": "KR",
    "korea": "KR",
    "japan": "JP",
    "united kingdom": "GB",
    "great britain": "GB",
    "britain": "GB",
    "british": "GB",
    "uk": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "netherlands": "NL",
    "belgium": "BE",
    "ireland": "IE",
    "austria": "AT",
    "switzerland": "CH",
    "poland": "PL",
    "czech republic": "CZ",
    "slovakia": "SK",
    "slovenia": "SI",
    "croatia": "HR",
    "serbia": "RS",
    "bosnia": "BA",
    "montenegro": "ME",
    "greece": "GR",
    "turkey": "TR",
    "australia": "AU",
    "new zealand": "NZ",
    "india": "IN",
    "indonesia": "ID",
    "thailand": "TH",
    "vietnam": "VN",
    "philippines": "PH",
    "malaysia": "MY",
    "singapore": "SG",
    "south africa": "ZA",
}

# Serotype detection: most specific terms first.
_SEROTYPE_MAPPING: list[tuple[tuple[str, ...], str]] = [
    (("andes virus", "andv"), "ANDV"),
    (("sin nombre", "snv"), "SNV"),
    (("puumala", "puuv"), "PUUV"),
    (("hantaan", "htnv"), "HTNV"),
    (("seoul virus", "seov"), "SEOV"),
    (("dobrava", "dobv"), "DOBV"),
    (("laguna negra", "lanv"), "LANV"),
    (("choclo", "chov"), "CHOV"),
    (("bayou", "bayv"), "BAYV"),
    (("black creek canal", "bccv"), "BCCV"),
    (("new york virus", "ny-1", "ny1"), "NY-1"),
    (("tula", "tulv"), "TULV"),
]

_REGION_PAREN = re.compile(r"\(([^)]+)\)")


def detect_country(text: str) -> str | None:
    """Find the first matching country name. Longest-first to avoid collisions."""
    if not text:
        return None
    lower = text.lower()
    for name in sorted(_COUNTRY_MAP.keys(), key=len, reverse=True):
        if name in lower:
            return _COUNTRY_MAP[name]
    return None


def detect_serotype(text: str) -> str | None:
    if not text:
        return None
    lower = text.lower()
    for needles, code in _SEROTYPE_MAPPING:
        if any(n in lower for n in needles):
            return code
    return None


def extract_region(text: str) -> str | None:
    if not text:
        return None
    m = _REGION_PAREN.search(text)
    if m:
        return m.group(1).strip()
    return None
