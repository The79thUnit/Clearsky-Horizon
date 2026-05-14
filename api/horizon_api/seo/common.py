"""Shared SEO helpers: HTML escape, URL builders, country/serotype tables."""

from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime, timezone

BASE_URL = "https://hantavirus.software"

# ISO-2 → (English name, region tag) for the countries plausibly in scope of
# any hantavirus outbreak we'd track. Used to build /countries/{iso} pages
# and to enrich JSON-LD spatialCoverage entries.
COUNTRY_NAMES: dict[str, str] = {
    "AR": "Argentina",
    "AT": "Austria",
    "AU": "Australia",
    "BA": "Bosnia and Herzegovina",
    "BE": "Belgium",
    "BO": "Bolivia",
    "BR": "Brazil",
    "CA": "Canada",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colombia",
    "CV": "Cape Verde",
    "CZ": "Czechia",
    "DE": "Germany",
    "DK": "Denmark",
    "EC": "Ecuador",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GB": "United Kingdom",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "JP": "Japan",
    "KR": "South Korea",
    "KP": "North Korea",
    "MX": "Mexico",
    "NL": "Netherlands",
    "NO": "Norway",
    "NZ": "New Zealand",
    "PA": "Panama",
    "PE": "Peru",
    "PL": "Poland",
    "PT": "Portugal",
    "PY": "Paraguay",
    "RO": "Romania",
    "RU": "Russia",
    "SE": "Sweden",
    "SH": "Saint Helena",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "TR": "Türkiye",
    "UA": "Ukraine",
    "US": "United States",
    "UY": "Uruguay",
    "ZA": "South Africa",
}


