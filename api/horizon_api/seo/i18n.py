"""Multi-locale support for HORIZON SEO pages.

We serve English (default, no prefix) and Spanish (under /es/). Both
variants are hreflang-linked so Google understands they're equivalents
and routes the right language to the right user.

Why Spanish: hantavirus is endemic across the entire Spanish-speaking
Andes (Argentina, Chile, Bolivia, Peru, Paraguay, Uruguay), plus Panama,
Costa Rica, and Spain. Search volume for "hantavirus síntomas",
"virus de los Andes", "fiebre hemorrágica con síndrome renal" etc. is
substantial and current Spanish-language tracker pages are sparse.

Why not auto-translate: we own the prose, we cite WHO/CDC/PAHO sources,
and Spanish-language medical authorities (Salud Argentina, Ministerio
de Salud Chile, ISCIII España) have their own terminology that we mirror
rather than blindly translating English jargon.

Translation philosophy: every paragraph is from a Spanish-language
medical reference frame, not a literal calque. We say "síndrome
cardiopulmonar por hantavirus" not "síndrome pulmonar por hantavirus"
because that's how Argentine and Chilean MoH publications write it.
"""

from __future__ import annotations

from typing import Final

# Supported locales. Each tuple = (locale_tag, url_prefix, og_locale).
LOCALES: Final[list[tuple[str, str, str]]] = [
    ("en-GB", "",     "en_GB"),
    ("es-ES", "/es",  "es_ES"),
]


def hreflang_links(canonical_path: str) -> list[tuple[str, str]]:
    """Return list of (hreflang, href) for the given path.

    The canonical_path is the path AFTER any locale prefix (e.g.,
    `/hantavirus` not `/es/hantavirus`).
    """
    from .common import BASE_URL
    links: list[tuple[str, str]] = []
    for lang, prefix, _ in LOCALES:
        links.append((lang, f"{BASE_URL}{prefix}{canonical_path}"))
    # Pure language fallbacks
    links.append(("es", f"{BASE_URL}/es{canonical_path}"))
    links.append(("en", f"{BASE_URL}{canonical_path}"))
    # x-default points at English
    links.append(("x-default", f"{BASE_URL}{canonical_path}"))
    return links


# ---------------------------------------------------------------------------
# Spanish editorial — hantavirus hub
# ---------------------------------------------------------------------------

ES_NOT_MEDICAL_ADVICE = (
    '<aside class="callout"><strong>Esto no es asesoramiento médico.</strong> '
    'HORIZON es una plataforma de vigilancia de salud pública y OSINT. '
    'Si presenta síntomas, consulte con un profesional sanitario o con su '
    'autoridad de salud pública local. Véase '
    '<a href="https://www.argentina.gob.ar/salud" rel="external">Ministerio de Salud Argentina</a>, '
    '<a href="https://www.minsal.cl/" rel="external">Ministerio de Salud de Chile</a>, '
    'o <a href="https://www.who.int/es" rel="external">OMS Hantavirus</a>.'
    '</aside>'
)


ES_CTA_LIVE_MAP = '<p><a class="cta" href="/">Abrir el mapa de brotes en vivo →</a></p>'


