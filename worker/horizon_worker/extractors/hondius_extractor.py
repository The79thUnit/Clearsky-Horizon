"""
MV Hondius hantavirus cluster — structured-fact extractor.

Reads case_reports (the ingested article corpus), pulls out:

  * country-level case totals  ("X confirmed in Y", "X deaths in Y")
  * new port calls             ("ship docked at <port> on <date>")
  * new death events           ("X passenger dies in <location>")
  * evacuation events          ("N evacuated from <port>")
  * repatriation flights       ("N flown from <port> to <country>")

…and writes each to extraction_proposals. High-confidence proposals (from
NATO A1/A2/B1/B2 sources, ie. WHO/ECDC/CDC/PAHO) corroborated by at least
one other independent source within 48h are auto-applied to:

  - incident_countries (running confirmed/suspected/death counts)
  - entities          (new death_event / port entities)
  - relationships     (new port_called rows on the vessel)

This closes the loop between the existing live article ingestion
(50+ Celery beat connectors) and the incident ontology that drives the
map. Adding a new country case = a new red pin appearing automatically
within ~15 minutes of WHO publishing.

Version pinned in EXTRACTOR_VERSION so an upgrade re-processes corpus.
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

log = logging.getLogger("horizon.extractor.hondius")

EXTRACTOR_VERSION = "hondius-v1.6"

# Cluster-tie scoring (Phoenix rule 12 May 2026):
# A proposal can only auto-update the ontology if the article it came
# from is provably tied to the MV Hondius cluster. The score is set per
# article in _classify_tie() and copied onto every proposal it produces.
#
#   STRONG = 1.0  — explicit ship / port / operator mention
#   MEDIUM = 0.5  — hantavirus + repatriation + route country
#   WEAK   = 0.0  — hantavirus alone; we don't even produce proposals
STRONG_TIE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE) for p in (
        r"\bm\.?\s*v\.?\s*hondius\b",
        r"\bhondius\b",
        r"\boceanwide\s+expeditions?\b",
        r"\bdutch\s+cruise\s+ship\b",
        r"\bhantavirus[\s\-]+(?:hit\s+|stricken\s+|struck\s+)?cruise\b",
        r"\bcruise\s+ship.{0,40}hantavirus\b",
        r"\bhantavirus.{0,40}cruise\s+ship\b",
        r"\bpolar\s+expedition\b",
        # Route-port names + cruise/ship context within 40 chars
        r"\b(?:ushuaia|tristan\s+da\s+cunha|saint\s+helena|st\.?\s+helena|"
        r"jamestown|ascension\s+island|georgetown|praia|cape\s+verde|cabo\s+verde|"
        r"tenerife|santa\s+cruz\s+de\s+tenerife|rotterdam)\b"
        r".{0,60}(?:cruise|ship|vessel|hondius|outbreak)",
    )
)
MEDIUM_TIE_KEYWORDS = (
    "evacuat", "repatriat", "quarantine", "isolat", "flown\\s+home",
    "passenger", "outbreak", "cluster",
)
MEDIUM_TIE_COUNTRIES_RE = re.compile(
    r"\b(?:netherlands|holland|dutch|france|french|"
    r"united\s+states|usa|americans?|south\s+africa|spain|spanish|"
    r"argentina|argentinian|cape\s+verde|saint\s+helena|"
    r"united\s+kingdom|britain|uk|british)\b",
    re.IGNORECASE,
)


def _classify_tie(text: str) -> tuple[float, str]:
    """
    Return (cluster_tie_score, reason). Score in {1.0, 0.5, 0.0}.
    """
    for pat in STRONG_TIE_PATTERNS:
        m = pat.search(text)
        if m:
            return 1.0, f"strong: {pat.pattern!r} matched at {m.start()}"
    if "hantavirus" not in text.lower():
        return 0.0, "weak: no hantavirus keyword"
    has_kw = any(re.search(kw, text, re.IGNORECASE) for kw in MEDIUM_TIE_KEYWORDS)
    has_country = bool(MEDIUM_TIE_COUNTRIES_RE.search(text))
    if has_kw and has_country:
        return 0.5, "medium: hantavirus + evacuation/repatriation context + route country"
    return 0.0, "weak: hantavirus mention without ship / port / repatriation context"
INCIDENT_CODE = "mv-hondius-2026"

# Curated geocoding gazetteer — place name → (lat, lng, country_iso2).
# Restricted to locations realistically in scope of the MV Hondius cluster.
# Adding a new place = one line. Lat/lng pulled from Wikipedia / UN/LOCODE.
# Used by port-call, death-event and flight-route extractors to convert
# place-name mentions into mappable coordinates with HIGH confidence.
KNOWN_LOCATIONS: dict[str, tuple[float, float, str | None]] = {
    # Ports the ship has called at
    "ushuaia":            (-54.8019, -68.3030, "AR"),
    "tristan da cunha":   (-37.0676, -12.3107, "SH"),
    "edinburgh of the seven seas": (-37.0676, -12.3107, "SH"),
    "saint helena":       (-15.9252,  -5.7281, "SH"),
    "st helena":          (-15.9252,  -5.7281, "SH"),
    "st. helena":         (-15.9252,  -5.7281, "SH"),
    "jamestown":          (-15.9252,  -5.7281, "SH"),
    "ascension island":   ( -7.9286, -14.4146, "SH"),
    "ascension":          ( -7.9286, -14.4146, "SH"),
    "georgetown":         ( -7.9286, -14.4146, "SH"),
    "praia":              ( 14.9177, -23.5092, "CV"),
    "cape verde":         ( 14.9177, -23.5092, "CV"),
    "cabo verde":         ( 14.9177, -23.5092, "CV"),
    "tenerife":           ( 28.4682, -16.2546, "ES"),
    "santa cruz de tenerife": ( 28.4682, -16.2546, "ES"),
    "rotterdam":          ( 51.9244,   4.4777, "NL"),
    # Repatriation / treatment destinations
    "cape town":          (-33.9249,  18.4241, "ZA"),
    "groote schuur":      (-33.9396,  18.4644, "ZA"),
    "groote schuur hospital": (-33.9396,  18.4644, "ZA"),
    "amsterdam":          ( 52.3676,   4.9041, "NL"),
    "lumc":               ( 52.1690,   4.4790, "NL"),
    "amc":                ( 52.2967,   4.9609, "NL"),
    "paris":              ( 48.8566,   2.3522, "FR"),
    "bichat":             ( 48.8989,   2.3360, "FR"),
    "london":             ( 51.5074,  -0.1278, "GB"),
    "brize norton":       ( 51.7500,  -1.5837, "GB"),
    "arrowe park":        ( 53.3674,  -3.0944, "GB"),
    "lisbon":             ( 38.7813,  -9.1359, "PT"),
    "boston":             ( 42.3601, -71.0589, "US"),
    "new york":           ( 40.7128, -74.0060, "US"),
    "berlin":             ( 52.5200,  13.4050, "DE"),
    "madrid":             ( 40.4168,  -3.7038, "ES"),
}
# Build a regex that recognises ANY of these place names (case-insensitive,
# whole-word). Sorted by length so longer names match first ("st. helena"
# before "helena" alone).
_LOCATION_NAMES_SORTED = sorted(KNOWN_LOCATIONS.keys(), key=len, reverse=True)
LOCATION_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(n) for n in _LOCATION_NAMES_SORTED) + r")\b",
    re.IGNORECASE,
)

# Phrase patterns identifying an article as MV Hondius-relevant. Title OR
# summary must contain at least one. Patterns are REGEX so dashes / spacing
# in real headlines ("hantavirus-hit cruise") match.
HONDIUS_PATTERNS: tuple[str, ...] = (
    r"\bhondius\b",
    r"\bmv\s+hondius\b",
    r"\bpolar\s+expedition\b",
    r"\boceanwide\s+expedition",
    r"\bhantavirus[\s\-]+(?:hit\s+|stricken\s+)?cruise\b",
    r"\bcruise[\s\-]+(?:ship\s+)?hantavirus\b",
    r"\bdutch\s+cruise\s+ship\b",
    r"\bcruise\s+ship.{0,40}hantavirus",
    r"\bhantavirus.{0,40}cruise\s+ship",
)
HONDIUS_PATTERN_RE = re.compile("|".join(HONDIUS_PATTERNS), re.IGNORECASE)

# Country name → ISO2 mapping. Restricted to countries in scope of this
# cluster — keeps the matcher tight and reduces false positives. (Adding
# new countries = one line.)
COUNTRY_PATTERNS: dict[str, str] = {
    # Pattern → ISO-2
    r"\b(?:netherlands|the netherlands|holland|dutch)\b":   "NL",
    r"\b(?:france|french)\b":                                "FR",
    r"\b(?:united states|usa|u\.s\.|u\.s\.a\.|americans?)\b": "US",
    r"\b(?:south africa|south african|s\. africa)\b":        "ZA",
    r"\b(?:united kingdom|britain|uk|british)\b":            "GB",
    r"\b(?:germany|german)\b":                               "DE",
    r"\b(?:spain|spanish)\b":                                "ES",
    r"\b(?:argentina|argentine|argentinian)\b":              "AR",
    r"\b(?:portugal|portuguese)\b":                          "PT",
    r"\b(?:cape verde|cabo verde)\b":                        "CV",
    r"\b(?:saint helena|st\.? helena)\b":                    "SH",
    r"\b(?:tristan da cunha)\b":                             "SH",
    r"\b(?:ascension island)\b":                             "SH",
}

# Number-word fallback (article-style English: "three confirmed", "two died")
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}
NUMBER_WORD_RE = "|".join(NUMBER_WORDS.keys())

# Fact-extraction regexes. Each is a LIST of patterns to match different
# real-world phrasings. Real headlines mix verb-first ("Spain confirms one
# new case") and adjective-first ("12 confirmed cases") forms.

# Confirmed cases — try several wordings
CONFIRMED_PATTERNS = [
    # "X confirmed/lab-confirmed cases"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+(?:additional |new |more |further )?"
    r"(?:confirmed|laboratory[- ]confirmed|lab[- ]confirmed|pcr[- ]confirmed|positive)\s+"
    r"(?:hantavirus\s+)?(?:cases?|patients?|infections?)\b",
    # "confirms X (new) cases" / "confirmed X cases" — verb-first
    rf"\b(?:confirms?|confirmed|reports?|reported|announces?|announced|detected?)\s+"
    r"(?:a\s+)?(?P<count>\d{1,4}|" + NUMBER_WORD_RE + r")\s+"
    r"(?:additional |new |more |further )?"
    r"(?:confirmed |laboratory[- ]confirmed |lab[- ]confirmed |pcr[- ]confirmed )?"
    r"(?:hantavirus\s+)?(?:cases?|infections?|patients?)\b",
    # "X new cases reported / detected"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+new\s+"
    r"(?:hantavirus\s+)?(?:cases?|infections?|patients?)\b",
]

# Probable / suspected
SUSPECTED_PATTERNS = [
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+(?:additional |new |more |further )?"
    r"(?:probable|suspected|under\s+investigation|presumed|presumptive)\s+"
    r"(?:hantavirus\s+)?(?:cases?|patients?|infections?)?",
    rf"\b(?:probable|suspected|under\s+investigation)\s+cases?\s+"
    r"(?:rose|increased|stood)\s+to\s+(?P<count>\d{1,4}|" + NUMBER_WORD_RE + r")",
]

# Deaths / fatalities
DEATHS_PATTERNS = [
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+"
    r"(?:passengers?\s+|crew\s+|people\s+|patients?\s+|persons?\s+|individuals?\s+|deaths?\s+|fatalities\s+)?"
    r"(?:dead|deaths?|fatalities|fatality|died|killed|deceased|perished)\b",
    rf"\b(?:death|fatality)\s+toll\s+(?:rose|increased|stood)\s+to\s+"
    r"(?P<count>\d{1,4}|" + NUMBER_WORD_RE + r")",
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})(?:st|nd|rd|th)?\s+"
    r"(?:death|fatality|fatal\s+case)",
]

# --- Additional confirmed patterns: real headline forms we observed in
#     the live corpus (The Independent, The Sun, BBC, NBC, Al Jazeera, etc).
CONFIRMED_PATTERNS += [
    # "one tests positive" / "N tested positive for hantavirus"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+"
    r"(?:passengers?\s+|crew\s+members?\s+|americans?\s+|britons?\s+|nationals?\s+|people\s+|persons?\s+)?"
    r"(?:tests?|tested|testing|test)\s+(?:positive)\b",
    # "X-th case" — ordinal denoting cumulative confirmed count
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})(?:st|nd|rd|th)\s+"
    r"(?:hantavirus\s+)?(?:confirmed\s+)?cases?\b",
    # "N more / N additional confirmed"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+(?:more|additional|further)\s+"
    r"(?:confirmed\s+)?cases?\b",
    # "(hantavirus) cases rise/rises/rose/climb/climbs/jump/jumps/grew to N"
    rf"\b(?:hantavirus\s+)?(?:cases?|infections?|confirmed)\s+"
    r"(?:rise|rises|rose|risen|climb|climbs|climbed|jump|jumps|jumped|grew|grow|grown|increased|now\s+(?:stands?\s+)?at|stand\s+at)\s+"
    r"(?:to\s+)?(?P<count>\d{1,4}|" + NUMBER_WORD_RE + r")",
    # "N hantavirus cases" / "N hantavirus infections"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+hantavirus\s+(?:cases?|infections?|patients?)\b",
]

# Patterns that imply count=1 (singular "reports new case", "first hantavirus case")
SINGLE_CASE_PATTERNS = [
    # "reports new hantavirus case" — no explicit number, means 1
    r"\b(?:reports?|reported|announces?|announced|confirms?|confirmed|detected?)\s+"
    r"(?:a\s+)?new\s+(?:hantavirus\s+)?(?:case|infection|patient)\b",
    # "new hantavirus case" as standalone phrase
    r"\bnew\s+(?:hantavirus|andv|ANDV)\s+case\b",
]
SINGLE_CASE_RES = [re.compile(p, re.IGNORECASE) for p in SINGLE_CASE_PATTERNS]

# Ordinal-singular pattern: "first hantavirus case" maps to count=N
ORDINAL_MAP = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
ORDINAL_RE = re.compile(
    r"\b(?P<ord>first|second|third|fourth|fifth)\s+(?:hantavirus\s+|andv\s+)?"
    r"(?:confirmed\s+|lab[- ]confirmed\s+)?case\b",
    re.IGNORECASE,
)

# --- Additional suspected patterns: quarantine + isolation language
SUSPECTED_PATTERNS += [
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+"
    r"(?:passengers?|crew\s+members?|crew|americans?|britons?|french|dutch|"
    r"germans?|spanish|portuguese|people|nationals?|patients?|individuals?|persons?)\s+"
    r"(?:are\s+|have\s+been\s+|been\s+)?"
    r"(?:quarantined|self[- ]isolat\w*|isolat\w*|in\s+isolation|placed\s+under\s+observation)",
    # "N possible / potential cases"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+"
    r"(?:possible|potential|probable|likely|presumptive)\s+"
    r"(?:hantavirus\s+)?(?:cases?|infections?|patients?)?\b",
]

CONFIRMED_RES = [re.compile(p, re.IGNORECASE) for p in CONFIRMED_PATTERNS]
SUSPECTED_RES = [re.compile(p, re.IGNORECASE) for p in SUSPECTED_PATTERNS]
DEATHS_RES = [re.compile(p, re.IGNORECASE) for p in DEATHS_PATTERNS]


# ---- Port call patterns ----------------------------------------------------
# Detect when an article mentions the ship calling at a specific port.
PORT_CALL_PATTERNS = [
    # "docked at / arrived at / called at / put in at <place>"
    r"\b(?:docked|arrived|put\s+in|moored|berthed|made\s+port|called|stopped)\s+(?:at|in|in\s+at)\s+(?P<place>[A-Z][A-Za-z\.\s'-]{2,40})",
    # "ship diverted / detoured / re-routed to <place>"
    r"\b(?:diverted|detoured|re-routed|rerouted|headed|sailed|en\s+route)\s+(?:to|towards|for)\s+(?P<place>[A-Z][A-Za-z\.\s'-]{2,40})",
    # "expected to dock in <place> on <date>"
    r"\b(?:expected|due|scheduled|anticipated)\s+to\s+(?:arrive|dock|port|call)\s+(?:at|in)\s+(?P<place>[A-Z][A-Za-z\.\s'-]{2,40})",
]
PORT_CALL_RES = [re.compile(p) for p in PORT_CALL_PATTERNS]

# ---- Evacuation / flight patterns -----------------------------------------
EVACUATION_PATTERNS = [
    # "N passengers / crew / people evacuated / flown / repatriated"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+"
    r"(?:passengers?|crew\s+members?|crew|people|patients?|individuals?|persons?|nationals?)\s+"
    r"(?:were\s+|have\s+been\s+|been\s+)?"
    r"(?:evacuated|flown\s+home|flown\s+back|repatriated|airlifted|disembarked|removed)",
    # "evacuated/flew N from <origin> to <destination>"
    rf"\b(?:evacuated|flew|airlifted|repatriated|flown)\s+(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+"
    r"(?:passengers?|people|patients?|crew\s+members?|crew)\s+"
    r"(?:from|via)\s+(?P<origin>[A-Z][A-Za-z\.\s'-]{2,40})",
]
EVACUATION_RES = [re.compile(p, re.IGNORECASE) for p in EVACUATION_PATTERNS]

# "<N> flown to <destination>" — destination-tagged
FLIGHT_DESTINATION_PATTERNS = [
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})\s+"
    r"(?:passengers?|people|patients?|nationals?|evacuees?)\s+"
    r"(?:were\s+|have\s+been\s+)?(?:flown|repatriated|airlifted|transported|sent)\s+"
    r"(?:to|back\s+to|home\s+to)\s+(?P<destination>[A-Z][A-Za-z\.\s'-]{2,40})",
]
FLIGHT_DESTINATION_RES = [re.compile(p, re.IGNORECASE) for p in FLIGHT_DESTINATION_PATTERNS]

# ---- Death location patterns ----------------------------------------------
DEATH_LOCATION_PATTERNS = [
    # "died/passed in/at <place>"
    r"\b(?:died|passed\s+away|succumbed|deceased|killed)\s+(?:in|at|aboard|on)\s+(?P<place>[A-Z][A-Za-z\.\s'-]{2,40})",
    # "<N>(th|st) death (reported|confirmed) in <place>"
    rf"\b(?P<count>\d{{1,4}}|{NUMBER_WORD_RE})(?:st|nd|rd|th)?\s+(?:death|fatality)\s+"
    r"(?:reported|confirmed|recorded|occurred|in)\s+(?:in|at)?\s*(?P<place>[A-Z][A-Za-z\.\s'-]{2,40})",
]
DEATH_LOCATION_RES = [re.compile(p) for p in DEATH_LOCATION_PATTERNS]


@dataclass(frozen=True, slots=True)
class CaseReport:
    """Subset of a case_reports row used by the extractor."""

    id: str
    title: str
    summary: str
    country_iso2: str | None
    source_code: str
    nato_reliability: str | None
    nato_credibility: str | None
    raw_url: str
    reported_date: datetime | None
    ingested_at: datetime


@dataclass
class Proposal:
    """One structured fact extracted from one article."""

    case_id: str
    fact_type: str
    country_iso2: str | None = None
    value_numeric: int | None = None
    value_date: datetime | None = None
    value_text: str | None = None
    value_lat: float | None = None
    value_lng: float | None = None
    source_code: str = ""
    source_url: str = ""
    nato_reliability: str | None = None
    nato_credibility: str | None = None
    extractor_confidence: float = 0.5
    cluster_tie_score: float = 0.0
    cluster_tie_reason: str = ""
    notes: str = ""

    @property
    def fingerprint(self) -> str:
        """Stable hash so re-running the extractor is idempotent."""
        parts = [
            EXTRACTOR_VERSION,
            self.case_id,
            self.fact_type,
            self.country_iso2 or "",
            str(self.value_numeric) if self.value_numeric is not None else "",
            self.value_text or "",
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def _normalise(text: str) -> str:
    """Strip accents, collapse whitespace — makes regexes work on real prose."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


