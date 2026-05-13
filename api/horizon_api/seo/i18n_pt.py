"""Brazilian Portuguese (pt-BR) translations for HORIZON SEO pages.

Brazil is one of the most hantavirus-endemic countries in the Americas
(São Paulo, Mato Grosso do Sul, Rio Grande do Sul, Santa Catarina,
Paraná). Andes-virus-relative <em>Juquitiba</em> and <em>Araraquara</em>
hantaviruses circulate locally. Search demand for "hantavirose sintomas",
"vírus hantavírus", "síndrome cardiopulmonar por hantavírus" is high
and current pt-BR coverage in tracker apps is essentially zero.

Translation philosophy mirrors the Spanish module: every paragraph is
written in the medical vocabulary used by the Ministério da Saúde, OPAS
Brasil, and Fiocruz — not a calque of English jargon. We say "síndrome
cardiopulmonar por hantavírus" (SCPH), the term Brazilian MoH
publications use, not "síndrome pulmonar por hantavírus".
"""

from __future__ import annotations

PT_NOT_MEDICAL_ADVICE = (
    '<aside class="callout"><strong>Isto não é orientação médica.</strong> '
    'O HORIZON é uma plataforma de vigilância em saúde pública e OSINT. '
    'Se você tem sintomas, procure um profissional de saúde ou a Secretaria '
    'de Saúde local. Veja '
    '<a href="https://www.gov.br/saude" rel="external">Ministério da Saúde</a>, '
    '<a href="https://www.paho.org/pt" rel="external">OPAS</a> ou '
    '<a href="https://www.cdc.gov/hantavirus/" rel="external">CDC Hantavirus</a>.'
    '</aside>'
)

PT_CTA_LIVE_MAP = '<p><a class="cta" href="/">Abrir o mapa de surtos em tempo real →</a></p>'


