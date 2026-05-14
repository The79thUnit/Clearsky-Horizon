"""Schema.org JSON-LD builders for HORIZON SEO pages.

Each builder returns a list of @graph nodes ready to splice into
`PageSpec.jsonld_nodes`. They all reference the shared
`https://hantavirus.software/#org` and `#site` identifiers defined in
`html_shell._jsonld_graph()` so the entity graph is fully connected.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .common import BASE_URL, COUNTRY_NAMES, SEROTYPES, country_name


def medical_condition_hantavirus() -> dict[str, Any]:
    return {
        "@type": "MedicalCondition",
        "@id": f"{BASE_URL}/hantavirus#condition",
        "name": "Hantavirus infection",
        "alternateName": [
            "Orthohantavirus infection",
            "Hantavirus disease",
        ],
        "code": [
            {
                "@type": "MedicalCode",
                "codingSystem": "ICD-10",
                "codeValue": "A98.5",
                "name": "Hantavirus disease with renal manifestations (HFRS)",
            },
            {
                "@type": "MedicalCode",
                "codingSystem": "ICD-10",
                "codeValue": "B33.4",
                "name": "Hantavirus (cardio-)pulmonary syndrome (HPS)",
            },
        ],
        "associatedAnatomy": [
            {"@type": "AnatomicalSystem", "name": "Respiratory system"},
            {"@type": "AnatomicalSystem", "name": "Renal system"},
            {"@type": "AnatomicalSystem", "name": "Cardiovascular system"},
        ],
        "cause": [
            {
                "@type": "MedicalCause",
                "name": "Inhalation of aerosolised rodent excreta containing orthohantavirus particles",
            }
        ],
        "signOrSymptom": [
            {"@type": "MedicalSymptom", "name": s} for s in [
                "Fever",
                "Myalgia",
                "Headache",
                "Cough",
                "Shortness of breath",
                "Non-cardiogenic pulmonary oedema",
                "Acute kidney injury",
                "Thrombocytopenia",
                "Haemorrhage",
                "Hypotension",
            ]
        ],
        "epidemiology": (
            "Endemic across the Americas (Sin Nombre virus, Andes virus), "
            "Europe and western Russia (Puumala virus, Dobrava-Belgrade virus), "
            "east Asia (Hantaan virus, Seoul virus). Transmission is "
            "rodent-to-human via aerosolised excreta; Andes virus is the only "
            "orthohantavirus with documented person-to-person transmission."
        ),
        "possibleTreatment": (
            "Supportive critical care including mechanical ventilation, fluid "
            "management, vasopressors, ECMO, and renal replacement therapy. "
            "Ribavirin shows benefit in early HFRS but limited efficacy in HPS. "
            "No licensed antiviral or vaccine outside South Korea's Hantavax "
            "(Hantaan virus only)."
        ),
        "riskFactor": [
            {"@type": "MedicalRiskFactor", "name": rf} for rf in [
                "Occupational rodent exposure (military, agricultural, conservation workers)",
                "Cleaning rodent-infested structures without respiratory protection",
                "Living in or visiting endemic regions",
                "Close household contact with Andes virus cases (person-to-person)",
            ]
        ],
        "sameAs": [
            "https://www.cdc.gov/hantavirus/",
            "https://www.who.int/news-room/fact-sheets/detail/hantavirus-disease",
            "https://en.wikipedia.org/wiki/Orthohantavirus",
            "https://www.wikidata.org/wiki/Q1340089",
            "https://meshb.nlm.nih.gov/record/ui?ui=D006362",
        ],
    }


def medical_web_page(canonical: str, name: str, about_id: str) -> dict[str, Any]:
    return {
        "@type": "MedicalWebPage",
        "@id": f"{canonical}#medical-webpage",
        "url": canonical,
        "name": name,
        "about": {"@id": about_id},
        "audience": [
            {"@type": "MedicalAudience", "audienceType": "Patient"},
            {"@type": "MedicalAudience", "audienceType": "MedicalResearcher"},
            {"@type": "MedicalAudience", "audienceType": "Clinician"},
        ],
        "lastReviewed": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "reviewedBy": {"@id": f"{BASE_URL}/#org"},
        "isPartOf": {"@id": f"{BASE_URL}/#site"},
    }


def serotype_node(s: dict[str, str]) -> dict[str, Any]:
    canonical = f"{BASE_URL}/hantavirus/{s['slug']}"
    same_as: list[str] = []
    if s.get("wikipedia"):
        same_as.append(s["wikipedia"])
    if s.get("wikidata"):
        same_as.append(f"https://www.wikidata.org/wiki/{s['wikidata']}")
    return {
        "@type": "MedicalCondition",
        "@id": f"{canonical}#condition",
        "name": s["name"],
        "alternateName": [s["code"]],
        "code": {
            "@type": "MedicalCode",
            "codingSystem": "ICD-10",
            "codeValue": s["icd"],
        },
        "epidemiology": s["summary"],
        "sameAs": same_as or None,
    }


def faq_page_from_entries(canonical: str, entries: list[tuple[str, str]]) -> dict[str, Any]:
    import re as _re
    def _strip_html(s: str) -> str:
        # Strip tags for the FAQ Answer text (schema requires plain text)
        return _re.sub(r"<[^>]+>", "", s)
    return {
        "@type": "FAQPage",
        "@id": f"{canonical}#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": _strip_html(a),
                },
            }
            for q, a in entries
        ],
    }


def news_article(
    article_id: str,
    headline: str,
    summary: str | None,
    url: str,
    raw_url: str,
    published: datetime | None,
    modified: datetime,
    country_iso2: str | None,
    serotype_code: str | None,
    source_name: str,
    nato_reliability: str,
    nato_credibility: int,
) -> dict[str, Any]:
    """NewsArticle JSON-LD for a single ingested case_report."""
    return {
        "@type": "NewsArticle",
        "@id": f"{url}#article",
        "url": url,
        "headline": headline[:110],
        "alternativeHeadline": headline,
        "description": (summary or headline)[:280],
        "datePublished": (published or modified).strftime("%Y-%m-%d"),
        "dateModified": modified.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "isBasedOn": raw_url,
        "publisher": {"@id": f"{BASE_URL}/#org"},
        "author": [{"@type": "Organization", "name": source_name}],
        "about": {"@id": f"{BASE_URL}/hantavirus#condition"},
        "mentions": (
            [{"@type": "Country", "name": country_name(country_iso2)}]
            if country_iso2 else None
        ),
        "keywords": ",".join(filter(None, [
            "hantavirus",
            f"orthohantavirus {serotype_code.lower()}" if serotype_code else None,
            country_name(country_iso2).lower() if country_iso2 else None,
            "outbreak",
            "surveillance",
        ])),
        "citation": {
            "@type": "CreativeWork",
            "name": source_name,
            "url": raw_url,
        },
        # NATO Admiralty Scale as additionalProperty (schema-compatible
        # representation of the source qualification).
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "NATO reliability",
                "value": nato_reliability,
            },
            {
                "@type": "PropertyValue",
                "name": "NATO credibility",
                "value": int(nato_credibility),
            },
        ],
    }


def country_place(iso2: str) -> dict[str, Any]:
    name = country_name(iso2)
    canonical = f"{BASE_URL}/countries/{iso2.lower()}"
    return {
        "@type": "Place",
        "@id": f"{canonical}#place",
        "name": name,
        "address": {"@type": "PostalAddress", "addressCountry": iso2},
        "url": canonical,
        "isPartOf": {"@id": f"{BASE_URL}/#site"},
    }


def event_incident(
    incident_code: str,
    name: str,
    summary: str | None,
    started_at: datetime | None,
    ended_at: datetime | None,
    countries: list[str],
    status: str,
    confirmed: int,
    deaths: int,
) -> dict[str, Any]:
    canonical = f"{BASE_URL}/outbreaks/{incident_code}"
    return {
        "@type": ["MedicalCondition", "Event", "SpecialAnnouncement"],
        "@id": f"{canonical}#incident",
        "name": name,
        "description": summary or name,
        "startDate": started_at.strftime("%Y-%m-%d") if started_at else None,
        "endDate": ended_at.strftime("%Y-%m-%d") if ended_at else None,
        "datePosted": started_at.strftime("%Y-%m-%d") if started_at else None,
        "url": canonical,
        "eventStatus": (
            "https://schema.org/EventScheduled" if status == "active"
            else "https://schema.org/EventPostponed" if status == "monitoring"
            else "https://schema.org/EventCancelled"
        ),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "category": "https://www.wikidata.org/wiki/Q1340089",
        "publisher": {"@id": f"{BASE_URL}/#org"},
        "spatialCoverage": [
            {"@type": "Country", "name": country_name(c)} for c in countries
        ],
        "about": {"@id": f"{BASE_URL}/hantavirus#condition"},
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Confirmed cases", "value": int(confirmed)},
            {"@type": "PropertyValue", "name": "Deaths", "value": int(deaths)},
            {"@type": "PropertyValue", "name": "Status", "value": status},
        ],
    }


def collection_page(
    canonical: str,
    name: str,
    description: str,
    item_urls: list[tuple[str, str]],  # (name, url)
) -> dict[str, Any]:
    return {
        "@type": "CollectionPage",
        "@id": f"{canonical}#collection",
        "url": canonical,
        "name": name,
        "description": description,
        "isPartOf": {"@id": f"{BASE_URL}/#site"},
        "hasPart": [
            {
                "@type": "WebPage",
                "name": n,
                "url": u,
            }
            for n, u in item_urls
        ],
    }


def live_blog_posting(
    canonical: str,
    incident_name: str,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """LiveBlogPosting for an active outbreak's chronology feed.

    Each `events` entry must have `id`, `headline`, `date`, `url`.
    """
    return {
        "@type": "LiveBlogPosting",
        "@id": f"{canonical}#liveblog",
        "url": canonical,
        "headline": f"Live updates — {incident_name}",
        "coverageStartTime": "2026-04-01T00:00:00+00:00",
        "coverageEndTime": "2026-12-31T23:59:59+00:00",
        "publisher": {"@id": f"{BASE_URL}/#org"},
        "liveBlogUpdate": [
            {
                "@type": "BlogPosting",
                "@id": f"{BASE_URL}/articles/{ev['id']}#post",
                "headline": ev["headline"],
                "datePublished": ev["date"],
                "url": ev["url"],
            }
            for ev in events
        ],
    }
