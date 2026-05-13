-- HORIZON migration 002: seed serotype reference data.
-- Orthohantaviruses recognised for Phase 1 classification.

\echo '==> HORIZON 002 seed serotypes'

INSERT INTO serotypes (code, name, syndrome, geo_distribution, cfr_estimate_pct, notes) VALUES
('SNV',  'Sin Nombre virus',         'HPS',  'North America (US Southwest Four Corners endemic)', 36.0,
    'Deer mouse (Peromyscus maniculatus) reservoir. 1993 Four Corners outbreak source.'),
('ANDV', 'Andes virus',              'HPS',  'South America (Argentina, Chile, Uruguay)',          35.0,
    'Long-tailed pygmy rice rat (Oligoryzomys longicaudatus) reservoir. Only hantavirus with documented person-to-person transmission.'),
('HTNV', 'Hantaan virus',            'HFRS', 'East Asia (China, Korea, Russia Far East)',          15.0,
    'Striped field mouse (Apodemus agrarius). Severe HFRS form.'),
('PUUV', 'Puumala virus',            'HFRS', 'Europe (Scandinavia, Finland, Russia, Germany)',     0.4,
    'Bank vole (Myodes glareolus). Mild HFRS form (nephropathia epidemica).'),
('SEOV', 'Seoul virus',              'HFRS', 'Global (urban rats)',                                 1.0,
    'Norway rat (Rattus norvegicus). Distributed worldwide via shipping. Pet-rat associated outbreaks.'),
('DOBV', 'Dobrava-Belgrade virus',   'HFRS', 'Balkans, Eastern Europe',                            12.0,
    'Yellow-necked mouse (Apodemus flavicollis). Severe HFRS.'),
('BAYV', 'Bayou virus',              'HPS',  'Southeastern USA',                                   30.0,
    'Marsh rice rat (Oryzomys palustris).'),
('BCCV', 'Black Creek Canal virus',  'HPS',  'Florida',                                            30.0,
    'Cotton rat (Sigmodon hispidus).'),
('NY-1', 'New York virus',           'HPS',  'Northeastern USA',                                   30.0,
    'White-footed mouse (Peromyscus leucopus).'),
('CHOV', 'Choclo virus',             'HPS',  'Panama',                                              9.0,
    'Costa Rican pygmy rice rat (Oligoryzomys fulvescens). Milder course than other HPS-causing strains.'),
('LANV', 'Laguna Negra virus',       'HPS',  'Paraguay, Bolivia, Argentina',                       12.0,
    'Vesper mouse (Calomys laucha).'),
('TULV', 'Tula virus',               'HFRS', 'Europe',                                              0.5,
    'European common vole (Microtus arvalis). Rare human disease.');

\echo '==> 002 done (12 serotypes seeded)'