PT_HANTAVIRUS_HUB_BODY = f"""
<p class="lead">
Os hantavírus são uma família de vírus de RNA transmitidos por roedores
(gênero <em>Orthohantavirus</em>, família <em>Hantaviridae</em>) capazes
de causar duas síndromes clínicas distintas em humanos: a
<strong>síndrome cardiopulmonar por hantavírus (SCPH)</strong>,
predominante nas Américas, e a <strong>febre hemorrágica com síndrome
renal (FHSR)</strong>, predominante na Eurásia. O HORIZON rastreia todos
os orthohantavírus de importância para a saúde pública e agrega sinais de
surto da OMS, OPAS, CDC, ECDC, ProMED, literatura revisada por pares e
notícias abertas — cada registro carrega procedência de fonte em nível
de auditoria.
</p>

{PT_NOT_MEDICAL_ADVICE}

<h2>O que é hantavírus</h2>
<p>
Os hantavírus são vírus de RNA fita simples de polaridade negativa com
genoma trissegmentado dentro da família <em>Hantaviridae</em>. Cada
sorotipo está associado a uma espécie reservatório específica — a
coespecificidade é tão estreita que a coevolução com a linhagem do roedor
é uma das características evolutivas dominantes da família. Humanos se
infectam ao inalar partículas virais aerossolizadas a partir de excretas
de roedores (urina, fezes, saliva). Com uma exceção — o vírus Andes — os
hantavírus não se transmitem entre pessoas.
</p>

<h3>Cepas relevantes no Brasil</h3>
<p>
O Brasil é um dos países americanos com maior atividade de hantavirose.
Cepas locais incluem <strong>Juquitiba (JUQV)</strong>, presente no Sul e
Sudeste; <strong>Araraquara (ARQV)</strong>, no Centro-Oeste e Sudeste,
de letalidade elevada (40 a 50%); <strong>Castelo dos Sonhos</strong> e
<strong>Anajatuba</strong> em focos amazônicos. Reservatórios:
<em>Oligoryzomys nigripes</em> (rato-do-mato) e <em>Necromys lasiurus</em>.
</p>

<h3>Surto ativo</h3>
<p>
O <a href="/pt-br/surtos/mv-hondius-2026">surto do MV Hondius 2026</a> é
a investigação principal exibida no mapa em tempo real do HORIZON. O
agrupamento se origina em uma exposição pré-embarque suspeita durante
uma excursão de observação de aves perto de Ushuaia (Terra do Fogo,
Argentina), com vírus Andes (ANDV) confirmado por PCR no caso
sul-africano. Contagens oficiais vêm do OMS Disease Outbreak News
2026-DON600 e das atualizações de vigilância do ECDC.
</p>

{PT_CTA_LIVE_MAP}

<h2>As duas síndromes clínicas</h2>

<h3>Síndrome Cardiopulmonar por Hantavírus (SCPH)</h3>
<p>
A SCPH é a apresentação mais letal, com letalidade entre 30 e 50% para o
vírus Andes e aproximadamente 38% para Sin Nombre segundo a vigilância
do CDC. No Brasil, a letalidade de Araraquara chega a 40-50%. Após
incubação de 1 a 8 semanas, os pacientes desenvolvem breve pródromo
gripal (febre, mialgia, cefaleia) seguido de colapso cardiopulmonar
rápido com edema pulmonar não cardiogênico e choque. O achado
laboratorial definitório é a trombocitopenia com desvio à esquerda e
imunoblastos circulantes.
</p>

<h3>Febre Hemorrágica com Síndrome Renal (FHSR)</h3>
<p>
A FHSR é associada aos sorotipos do Velho Mundo. Vírus Hantaan e
Dobrava-Belgrade produzem doença grave (letalidade 5 a 15%); Puumala e
Seoul, formas mais leves (letalidade abaixo de 2%). O curso clássico
de cinco fases (febril, hipotensiva, oligúrica, diurética, convalescente)
é mais reconhecível na doença por vírus Hantaan. Lesão renal aguda é a
característica renal definitória.
</p>

<p>
Detalhe ampliado nas páginas
<a href="/pt-br/hantavirus/sintomas">sintomas</a>,
<a href="/pt-br/hantavirus/transmissao">transmissão</a>,
<a href="/pt-br/hantavirus/prevencao">prevenção</a> e
<a href="/pt-br/hantavirus/tratamento">tratamento</a>.
</p>

<h2>Sorotipos rastreados</h2>
<p>
O HORIZON apresenta uma página dedicada a cada sorotipo de
orthohantavírus de importância para a saúde pública. Cada página detalha
a espécie reservatório, o intervalo endêmico, o tipo de síndrome, a
estimativa de letalidade e o perfil de transmissão.
</p>

<ul>
<li><strong><a href="/pt-br/hantavirus/virus-andes">Vírus Andes (ANDV)</a></strong> — SCPH; Argentina, Chile; única espécie com transmissão pessoa-pessoa.</li>
<li><strong><a href="/pt-br/hantavirus/sin-nombre">Vírus Sin Nombre (SNV)</a></strong> — SCPH; região Four Corners dos EUA.</li>
<li><strong><a href="/pt-br/hantavirus/puumala">Vírus Puumala (PUUV)</a></strong> — nefropatia epidêmica; Escandinávia e Europa Central.</li>
<li><strong><a href="/pt-br/hantavirus/hantaan">Vírus Hantaan (HTNV)</a></strong> — FHSR; China e península coreana.</li>
<li><strong><a href="/pt-br/hantavirus/seoul">Vírus Seoul (SEOV)</a></strong> — FHSR leve; distribuição mundial via Rattus.</li>
</ul>

<h2>Metodologia e procedência de fontes</h2>
<p>
Cada registro do HORIZON carrega uma <a href="/methodology">citação em
nível de auditoria</a> incluindo: citação de referência ICD 206;
classificação NATO de confiabilidade (A–F) e credibilidade (1–6); modelo
de dupla confiança (pipeline automática + analista humano); hash SHA-256
de cadeia de custódia conforme o Protocolo de Berkeley.
</p>

<h2>Dados abertos — CC BY 4.0</h2>
<p>
Todos os dados do HORIZON são publicados sob a licença
<a href="https://creativecommons.org/licenses/by/4.0/deed.pt_BR" rel="external license">Creative Commons Atribuição 4.0 Internacional</a>. Réplica, scraping, indexação e
treinamento de modelos são permitidos com atribuição à 79th Unit Limited.
</p>

{PT_CTA_LIVE_MAP}
"""


