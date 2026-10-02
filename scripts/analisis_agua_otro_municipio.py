#!/usr/bin/env python3
"""Cruza el corte AyD del 2026-03-05 (Guadalupe, Apodaca, San Nicolas; cambio de valvulas) y el corte Apodaca 2026-09-02 (lista completa N+) con las 167 colonias por NOMBRE + mismo municipio.
Sin red: listas transcritas de las paginas citadas (vistas 2026-10-02). Reusa la normalizacion de scripts/analisis_sadm_agua_confiabilidad.py (no la modifica).
Salida: v2/data/agua_otro_municipio_match.csv, v2/data/agua_otro_municipio_eventos.csv. No toca scores."""
import csv, re, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\[.*?\]|\(.*?\)", " ", s)
    s = re.sub(r"\b(ampliacion|ampl|col|colonia|sector(es)?|sec|1er|2do|3er|4to|5to|7|i|ii|iii|iv|residencial|fracc|fraccionamiento|de|del|la|las|los|el|y)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
U1 = "https://www.milenio.com/estados/anuncian-cortes-agua-apodaca-guadalupe-san-nicolas-colonias-afectadas"
U1b = "https://www.nmas.com.mx/nuevo-leon/sociedad/cuando-inician-cortes-agua-nuevo-leon-lista-200-colonias-afectadas-apodaca-guadalupe-san-nicolas/"
U2 = "https://www.nmas.com.mx/nuevo-leon/sociedad/corte-de-agua-apodaca-hoy-54-colonias-municipio-de-nuevo-leon-no-tendran-suministro/"
U3 = "https://mvsnoticias.com/nuevo-leon/2026/4/7/estas-son-las-colonias-sin-agua-hoy-de-abril-en-escobedo-guadalupe-santa-catarina-728538.html"
GDL = """20 de noviembre|Agua Nueva|Ángel Martínez Villarreal|Arboledas de Nueva Lindavista|Benito Juárez|Bosques del Oriente|Chula Vista|Fomerrey 7, 18 y 31|Fovissste Talaverna|Guadalupe Chávez|Hacienda Los Encinos|Infonavit La Joya|Insurgentes|Jardines de Nueva Lindavista|Jardines de San Miguel|Jardines del Río|La Amistad|La Esperanza|La Floresta|La Joya|La Victoria|Las Dalias|Los Almendros|Los Lermas|Los Olivos|Maya|Misión del Valle|Nuevo Milenio|Nuevo San Miguel|Nuevo San Rafael|Parque Industrial Kalos|Parque Industrial San Miguel|Parque Industrial San Rafael|Parques de Guadalupe|Paseo de San Miguel|Pedregal de Lindavista 1 al 5|Pedregal de Oriente|Privadas de Lindavista|Pro Vivienda Guadalupe|Puerta Oriente|Residencial Guadalupe|Residencial Las Quintas|Rincón de Linda Vista|Rincón del Oriente|San Antonio|San Rafael|San Sebastián|Siete Colinas|Solidaridad|Tacubaya|Tres Caminos|Tres Caminos Norte|Unidad Modelo|Unión Habitacional Española|Valle de San Antonio|Valle de San Miguel|Valle de San Rafael|Villa de San Antonio|Villa de San Sebastián|Villa Española|Villas del Río|Zertuche""".split("|")
APO = """Altabrisa 1|Altabrisa Premier|Altamura Residencial|Andalucía|Andana Residencial|Antigua Santa Rosa|Ara Crystal Lagoons|Arbado|Arboledas Del Mezquital|Arboledas Del Virrey|Aria Residencial|Balcones Del Mezquital|Bonaterra|Bosque De Agua|Bosque Real|Camino Al Ojo De Agua|Cantizales|Cerradas Ámbar Sector Oriente|Cerradas de Concordia|Cerradas De Santa Rosa|Cerradas Del Parque|Cerradas Del Parque Premier|Cerradas Magenta|Cerradas Providencia|Colonial Apodaca|Corinto Residencial|Cortijo Las Palmas|Ejido El Mezquital|El Manantial|El Mezquital|Estancias Valle De Plata|Francisco Elizondo|Garcia Mireles|Hacienda De Los Nogales|Hacienda Del Mezquital|Hacienda Los Encinos|Hacienda Los Pinos|Hacienda Santa Isabel|Insurgentes|Jardines De Apodaca|Jardines De Los Pinos|Kebana 1Er Sector|La Hacienda|La Morada|Las Américas|Las Praderas|Lombardía Residencial|Los Cantú|Los Encinos|Los Fresnos|Los Pinos|Magnolias|Metroplex|Misión De San José|Misión de los Ángeles|Molinos San Francisco|Monetta|Mujeres Ilustres|Nueva Democracia|Nuevo Amanecer|Nuevo Las Puentes Sectores 1 al 6|Nuevo Mezquital|Parque Industrial Apodaca|Parque Industrial Kuadrum|Paseo De Las Palmas Sectores 1 al 4|Paseo De Los Nogales|Paseo De Los Pinos|Planicies|Portal De Anáhuac|Praderas De Apodaca|Praderas De La Enramada|Prados De La Cieneguita|Prados De Los Pinos|Prados Del Virrey|Privada Los Olmos|Privalia Concordia|Radica|Residencial Hacienda Del Moro|Residencial La Enramada|Residencial Las Estancias|Residencial Las Palmas|Residencial Los Ébanos|Residencial Los Ébanos Norte|Residencial Los Robles|Residencial San Francisco|Rincón De La Moraleja|San Francisco|Santa Cecilia|Valle De Apodaca|Valle De Las Bugambilias|Valle De Las Palmas|Valle De Los Nogales|Valle De San Francisco|Valle Del Mezquital|Vellania Residencial|Villa De Las Puentes|Villas Premier""".split("|")
SN = """Alejandría|Albatierra Residencial|Ampliación Parques de Santo Domingo|Andalucía|Ángeles 1 al 8|Arboledas de San Cristóbal|Arboledas de Santo Domingo|Arboledas del Mezquital|Balneario Los Rodríguez|Bosques de Lindavista|Bosques de Lindavista Diamante|Blas Chumacero C.T.M.|Casa Blanca|Casa Blanca San Ángel|Cerradas Casa Blanca|Cerradas Casa Blanca Norte|Del Lago|El Refugio|Fomerrey 4, 30, 33, 34, 44 y 119|Fresnos del Lago|Hacienda de los Ángeles|Hacienda Los Morales|Hacienda Santa Fe|Hacienda Santo Domingo|Ignacio Ramírez|Industrial Los Parques|Jardines de Casa Blanca|Jardines del Mezquital|La Fe|La Talaverna|Las Américas|Los Arrecifes|Los Cipreses|Los Laureles|Los Morales|Los Naranjos|Los Pinos|Miguel Alemán|Misión de Casa Blanca|Nuevo Mezquital|Palmas Diamante|Parque La Talaverna|Parques de Santo Domingo|Portal de Anáhuac|Praderas de Santo Domingo|Privadas de Casa Blanca|Privadas del Parque|Residencial Cipreses|Residencial La Enramada|Residencial Los Morales|Residencial Los Pinos|Residencial Orión|Residencial Paseo de los Ángeles|Residencial San Cristóbal|Residencial Santo Domingo|Rincón de Casa Blanca|Rincón de los Ángeles|San Benito del Lago|Santo Domingo|Tacuba|Unidad La Enramada|Unidad Laboral|Urbi Quinta Montecarlo|Valle de Casa Blanca|Valle de las Flores|Valle de San Carlos|Valle de Santo Domingo|Vicente Guerrero|Villas de San Cristóbal|Villas de Santo Domingo""".split("|")
APO2 = """Amberes Residencial|Arbado|Arboledas De Santa Rosa|Balcones de Santa Rosa|Bosques de Santa Rosa|Capellanía|Cerradas de Rinconada|Cosmópolis|El Molino|Ex-Hacienda Santa Rosa|Ferroviario|Hacienda Las Yucas|Industrial Apodaca|Jardines de Las Palmas|Jardines de San Andrés|Jardines de Santa Rosa|Las Huertas|Los Amarantos|Los Fresnos|Los Lirios|Los Murales|Los Soles|Mirador del Topo|Misión Del Parque|Misión Fundadores|Muran Residencial|Paraje Santa Rosa|Paraje Santa Rosa Sur|Parque Industrial Eli-Can|Paseo de Apodaca|Paseo Santa Rosa|Portal de Santa Rosa|Prados de Santa Rosa|Privada Lumena|Privada Tiara|Privadas Borneo|Privadas de Santa Rosa|Privadas del Rey|Quinta Colonial|Real de San Andrés|Recova|Renaceres Residencial|Reserva de San Francisco|Residencial Los Lienzos|Rincón de Santa Rosa|Santa Alicia|Santa Elena|Santo Tomás|Sierra La Esperanza|Valle del Salduero|Valle de San Andrés|Ventura de Santa Rosa|Villas de Santa Rosa""".split("|")
EV = [("A01", "2026-03-05", "Corte programado 16:00 (5-mar) a 00:00 (6-mar): cambio de válvulas (N+: tres válvulas de 36 pulgadas) en Guadalupe", U1, "Guadalupe", GDL, "Milenio 2026-03-04 20:16; N+ confirma «226 colonias» en tres municipios: " + U1b),
      ("A02", "2026-03-05", "Idem A01", U1, "Apodaca", APO, "Mismo aviso (lista Apodaca)"),
      ("A03", "2026-03-05", "Idem A01", U1, "San Nicolás de los Garza", SN, "Mismo aviso (lista San Nicolás)"),
      ("A04", "2026-09-02", "Corte programado 16:00 (2-sep) a ~04:00 (3-sep): mantenimiento preventivo tubería 24\" límite Escobedo-Apodaca", U2, "Apodaca", APO2, "N+ titula «54 colonias»; transcribí 53 nombres de su lista (el texto repite «Cosmópolis» y trae un «Jardines» suelto); el doc previo (E16) sólo extrajo 6"),
      ("A05", "2026-04-07", "Reparación de tubería general (corte de horas; normalización estimada 14:00-17:00)", U3, "General Escobedo", ["Eulalio Villarreal Ayala", "Loma del Topo Chico", "Pedregal del Topo Chico", "Serranía"], "MVS 2026-04-07; también Santa Catarina (López Mateos) y Guadalupe (Camino Real), sin match en las 167"),
      ("A06", "2026-04-07", "Idem A05", U3, "Santa Catarina", ["López Mateos"], "MVS 2026-04-07"),
      ("A07", "2026-04-07", "Idem A05", U3, "Guadalupe", ["Camino Real"], "MVS 2026-04-07")]
cols = list(csv.DictReader(open(ROOT / "v2/data/colonias_v3.csv", encoding="utf-8")))
def match(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb: return None
    if na == nb: return "exacto"
    if (na in nb or nb in na) and min(len(na), len(nb)) >= 6: return "parcial"
    return None
with open(ROOT / "v2/data/agua_otro_municipio_eventos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["id", "fecha_evento", "tipo", "url", "municipio", "n_colonias_extractadas", "colonias_extractadas", "nota"])
    for e in EV: w.writerow([e[0], e[1], e[2], e[3], e[4], len(e[5]), "; ".join(e[5]), e[6]])
hits = {}
for e in EV:
    for c in cols:
        if c["municipio"] != e[4]: continue
        for nm in e[5]:
            m = match(c["colonia"], nm)
            if m: hits.setdefault(c["cve_col"], []).append((e, nm, m))
out = []
for c in cols:
    h = hits.get(c["cve_col"])
    if not h: continue
    ex = [x for x in h if x[2] == "exacto"]
    out.append(dict(rank_base=c["rank_base"], cve_col=c["cve_col"], colonia=c["colonia"], municipio=c["municipio"], score_base=c["score_base"],
                    nivel="MEDIO (corte puntual de horas)" if ex else "MEDIO-BAJO", verificacion=("VERIFICADO nombre exacto; homonimia posible (confirmar polígono)" if ex else "SUPUESTO (nombre parcial)"),
                    eventos=";".join(sorted({x[0][0] for x in h})), nombres_en_aviso=" | ".join(sorted({f"{x[1]} ({x[2]})" for x in h})),
                    fechas=";".join(sorted({x[0][1] for x in h})), urls=" ".join(sorted({x[0][3] for x in h}))))
out.sort(key=lambda r: ({"MEDIO (corte puntual de horas)": 0}.get(r["nivel"], 1), int(r["rank_base"])))
with open(ROOT / "v2/data/agua_otro_municipio_match.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(len(GDL), len(APO), len(SN), len(APO2), len(out))
for r in out: print(r["rank_base"], r["colonia"], "|", r["municipio"], "|", r["nivel"][:10], "|", r["eventos"], "|", r["nombres_en_aviso"])
