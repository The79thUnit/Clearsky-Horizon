"""Parser-level tests for every new connector.

Each test builds a tiny realistic payload (RSS / JSON / HTML), feeds it to the
connector's `parse()` method, and asserts the resulting ParsedItem batch
shape. Network is never touched; tests are deterministic.

These tests defend the connectors against parser drift (e.g. upstream changes
their key names) and against accidental regression when we refactor a base.
"""

from __future__ import annotations

import pytest
from horizon_worker.connectors.arxiv import ArxivConnector
from horizon_worker.connectors.biorxiv import BioRxivConnector
from horizon_worker.connectors.cdc_han import CDCHANConnector
from horizon_worker.connectors.cdc_mmwr import CDCMMWRConnector
from horizon_worker.connectors.crossref import CrossrefConnector
from horizon_worker.connectors.ecdc import ECDCConnector
from horizon_worker.connectors.europe_pmc import EuropePMCConnector
from horizon_worker.connectors.gdelt import GDELTConnector
from horizon_worker.connectors.google_news import GoogleNewsConnector
from horizon_worker.connectors.healthmap import HealthMapConnector
from horizon_worker.connectors.medrxiv import MedRxivConnector
from horizon_worker.connectors.nm_health import NMHealthConnector
from horizon_worker.connectors.paho import PAHOConnector
from horizon_worker.connectors.reddit import RedditConnector
from horizon_worker.connectors.text_utils import parse_date_safe
from horizon_worker.connectors.who_don import WHODonConnector

# ---------------- text_utils ----------------


def test_parse_date_safe_returns_first_match() -> None:
    from datetime import date

    assert parse_date_safe("2026-05-11", "%Y-%m-%d") == date(2026, 5, 11)
    assert parse_date_safe("11 May 2026", "%d %B %Y") == date(2026, 5, 11)
    assert parse_date_safe("garbage", "%Y-%m-%d") is None
    assert parse_date_safe("", "%Y-%m-%d") is None


# ---------------- RSS connectors ----------------