PT_SYMPTOMS_BODY = f"""
<p class="lead">
A doença por hantavírus se apresenta com duas síndromes clínicas
distintas dependendo do sorotipo causador. Ambas compartilham um
pródromo gripal de 3 a 7 dias e então divergem: a <strong>SCPH</strong>
progride a falência cardiopulmonar; a <strong>FHSR</strong> a falência
renal com sangramento. A incubação é de 1 a 8 semanas.
</p>

{PT_NOT_MEDICAL_ADVICE}

<h2>Fase 1 — Pródromo (dias 1 a 7)</h2>
<p>
Ambas as síndromes começam de forma similar e são facilmente confundidas
com influenza, COVID-19, dengue, leptospirose, febre amarela ou sepse
precoce. Características típicas:
</p>
<ul>
<li>Febre alta (frequentemente 39–40 °C)</li>
<li>Mialgia severa, especialmente em coxas, quadris e região lombar</li>
<li>Cefaleia</li>
<li>Fadiga e mal-estar geral</li>
<li>Sintomas gastrointestinais — náuseas, vômitos, dor abdominal, diarreia</li>
<li>Tontura, calafrios</li>
</ul>

<h2>Fase cardiopulmonar (SCPH)</h2>
<p>
Quatro a dez dias após o início dos sintomas, a SCPH transita
rapidamente para a fase cardiopulmonar. A característica definitória é o
edema pulmonar não cardiogênico com choque. CDC reporta letalidade
global da SCPH de 38% para Sin Nombre e 30–50% para Andes. No Brasil, o
sorotipo Araraquara apresenta letalidade de 40–50%. Achados-chave:
</p>
<ul>
<li>Tosse e dispneia progressiva</li>
<li>Taquipneia e hipoxemia</li>
<li>Infiltrados pulmonares bilaterais na radiografia de tórax</li>
<li>Hipotensão e colapso circulatório</li>
<li>Trombocitopenia (plaquetas inferiores a 150.000/μL)</li>
<li>Hemoconcentração e acidose láctica</li>
<li>Leucocitose com desvio à esquerda e imunoblastos circulantes</li>
</ul>

<h2>Fases da FHSR (Velho Mundo)</h2>
<table class="facts">
<tr><th>Fase</th><th>Características</th></tr>
<tr><th>Febril (dias 3–7)</th><td>Febre, rubor, injeção conjuntival, exantema petequial, dor retro-orbital</td></tr>
<tr><th>Hipotensiva</th><td>Extravasamento vascular, choque, taquicardia, início da oligúria</td></tr>
<tr><th>Oligúrica (dias 2–10)</th><td>Lesão renal aguda, sobrecarga de líquidos, complicações hemorrágicas</td></tr>
<tr><th>Diurética</th><td>Poliúria com recuperação renal; manejo crítico de fluidos e eletrólitos</td></tr>
<tr><th>Convalescente</th><td>Retorno gradual ao basal; comprometimento renal persistente em alguns pacientes</td></tr>
</table>

<h2>Quando procurar atendimento</h2>
<p>
Qualquer pessoa com os sintomas prodromáis acima e um histórico de
exposição crível — contato com roedores em zona rural, viagem recente a
área endêmica (Sul/Sudeste/Centro-Oeste brasileiro), exposição
ocupacional (camping, caça, conservação, agricultura, limpeza de
estruturas infestadas) — deve procurar atendimento urgente. A detecção
precoce e a terapia intensiva são os preditores mais fortes de
sobrevivência.
</p>

<p><a href="/pt-br/hantavirus">← Voltar à visão geral</a></p>
{PT_CTA_LIVE_MAP}
"""