def _parse_count(token: str) -> int | None:
    token = token.lower().strip()
    if token in NUMBER_WORDS:
        return NUMBER_WORDS[token]
    if token.isdigit():
        try:
            return int(token)
        except ValueError:
            return None
    return None


def _is_relevant(report: CaseReport) -> bool:
    """
    Return True if the article is about the MV Hondius cluster.

    The SQL pre-filter in tasks/extraction.py already restricts to articles
    matching 'hondius' OR ('hantavirus' AND 'cruise'). So at this stage we
    only reject articles whose title is clearly about UNRELATED hantavirus
    activity (e.g., a Korea HFRS update). Anything that mentions hantavirus
    AND any cruise/cluster/outbreak-context word passes.
    """
    haystack = _normalise(f"{report.title} {report.summary}").lower()
    if "hondius" in haystack:
        return True
    has_hanta = "hantavirus" in haystack
    if not has_hanta:
        return False
    # Hantavirus + any of these contextual words → the Hondius cluster
    return any(
        kw in haystack for kw in (
            "cruise", "ship", "vessel", "outbreak", "cluster",
            "evacuat", "passenger", "polar", "expedition", "oceanwide",
            "ushuaia", "tenerife", "tristan", "ascension", "st helena",
            "saint helena", "cape verde", "rotterdam",
        )
    )