ES_HANTAVIRUS_HUB_BODY = f"""
<p class="lead">
Los hantavirus son una familia de virus de ARN transmitidos por roedores
(género <em>Orthohantavirus</em>, familia <em>Hantaviridae</em>) capaces de
causar dos síndromes clínicos distintos en humanos: el
<strong>síndrome cardiopulmonar por hantavirus (SCPH)</strong>,
predominante en las Américas, y la <strong>fiebre hemorrágica con
síndrome renal (FHSR)</strong>, predominante en Eurasia. HORIZON rastrea
todos los orthohantavirus de importancia para la salud pública y agrega
la señal de brotes desde OMS, OPS, CDC, ECDC, ProMED, literatura
revisada por pares y noticias abiertas — con procedencia de fuente de
nivel auditoría sobre cada registro.
</p>

{ES_NOT_MEDICAL_ADVICE}

<h2>Qué es el hantavirus</h2>
<p>
Los hantavirus son virus de ARN monocatenario de polaridad negativa y
genoma trisegmentado dentro de la familia <em>Hantaviridae</em>. Cada
serotipo está asociado a una especie reservorio específica — la
especificidad es tan estrecha que la coevolución con la línea de roedor
es una de las características evolutivas dominantes de la familia. Las
personas se infectan al inhalar virus aerosolizado a partir de excretas
de roedores (orina, heces, saliva), o más raramente por contacto directo
con animales infectados. Con una excepción — el virus de los Andes — los
hantavirus no se transmiten de persona a persona.
</p>

<h3>Seguimiento de brotes activos</h3>
<p>
El <a href="/es/brotes/mv-hondius-2026">brote del MV Hondius 2026</a> es
la investigación principal actualmente visible en el mapa en vivo de
HORIZON. El grupo se traza hasta una exposición previa al embarque
sospechada durante una excursión de avistamiento de aves cerca de Ushuaia
(Tierra del Fuego, Argentina), con virus de los Andes (ANDV) confirmado
por PCR en el caso de Sudáfrica. Los conteos oficiales provienen del
boletín OMS Disease Outbreak News 2026-DON600 y de las actualizaciones de
vigilancia del ECDC; la corroboración periodística se rebaja con la
escala NATO de Almirantazgo y un modelo de doble confianza.
</p>

{ES_CTA_LIVE_MAP}

<h2>Los dos síndromes clínicos</h2>

<h3>Síndrome Cardiopulmonar por Hantavirus (SCPH)</h3>
<p>
El SCPH es la presentación más letal, con letalidad global del 30 al 50
por ciento para el virus de los Andes y aproximadamente 38 por ciento
para Sin Nombre según la vigilancia del CDC. Tras una incubación de 1 a
8 semanas, los pacientes desarrollan un breve pródromo de tipo gripal
(fiebre, mialgia, cefalea) seguido de un colapso cardiopulmonar rápido
con edema pulmonar no cardiogénico y choque. El hallazgo de laboratorio
definitorio es trombocitopenia con desviación a la izquierda y blastos
inmunológicos circulantes.
</p>

<h3>Fiebre Hemorrágica con Síndrome Renal (FHSR)</h3>
<p>
La FHSR se asocia con serotipos del Viejo Mundo. Los virus Hantaan y
Dobrava-Belgrade producen enfermedad grave (letalidad 5 a 15 por ciento);
Puumala y Seoul producen presentaciones más leves (letalidad menor al
2 por ciento). El curso clínico clásico de cinco fases (febril,
hipotensiva, oligúrica, diurética, convaleciente) es más reconocible
en la enfermedad por virus Hantaan. La lesión renal aguda es la
característica renal definitoria.
</p>

<p>
Detalle ampliado en las páginas
<a href="/es/hantavirus/sintomas">síntomas</a>,
<a href="/es/hantavirus/transmision">transmisión</a>,
<a href="/es/hantavirus/prevencion">prevención</a> y
<a href="/es/hantavirus/tratamiento">tratamiento</a>.
</p>

<h2>Serotipos rastreados</h2>
<p>
HORIZON expone una página dedicada por cada serotipo de orthohantavirus
de importancia documentada para la salud pública. Cada página detalla
la especie reservorio, el rango endémico, el tipo de síndrome, la
estimación de letalidad y el perfil de transmisión.
</p>

<ul>
<li><strong><a href="/es/hantavirus/virus-de-los-andes">Virus de los Andes (ANDV)</a></strong> — SCPH; reservorio <em>Oligoryzomys longicaudatus</em>; Argentina, Chile, Patagonia austral.</li>
<li><strong><a href="/es/hantavirus/sin-nombre">Virus Sin Nombre (SNV)</a></strong> — SCPH; reservorio <em>Peromyscus maniculatus</em>; región Four Corners de EE. UU.</li>
<li><strong><a href="/es/hantavirus/puumala">Virus Puumala (PUUV)</a></strong> — nefropatía epidémica; reservorio <em>Myodes glareolus</em>; Escandinavia y Europa central.</li>
<li><strong><a href="/es/hantavirus/hantaan">Virus Hantaan (HTNV)</a></strong> — FHSR; reservorio <em>Apodemus agrarius</em>; China y península de Corea.</li>
<li><strong><a href="/es/hantavirus/seoul">Virus Seoul (SEOV)</a></strong> — FHSR leve; reservorio <em>Rattus norvegicus</em>; distribución mundial.</li>
<li><strong><a href="/es/hantavirus/dobrava-belgrado">Virus Dobrava-Belgrado (DOBV)</a></strong> — FHSR severa; reservorio <em>Apodemus flavicollis</em>; Balcanes y Europa central.</li>
<li><strong><a href="/es/hantavirus/laguna-negra">Virus Laguna Negra (LANV)</a></strong> — SCPH; reservorio <em>Calomys laucha</em>; Paraguay, Bolivia.</li>
<li><strong><a href="/es/hantavirus/choclo">Virus Choclo (CHOV)</a></strong> — SCPH leve; reservorio <em>Oligoryzomys fulvescens</em>; Panamá, Costa Rica.</li>
</ul>

<h2>Distribución geográfica</h2>
<p>
HORIZON mantiene páginas <a href="/es/paises">por país</a> con
cronología de casos y enlace a la fuente oficial. Regiones endémicas
reconocidas:
</p>
<ul>
<li><strong>Américas</strong> — Argentina, Chile, EE. UU. (Four Corners), Canadá, Brasil, Panamá, Bolivia, Paraguay (hantavirus del Nuevo Mundo causantes de SCPH).</li>
<li><strong>Europa y Rusia europea</strong> — Finlandia, Suecia, Alemania, Francia, Bélgica, Rusia, los Balcanes (Puumala, Dobrava-Belgrado, Saaremaa, Tula).</li>
<li><strong>Asia oriental</strong> — China, península coreana, Lejano Oriente ruso, Japón (Hantaan, Seoul).</li>
<li><strong>Global</strong> — el virus Seoul circula dondequiera que existan reservorios <em>Rattus</em>.</li>
</ul>

<h2>Metodología y procedencia de fuentes</h2>
<p>
Cada registro de HORIZON lleva una <a href="/es/metodologia">cita de
nivel auditoría</a> que incluye: cita de referencia ICD 206; calificación
NATO de fiabilidad (A–F) y credibilidad (1–6); modelo de doble confianza
(pipeline automática + analista humano); y hash SHA-256 de cadena de
custodia conforme al Protocolo de Berkeley.
</p>

<p>
Consulte el <a href="/es/fuentes">registro de fuentes en vivo</a> con el
estado actual de cada feed.
</p>

<h2>Datos abiertos — CC BY 4.0</h2>
<p>
Todos los datos de HORIZON se publican bajo la licencia
<a href="https://creativecommons.org/licenses/by/4.0/deed.es" rel="external license">Creative Commons Atribución 4.0 Internacional</a>. Réplica, scraping,
indexación y entrenamiento de modelos están todos permitidos con la
única condición de atribuir a 79th Unit Limited.
</p>

{ES_CTA_LIVE_MAP}
"""