PT_TRANSMISSION_BODY = f"""
<p class="lead">
Os hantavírus são <strong>transmitidos por roedores</strong>. Humanos são
hospedeiros acidentais e terminais para quase todos os sorotipos. A
transmissão é predominantemente por inalação de excretas aerossolizadas
em espaços fechados. <strong>O vírus Andes é a única exceção</strong>:
tem transmissão documentada de pessoa a pessoa, especialmente entre
contatos domiciliares próximos.
</p>

{PT_NOT_MEDICAL_ADVICE}

<h2>Rota primária: aerossol roedor → humano</h2>
<p>
Roedores infectados eliminam vírus na urina, fezes e saliva. Quando as
excretas secas são perturbadas — ao varrer, aspirar ou pela movimentação
de veículos em um celeiro ou cabana — partículas carregadas de vírus se
aerossolizam e podem ser inaladas. O risco é máximo em estruturas mal
ventiladas e infestadas: cabanas, dependências rurais, armazéns,
veículos abandonados, alojamentos militares e apartamentos com presença
de roedores.
</p>

<h2>Transmissão pessoa-pessoa do vírus Andes</h2>
<p>
O vírus Andes (ANDV) é o único orthohantavírus com transmissão
documentada de pessoa a pessoa. Evidências do agrupamento de El Bolsón
(Argentina, 1996), de clusters na Patagônia chilena (2018–2019), e
agora do <a href="/pt-br/surtos/mv-hondius-2026">grupo MV Hondius</a>
sob monitoramento ativo.
</p>

<h2>O que NÃO transmite hantavírus</h2>
<ul>
<li>Mosquitos, carrapatos ou outros vetores artrópodes — hantavírus <em>não</em> são arboviroses.</li>
<li>Contato casual com pacientes (exceto contatos próximos do ANDV).</li>
<li>Alimentos preparados em cozinhas sem contaminação por roedores.</li>
<li>Transfusão sanguínea (sem casos documentados).</li>
<li>Transmissão sexual (sem casos documentados).</li>
</ul>

<p>Veja <a href="/pt-br/hantavirus/prevencao">prevenção</a> para medidas baseadas em evidência.</p>

<p><a href="/pt-br/hantavirus">← Voltar à visão geral</a></p>
{PT_CTA_LIVE_MAP}
"""


PT_PREVENTION_BODY = f"""
<p class="lead">
Não existe vacina contra hantavírus licenciada na Europa ou América do
Norte. A única vacina autorizada — <strong>Hantavax</strong> da Coreia
do Sul — cobre o vírus Hantaan. A prevenção, portanto, é
<strong>controle de exposição</strong>: reduzir populações de roedores,
suprimir geração de aerossóis durante limpeza e usar proteção
respiratória adequada.
</p>

{PT_NOT_MEDICAL_ADVICE}

<h2>Reduzir a presença de roedores em casa</h2>
<ul>
<li>Vede aberturas maiores que 6 mm com lã de aço e silicone; cubra ralos e respiros com tela metálica.</li>
<li>Elimine fontes de alimento: grãos e ração de animais em recipientes vedados de metal ou vidro; remova frutas caídas; tampe o lixo.</li>
<li>Elimine abrigos: corte mato em até 30 m das estruturas; eleve a lenha pelo menos 30 cm do chão e a 30 m da casa.</li>
<li>Use armadilhas de mola continuamente; rotacione locais.</li>
<li>Evite captura viva e soltura — locais de soltura tornam-se focos de reinfestação.</li>
</ul>

<h2>Limpeza segura de áreas contaminadas</h2>
<p>
Conforme protocolo do CDC e Ministério da Saúde brasileiro,
<strong>nunca varra nem aspire excretas secas</strong> — ambos os
métodos aerossolizam vírus. Protocolo:
</p>
<ol>
<li>Ventile o local por pelo menos 30 minutos antes de entrar; abra portas e janelas.</li>
<li>Use respirador N95/FFP3, luvas de borracha ou látex e óculos.</li>
<li>Sature as excretas e superfícies contaminadas com água sanitária diluída 1:10 (5.000 ppm) ou desinfetante registrado; deixe agir 5 minutos.</li>
<li>Limpe com papel toalha; ensaque os resíduos; dupla-embale e sele.</li>
<li>Esfregue o piso com desinfetante; não aspire mesmo após desinfecção.</li>
</ol>

<p><a href="/pt-br/hantavirus">← Voltar à visão geral</a></p>
{PT_CTA_LIVE_MAP}
"""


