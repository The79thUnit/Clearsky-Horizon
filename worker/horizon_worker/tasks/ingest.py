"""Celery ingest task. Pulls from one connector, writes records + scores + log."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable
from datetime import UTC, date, datetime
from typing import Any

from ..celery_app import app
from ..config import settings
from ..connectors.afludiary import AvianFluDiaryConnector
from ..connectors.argentina_msal import ArgentinaMSALConnector
from ..connectors.arxiv import ArxivConnector
from ..connectors.australia_health import AustraliaHealthConnector
from ..connectors.base import BaseConnector, FetchResult
from ..connectors.biorxiv import BioRxivConnector
from ..connectors.bolivia_msd import BoliviaMSDConnector
from ..connectors.brazil_ms import BrazilMSConnector
from ..connectors.cdc_eid import CDCEIDConnector
from ..connectors.cdc_eid_ahead import CDCEIDAheadConnector
from ..connectors.cdc_han import CDCHANConnector
from ..connectors.cdc_mmwr import CDCMMWRConnector
from ..connectors.chile_deis import ChileDEISConnector
from ..connectors.china_cdc import ChinaCDCConnector
from ..connectors.cidrap import CIDRAPNewsConnector
from ..connectors.crossref import CrossrefConnector
from ..connectors.ecdc import ECDCConnector
from ..connectors.ecdc_cdtr import ECDCCDTRConnector
from ..connectors.ecdc_epid_updates import ECDCEpidUpdatesConnector
from ..connectors.ecdc_risk import ECDCRiskConnector
from ..connectors.elife import ELifeConnector
from ..connectors.europe_pmc import EuropePMCConnector
from ..connectors.eurosurveillance import EurosurveillanceConnector
from ..connectors.gbif import GBIFConnector
from ..connectors.gdelt import GDELTConnector
from ..connectors.google_news import GoogleNewsConnector
from ..connectors.healthmap import HealthMapConnector
from ..connectors.hpsc import HPSCConnector
from ..connectors.inaturalist import INaturalistConnector
from ..connectors.japan_niid import JapanNIIDConnector
from ..connectors.jvi_asm import JVIASMConnector
from ..connectors.lancet_id import LancetIDConnector
from ..connectors.mastodon_hantavirus import MastodonHantavirusConnector
from ..connectors.mastodon_hondius import MastodonHondiusConnector
from ..connectors.mbio import MBioConnector
from ..connectors.medrxiv import MedRxivConnector
from ..connectors.nature_news import NatureNewsConnector
from ..connectors.ncbi_virus import NCBIVirusConnector
from ..connectors.nm_health import NMHealthConnector
from ..connectors.norway_fhi import NorwayFHIConnector
from ..connectors.nz_moh import NZMoHConnector
from ..connectors.one_health import OneHealthConnector
from ..connectors.outbreak_news_today import OutbreakNewsTodayConnector
from ..connectors.paho import PAHOConnector
from ..connectors.paho_news import PAHONewsConnector
from ..connectors.peru_minsa import PeruMINSAConnector
from ..connectors.phac import PHACConnector
from ..connectors.phs import PHSConnector
from ..connectors.plos_ntds import PLOSNTDsConnector
from ..connectors.plos_pathogens import PLOSPathogensConnector
from ..connectors.promed_rss import ProMEDRSSConnector
from ..connectors.pubmed import PubMedConnector
from ..connectors.reddit import RedditConnector
from ..connectors.rivm import RIVMConnector
from ..connectors.rki import RKIConnector
from ..connectors.science_news import ScienceNewsConnector
from ..connectors.spf_france import SPFFranceConnector
from ..connectors.sweden_fhm import SwedenFHMConnector
from ..connectors.text_utils import topic_hash
from ..connectors.ukhsa import UKHSAConnector
from ..connectors.venezuela_mpps import VenezuelaMPPSConnector
from ..connectors.viruses_mdpi import VirusesMDPIConnector
from ..connectors.wahis import WAHISConnector
from ..connectors.who_afro import WHOAFROConnector
from ..connectors.who_don import WHODonConnector
from ..connectors.who_emro import WHOEMROConnector
from ..connectors.who_euro import WHOEUROConnector
from ..connectors.who_searo import WHOSEAROConnector
from ..connectors.who_wpro import WHOWPROConnector
from ..core.chain_of_custody import compute_hash
from ..core.clustering import CaseFingerprint, DetectedCluster, detect_clusters
from ..core.nato import NATOScore
from ..core.qualification import QualificationInputs, calculate
from ..core.src_citation import SRCCitation
from ..db import DBConn, get_conn

# Default linkage confidence for case-to-cluster assignment.
# Phase 2 starter value. Phase 3 may compute per-link confidence properly.
CASE_TO_CLUSTER_DEFAULT_CONFIDENCE = 0.85

# Lookback window for cluster recomputation. Cases older than this don't drag
# detection. 90 days covers reasonable outbreak durations + the 14-day window.
CLUSTER_LOOKBACK_DAYS = 90

logger = logging.getLogger(__name__)

# Connector registry. Every source_code declared here must also exist in
# the `sources` table (migration 003 + 004). The dict value is intentionally
# typed broadly (mypy can't infer that every entry is a concrete subclass).
CONNECTORS: dict[str, type[BaseConnector]] = {
    # Original 16 (migrations 003 + 004)
    ProMEDRSSConnector.SOURCE_CODE: ProMEDRSSConnector,
    CDCMMWRConnector.SOURCE_CODE: CDCMMWRConnector,
    GoogleNewsConnector.SOURCE_CODE: GoogleNewsConnector,
    ArxivConnector.SOURCE_CODE: ArxivConnector,
    BioRxivConnector.SOURCE_CODE: BioRxivConnector,
    MedRxivConnector.SOURCE_CODE: MedRxivConnector,
    EuropePMCConnector.SOURCE_CODE: EuropePMCConnector,
    CrossrefConnector.SOURCE_CODE: CrossrefConnector,
    GDELTConnector.SOURCE_CODE: GDELTConnector,
    HealthMapConnector.SOURCE_CODE: HealthMapConnector,
    WHODonConnector.SOURCE_CODE: WHODonConnector,
    CDCHANConnector.SOURCE_CODE: CDCHANConnector,
    PAHOConnector.SOURCE_CODE: PAHOConnector,
    ECDCConnector.SOURCE_CODE: ECDCConnector,
    NMHealthConnector.SOURCE_CODE: NMHealthConnector,
    RedditConnector.SOURCE_CODE: RedditConnector,
    # Wave Z expansion (migration 005)
    UKHSAConnector.SOURCE_CODE: UKHSAConnector,
    PHACConnector.SOURCE_CODE: PHACConnector,
    RKIConnector.SOURCE_CODE: RKIConnector,
    PHSConnector.SOURCE_CODE: PHSConnector,
    HPSCConnector.SOURCE_CODE: HPSCConnector,
    WHOAFROConnector.SOURCE_CODE: WHOAFROConnector,
    CIDRAPNewsConnector.SOURCE_CODE: CIDRAPNewsConnector,
    ECDCCDTRConnector.SOURCE_CODE: ECDCCDTRConnector,
    OutbreakNewsTodayConnector.SOURCE_CODE: OutbreakNewsTodayConnector,
    CDCEIDConnector.SOURCE_CODE: CDCEIDConnector,
    CDCEIDAheadConnector.SOURCE_CODE: CDCEIDAheadConnector,
    EurosurveillanceConnector.SOURCE_CODE: EurosurveillanceConnector,
    LancetIDConnector.SOURCE_CODE: LancetIDConnector,
    VirusesMDPIConnector.SOURCE_CODE: VirusesMDPIConnector,
    JVIASMConnector.SOURCE_CODE: JVIASMConnector,
    NatureNewsConnector.SOURCE_CODE: NatureNewsConnector,
    ScienceNewsConnector.SOURCE_CODE: ScienceNewsConnector,
    PubMedConnector.SOURCE_CODE: PubMedConnector,
    INaturalistConnector.SOURCE_CODE: INaturalistConnector,
    GBIFConnector.SOURCE_CODE: GBIFConnector,
    # Wave Z+ expansion (migration 006) — 16 more sources
    WHOEUROConnector.SOURCE_CODE: WHOEUROConnector,
    WHOEMROConnector.SOURCE_CODE: WHOEMROConnector,
    WHOSEAROConnector.SOURCE_CODE: WHOSEAROConnector,
    WHOWPROConnector.SOURCE_CODE: WHOWPROConnector,
    ChinaCDCConnector.SOURCE_CODE: ChinaCDCConnector,
    JapanNIIDConnector.SOURCE_CODE: JapanNIIDConnector,
    AustraliaHealthConnector.SOURCE_CODE: AustraliaHealthConnector,
    NZMoHConnector.SOURCE_CODE: NZMoHConnector,
    ArgentinaMSALConnector.SOURCE_CODE: ArgentinaMSALConnector,
    ChileDEISConnector.SOURCE_CODE: ChileDEISConnector,
    BrazilMSConnector.SOURCE_CODE: BrazilMSConnector,
    PLOSPathogensConnector.SOURCE_CODE: PLOSPathogensConnector,
    PLOSNTDsConnector.SOURCE_CODE: PLOSNTDsConnector,
    MBioConnector.SOURCE_CODE: MBioConnector,
    ELifeConnector.SOURCE_CODE: ELifeConnector,
    WAHISConnector.SOURCE_CODE: WAHISConnector,
    # Tier-1 audit follow-on (13 May 2026): RIVM Netherlands MoH —
    # critical for MV Hondius (NL-flagged, Rotterdam dock, Dutch index
    # couple). RIVM has no RSS feed; HTMLScraperBase against /en/news.
    RIVMConnector.SOURCE_CODE: RIVMConnector,
    # Tier-2 audit batch 1 (13 May 2026, migration 037):
    # Avian Flu Diary — Mike Coston's outbreak commentary blog (B3,
    # since 2006). Covers full zoonotic portfolio not just avian.
    # One Health — Elsevier peer-reviewed journal (A2, ISSN 2352-7714)
    # for reservoir-host ecology and spillover papers.
    AvianFluDiaryConnector.SOURCE_CODE: AvianFluDiaryConnector,
    OneHealthConnector.SOURCE_CODE: OneHealthConnector,
    # Tier-2 (13 May 2026, migration 038): NCBI GenBank molecular confirmation.
    # Two-step E-utilities: esearch(orthohantavirus[organism], reldate=14)
    # → esummary. Dedupes by isolate (one record per genome, not per segment).
    # Swiss ANDV/Hu-3337/2026 deposited 2026-05-11 before public WHO update.
    NCBIVirusConnector.SOURCE_CODE: NCBIVirusConnector,
    # Tier-2 (13 May 2026, migration 039): Mastodon social feeds (NATO C3).
    # mastodon.social public hashtag RSS — no auth required. #hantavirus
    # (general) and #MVHondius (vessel-specific cluster feed, ~42KB, very
    # active during outbreak).
    MastodonHantavirusConnector.SOURCE_CODE: MastodonHantavirusConnector,
    MastodonHondiusConnector.SOURCE_CODE: MastodonHondiusConnector,
    # Tier-2 batch 3 (13 May 2026, migration 045):
    # PAHO News RSS — PAHO general news feed (NATO B2). Complements
    # paho-alerts (A1, hantavirus topic page); catches cross-disease
    # items mentioning hantavirus before the topic page updates.
    PAHONewsConnector.SOURCE_CODE: PAHONewsConnector,
    # Bolivia MSD — Ministerio de Salud y Deportes Joomla RSS (NATO B2).
    # Bolivia is ANDV endemic (Beni/Pando departments). Closes ANDV-region
    # gap alongside argentina-msal and brazil-ms.
    BoliviaMSDConnector.SOURCE_CODE: BoliviaMSDConnector,
    # Tier-2 batch 4 (13 May 2026, migration 048): LatAm ANDV expansion.
    # Venezuela MPPS — WordPress RSS (NATO B2). ANDV-endemic (Orinoco basin,
    # Mérida/Barinas/Trujillo states). Under-reported in international DBs.
    VenezuelaMPPSConnector.SOURCE_CODE: VenezuelaMPPSConnector,
    # Peru MINSA — gob.pe JSON API (NATO B2). ANDV-endemic (Amazonas, Loreto,
    # Ucayali). Spanish long-form date. minsa.gob.pe returns 403.
    PeruMINSAConnector.SOURCE_CODE: PeruMINSAConnector,
    # European coverage expansion (13 May 2026, migration 051): three national
    # public health authorities closing Tier-1 European gaps.
    # SPF France (NATO A2): coordinating authority for French MV Hondius cases
    #   (43 in France cluster) + PUUV endemic in Ardennes/Champagne-Ardenne.
    # Sweden FHM (NATO A2): highest per-capita PUUV incidence in Europe
    #   (sorkfeber, Norrland/Ångermanland/Jämtland). Topic-filtered RSS.
    # Norway FHI (NATO A2): PUUV cases in Innlandet (Hedmark/Oppland) + Seoul
    #   virus monitoring for imported rodents.
    SPFFranceConnector.SOURCE_CODE: SPFFranceConnector,
    SwedenFHMConnector.SOURCE_CODE: SwedenFHMConnector,
    NorwayFHIConnector.SOURCE_CODE: NorwayFHIConnector,
    # ECDC sub-feed expansion (13 May 2026, migration 052): Rapid Risk
    # Assessments + Epidemiological Updates. Complement ecdc-cdtr
    # (super-feed). High-signal EU-level publications for significant events.
    # Content-topic dedup handles any overlap with ecdc-cdtr.
    ECDCRiskConnector.SOURCE_CODE: ECDCRiskConnector,
    ECDCEpidUpdatesConnector.SOURCE_CODE: ECDCEpidUpdatesConnector,
}


def _today_utc() -> date:
    return datetime.now(tz=UTC).date()


def persist_fetch_result(
    conn: DBConn,
    source_code: str,
    result: FetchResult,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Write a connector's FetchResult to the DB. Pure of connector logic.

    Tests can call this directly with a real Postgres connection
    or a savepoint-wrapped one.
    """
    today_value = today or _today_utc()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, nato_reliability, nato_credibility
            FROM sources WHERE code = %s
            """,
            (source_code,),
        )
        srow = cur.fetchone()
        if srow is None:
            raise RuntimeError(f"source {source_code!r} not seeded in DB")
        source_id = srow["id"]
        source_name = srow["name"]
        nato = NATOScore.parse(f"{srow['nato_reliability']}{srow['nato_credibility']}")

        ingested = 0
        duplicate = 0
        cross_source_linked = 0

        for item in result.items:
            content_hash = compute_hash(item.raw_content)

            # Cross-source dedup: compute a topic hash from the normalised
            # title. If another article with the same topic hash was ingested
            # in the last 7 days, this is the SAME news event reported by a
            # different source. We still record it (chain of custody), but we
            # link it to the original and DO NOT count it as a new event.
            item_topic = topic_hash(item.title)
            existing_topic_row = None
            if item_topic:
                cur.execute(
                    """
                    SELECT id
                    FROM case_reports
                    WHERE content_topic_hash = %s
                      AND ingested_at >= NOW() - INTERVAL '7 days'
                      AND source_id <> %s
                    ORDER BY ingested_at ASC
                    LIMIT 1
                    """,
                    (item_topic, source_id),
                )
                existing_topic_row = cur.fetchone()

            citation = SRCCitation(
                source_code=source_code,
                source_name=source_name,
                nato_score=nato,
                title=item.title,
                issued_on=item.reported_date,
            )

            age_days = 0
            if item.reported_date:
                age_days = max(0, (today_value - item.reported_date).days)

            qresult = calculate(
                QualificationInputs(
                    nato=nato,
                    corroboration_count=0,
                    age_days=age_days,
                )
            )

            serotype_id = None
            if item.serotype_text:
                cur.execute(
                    "SELECT id FROM serotypes WHERE code = %s",
                    (item.serotype_text,),
                )
                serow = cur.fetchone()
                if serow:
                    serotype_id = serow["id"]

            cur.execute(
                """
                INSERT INTO case_reports
                    (source_id, external_id, src_citation, title, summary,
                     country_iso2, region, lat, lng, serotype_id, serotype_text,
                     reported_date, case_count, death_count,
                     raw_url, raw_content_hash, content_topic_hash, parser_version)
                VALUES (%s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s)
                ON CONFLICT (source_id, external_id) DO NOTHING
                RETURNING id
                """,
                (
                    source_id,
                    item.external_id,
                    str(citation),
                    item.title,
                    item.summary,
                    item.country_iso2,
                    item.region,
                    item.lat,
                    item.lng,
                    serotype_id,
                    item.serotype_text,
                    item.reported_date,
                    item.case_count,
                    item.death_count,
                    item.raw_url,
                    content_hash,
                    item_topic or None,
                    result.parser_version,
                ),
            )
            inserted = cur.fetchone()
            if inserted is None:
                duplicate += 1
                continue

            ingested += 1
            case_id = inserted["id"]
            if existing_topic_row is not None:
                cross_source_linked += 1

            cur.execute(
                """
                INSERT INTO qualification_scores
                    (case_report_id, nato_reliability, nato_credibility,
                     pipeline_confidence, pipeline_factors)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                (
                    case_id,
                    nato.reliability.value,
                    nato.credibility.value,
                    qresult.pipeline_confidence,
                    json.dumps(qresult.factors),
                ),
            )

        cur.execute(
            """
            INSERT INTO source_quality_log
                (source_id, http_status, latency_ms, items_seen, items_ingested,
                 items_duplicate, items_filtered, parser_version, error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                source_id,
                result.http_status,
                result.latency_ms,
                result.items_seen,
                ingested,
                duplicate,
                result.items_filtered,
                result.parser_version,
                result.error,
            ),
        )

    # Recompute clusters for any (country, serotype) keys touched by this batch.
    touched_keys: set[tuple[str, str | None]] = {
        (item.country_iso2, item.serotype_text)
        for item in result.items
        if item.country_iso2 is not None
    }
    cluster_summary = recompute_clusters_for_keys(conn, touched_keys)

    return {
        "source_code": source_code,
        "http_status": result.http_status,
        "latency_ms": result.latency_ms,
        "items_seen": result.items_seen,
        "items_ingested": ingested,
        "items_duplicate": duplicate,
        "items_cross_source_linked": cross_source_linked,
        "items_filtered": result.items_filtered,
        "clusters_upserted": cluster_summary["upserted"],
        "error": result.error,
    }


# ----------------------------------------------------------------------------
# Cluster recomputation
# ----------------------------------------------------------------------------


def _fetch_fingerprints(
    conn: DBConn,
    country: str,
    serotype_text: str | None,
    *,
    lookback_days: int = CLUSTER_LOOKBACK_DAYS,
) -> list[CaseFingerprint]:
    """Fetch case fingerprints for one (country, serotype) key within lookback."""
    with conn.cursor() as cur:
        if serotype_text is None:
            cur.execute(
                """
                SELECT id::text AS id, country_iso2, serotype_text, reported_date
                FROM case_reports
                WHERE country_iso2 = %s
                  AND serotype_text IS NULL
                  AND reported_date IS NOT NULL
                  AND ingested_at >= NOW() - make_interval(days => %s)
                """,
                (country, lookback_days),
            )
        else:
            cur.execute(
                """
                SELECT id::text AS id, country_iso2, serotype_text, reported_date
                FROM case_reports
                WHERE country_iso2 = %s
                  AND serotype_text = %s
                  AND reported_date IS NOT NULL
                  AND ingested_at >= NOW() - make_interval(days => %s)
                """,
                (country, serotype_text, lookback_days),
            )
        rows = cur.fetchall()
    return [
        CaseFingerprint(
            case_id=r["id"],
            country_iso2=r["country_iso2"],
            serotype_text=r["serotype_text"],
            reported_date=r["reported_date"],
        )
        for r in rows
    ]


def _upsert_cluster(conn: DBConn, cluster: DetectedCluster) -> str:
    """Insert or update one cluster + populate case_to_cluster. Returns cluster id."""
    with conn.cursor() as cur:
        # Resolve serotype_id from the code, if any.
        serotype_id: str | None = None
        if cluster.serotype_code:
            cur.execute(
                "SELECT id FROM serotypes WHERE code = %s",
                (cluster.serotype_code,),
            )
            srow = cur.fetchone()
            if srow:
                serotype_id = srow["id"]

        # Find existing cluster by (country, serotype_id, started_at).
        cur.execute(
            """
            SELECT id FROM clusters
            WHERE country_iso2 = %s
              AND ((serotype_id = %s) OR (serotype_id IS NULL AND %s::uuid IS NULL))
              AND started_at = %s
            """,
            (cluster.country_iso2, serotype_id, serotype_id, cluster.started_at),
        )
        existing = cur.fetchone()

        if existing:
            cluster_id: str = existing["id"]
            cur.execute(
                """
                UPDATE clusters
                SET ended_at = %s,
                    case_count = %s,
                    name = %s
                WHERE id = %s
                """,
                (cluster.ended_at, cluster.case_count, cluster.name, cluster_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO clusters
                    (country_iso2, serotype_id, started_at, ended_at,
                     status, case_count, name)
                VALUES (%s, %s, %s, %s, 'active', %s, %s)
                RETURNING id
                """,
                (
                    cluster.country_iso2,
                    serotype_id,
                    cluster.started_at,
                    cluster.ended_at,
                    cluster.case_count,
                    cluster.name,
                ),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("cluster INSERT returned no row")
            cluster_id = row["id"]

        # Populate case_to_cluster (idempotent via PK).
        for case_id in cluster.case_ids:
            cur.execute(
                """
                INSERT INTO case_to_cluster
                    (case_report_id, cluster_id, confidence)
                VALUES (%s, %s, %s)
                ON CONFLICT (case_report_id, cluster_id) DO NOTHING
                """,
                (case_id, cluster_id, CASE_TO_CLUSTER_DEFAULT_CONFIDENCE),
            )
    return cluster_id


def recompute_clusters_for_keys(
    conn: DBConn,
    keys: Iterable[tuple[str, str | None]],
) -> dict[str, int]:
    """For each (country, serotype) key, recompute clusters + upsert.

    Returns a summary dict so the ingest task can log it.
    """
    upserted = 0
    for country, serotype in keys:
        fingerprints = _fetch_fingerprints(conn, country, serotype)
        detected = detect_clusters(fingerprints)
        for cluster in detected:
            _upsert_cluster(conn, cluster)
            upserted += 1
    return {"upserted": upserted}


@app.task(  # type: ignore[untyped-decorator]
    name="horizon_worker.tasks.ingest.fetch_source",
    bind=True,
    max_retries=3,
)
def fetch_source(self: Any, source_code: str) -> dict[str, Any]:
    """Celery entry: fetch from connector, persist."""
    cls = CONNECTORS.get(source_code)
    if cls is None:
        raise ValueError(f"unknown source_code={source_code!r}")
    connector = cls(user_agent=settings.user_agent)

    try:
        result: FetchResult = asyncio.run(connector.run())
    except Exception as exc:
        logger.exception("connector run failed for %s", source_code)
        raise self.retry(exc=exc, countdown=60) from exc

    with get_conn() as conn:
        summary = persist_fetch_result(conn, source_code, result)
        conn.commit()

    logger.info("ingest summary: %s", summary)
    return summary