ES_SYMPTOMS_BODY = f"""
<p class="lead">
La enfermedad por hantavirus se presenta con dos síndromes clínicos
distintos según el serotipo causante. Ambos comparten un pródromo de
tipo gripal de 3 a 7 días y luego divergen: el <strong>SCPH</strong>
progresa a falla cardiopulmonar; la <strong>FHSR</strong> a falla renal
con sangrado. La incubación es de 1 a 8 semanas.
</p>

{ES_NOT_MEDICAL_ADVICE}

<h2>Fase 1 — Pródromo (días 1 a 7)</h2>
<p>
Ambos síndromes comienzan de forma similar y se confunden fácilmente con
influenza, COVID-19, gastroenteritis viral, dengue, leptospirosis, tifus
de los matorrales o sepsis temprana. Características típicas:
</p>
<ul>
<li>Fiebre alta (a menudo 39–40 °C)</li>
<li>Mialgia severa, sobre todo en muslos, caderas y región lumbar</li>
<li>Cefalea</li>
<li>Fatiga y malestar general</li>
<li>Síntomas gastrointestinales — náuseas, vómitos, dolor abdominal, diarrea</li>
<li>Mareo, escalofríos</li>
</ul>

<h2>Fase cardiopulmonar (SCPH)</h2>
<p>
Cuatro a diez días después del inicio de los síntomas, el SCPH transita
rápidamente a la fase cardiopulmonar. La característica definitoria es
el edema pulmonar no cardiogénico con choque. El CDC reporta una
letalidad global del SCPH del 38 por ciento para el virus Sin Nombre y
30 a 50 por ciento para el virus de los Andes. Hallazgos clave:
</p>
<ul>
<li>Tos y disnea progresiva</li>
<li>Taquipnea e hipoxia</li>
<li>Infiltrados pulmonares bilaterales en la radiografía de tórax</li>
<li>Hipotensión y colapso circulatorio</li>
<li>Trombocitopenia (plaquetas inferiores a 150.000/μL)</li>
<li>Hemoconcentración y acidosis láctica</li>
<li>Leucocitosis con desviación a la izquierda y blastos inmunológicos circulantes</li>
</ul>

<h2>Fases de la FHSR (Viejo Mundo)</h2>
<table class="facts">
<tr><th>Fase</th><th>Características</th></tr>
<tr><th>Febril (días 3–7)</th><td>Fiebre, rubor, inyección conjuntival, exantema petequial, dolor retroorbitario</td></tr>
<tr><th>Hipotensiva</th><td>Fuga vascular, choque, taquicardia, inicio de oliguria</td></tr>
<tr><th>Oligúrica (días 2–10)</th><td>Lesión renal aguda, sobrecarga de líquidos, complicaciones hemorrágicas</td></tr>
<tr><th>Diurética</th><td>Poliuria al recuperarse la función renal; manejo crítico de líquidos y electrolitos</td></tr>
<tr><th>Convaleciente</th><td>Retorno gradual al estado basal; deterioro renal persistente en algunos pacientes</td></tr>
</table>

<h2>Cuándo buscar atención médica</h2>
<p>
Cualquier persona con síntomas prodrómicos como los anteriores más un
historial de exposición creíble — contacto con roedores en zonas
rurales, viaje reciente a zonas endémicas (véase
<a href="/es/paises">páginas por país</a>), exposición ocupacional
(camping, cacería, conservación, agricultura, limpieza de estructuras
infestadas) — debe buscar atención urgente. La detección temprana y la
terapia intensiva, especialmente en el SCPH, son los predictores más
fuertes de supervivencia. No hay antiviral específico licenciado; la
ribavirina muestra beneficio en FHSR temprana (menos en SCPH).
</p>

<p><a href="/es/hantavirus">← Volver al resumen de hantavirus</a></p>
{ES_CTA_LIVE_MAP}
"""