PT_FAQ_ENTRIES: list[tuple[str, str]] = [
    (
        "O que é hantavírus?",
        "Hantavírus é uma família de vírus (gênero <em>Orthohantavirus</em>, família <em>Hantaviridae</em>) transmitidos por roedores que podem causar doença grave em humanos. As duas síndromes principais são a síndrome cardiopulmonar por hantavírus (SCPH, comum nas Américas) e a febre hemorrágica com síndrome renal (FHSR, comum na Eurásia). Veja <a href=\"/pt-br/hantavirus\">a página geral</a>.",
    ),
    (
        "Como é transmitido o hantavírus?",
        "A maioria dos hantavírus é transmitida de roedores a humanos por inalação de excretas aerossolizadas (urina, fezes, saliva). O <strong>vírus Andes é a única exceção</strong>, com transmissão pessoa-pessoa documentada, principalmente entre contatos domiciliares próximos. Detalhes em <a href=\"/pt-br/hantavirus/transmissao\">transmissão</a>.",
    ),
    (
        "Quais são os sintomas da doença por hantavírus?",
        "Sintomas iniciais aparecem entre 1 e 8 semanas após exposição: febre, mialgia severa, fadiga, cefaleia e sintomas gastrointestinais. Na SCPH evolui para tosse, dispneia e edema pulmonar — letalidade 30–50%. Na FHSR os pacientes desenvolvem falência renal, plaquetas baixas e sangramento — letalidade 1–15%. Veja <a href=\"/pt-br/hantavirus/sintomas\">a página completa</a>.",
    ),
    (
        "Existe vacina ou tratamento para hantavírus?",
        "A Coreia do Sul licencia a Hantavax para o vírus Hantaan. Não há vacina licenciada no Brasil, UE ou EUA. O tratamento é cuidado crítico de suporte: manejo de fluidos, ventilação mecânica, ECMO e terapia de substituição renal. A ribavirina mostra benefício na FHSR precoce mas não na SCPH.",
    ),
    (
        "Quais países reportam casos de hantavírus?",
        "Casos são reportados nas Américas (Argentina, Chile, Brasil, EUA, Canadá, Panamá, Bolívia, Paraguai), Europa (Alemanha, Finlândia, Rússia, Bélgica, França, Bálcãs) e Ásia Oriental (China, Coreia do Sul, Japão). HORIZON mantém <a href=\"/countries\">páginas por país</a>.",
    ),
    (
        "Hantavirose existe no Brasil?",
        "Sim. O Brasil tem hantavirose endêmica em vários estados, especialmente São Paulo, Mato Grosso do Sul, Rio Grande do Sul, Santa Catarina, Paraná, Goiás, Minas Gerais e parte da Amazônia. Sorotipos circulantes incluem Juquitiba, Araraquara, Castelo dos Sonhos e Anajatuba. O Ministério da Saúde mantém vigilância via SINAN. Reservatórios primários são <em>Oligoryzomys nigripes</em> e <em>Necromys lasiurus</em>.",
    ),
    (
        "O que é o agrupamento MV Hondius?",
        "Um agrupamento de casos por vírus Andes a bordo do navio de expedição polar <strong>MV Hondius</strong> (IMO 9818709, MMSI 244327000, Oceanwide Expeditions, bandeira holandesa). Exposição pré-embarque suspeita durante excursão perto de Ushuaia, Terra do Fogo, Argentina. Sob monitoramento por OMS, ECDC, CDC, OPAS e Ministério da Saúde argentino. Cronologia em <a href=\"/pt-br/surtos/mv-hondius-2026\">/pt-br/surtos/mv-hondius-2026</a>.",
    ),
    (
        "Como prevenir a infecção por hantavírus?",
        "Reduza a população de roedores próxima; nunca varra ou aspire excretas secas; use respirador N95/FFP3 e umedeça com água sanitária diluída (1:10) antes de limpar. Acampantes e excursionistas devem evitar dormir perto de ninhos. Protocolo completo em <a href=\"/pt-br/hantavirus/prevencao\">prevenção</a>.",
    ),
    (
        "Posso usar estes dados?",
        "Sim. Todos os dados do HORIZON são publicados sob <a href=\"https://creativecommons.org/licenses/by/4.0/deed.pt_BR\" rel=\"license external\">CC BY 4.0</a>. Réplica, scraping, indexação e treinamento de modelos são permitidos com atribuição à 79th Unit Limited.",
    ),
]