_RSS_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>test</title>
<item>
<title>Hantavirus, Argentina (Chubut): Andes virus, 3 cases</title>
<link>https://example.org/post/1</link>
<guid>test-1</guid>
<pubDate>Sat, 04 May 2026 12:00:00 GMT</pubDate>
<description>Three confirmed Andes hantavirus cases in Chubut.</description>
</item>
<item>
<title>Influenza, USA: 2026 season summary</title>
<link>https://example.org/post/2</link>
<guid>test-2</guid>
<pubDate>Sat, 04 May 2026 13:00:00 GMT</pubDate>
<description>Annual influenza summary.</description>
</item>
</channel></rss>"""


@pytest.mark.parametrize("cls", [CDCMMWRConnector, GoogleNewsConnector, ArxivConnector])
def test_rss_base_parses_and_filters(cls: type) -> None:
    connector = cls()
    parsed = connector.parse(_RSS_FEED)
    relevant = connector.filter_relevant(parsed)
    # Two items in feed, only the hantavirus one should survive the keyword filter
    assert len(parsed) == 2
    assert len(relevant) == 1
    assert "Hantavirus" in relevant[0].title
    assert relevant[0].country_iso2 == "AR"
    assert relevant[0].serotype_text == "ANDV"


# ---------------- JSON API connectors ----------------


_BIORXIV_JSON = b"""{
  "messages": [{"status": "ok", "total": 1, "interval": "30d"}],
  "collection": [
    {
      "doi": "10.1101/2026.05.01.000001",
      "title": "Hantavirus Andes virus serology study in Chubut province, Argentina",
      "abstract": "Three confirmed cases of ANDV in rural workers and family contacts.",
      "date": "2026-05-04"
    },
    {
      "doi": "10.1101/2026.05.01.000002",
      "title": "Influenza vaccine efficacy 2026",
      "abstract": "Unrelated.",
      "date": "2026-05-05"
    }
  ]
}"""


def test_biorxiv_parses() -> None:
    connector = BioRxivConnector()
    parsed = connector.parse(_BIORXIV_JSON)
    assert len(parsed) == 2
    relevant = connector.filter_relevant(parsed)
    assert len(relevant) == 1
    item = relevant[0]
    assert item.country_iso2 == "AR"
    assert item.serotype_text == "ANDV"
    assert "10.1101/2026.05.01.000001" in item.external_id


def test_medrxiv_inherits_biorxiv_parsing() -> None:
    # medRxiv uses identical payload shape
    connector = MedRxivConnector()
    parsed = connector.parse(_BIORXIV_JSON)
    assert len(parsed) == 2


_EUROPE_PMC_JSON = b"""{
  "resultList": {
    "result": [
      {
        "id": "12345",
        "pmid": "39999999",
        "doi": "10.1234/example.5678",
        "title": "Andes virus outbreak surveillance Chile 2026",
        "abstractText": "Surveillance report on hantavirus cases in Aysen region.",
        "firstPublicationDate": "2026-05-04"
      }
    ]
  }
}"""


def test_europe_pmc_parses() -> None:
    connector = EuropePMCConnector()
    parsed = connector.parse(_EUROPE_PMC_JSON)
    assert len(parsed) == 1
    item = parsed[0]
    assert item.country_iso2 == "CL"
    assert item.serotype_text == "ANDV"
    assert "12345" in item.external_id or "39999999" in item.external_id


_CROSSREF_JSON = b"""{
  "message": {
    "items": [
      {
        "DOI": "10.1234/cr.99",
        "title": ["Sin Nombre virus seroprevalence in deer mice, New Mexico"],
        "abstract": "<jats:p>Hantavirus survey covering Four Corners.</jats:p>",
        "issued": {"date-parts": [[2026, 4, 12]]}
      }
    ]
  }
}"""


def test_crossref_parses() -> None:
    connector = CrossrefConnector()
    parsed = connector.parse(_CROSSREF_JSON)
    assert len(parsed) == 1
    item = parsed[0]
    assert item.serotype_text == "SNV"
    assert "Sin Nombre" in item.title
    # JATS markup should be stripped
    assert item.summary is not None
    assert "<jats:p>" not in item.summary


_GDELT_JSON = b"""{
  "articles": [
    {
      "url": "https://example.com/article-1",
      "title": "Hantavirus cases rise in Argentina amid 2026 outbreak",
      "seendate": "20260504T093000Z",
      "sourcecountry": "AR",
      "domain": "example.com"
    }
  ]
}"""


def test_gdelt_parses() -> None:
    connector = GDELTConnector()
    parsed = connector.parse(_GDELT_JSON)
    assert len(parsed) == 1
    item = parsed[0]
    assert item.country_iso2 == "AR"
    assert "Hantavirus" in item.title


_HEALTHMAP_JSON = b"""[
  {
    "alert_id": "42",
    "summary": "Hantavirus Andes virus cluster reported in Chubut, Argentina",
    "link": "https://www.healthmap.org/article/42",
    "date": "2026-05-04",
    "country": "AR",
    "lat": -43.0,
    "lng": -65.0
  }
]"""


def test_healthmap_parses() -> None:
    connector = HealthMapConnector()
    parsed = connector.parse(_HEALTHMAP_JSON)
    assert len(parsed) == 1
    item = parsed[0]
    assert item.country_iso2 == "AR"
    assert item.serotype_text == "ANDV"
    assert item.lat == -43.0


_REDDIT_JSON = b"""{
  "data": {
    "children": [
      {
        "data": {
          "id": "abc123",
          "title": "Anyone read about the Andes virus cluster on the cruise ship?",
          "selftext": "Looking for primary sources on the MV Hondius outbreak.",
          "permalink": "/r/medicine/comments/abc123/",
          "subreddit": "medicine",
          "created_utc": 1746360000
        }
      }
    ]
  }
}"""


def test_reddit_parses() -> None:
    connector = RedditConnector()
    parsed = connector.parse(_REDDIT_JSON)
    assert len(parsed) == 1
    item = parsed[0]
    assert item.region == "medicine"
    assert item.serotype_text == "ANDV"


# ---------------- HTML scraper connectors ----------------

_WHO_HTML = b"""<html><body>
<main>
  <a class="list-view--item__link" href="/emergencies/disease-outbreak-news/item/2026-DON600">
    Hantavirus cluster linked to cruise ship travel, Multi-country
  </a>
  <a href="/emergencies/disease-outbreak-news/item/2026-DON599">
    Hantavirus, Multi-country: cluster update
  </a>
  <a href="/news/item/unrelated">Unrelated WHO news item</a>