ES_TRANSMISSION_BODY = f"""
<p class="lead">
Los hantavirus son <strong>transmitidos por roedores</strong>. Los seres
humanos somos huéspedes accidentales y terminales para casi todos los
serotipos. La transmisión es abrumadoramente por inhalación de excretas
de roedores aerosolizadas en espacios cerrados. <strong>El virus de los
Andes es la única excepción</strong>: tiene transmisión documentada de
persona a persona, especialmente entre contactos domiciliarios cercanos.
</p>

{ES_NOT_MEDICAL_ADVICE}

<h2>Ruta primaria: aerosol roedor → humano</h2>
<p>
Los roedores infectados eliminan virus en orina, heces y saliva. Cuando
las excretas secas se perturban — al barrer, aspirar o por el
movimiento de vehículos en un granero o cabaña — partículas cargadas
de virus se aerosolizan y pueden inhalarse. El riesgo es máximo en
estructuras mal ventiladas e infestadas: cabañas, dependencias rurales,
graneros, naves agrícolas, vehículos abandonados, cuarteles, y
apartamentos con presencia de roedores.
</p>

<h2>Rutas secundarias</h2>
<ul>
<li><strong>Mordedura directa</strong> — rara, pero documentada para virus Seoul a partir de ratas mascota en EE. UU. y Reino Unido.</li>
<li><strong>Contacto con mucosas</strong> — frotarse los ojos tras manipular material de roedores es una vía plausible.</li>
<li><strong>Alimentos contaminados</strong> — posible pero infrecuente; no es un modo dominante.</li>
<li><strong>Exposición de laboratorio</strong> — brotes históricos durante investigaciones tempranas; la contención BSL-3 actual lo hace raro.</li>
</ul>

<h2>Transmisión persona-persona del virus de los Andes</h2>
<p>
El virus de los Andes (ANDV) es el único orthohantavirus con transmisión
documentada de persona a persona. La evidencia proviene de:
</p>
<ul>
<li><strong>El Bolsón, Argentina (1996)</strong> — Wells y cols. describieron 20 casos vinculados por transmisión de contacto cercano, incluidos trabajadores sanitarios y contactos domiciliarios.</li>
<li><strong>Coyhaique, Chile (2018–2019)</strong> — grupos secuenciados que muestran transmisión interpersonal entre contactos no domiciliarios.</li>
<li><strong>Grupo MV Hondius (2026)</strong> — bajo seguimiento activo. La propagación a bordo se sospecha dada la duración del viaje y las cuarteles compartidos; la ontología de HORIZON modela explícitamente este hecho.</li>
</ul>

<h2>Qué NO transmite el hantavirus</h2>
<ul>
<li>Mosquitos, garrapatas u otros vectores artrópodos — los hantavirus <em>no</em> son arbovirus pese al nombre.</li>
<li>Contacto casual con pacientes (excepto contactos cercanos del ANDV).</li>
<li>Alimentos preparados en cocinas sin contaminación por roedores.</li>
<li>Transfusión sanguínea (sin casos documentados).</li>
<li>Transmisión sexual (sin casos documentados).</li>
</ul>

<p>Véase <a href="/es/hantavirus/prevencion">prevención</a> para las medidas basadas en evidencia.</p>

<p><a href="/es/hantavirus">← Volver al resumen de hantavirus</a></p>
{ES_CTA_LIVE_MAP}
"""