def _find_country_context(text: str, match: re.Match[str], window: int = 80) -> str | None:
    """
    Find the country mentioned closest to a numeric match. Falls back to the
    article's overall country_iso2 if no nearby country word is present.
    """
    text_norm = _normalise(text).lower()
    start = max(0, match.start() - window)
    end = min(len(text_norm), match.end() + window)
    near = text_norm[start:end]
    for pat, iso in COUNTRY_PATTERNS.items():
        if re.search(pat, near, re.IGNORECASE):
            return iso
    return None


def _geocode_place(raw_name: str) -> tuple[float, float, str | None] | None:
    """
    Return (lat, lng, country_iso2) for a place name, or None if it isn't
    in the curated gazetteer. Strips trailing punctuation/articles so
    things like "Saint Helena," or "the Cape Town hospital" still match.
    """
    if not raw_name:
        return None
    name = raw_name.lower().strip()
    # Strip leading article + trailing punctuation
    name = re.sub(r"^(the\s+)", "", name)
    name = re.sub(r"[\.,;:!?)]+$", "", name).strip()
    # Try exact match first
    if name in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[name]
    # Try recognising any known location SUBSTRING (catches "Saint Helena harbour")
    m = LOCATION_RE.search(name)
    if m:
        return KNOWN_LOCATIONS[m.group(0).lower()]
    return None


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def extract(report: CaseReport) -> list[Proposal]:
    """Extract every structured fact we can find in one article."""
    if not _is_relevant(report):
        return []

    text = _normalise(f"{report.title}. {report.summary or ''}")

    # STRICT cluster-tie gate: weak ties (score 0) produce ZERO proposals.
    # No silent assumption that an article is about the Hondius cluster
    # just because it mentions hantavirus.
    tie_score, tie_reason = _classify_tie(text)
    if tie_score <= 0.0:
        return []

    out: list[Proposal] = []

    def _make(
        fact_type: str,
        count: int,
        country: str | None,
        match: re.Match[str],
    ) -> Proposal:
        nearby_country = country
        confidence = 0.85 if nearby_country else 0.40
        return Proposal(
            case_id=report.id,
            fact_type=fact_type,
            country_iso2=nearby_country,
            value_numeric=count,
            source_code=report.source_code,
            source_url=report.raw_url,
            nato_reliability=report.nato_reliability,
            nato_credibility=report.nato_credibility,
            extractor_confidence=confidence,
            cluster_tie_score=tie_score,
            cluster_tie_reason=tie_reason,
            notes=f"Span: {text[max(0,match.start()-40):match.end()+40]!r}",
        )

    seen_spans: set[tuple[int, int]] = set()

    def _resolve_country(m: re.Match[str]) -> str | None:
        """
        Resolve the most specific country for a count match.

        Priority:
          1. Country name within ±80 chars of the match (most precise).
          2. Country name anywhere in the full article text, but ONLY if
             exactly one unique country is mentioned (avoids wrong attribution
             in multi-country articles like "NL 3 cases, FR 2 cases").

        NOTE: Pass 3 (article-level metadata fallback) is intentionally
        omitted. An article's connector country_iso2 (e.g., 'US' for NBC
        News) indicates the article's origin, NOT which country the case/
        death counts belong to. Using it caused cluster-total counts from
        US-origin media to be attributed to the US as per-country counts.
        Without explicit in-text attribution, country=None is returned and
        the proposal is stored for analyst review but NOT auto-applied.

        Returns None if the country is genuinely ambiguous.
        """
        # --- Pass 1: narrow window (original behaviour) ---------------------
        found = _find_country_context(text, m)
        if found:
            return found

        # --- Pass 2: full-text scan with ambiguity guard --------------------
        full_text_countries: set[str] = set()
        for pat, iso in COUNTRY_PATTERNS.items():
            if re.search(pat, text, re.IGNORECASE):
                full_text_countries.add(iso)
        if len(full_text_countries) == 1:
            return next(iter(full_text_countries))

        return None

    # 1. Count-based facts (confirmed / suspected / deaths)
    for regex_list, fact_type in (
        (CONFIRMED_RES, "confirmed_count"),
        (SUSPECTED_RES, "suspected_count"),
        (DEATHS_RES, "death_count"),
    ):
        for regex in regex_list:
            for m in regex.finditer(text):
                if (m.start(), m.end()) in seen_spans:
                    continue
                seen_spans.add((m.start(), m.end()))
                n = _parse_count(m.group("count"))
                if n is None or n > 200:
                    continue
                country = _resolve_country(m)
                out.append(_make(fact_type, n, country, m))

    # 1a. Singular "reports new case" → count = 1
    for regex in SINGLE_CASE_RES:
        for m in regex.finditer(text):
            if (m.start(), m.end()) in seen_spans:
                continue
            seen_spans.add((m.start(), m.end()))
            country = _resolve_country(m)
            out.append(_make("confirmed_count", 1, country, m))

    # 1b. Ordinal "first/second/third hantavirus case" → cumulative count
    for m in ORDINAL_RE.finditer(text):
        if (m.start(), m.end()) in seen_spans:
            continue
        seen_spans.add((m.start(), m.end()))
        n = ORDINAL_MAP.get(m.group("ord").lower())
        if n is None:
            continue
        country = _resolve_country(m)
        out.append(_make("confirmed_count", n, country, m))

    # 2. Port-call mentions — only if the named place is in our gazetteer
    for regex in PORT_CALL_RES:
        for m in regex.finditer(text):
            if (m.start(), m.end()) in seen_spans:
                continue
            seen_spans.add((m.start(), m.end()))
            place = m.group("place")
            geo = _geocode_place(place)
            if geo is None:
                continue
            lat, lng, iso = geo
            out.append(Proposal(
                case_id=report.id,
                fact_type="port_call",
                country_iso2=iso,
                value_text=_normalise(place)[:80],
                value_lat=lat,
                value_lng=lng,
                source_code=report.source_code,
                source_url=report.raw_url,
                nato_reliability=report.nato_reliability,
                nato_credibility=report.nato_credibility,
                extractor_confidence=0.85,
                cluster_tie_score=tie_score,
                cluster_tie_reason=tie_reason,
                notes=f"Span: {text[max(0,m.start()-30):m.end()+30]!r}",
            ))

    # 3. Death-event location — needs a recognised location near "died/death"
    for regex in DEATH_LOCATION_RES:
        for m in regex.finditer(text):
            if (m.start(), m.end()) in seen_spans:
                continue
            seen_spans.add((m.start(), m.end()))
            place = m.group("place") if "place" in m.groupdict() else None
            if not place:
                continue
            geo = _geocode_place(place)
            if geo is None:
                continue
            lat, lng, iso = geo
            out.append(Proposal(
                case_id=report.id,
                fact_type="death_event",
                country_iso2=iso,
                value_text=_normalise(place)[:80],
                value_lat=lat,
                value_lng=lng,
                source_code=report.source_code,
                source_url=report.raw_url,
                nato_reliability=report.nato_reliability,
                nato_credibility=report.nato_credibility,
                extractor_confidence=0.85,
                cluster_tie_score=tie_score,
                cluster_tie_reason=tie_reason,
                notes=f"Span: {text[max(0,m.start()-30):m.end()+30]!r}",
            ))

    # 4. Evacuation count (cluster-wide; no destination yet)
    for regex in EVACUATION_RES:
        for m in regex.finditer(text):
            if (m.start(), m.end()) in seen_spans:
                continue
            seen_spans.add((m.start(), m.end()))
            n = _parse_count(m.group("count"))
            if n is None or n > 500:
                continue
            origin = m.groupdict().get("origin")
            origin_geo = _geocode_place(origin) if origin else None
            country = origin_geo[2] if origin_geo else _find_country_context(text, m)
            out.append(Proposal(
                case_id=report.id,
                fact_type="evacuation_event",
                country_iso2=country,
                value_numeric=n,
                value_text=(_normalise(origin)[:80] if origin else None),
                value_lat=origin_geo[0] if origin_geo else None,
                value_lng=origin_geo[1] if origin_geo else None,
                source_code=report.source_code,
                source_url=report.raw_url,
                nato_reliability=report.nato_reliability,
                nato_credibility=report.nato_credibility,
                extractor_confidence=0.8 if origin_geo else 0.55,
                cluster_tie_score=tie_score,
                cluster_tie_reason=tie_reason,
                notes=f"Span: {text[max(0,m.start()-30):m.end()+30]!r}",
            ))

    # 5. Flight repatriation route (origin known + destination named)
    for regex in FLIGHT_DESTINATION_RES:
        for m in regex.finditer(text):
            if (m.start(), m.end()) in seen_spans:
                continue
            seen_spans.add((m.start(), m.end()))
            n = _parse_count(m.group("count"))
            if n is None or n > 500:
                continue
            dest = m.groupdict().get("destination")
            dest_geo = _geocode_place(dest) if dest else None
            if dest_geo is None:
                continue
            lat, lng, iso = dest_geo
            out.append(Proposal(
                case_id=report.id,
                fact_type="flight_route",
                country_iso2=iso,
                value_numeric=n,
                value_text=_normalise(dest)[:80],
                value_lat=lat,
                value_lng=lng,
                source_code=report.source_code,
                source_url=report.raw_url,
                nato_reliability=report.nato_reliability,
                nato_credibility=report.nato_credibility,
                extractor_confidence=0.8,
                cluster_tie_score=tie_score,
                cluster_tie_reason=tie_reason,
                notes=f"Span: {text[max(0,m.start()-30):m.end()+30]!r}",
            ))

    return out


def extract_many(reports: Iterable[CaseReport]) -> list[Proposal]:
    """Convenience: extract over a corpus, return all proposals flat."""
    all_proposals: list[Proposal] = []
    for r in reports:
        all_proposals.extend(extract(r))
    return all_proposals
