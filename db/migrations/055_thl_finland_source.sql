-- HORIZON migration 055: Terveyden ja hyvinvoinnin laitos (THL) — Finland.
--
-- THL is Finland's national public health authority and the primary reporting
-- institution for hantavirus in Europe's highest-burden country. Finland records
-- the highest hantavirus notification rate in the EU/EEA: 14.5 per 100,000
-- (ECDC Annual Epidemiological Report 2023), driven by Puumala virus (PUUV)
-- in the bank vole (Myodes glareolus) reservoir.
--
-- Peak incidence follows bank vole population cycles (mast-year dynamics):
-- major epidemic years recorded in 2008, 2012, 2016, and 2020. Onset
-- typically peaks July-August in Norrland/Ångermanland-equivalent Finnish regions
-- (Häme, Pirkanmaa, Central Finland, North Karelia, South Savo).
--
-- THL publishes bilingual (Finnish/English) news on infectious diseases. The
-- connector targets the English-language hantavirus topic feed.
--
-- NATO A1 (completely reliable): national public health authority with statutory
-- notifiable disease reporting mandate under Finnish Law on Communicable Diseases.
-- Tier 1. official-authority.

\echo '==> HORIZON 055 THL Finland source'

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'thl-finland',
    'Terveyden ja hyvinvoinnin laitos (THL) — Finnish Institute for Health and Welfare',
    'https://thl.fi/en/web/infectious-diseases-and-vaccinations/-/topics/hantavirus-in-finland',
    1,
    'official-authority',
    'A',
    1,
    TRUE,
    'Added 2026-05-14 (migration 055). Finland has the highest hantavirus '
    'notification rate in the EU/EEA: 14.5/100,000 (ECDC AER 2023). '
    'Puumala virus (PUUV) dominant; bank vole (Myodes glareolus) reservoir. '
    'Peak incidence July-August, major epidemic years 2008/2012/2016/2020 '
    'following mast-year-driven vole population surges. '
    'English-language hantavirus topic RSS. NATO A1. '
    'Beat: hourly minute=16 (new slot).'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

INSERT INTO schema_migrations (version) VALUES ('055_thl_finland_source')
    ON CONFLICT DO NOTHING;

\echo '==> 055 done (THL Finland seeded)'