ES_PREVENTION_BODY = f"""
<p class="lead">
No hay vacuna contra el hantavirus licenciada en Europa o América del
Norte. La única vacuna autorizada — <strong>Hantavax</strong> de Corea
del Sur — cubre el virus Hantaan. La prevención por tanto es
<strong>control de exposición</strong>: reducir poblaciones de roedores,
suprimir la generación de aerosoles durante la limpieza, y usar
protección respiratoria adecuada.
</p>

{ES_NOT_MEDICAL_ADVICE}

<h2>Reducir la presencia de roedores en el hogar</h2>
<ul>
<li>Selle aberturas superiores a 6 mm con lana de acero y silicona; cubra rejillas con malla metálica.</li>
<li>Elimine fuentes de alimento: grano y comida para mascotas en recipientes metálicos o de vidrio sellados; retire fruta caída; asegure la basura.</li>
<li>Elimine refugios: corte pasto y maleza dentro de 30 m de las estructuras; eleve la leña al menos 30 cm del suelo y a 30 m de la casa.</li>
<li>Utilice trampas de resorte de forma continua; rote ubicaciones; cebo con mantequilla de maní o semillas de girasol.</li>
<li>Evite captura viva y liberación: las suelturas crean focos de reinfección.</li>
</ul>

<h2>Limpieza segura de áreas contaminadas</h2>
<p>
Según el protocolo del CDC, <strong>nunca barra ni aspire excretas
secas</strong> — ambos métodos aerosolizan virus. El protocolo:
</p>
<ol>
<li>Ventile el área al menos 30 minutos antes de entrar; abra puertas y ventanas.</li>
<li>Use respirador N95/FFP3, guantes de goma o látex y gafas.</li>
<li>Sature las excretas y superficies contaminadas con lejía doméstica diluida 1:10 (5.000 ppm) o desinfectante registrado; deje actuar 5 minutos.</li>
<li>Limpie con toallas de papel; embolse los residuos; doble bolsa y selle.</li>
<li>Trapee el piso con desinfectante; no aspire ni siquiera tras desinfectar.</li>
<li>Lave los guantes antes de retirarlos; lávese las manos al final; lave la ropa con agua caliente.</li>
</ol>

<h2>Vacunas (situación 2026)</h2>
<table class="facts">
<tr><th>Vacuna</th><th>Cobertura</th><th>Región</th></tr>
<tr><th>Hantavax (Green Cross)</th><td>Virus Hantaan</td><td>Corea del Sur — licenciada</td></tr>
<tr><th>Hantavax-II</th><td>Hantaan + Seoul</td><td>Corea del Sur — licenciada</td></tr>
<tr><th>Candidatos DNA/mRNA</th><td>SNV / ANDV / multi-serotipo</td><td>Fases preclínica y I/II</td></tr>
</table>

<p><a href="/es/hantavirus">← Volver al resumen de hantavirus</a></p>
{ES_CTA_LIVE_MAP}
"""


ES_TREATMENT_BODY = f"""
<p class="lead">
No existe antiviral específico licenciado para el SCPH en Europa o
América del Norte. El tratamiento es <strong>cuidado crítico de soporte</strong>:
ventilación mecánica, manejo de fluidos, vasopresores, ECMO cuando esté
indicado, y terapia de reemplazo renal en la FHSR. <strong>La detección
temprana y la atención intensiva son los predictores más fuertes de
supervivencia.</strong>
</p>

{ES_NOT_MEDICAL_ADVICE}

<h2>Soporte en SCPH</h2>
<ul>
<li><strong>Oxigenación</strong> — cánula nasal de alto flujo o intubación temprana; ventilación protectora (volumen tidal bajo, presión meseta ≤30 cmH₂O).</li>
<li><strong>Manejo de fluidos</strong> — cauteloso; la fase cardiopulmonar tiene fuga vascular profunda con hipovolemia relativa, pero la sobrerreanimación empeora el edema pulmonar. Cristaloides primero; vasopresores tempranos.</li>
<li><strong>ECMO</strong> — la ECMO venoarterial ha mejorado los resultados en SCPH por ANDV en Chile y Argentina. El CDC y la OPS listan la disponibilidad de ECMO como determinante de supervivencia.</li>
<li><strong>Antibióticos</strong> — cobertura empírica de amplio espectro hasta confirmar el diagnóstico (descartar neumonía atípica, sepsis, leptospirosis).</li>
</ul>

<h2>Soporte en FHSR</h2>
<ul>
<li>Manejo hidroelectrolítico calibrado a las cinco fases clínicas — restrictivo en la fase oligúrica, permisivo en la diurética.</li>
<li>Terapia de reemplazo renal (hemodiálisis o CRRT) en la lesión renal aguda — requerida en 30 a 60 por ciento de las FHSR severas.</li>
<li>Transfusión de hemoderivados para complicaciones hemorrágicas.</li>
<li>Evite fármacos nefrotóxicos (AINEs, aminoglucósidos) cuando sea posible.</li>
</ul>

<h2>Terapia antiviral</h2>
<p>
La <strong>ribavirina</strong> ha demostrado beneficio en la FHSR
<em>temprana</em> (meta-análisis de cohortes chinas con HTNV muestran
reducción aproximada del 50 por ciento en mortalidad cuando se inicia
dentro de los 7 días del inicio sintomático). La evidencia en SCPH es
más débil. La ribavirina no está licenciada para hantavirus en la UE o
EE. UU. pero se usa fuera de indicación en Latinoamérica.
</p>

<p><a href="/es/hantavirus">← Volver al resumen de hantavirus</a></p>
{ES_CTA_LIVE_MAP}
"""