def render_pt_faq_body() -> str:
    parts = [
        '<p class="lead">Perguntas frequentes sobre a doença por hantavírus, o surto do MV Hondius 2026 e a plataforma HORIZON.</p>',
    ]
    for q, a in PT_FAQ_ENTRIES:
        parts.append(f'<h2>{q}</h2>\n<div>{a}</div>')
    parts.append('<p><a href="/pt-br/hantavirus">← Voltar à visão geral</a></p>')
    parts.append(PT_CTA_LIVE_MAP)
    return "".join(parts)


PT_SEROTYPE_PROSE: dict[str, dict[str, str]] = {
    "virus-andes": {
        "name": "Vírus Andes (ANDV)",
        "syndrome": "Síndrome Cardiopulmonar por Hantavírus (SCPH)",
        "reservoir": "Oligoryzomys longicaudatus (rato-do-mato-de-cauda-longa)",
        "endemic": "Argentina, Chile, Patagônia austral, Terra do Fogo",
        "cfr": "30 a 50 por cento",
        "p2p": "Único orthohantavírus com transmissão pessoa-pessoa documentada, principalmente entre contatos domiciliares próximos.",
        "summary": (
            "O vírus Andes é o sorotipo de hantavírus mais letal reconhecido nas "
            "Américas. Endêmico do Cone Sul sul-americano, é o sorotipo "
            "principal implicado no surto do MV Hondius 2026. Sintomas surgem "
            "entre 1 e 8 semanas após exposição e evoluem rapidamente para "
            "colapso cardiopulmonar sem cuidados intensivos."
        ),
    },
    "sin-nombre": {
        "name": "Vírus Sin Nombre (SNV)",
        "syndrome": "Síndrome Cardiopulmonar por Hantavírus (SCPH)",
        "reservoir": "Peromyscus maniculatus (rato-cervo)",
        "endemic": "Região Four Corners dos EUA, Canadá, México",
        "cfr": "aproximadamente 38 por cento",
        "p2p": "Sem transmissão pessoa-pessoa documentada.",
        "summary": (
            "O vírus Sin Nombre é a causa principal de SCPH na América do Norte. "
            "Identificado em 1993 durante o surto Four Corners, é portado pelo "
            "rato-cervo e transmitido a humanos por inalação de excretas "
            "aerossolizadas em estruturas rurais fechadas."
        ),
    },
    "puumala": {
        "name": "Vírus Puumala (PUUV)",
        "syndrome": "Nefropatia epidêmica (FHSR leve)",
        "reservoir": "Myodes glareolus (arganaz)",
        "endemic": "Escandinávia, Báltico, Europa Central, Rússia europeia",
        "cfr": "menos de 1 por cento",
        "p2p": "Sem transmissão pessoa-pessoa documentada.",
        "summary": (
            "O vírus Puumala é a causa mais comum de doença por hantavírus na "
            "Europa. Produz uma variante renal mais leve chamada nefropatia "
            "epidêmica."
        ),
    },
    "hantaan": {
        "name": "Vírus Hantaan (HTNV)",
        "syndrome": "Febre Hemorrágica com Síndrome Renal (FHSR)",
        "reservoir": "Apodemus agrarius (rato-de-listra)",
        "endemic": "China, península coreana, Extremo Oriente russo",
        "cfr": "5 a 15 por cento",
        "p2p": "Sem transmissão pessoa-pessoa documentada.",
        "summary": (
            "O vírus Hantaan é o protótipo da família e a causa mais severa de "
            "FHSR na Ásia Oriental. Coreia do Sul licencia uma vacina (Hantavax) "
            "para este sorotipo."
        ),
    },
    "seoul": {
        "name": "Vírus Seoul (SEOV)",
        "syndrome": "FHSR leve",
        "reservoir": "Rattus norvegicus, Rattus rattus",
        "endemic": "Mundial via distribuição global de Rattus",
        "cfr": "1 a 2 por cento",
        "p2p": "Sem transmissão pessoa-pessoa documentada.",
        "summary": (
            "O vírus Seoul circula onde existirem seus reservatórios — "
            "efetivamente global. Surtos foram reportados em criadores de "
            "ratos pet nos EUA e Reino Unido."
        ),
    },
}