</main>
</body></html>"""


def test_who_don_parses() -> None:
    connector = WHODonConnector()
    parsed = connector.parse(_WHO_HTML)
    relevant = connector.filter_relevant(parsed)
    # Two DON items should be found; unrelated one shouldn't match the URL filter
    assert len(parsed) == 2
    assert len(relevant) == 2
    assert all("disease-outbreak-news" in p.raw_url for p in parsed)


_CDC_HAN_HTML = b"""<html><body>
<a href="/han/php/notices/han00528.html">HAN00528: Multi-country Hantavirus Cluster Linked to Cruise Ship</a>
<a href="/han/php/notices/han00527.html">HAN00527: Unrelated</a>
</body></html>"""


def test_cdc_han_parses() -> None:
    connector = CDCHANConnector()
    parsed = connector.parse(_CDC_HAN_HTML)
    relevant = connector.filter_relevant(parsed)
    assert len(parsed) == 2
    assert len(relevant) == 1
    assert "Hantavirus" in relevant[0].title
    assert relevant[0].country_iso2 == "US"


_PAHO_HTML = b"""<html><body>
<div class="view-content">
  <a href="/en/documents/epidemiological-alert-hantavirus-2025">
    Epidemiological Alert: Hantavirus pulmonary syndrome in Americas
  </a>
  <a href="/en/news/7-5-2026-paho-supports-international-response-hantavirus">
    PAHO supports international response to hantavirus cluster
  </a>
</div>
</body></html>"""


def test_paho_parses() -> None:
    connector = PAHOConnector()
    parsed = connector.parse(_PAHO_HTML)
    relevant = connector.filter_relevant(parsed)
    assert len(parsed) == 2
    assert len(relevant) == 2


_ECDC_HTML = b"""<html><body>
<div>
  <a href="/en/publications-data/hantavirus-infection-annual-epidemiological-report-2023">
    Hantavirus infection - Annual Epidemiological Report for 2023
  </a>
  <a href="/en/news-events/ecdc-monitoring-hantavirus-outbreak-cruise-ship">
    ECDC monitoring suspected hantavirus outbreak linked to cruise ship
  </a>
</div>
</body></html>"""


def test_ecdc_parses() -> None:
    connector = ECDCConnector()
    parsed = connector.parse(_ECDC_HTML)
    relevant = connector.filter_relevant(parsed)
    assert len(parsed) == 2
    assert len(relevant) == 2


_NM_HEALTH_HTML = b"""<html><body>
<main>
  <h1>Hantavirus Pulmonary Syndrome - NM HPS Surveillance</h1>
  <p>The New Mexico Department of Health monitors HPS cases statewide.
  Latest case count includes Sin Nombre virus exposures in Four Corners.</p>
</main>
</body></html>"""


def test_nm_health_parses() -> None:
    connector = NMHealthConnector()
    parsed = connector.parse(_NM_HEALTH_HTML)
    assert len(parsed) == 1
    item = parsed[0]
    assert item.country_iso2 == "US"
    assert item.region == "New Mexico"
    assert item.serotype_text == "SNV"