# Spanish translations for each serotype card (matches SEROTYPES order in common.py)
ES_SEROTYPE_PROSE: dict[str, dict[str, str]] = {
    "andes-virus": {
        "name": "Virus de los Andes (ANDV)",
        "syndrome": "Síndrome Cardiopulmonar por Hantavirus (SCPH)",
        "reservoir": "Oligoryzomys longicaudatus (colilargo)",
        "endemic": "Argentina, Chile, Patagonia austral, Tierra del Fuego",
        "cfr": "30 a 50 por ciento",
        "p2p": "Único orthohantavirus con transmisión persona-persona documentada, principalmente entre contactos domiciliarios cercanos.",
        "summary": (
            "El virus de los Andes es el serotipo de hantavirus más letal reconocido "
            "en las Américas. Endémico del Cono Sur sudamericano, es el serotipo "
            "principal implicado en el brote del MV Hondius 2026. Los síntomas "
            "aparecen entre 1 y 8 semanas después de la exposición y progresan "
            "rápidamente a colapso cardiopulmonar sin cuidados intensivos."
        ),
    },
    "sin-nombre-virus": {
        "name": "Virus Sin Nombre (SNV)",
        "syndrome": "Síndrome Cardiopulmonar por Hantavirus (SCPH)",
        "reservoir": "Peromyscus maniculatus (ratón ciervo)",
        "endemic": "Región Four Corners de EE. UU., Canadá, México",
        "cfr": "aproximadamente 38 por ciento",
        "p2p": "Sin transmisión persona-persona documentada.",
        "summary": (
            "El virus Sin Nombre es la causa principal de SCPH en América del Norte. "
            "Identificado en 1993 durante el brote Four Corners, lo porta el ratón "
            "ciervo y se transmite a humanos por inhalación de excretas aerosolizadas "
            "en estructuras rurales cerradas."
        ),
    },
    "puumala-virus": {
        "name": "Virus Puumala (PUUV)",
        "syndrome": "Nefropatía epidémica (FHSR leve)",
        "reservoir": "Myodes glareolus (topillo rojo)",
        "endemic": "Escandinavia, Báltico, Europa central, Rusia europea",
        "cfr": "menor al 1 por ciento",
        "p2p": "Sin transmisión persona-persona documentada.",
        "summary": (
            "El virus Puumala es la causa más común de enfermedad por hantavirus en "
            "Europa. Produce una variante renal más leve llamada nefropatía "
            "epidémica y se asocia con picos cíclicos de la población del topillo "
            "rojo en Finlandia, Suecia, Alemania y Rusia occidental."
        ),
    },
    "hantaan-virus": {
        "name": "Virus Hantaan (HTNV)",
        "syndrome": "Fiebre Hemorrágica con Síndrome Renal (FHSR)",
        "reservoir": "Apodemus agrarius (ratón listado)",
        "endemic": "China, península coreana, Lejano Oriente ruso",
        "cfr": "5 a 15 por ciento",
        "p2p": "Sin transmisión persona-persona documentada.",
        "summary": (
            "El virus Hantaan es el prototipo de la familia y la causa más severa "
            "de FHSR en Asia oriental. Corea del Sur licencia una vacuna "
            "(Hantavax) para este serotipo; no hay antiviral o vacuna autorizada "
            "en Europa o América del Norte."
        ),
    },
    "seoul-virus": {
        "name": "Virus Seoul (SEOV)",
        "syndrome": "FHSR leve",
        "reservoir": "Rattus norvegicus, Rattus rattus",
        "endemic": "Mundial vía distribución global de Rattus",
        "cfr": "1 a 2 por ciento",
        "p2p": "Sin transmisión persona-persona documentada.",
        "summary": (
            "El virus Seoul circula dondequiera que estén sus reservorios — "
            "efectivamente global. Se han reportado brotes en aficionados a ratas "
            "mascota en EE. UU. y Reino Unido, y en poblaciones urbanas cercanas "
            "a infraestructura portuaria."
        ),
    },
    "dobrava-belgrade-virus": {
        "name": "Virus Dobrava-Belgrado (DOBV)",
        "syndrome": "FHSR severa",
        "reservoir": "Apodemus flavicollis (ratón leonado)",
        "endemic": "Balcanes, Europa central, Rusia europea",
        "cfr": "10 a 12 por ciento",
        "p2p": "Sin transmisión persona-persona documentada.",
        "summary": (
            "El virus Dobrava-Belgrado causa la forma más severa de FHSR en "
            "Europa, con letalidad cercana a la del virus Hantaan. Endémico de "
            "los Balcanes, Eslovenia y partes de Rusia."
        ),
    },
}