# Serotype reference data — one entry per orthohantavirus we describe with
# its own dedicated /hantavirus/{slug} landing page. Each row carries the
# editorial summary that drives the page body + JSON-LD.
SEROTYPES: list[dict[str, str]] = [
    {
        "slug": "andes-virus",
        "code": "ANDV",
        "name": "Andes virus (ANDV)",
        "icd": "B33.4",
        "syndrome": "Hantavirus Pulmonary Syndrome (HPS)",
        "reservoir": "Oligoryzomys longicaudatus (long-tailed pygmy rice rat)",
        "endemic": "Argentina, Chile, southern Patagonia, Tierra del Fuego",
        "cfr": "30 to 50 percent",
        "p2p": (
            "Andes virus is the only orthohantavirus with documented "
            "person-to-person transmission, predominantly between close "
            "household contacts. P2P has been linked to clusters in El "
            "Bolsón, Río Negro Province, Argentina (1996) and in Chile."
        ),
        "summary": (
            "Andes virus is the most lethal hantavirus serotype recognised "
            "in the Americas. It is endemic to the southern cone of South "
            "America and is the primary serotype implicated in the 2026 MV "
            "Hondius cluster. Symptoms appear 1 to 8 weeks after exposure "
            "and progress rapidly to cardiopulmonary collapse without "
            "intensive supportive care."
        ),
        "wikidata": "Q575211",
        "wikipedia": "https://en.wikipedia.org/wiki/Andes_orthohantavirus",
    },
    {
        "slug": "sin-nombre-virus",
        "code": "SNV",
        "name": "Sin Nombre virus (SNV)",
        "icd": "B33.4",
        "syndrome": "Hantavirus Pulmonary Syndrome (HPS)",
        "reservoir": "Peromyscus maniculatus (deer mouse)",
        "endemic": "United States Four Corners region, Canada, Mexico",
        "cfr": "approximately 38 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Sin Nombre virus is the principal cause of Hantavirus "
            "Pulmonary Syndrome in North America. First identified in "
            "1993 during the Four Corners outbreak, it is carried by the "
            "deer mouse Peromyscus maniculatus and transmitted to humans "
            "via aerosolised excreta in enclosed rural structures."
        ),
        "wikidata": "Q1422156",
        "wikipedia": "https://en.wikipedia.org/wiki/Sin_Nombre_orthohantavirus",
    },
    {
        "slug": "puumala-virus",
        "code": "PUUV",
        "name": "Puumala virus (PUUV)",
        "icd": "A98.5",
        "syndrome": "Nephropathia Epidemica (mild HFRS)",
        "reservoir": "Myodes glareolus (bank vole)",
        "endemic": "Scandinavia, Baltic states, central Europe, European Russia",
        "cfr": "less than 1 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Puumala virus is the most common cause of hantavirus disease "
            "in Europe. It produces a milder renal-syndrome variant called "
            "nephropathia epidemica and is associated with cyclical bank "
            "vole population peaks in Finland, Sweden, Germany, and "
            "western Russia."
        ),
        "wikidata": "Q577220",
        "wikipedia": "https://en.wikipedia.org/wiki/Puumala_orthohantavirus",
    },
    {
        "slug": "hantaan-virus",
        "code": "HTNV",
        "name": "Hantaan virus (HTNV)",
        "icd": "A98.5",
        "syndrome": "Haemorrhagic Fever with Renal Syndrome (HFRS)",
        "reservoir": "Apodemus agrarius (striped field mouse)",
        "endemic": "China, Korean peninsula, far-eastern Russia",
        "cfr": "5 to 15 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Hantaan virus is the prototype hantavirus and the most "
            "severe cause of HFRS in east Asia. South Korea licences a "
            "vaccine (Hantavax) targeting this serotype; no antiviral "
            "or vaccine is licensed in Europe or North America."
        ),
        "wikidata": "Q572893",
        "wikipedia": "https://en.wikipedia.org/wiki/Hantaan_orthohantavirus",
    },
    {
        "slug": "seoul-virus",
        "code": "SEOV",
        "name": "Seoul virus (SEOV)",
        "icd": "A98.5",
        "syndrome": "Haemorrhagic Fever with Renal Syndrome (HFRS, mild)",
        "reservoir": "Rattus norvegicus (brown rat), Rattus rattus (black rat)",
        "endemic": "Worldwide via global Rattus distribution",
        "cfr": "1 to 2 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Seoul virus circulates wherever its rat reservoirs do — "
            "effectively global. Outbreaks have been reported in pet-rat "
            "fanciers in the US and UK and in urban populations near port "
            "infrastructure. It causes a milder HFRS than Hantaan virus."
        ),
        "wikidata": "Q1369437",
        "wikipedia": "https://en.wikipedia.org/wiki/Seoul_orthohantavirus",
    },
    {
        "slug": "dobrava-belgrade-virus",
        "code": "DOBV",
        "name": "Dobrava-Belgrade virus (DOBV)",
        "icd": "A98.5",
        "syndrome": "Haemorrhagic Fever with Renal Syndrome (HFRS, severe)",
        "reservoir": "Apodemus flavicollis (yellow-necked mouse)",
        "endemic": "Balkans, central Europe, European Russia",
        "cfr": "10 to 12 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Dobrava-Belgrade virus causes the most severe form of "
            "HFRS in Europe, with case fatality rates approaching Hantaan "
            "virus levels. It is endemic across the Balkans, Slovenia, "
            "and parts of Russia."
        ),
        "wikidata": "Q587283",
        "wikipedia": "https://en.wikipedia.org/wiki/Dobrava-Belgrade_orthohantavirus",
    },
    {
        "slug": "bayou-virus",
        "code": "BAYV",
        "name": "Bayou virus (BAYV)",
        "icd": "B33.4",
        "syndrome": "Hantavirus Pulmonary Syndrome (HPS)",
        "reservoir": "Oryzomys palustris (marsh rice rat)",
        "endemic": "Southeastern United States",
        "cfr": "approximately 33 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Bayou virus is a New World hantavirus first identified in "
            "Louisiana in 1994. It produces HPS with prominent renal "
            "involvement and is carried by the marsh rice rat across the "
            "Gulf Coast and lower Mississippi watershed."
        ),
        "wikidata": "",
        "wikipedia": "",
    },
    {
        "slug": "laguna-negra-virus",
        "code": "LANV",
        "name": "Laguna Negra virus (LANV)",
        "icd": "B33.4",
        "syndrome": "Hantavirus Pulmonary Syndrome (HPS)",
        "reservoir": "Calomys laucha (small vesper mouse)",
        "endemic": "Paraguay, Bolivia, Argentina",
        "cfr": "10 to 20 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Laguna Negra virus is a South American HPS-causing "
            "orthohantavirus identified in Paraguay in 1995. It is one of "
            "several New World hantaviruses circulating in Calomys rodent "
            "populations across the Gran Chaco."
        ),
        "wikidata": "",
        "wikipedia": "",
    },
    {
        "slug": "choclo-virus",
        "code": "CHOV",
        "name": "Choclo virus (CHOV)",
        "icd": "B33.4",
        "syndrome": "Hantavirus Pulmonary Syndrome (HPS, milder)",
        "reservoir": "Oligoryzomys fulvescens (fulvous pygmy rice rat)",
        "endemic": "Panama, Costa Rica",
        "cfr": "approximately 10 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Choclo virus is the principal HPS-causing hantavirus in "
            "Panama, identified during the Los Santos outbreaks of 1999. "
            "Disease tends to be milder than Andes-virus HPS, with "
            "lower case fatality."
        ),
        "wikidata": "",
        "wikipedia": "",
    },
    {
        "slug": "tula-virus",
        "code": "TULV",
        "name": "Tula virus (TULV)",
        "icd": "A98.5",
        "syndrome": "Rarely causes human disease",
        "reservoir": "Microtus arvalis (common vole)",
        "endemic": "Europe, western Russia",
        "cfr": "very low (few documented cases)",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Tula virus is widespread in European vole populations but "
            "rarely causes recognised human disease. Sporadic cases of "
            "mild HFRS-like illness have been reported in immunocompromised "
            "patients in central Europe."
        ),
        "wikidata": "",
        "wikipedia": "",
    },
    {
        "slug": "saaremaa-virus",
        "code": "SAAV",
        "name": "Saaremaa virus (SAAV)",
        "icd": "A98.5",
        "syndrome": "Haemorrhagic Fever with Renal Syndrome (HFRS, mild)",
        "reservoir": "Apodemus agrarius (striped field mouse)",
        "endemic": "Estonia, Baltic states, Scandinavia, central Europe",
        "cfr": "less than 1 percent",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Saaremaa virus is a less-virulent close relative of Dobrava "
            "virus identified on the Estonian island of Saaremaa. It "
            "produces mild HFRS comparable to Puumala virus."
        ),
        "wikidata": "",
        "wikipedia": "",
    },
    {
        "slug": "black-creek-canal-virus",
        "code": "BCCV",
        "name": "Black Creek Canal virus (BCCV)",
        "icd": "B33.4",
        "syndrome": "Hantavirus Pulmonary Syndrome (HPS)",
        "reservoir": "Sigmodon hispidus (cotton rat)",
        "endemic": "Florida, southeastern United States",
        "cfr": "limited data; few cases",
        "p2p": "No documented person-to-person transmission.",
        "summary": (
            "Black Creek Canal virus is a Florida-endemic HPS-causing "
            "hantavirus identified in 1995. It is one of several "
            "Sigmodon-associated New World orthohantaviruses."
        ),
        "wikidata": "",
        "wikipedia": "",
    },
]


def esc(value: str | None) -> str:
    """HTML-escape a value; empty string for None."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def slugify(value: str) -> str:
    """ASCII slug suitable for URL paths."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "item"


def iso_dt(dt: datetime) -> str:
    """ISO-8601 UTC datetime suitable for sitemap <lastmod> and Atom."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def rfc2822(dt: datetime) -> str:
    """RFC-2822 datetime for RSS <pubDate>."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def country_name(iso2: str | None) -> str:
    if iso2 is None:
        return "Unknown"
    return COUNTRY_NAMES.get(iso2.upper(), iso2)


def serotype_by_slug(slug: str) -> dict[str, str] | None:
    for s in SEROTYPES:
        if s["slug"] == slug:
            return s
    return None


def serotype_by_code(code: str | None) -> dict[str, str] | None:
    if code is None:
        return None
    upper = code.upper()
    for s in SEROTYPES:
        if s["code"] == upper:
            return s
    return None
