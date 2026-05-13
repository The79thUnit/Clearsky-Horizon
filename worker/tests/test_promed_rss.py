"""Tests for ProMED RSS connector using a mocked feed."""

from datetime import date

import httpx
import pytest
from horizon_worker.connectors.promed_rss import ProMEDRSSConnector

MOCK_FEED_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>ProMED-mail</title>
<description>test feed</description>
<item>
<title>Hantavirus, Argentina (Chubut): Andes virus, 2 cases</title>
<link>https://promedmail.org/post/123</link>
<guid>20260504.1234567</guid>
<pubDate>Sat, 04 May 2026 12:00:00 GMT</pubDate>
<description>Two confirmed cases of Andes hantavirus in Chubut province.</description>
</item>
<item>
<title>Influenza, United States: 2026 season summary</title>
<link>https://promedmail.org/post/456</link>
<guid>20260504.7654321</guid>
<pubDate>Sat, 04 May 2026 13:00:00 GMT</pubDate>
<description>Annual influenza summary.</description>
</item>
<item>
<title>Hantavirus, Finland (Helsinki): Puumala virus</title>
<link>https://promedmail.org/post/789</link>
<guid>20260505.5555555</guid>
<pubDate>Sun, 05 May 2026 09:00:00 GMT</pubDate>
<description>Seasonal Puumala virus surveillance.</description>
</item>
</channel>
</rss>
"""


@pytest.fixture
def connector() -> ProMEDRSSConnector:
    return ProMEDRSSConnector()


class TestParse:
    def test_extracts_all_entries(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        assert len(items) == 3

    def test_external_id_from_guid(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        assert items[0].external_id == "20260504.1234567"

    def test_reported_date_parsed(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        assert items[0].reported_date == date(2026, 5, 4)

    def test_per_item_canonical_bytes_unique(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        bytes_list = [i.raw_content for i in items]
        assert len(set(bytes_list)) == 3


class TestFilter:
    def test_keeps_hantavirus_drops_influenza(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        relevant = connector.filter_relevant(items)
        assert len(relevant) == 2
        assert all("Hantavirus" in i.title for i in relevant)


class TestCountryExtraction:
    def test_argentina(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        ar = next(i for i in items if "Argentina" in i.title)
        assert ar.country_iso2 == "AR"

    def test_finland(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        fi = next(i for i in items if "Finland" in i.title)
        assert fi.country_iso2 == "FI"

    def test_united_states(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        us = next(i for i in items if "United States" in i.title)
        assert us.country_iso2 == "US"


class TestRegionExtraction:
    def test_region_from_parens(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        ar = next(i for i in items if "Argentina" in i.title)
        assert ar.region is not None
        assert "Chubut" in ar.region


class TestSerotypeDetection:
    def test_andes(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        ar = next(i for i in items if "Argentina" in i.title)
        assert ar.serotype_text == "ANDV"

    def test_puumala(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        fi = next(i for i in items if "Finland" in i.title)
        assert fi.serotype_text == "PUUV"

    def test_no_serotype_when_absent(self, connector: ProMEDRSSConnector) -> None:
        items = connector.parse(MOCK_FEED_XML)
        flu = next(i for i in items if "Influenza" in i.title)
        assert flu.serotype_text is None


class TestFetchAndParseEndToEnd:
    @pytest.mark.asyncio
    async def test_run_against_mock_transport(self, connector: ProMEDRSSConnector) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert "promedmail.org" in str(request.url)
            return httpx.Response(200, content=MOCK_FEED_XML)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await connector.fetch_and_parse(client)

        assert result.error is None
        assert result.http_status == 200
        assert result.items_seen == 3
        assert result.items_filtered == 1  # influenza dropped
        assert len(result.items) == 2
        assert result.parser_version == "0.1.1"
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_fetch_failure_returns_error_result(self, connector: ProMEDRSSConnector) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, content=b"upstream failure")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await connector.fetch_and_parse(client)

        assert result.error is not None
        assert result.items == []
        assert result.items_seen == 0