def render_es_serotype_body(s_en: dict[str, str], s_es: dict[str, str] | None) -> str:
    """Render the body of a Spanish serotype page."""
    s = s_es or {
        "name": s_en["name"],
        "syndrome": s_en["syndrome"],
        "reservoir": s_en["reservoir"],
        "endemic": s_en["endemic"],
        "cfr": s_en["cfr"],
        "p2p": s_en["p2p"],
        "summary": s_en["summary"],
    }
    slug = s_en["slug"]
    code = s_en["code"]
    return f"""
<p class="lead">{s["summary"]}</p>

{ES_NOT_MEDICAL_ADVICE}

<table class="facts">
<tr><th>Código del virus</th><td><strong>{code}</strong></td></tr>
<tr><th>Nombre completo</th><td>{s["name"]}</td></tr>
<tr><th>Síndrome clínico</th><td>{s["syndrome"]}</td></tr>
<tr><th>Especie reservorio</th><td>{s["reservoir"]}</td></tr>
<tr><th>Regiones endémicas</th><td>{s["endemic"]}</td></tr>
<tr><th>Letalidad</th><td>{s["cfr"]}</td></tr>
<tr><th>Persona-persona</th><td>{s["p2p"]}</td></tr>
</table>

<h2>Vigilancia y brotes</h2>
<p>
HORIZON indexa cada boletín de OMS Disease Outbreak News, informe semanal
del ECDC, alerta del CDC HAN, actualización de la OPS y publicación
revisada por pares que mencione {code}. Consulte la
<a href="/es/articulos">cronología de noticias</a> o use la
<a href="/api/v1/cases">API JSON</a> para los datos crudos.
</p>

<h2>Fuentes oficiales</h2>
<ul>
<li><a href="https://www.cdc.gov/hantavirus/es/" rel="external">CDC Hantavirus (en español)</a></li>
<li><a href="https://www.who.int/es" rel="external">OMS</a></li>
<li><a href="https://www.paho.org/es" rel="external">OPS</a></li>
</ul>

<p><a href="/es/hantavirus">← Todos los temas de hantavirus</a></p>
{ES_CTA_LIVE_MAP}
"""