def render_pt_serotype_body(s_en: dict, s_pt: dict | None) -> str:
    s = s_pt or {
        "name": s_en["name"],
        "syndrome": s_en["syndrome"],
        "reservoir": s_en["reservoir"],
        "endemic": s_en["endemic"],
        "cfr": s_en["cfr"],
        "p2p": s_en["p2p"],
        "summary": s_en["summary"],
    }
    code = s_en["code"]
    return f"""
<p class="lead">{s["summary"]}</p>

{PT_NOT_MEDICAL_ADVICE}

<table class="facts">
<tr><th>Código do vírus</th><td><strong>{code}</strong></td></tr>
<tr><th>Nome completo</th><td>{s["name"]}</td></tr>
<tr><th>Síndrome clínica</th><td>{s["syndrome"]}</td></tr>
<tr><th>Espécie reservatório</th><td>{s["reservoir"]}</td></tr>
<tr><th>Regiões endêmicas</th><td>{s["endemic"]}</td></tr>
<tr><th>Letalidade</th><td>{s["cfr"]}</td></tr>
<tr><th>Pessoa-pessoa</th><td>{s["p2p"]}</td></tr>
</table>

<h2>Sobre o {s["name"]}</h2>
<p>{s["summary"]}</p>

<h2>Vigilância e surtos</h2>
<p>
HORIZON indexa cada boletim OMS Disease Outbreak News, relatório semanal
ECDC, alerta CDC HAN, atualização OPAS e publicação revisada por pares
que mencione {code}.
</p>

<h2>Fontes oficiais</h2>
<ul>
<li><a href="https://www.gov.br/saude" rel="external">Ministério da Saúde — Brasil</a></li>
<li><a href="https://www.paho.org/pt" rel="external">OPAS Brasil</a></li>
<li><a href="https://www.cdc.gov/hantavirus/" rel="external">CDC Hantavirus</a></li>
<li><a href="https://www.who.int/" rel="external">OMS</a></li>
</ul>

<p><a href="/pt-br/hantavirus">← Todos os tópicos de hantavírus</a></p>
{PT_CTA_LIVE_MAP}
"""
