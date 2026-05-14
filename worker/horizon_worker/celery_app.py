"""Celery application + beat schedule for HORIZON ingestion."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from .config import settings

app = Celery(
    "horizon",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "horizon_worker.tasks.ingest",
        "horizon_worker.tasks.ais",
        "horizon_worker.tasks.extraction",
        "horizon_worker.tasks.indexnow",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="horizon",
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

# Beat schedule. One task per source. Intervals chosen by source freshness:
# - News + outbreak intel (Google News, GDELT, HealthMap, Reddit): every 15 min
# - Authoritative agency pages (WHO, CDC, PAHO, ECDC, NM): every hour
# - Academic / DOI registries (PubMed, bioRxiv, medRxiv, Europe PMC, Crossref, arXiv): every 6 hours
# NOTE: promed-rss removed 2026-05-13 (migration 046). ProMED fully paywalled
# (Auth0 + subscription). No public RSS or free API path exists.
app.conf.beat_schedule = {
    "fetch-google-news": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="*/15"),
        "args": ["google-news"],
    },
    "fetch-gdelt": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        # Reduced from */15 to */60 on 13 May 2026 audit (first pass).
        # Reduced again to */3h on 13 May 2026 after 3× HTTP 429 responses
        # at hourly cadence. GDELT appears to rate-limit bulk queries from
        # VPS IPs more aggressively than documented. Every 3h is 8 hits/day
        # vs 24/day at hourly; GDELT cache TTL is 900s so no signal loss.
        "schedule": crontab(minute="42", hour="*/3"),
        "args": ["gdelt"],
    },
    "fetch-healthmap": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="*/30"),
        "args": ["healthmap"],
    },
    "fetch-reddit": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="*/30"),
        "args": ["reddit"],
    },
    # Wire services + major broadcaster (migration 053, 2026-05-14).
    # Every 30 min: wire desks publish continuously; 30-min cadence captures
    # breaking stories within one cycle without hammering Google News.
    # Mercopress hourly: lower volume, regional Southern Cone wire.
    "fetch-bbc-health": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="7,37"),
        "args": ["bbc-health"],
    },
    "fetch-reuters-health": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="11,41"),
        "args": ["reuters-health"],
    },
    "fetch-ap-news": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="17,47"),
        "args": ["ap-news"],
    },
    "fetch-afp-wire": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="22,52"),
        "args": ["afp-wire"],
    },
    "fetch-efe-wire": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="26,56"),
        "args": ["efe-wire"],
    },
    "fetch-mercopress": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=44),
        "args": ["mercopress"],
    },
    "fetch-who-don": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=5),
        "args": ["who-don"],
    },
    "fetch-cdc-han": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=10),
        "args": ["cdc-han"],
    },
    "fetch-cdc-mmwr": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=15, hour="*/2"),
        "args": ["cdc-mmwr"],
    },
    "fetch-paho": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=20),
        "args": ["paho-alerts"],
    },
    # PAHO general news RSS (migration 045, 2026-05-13). Complements
    # paho-alerts (hantavirus topic page) by catching cross-disease items
    # that mention hantavirus in PAHO's broader news stream. Minute=25:
    # 5 min after paho-alerts, both hourly.
    "fetch-paho-news": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=25),
        "args": ["paho-news"],
    },
    "fetch-ecdc": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=25),
        "args": ["ecdc-tessy"],
    },
    # NOTE: nmh-data disabled 2026-05-13 (migration 042). www.nmhealth.org TCP
    # timeout from OVH VPS IP; US government site blocks commercial VPS ranges.
    # Coverage maintained by cdc-han, pubmed, google-news.
    # "fetch-nm-health": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=30, hour="*/6"),
    #     "args": ["nmh-data"],
    # },
    "fetch-biorxiv": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=35, hour="*/6"),
        "args": ["biorxiv"],
    },
    "fetch-medrxiv": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=40, hour="*/6"),
        "args": ["medrxiv"],
    },
    "fetch-europe-pmc": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=45, hour="*/6"),
        "args": ["europe-pmc"],
    },
    "fetch-crossref": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=50, hour="*/12"),
        "args": ["crossref"],
    },
    "fetch-arxiv": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=55, hour="*/12"),
        "args": ["arxiv"],
    },
    # --- Wave Z expansion (migration 005) ----------------------------------
    # National public health authorities: hourly, staggered minutes 2..52
    "fetch-ukhsa": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=2),
        "args": ["ukhsa"],
    },
    # RIVM (Netherlands) — added 2026-05-13 audit Tier-1. MV Hondius is
    # NL-flagged + Rotterdam dock; RIVM is the home-country authority
    # already publishing direct cluster coverage. HTML-scraped /en/news
    # listing. Hourly, offset minute 3 to interleave with UKHSA (m=2).
    "fetch-rivm": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=3),
        "args": ["rivm"],
    },
    "fetch-phac": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=7),
        "args": ["phac"],
    },
    "fetch-rki": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=12, hour="*/6"),
        "args": ["rki"],
    },
    # NOTE: phs (Public Health Scotland) disabled 2026-05-13 (migration 032).
    # /all-news/rss.xml and /news/rss.xml both 404. UKHSA (minute=2) covers UK.
    # "fetch-phs": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=17),
    #     "args": ["phs"],
    # },
    # NOTE: hpsc (Ireland) disabled 2026-05-13 (migration 032). HPSC retired RSS.
    # No endemic hantavirus in Ireland; acceptable to defer HTMLScraperBase build.
    # "fetch-hpsc": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=22),
    #     "args": ["hpsc"],
    # },
    "fetch-who-afro": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=27),
        "args": ["who-afro"],
    },
    # Folkehelseinstituttet (Norway FHI) — general news RSS. PUUV cases in
    # Innlandet (Hedmark/Oppland) + Seoul virus monitoring. NATO A2. Migration 051.
    # Minute=29: free slot between who-afro (27) and cidrap-news (*/30).
    "fetch-norway-fhi": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=29),
        "args": ["norway-fhi"],
    },
    # Aggregators: 30-min cadence for CIDRAP and Outbreak News; 6h for ECDC CDTR
    "fetch-cidrap-news": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="*/30"),
        "args": ["cidrap-news"],
    },
    "fetch-outbreak-news-today": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="3,33"),
        "args": ["outbreak-news-today"],
    },
    "fetch-ecdc-cdtr": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=32, hour="*/6"),
        "args": ["ecdc-cdtr"],
    },
    # ECDC sub-feeds (migration 052, 13 May 2026): Rapid Risk Assessments and
    # Epidemiological Updates. Complement ecdc-cdtr (super-feed). An ECDC RRA
    # or epidemiological update for hantavirus is very high-confidence signal.
    # Every 6h matches the episodic publication cadence.
    "fetch-ecdc-risk": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=36, hour="*/6"),
        "args": ["ecdc-risk"],
    },
    "fetch-ecdc-updates": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=43, hour="*/6"),
        "args": ["ecdc-updates"],
    },
    # Peer-reviewed journals: every 6h, staggered
    "fetch-cdc-eid": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=37, hour="*/6"),
        "args": ["cdc-eid"],
    },
    "fetch-cdc-eid-ahead": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=42, hour="*/6"),
        "args": ["cdc-eid-ahead"],
    },
    # NOTE: eurosurveillance disabled 2026-05-13 (migration 034). Publisher WAF
    # returns 403 from VPS IP. PubMed indexes all Eurosurveillance hantavirus papers.
    # "fetch-eurosurveillance": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=47, hour="*/6"),
    #     "args": ["eurosurveillance"],
    # },
    "fetch-lancet-id": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=52, hour="*/12"),
        "args": ["lancet-id"],
    },
    # NOTE: viruses-mdpi disabled 2026-05-13 (migration 034). MDPI WAF 403.
    # PubMed indexes all Viruses (MDPI) hantavirus papers.
    # "fetch-viruses-mdpi": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=8, hour="*/12"),
    #     "args": ["viruses-mdpi"],
    # },
    # NOTE: jvi-asm disabled 2026-05-13 (migration 034). ASM publisher WAF 403.
    # PubMed indexes all Journal of Virology hantavirus papers.
    # "fetch-jvi-asm": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=13, hour="*/12"),
    #     "args": ["jvi-asm"],
    # },
    "fetch-nature-news": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=18, hour="*/6"),
        "args": ["nature-news"],
    },
    "fetch-science-news": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=23, hour="*/6"),
        "args": ["science-news"],
    },
    "fetch-pubmed": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=28, hour="*/6"),
        "args": ["pubmed"],
    },
    # Ecological reservoir-host observations: every 12h
    "fetch-inaturalist": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=33, hour="*/12"),
        "args": ["inaturalist"],
    },
    "fetch-gbif": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=38, hour="*/12"),
        "args": ["gbif"],
    },
    # --- Wave Z+ expansion (migration 006): 16 more sources ----------------
    # WHO regional offices (hourly, staggered)
    # NOTE: who-euro, who-searo disabled 2026-05-13 (migration 032).
    # WHO CMS migration decommissioned all who.int/{region}/rss-feeds/news feeds.
    # Legacy subdomains return SSL errors or have no A record. Covered by who-don (A1).
    # Uncomment if WHO publishes replacement RSS URLs.
    # NOTE: who-wpro re-enabled 2026-05-13 (migration 047). Connector redirected
    # to global WHO RSS (rss-feeds/news-english.xml), which is confirmed working.
    # NOTE: who-emro disabled 2026-05-13 (migration 049). emro.who.int/rss-feeds/
    # whoemro-rss.xml returns 302→404. EMRO region has minimal ANDV/HFRS burden;
    # covered by who-don. Re-enable if WHO EMRO publishes a replacement RSS URL.
    # "fetch-who-euro": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=4),
    #     "args": ["who-euro"],
    # },
    # NOTE: who-emro disabled 2026-05-13 (migration 049). Dead URL (302→404).
    # Slot minute=9 repurposed for spf-france (migration 051).
    # Santé publique France — news RSS. France MV Hondius cluster (43 cases)
    # + PUUV endemic (Ardennes, Champagne-Ardenne). NATO A2.
    "fetch-spf-france": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=9),
        "args": ["spf-france"],
    },
    # NOTE: who-searo disabled 2026-05-13 (migration 032). Dead URL.
    # Slot minute=14 repurposed for sweden-fhm (migration 051).
    # Folkhälsomyndigheten — infectious disease news. Highest per-capita PUUV
    # incidence in Europe (sorkfeber, Norrland). NATO A2.
    "fetch-sweden-fhm": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=14),
        "args": ["sweden-fhm"],
    },
    # who-wpro re-enabled 2026-05-13 (migration 047): connector now uses the
    # global WHO RSS (rss-feeds/news-english.xml). Minute=19 preserved.
    "fetch-who-wpro": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=19),
        "args": ["who-wpro"],
    },
    # Asia-Pacific national authorities
    # NOTE: china-cdc disabled 2026-05-13 (migration 032). weekly.chinacdc.cn RSS
    # 404; /en/rss 403 (WAF). PubMed covers China CDC Weekly articles.
    # "fetch-china-cdc": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=24, hour="*/6"),
    #     "args": ["china-cdc"],
    # },
    # NOTE: japan-niid disabled 2026-05-13 (migration 032). NIID retired English
    # RSS; page exists as HTML only. google-news catches cluster announcements.
    # "fetch-japan-niid": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=29, hour="*/6"),
    #     "args": ["japan-niid"],
    # },
    "fetch-australia-health": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=34),
        "args": ["australia-health"],
    },
    # NOTE: nz-moh disabled (migration 030). NZ MoH 403 from VPS IP. NZ has
    # minimal hantavirus burden; coverage maintained by google-news.
    # "fetch-nz-moh": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=39),
    #     "args": ["nz-moh"],
    # },
    # Latin America (ANDV heartland)
    # Argentina BEN weekly bulletin. Re-enabled 2026-05-13 (migration 043):
    # HTMLScraperBase 0.2.0 replaces the dead salud/noticias.xml RSS feed with
    # the 2026 BEN bulletin index. Argentina is the global ANDV epicentre.
    # Hourly at minute=44 (Latin America block, between chile-deis at 49
    # [disabled] and brazil-ms at 54).
    "fetch-argentina-msal": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=44),
        "args": ["argentina-msal"],
    },
    # Bolivia MSD — Ministerio de Salud y Deportes Joomla RSS (migration 045,
    # 2026-05-13). Bolivia is ANDV endemic (Beni/Pando departments). Spanish-
    # language feed. Minute=46: 2 min after argentina-msal in the Latin
    # America block.
    "fetch-bolivia-msd": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=46),
        "args": ["bolivia-msd"],
    },
    # NOTE: chile-deis disabled 2026-05-13 (migration 042). minsal.cl WAF returns
    # 403 on ALL paths from OVH Gravelines IP. High-priority re-enable target --
    # Chile is a primary ANDV country. Coverage: paho-alerts (A1) + google-news.
    # "fetch-chile-deis": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=49),
    #     "args": ["chile-deis"],
    # },
    # Tier-2 batch 4 (13 May 2026, migration 048): Venezuela + Peru ANDV gap.
    "fetch-venezuela-mpps": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=48),
        "args": ["venezuela-mpps"],
    },
    "fetch-peru-minsa": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=52),
        "args": ["peru-minsa"],
    },
    "fetch-brazil-ms": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=54),
        "args": ["brazil-ms"],
    },
    # Peer-reviewed
    "fetch-plos-pathogens": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=11, hour="*/6"),
        "args": ["plos-pathogens"],
    },
    "fetch-plos-ntds": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=16, hour="*/6"),
        "args": ["plos-ntds"],
    },
    # NOTE: mbio disabled 2026-05-13 (migration 034). ASM publisher WAF 403.
    # PubMed indexes all mBio hantavirus papers.
    # "fetch-mbio": {
    #     "task": "horizon_worker.tasks.ingest.fetch_source",
    #     "schedule": crontab(minute=21, hour="*/12"),
    #     "args": ["mbio"],
    # },
    "fetch-elife": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=26, hour="*/12"),
        "args": ["elife"],
    },
    # Animal health
    "fetch-wahis": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=31, hour="*/6"),
        "args": ["wahis"],
    },
    # --- Tier-2 audit batch 1 (migration 037, 13 May 2026) ----------------
    # Avian Flu Diary — Mike Coston's outbreak commentary blog. NATO B3
    # (commentary on primary sources, since 2006). Posts 1-2x/day; every
    # 6h is plenty. Minute 6 dodges the 0/5/15/30/45 high-traffic marks
    # and the cruisemapper 2,7,12... cadence.
    "fetch-avian-flu-diary": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=6, hour="*/6"),
        "args": ["avian-flu-diary"],
    },
    # One Health (Elsevier, ISSN 2352-7714) — peer-reviewed open-access
    # journal at the human/animal/environment interface. NATO A2. Journals
    # update ahead-of-print a few times/week so every 12h is appropriate.
    "fetch-one-health": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=41, hour="*/12"),
        "args": ["one-health"],
    },
    # NCBI GenBank orthohantavirus sequences — molecular confirmation layer.
    # Two-step E-utilities (esearch + esummary), reldate=14 days. NATO A1.
    # Runs every 6h: genome deposits typically take 12-24h from submission
    # to visibility in esearch, so 6h polling catches everything while
    # respecting NCBI's courtesy limit of <=3 requests/second per IP.
    # Minute 48 avoids the 0/5/15/30/45 high-traffic marks.
    "fetch-ncbi-virus": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute=48, hour="*/6"),
        "args": ["ncbi-virus"],
    },
    # --- Tier-2 batch 2 (migration 039, 13 May 2026): Mastodon social ----
    # mastodon.social public hashtag RSS feeds, no auth. NATO C3 (social).
    # Every 15 min, offset from 0/15/30/45 to avoid competing with ProMED,
    # Google News, and extraction tasks that fire on those exact marks.
    #
    # #hantavirus — general outbreak discussion from epidemiologists +
    #   journalists. Fires at 4/19/34/49.
    "fetch-mastodon-hantavirus": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="4,19,34,49"),
        "args": ["mastodon-hantavirus"],
    },
    # #MVHondius — vessel-specific MV Hondius cluster feed, most active
    #   of all three hashtag feeds (42KB). Fires at 9/24/39/54.
    "fetch-mastodon-hondius": {
        "task": "horizon_worker.tasks.ingest.fetch_source",
        "schedule": crontab(minute="9,24,39,54"),
        "args": ["mastodon-hondius"],
    },
    # ----------------------------------------------------------------------
    # AIS vessel tracking — Kpler. Disabled 2026-05-13 by Phoenix: the
    # account that owns KPLER_API_KEY has no working path to the
    # Maritime AIS product. Every poll returns HTTP 401 and there is no
    # self-service action to fix it from our side. The dead schedule
    # entry stays commented in place (NOT deleted) so re-enabling is
    # a one-line uncomment if Kpler access is ever obtained.
    # Active AIS sources: aisstream (websocket) + cruisemapper + myshiptracking.
    # "ais-poll-latest": {
    #     "task": "horizon_worker.tasks.ais.poll_latest_positions",
    #     "schedule": crontab(minute="*/2"),
    #     "args": [],
    # },
    # Dead-reckoning fallback — every 30 min. Only writes a 'manual' fix
    # if no live aisstream/marinetraffic/myshiptracking hit in the last
    # 6h, so the map never shows a stale position from days ago.
    "ais-dead-reckon": {
        "task": "horizon_worker.tasks.ais.dead_reckon_position",
        "schedule": crontab(minute="*/30"),
        "args": [],
    },
    # MyShipTracking public-page scraper — every 5 min. Free, no API key,
    # parses one regex out of the public vessel page. Real live AIS data.
    "ais-myshiptracking": {
        "task": "horizon_worker.tasks.ais.poll_myshiptracking",
        "schedule": crontab(minute="*/5"),
        "args": [],
    },
    # CruiseMapper public-page scraper — every 5 min. Scrapes the JSON
    # blob CruiseMapper embeds in its vessel HTML. Aggregates terrestrial
    # + satellite AIS; verified to have fresher mid-ocean fixes than MST.
    "ais-cruisemapper": {
        "task": "horizon_worker.tasks.ais.poll_cruisemapper",
        "schedule": crontab(minute="2,7,12,17,22,27,32,37,42,47,52,57"),
        "args": [],
    },
    # Structured-fact extractor for MV Hondius — every 15 min. Closes the
    # loop between live article ingestion and the incident ontology so
    # the map auto-updates when new WHO/ECDC/CDC bulletins land.
    "extraction-hondius": {
        "task": "horizon_worker.tasks.extraction.run_hondius_extractor",
        "schedule": crontab(minute="*/15"),
        "args": [],
    },
    # IndexNow push — notifies Bing, Yandex, Seznam, Naver, Yep, DuckDuckGo
    # about freshly-ingested article URLs every 15 min. Standardised
    # crawler-notification protocol; cuts indexing latency from days to hours.
    "indexnow-submit": {
        "task": "horizon_worker.tasks.indexnow.submit_recent",
        "schedule": crontab(minute="8,23,38,53"),
        "args": [],
    },
}