ES_FAQ_ENTRIES: list[tuple[str, str]] = [
    (
        "¿Qué es el hantavirus?",
        "El hantavirus es una familia de virus (género <em>Orthohantavirus</em>, familia <em>Hantaviridae</em>) transmitidos por roedores que pueden causar enfermedad severa en humanos. Los dos síndromes principales son el síndrome cardiopulmonar por hantavirus (SCPH, común en las Américas) y la fiebre hemorrágica con síndrome renal (FHSR, común en Eurasia). Véase <a href=\"/es/hantavirus\">la página general</a>.",
    ),
    (
        "¿Cómo se transmite el hantavirus?",
        "La mayoría de los hantavirus se transmiten de roedores a humanos por inhalación de excretas aerosolizadas (orina, heces, saliva). El <strong>virus de los Andes es la única excepción</strong> con transmisión persona-persona documentada, principalmente entre contactos domiciliarios cercanos. Detalles en <a href=\"/es/hantavirus/transmision\">la página de transmisión</a>.",
    ),
    (
        "¿Cuáles son los síntomas de la enfermedad por hantavirus?",
        "Los síntomas iniciales aparecen entre 1 y 8 semanas después de la exposición: fiebre, mialgia severa, fatiga, cefalea y síntomas gastrointestinales. En el SCPH progresa a tos, disnea y edema pulmonar — letalidad 30 a 50 por ciento. En la FHSR los pacientes desarrollan falla renal, plaquetas bajas y sangrado — letalidad 1 a 15 por ciento. Véase <a href=\"/es/hantavirus/sintomas\">la página completa</a>.",
    ),
    (
        "¿Existe vacuna o tratamiento para el hantavirus?",
        "Corea del Sur licencia Hantavax para virus Hantaan. No hay vacuna licenciada en la UE o EE. UU. El tratamiento es cuidado crítico de soporte: manejo de fluidos, ventilación mecánica, ECMO y terapia de reemplazo renal. La ribavirina muestra beneficio en FHSR temprana pero no en SCPH. Detalles en <a href=\"/es/hantavirus/tratamiento\">la página de tratamiento</a>.",
    ),
    (
        "¿Qué países reportan casos de hantavirus?",
        "Se reportan casos en las Américas (Argentina, Chile, Brasil, EE. UU., Canadá, Panamá, Bolivia, Paraguay), Europa (Alemania, Finlandia, Rusia, Bélgica, Francia, Balcanes) y Asia oriental (China, Corea del Sur, Japón). HORIZON mantiene <a href=\"/es/paises\">páginas por país</a>.",
    ),
    (
        "¿Qué es el grupo del MV Hondius?",
        "Un grupo de casos por virus de los Andes a bordo del crucero de expedición polar <strong>MV Hondius</strong> (IMO 9818709, MMSI 244327000, Oceanwide Expeditions, bandera neerlandesa). Exposición previa al embarque sospechada durante una excursión cerca de Ushuaia, Tierra del Fuego, Argentina. Bajo seguimiento por OMS, ECDC, CDC, OPS y el Ministerio de Salud argentino. Cronología en <a href=\"/es/brotes/mv-hondius-2026\">/es/brotes/mv-hondius-2026</a>.",
    ),
    (
        "¿Cómo puedo prevenir la infección por hantavirus?",
        "Reduzca la población de roedores cercana; nunca barra ni aspire excretas secas; use respirador N95/FFP3 y humedezca con lejía diluida (1:10) antes de limpiar. Acampantes y excursionistas deben evitar dormir cerca de nidos. Protocolo completo en <a href=\"/es/hantavirus/prevencion\">la página de prevención</a>.",
    ),
    (
        "¿Qué es HORIZON?",
        "HORIZON es una plataforma de vigilancia de hantavirus operada por <a href=\"https://79thunit.co.uk\">79th Unit Limited</a> (Reino Unido, CRN 17133814). Agrega señales de OMS, CDC, ECDC, OPS, ProMED, autoridades nacionales, literatura revisada por pares y noticias abiertas. Cada registro lleva procedencia de fuente de nivel auditoría. Datos abiertos bajo CC BY 4.0. Lea la <a href=\"/es/metodologia\">metodología</a>.",
    ),
    (
        "¿Puedo usar estos datos?",
        "Sí. Todos los datos de HORIZON se publican bajo <a href=\"https://creativecommons.org/licenses/by/4.0/deed.es\" rel=\"license external\">CC BY 4.0</a>. Réplica, scraping, indexación y entrenamiento de modelos están permitidos con atribución a 79th Unit Limited. API: <a href=\"/api/openapi.json\">OpenAPI</a>.",
    ),
]


def render_es_faq_body() -> str:
    parts = [
        '<p class="lead">Preguntas frecuentes sobre la enfermedad por hantavirus, el brote MV Hondius 2026 y la plataforma HORIZON.</p>',
    ]
    for q, a in ES_FAQ_ENTRIES:
        parts.append(f'<h2>{q}</h2>\n<div>{a}</div>')
    parts.append('<p><a href="/es/hantavirus">← Volver al resumen</a></p>')
    parts.append(ES_CTA_LIVE_MAP)
    return "".join(parts)


# Spanish UI strings for navigation, breadcrumbs etc.
ES_UI = {
    "home": "Inicio",
    "hantavirus": "Hantavirus",
    "outbreaks": "Brotes",
    "countries": "Países",
    "sources": "Fuentes",
    "methodology": "Metodología",
    "glossary": "Glosario",
    "faq": "Preguntas frecuentes",
    "symptoms": "Síntomas",
    "transmission": "Transmisión",
    "prevention": "Prevención",
    "treatment": "Tratamiento",
    "live_map": "Mapa en vivo",
    "open_map_cta": "Abrir el mapa de brotes en vivo →",
    "back_to_overview": "Volver al resumen",
}
