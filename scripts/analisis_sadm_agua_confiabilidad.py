#!/usr/bin/env python3
"""Cruza avisos publicos de AyD/SADM (cortes, tandeos, baja presion; 2026) con las 167 colonias por NOMBRE (+ mismo municipio).
Sin red: los eventos estan curados a mano abajo (cada uno con URL y fecha, visto en pagina publica el 2026-10-02).
Salida: v2/data/sadm_agua_eventos_2026.csv, v2/data/sadm_agua_colonias_match.csv. No toca scores."""
import csv, re, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\[.*?\]|\(.*?\)", " ", s)
    s = re.sub(r"\b(ampliacion|ampl|col|colonia|sector(es)?|sec|1er|2do|3er|4to|5to|7|i|ii|iii|iv|residencial|fracc|fraccionamiento|de|del|la|las|los|el|y)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())
MVS_189 = "https://mvsnoticias.com/nuevo-leon/2026/7/18/hasta-189-colonias-de-nuevo-leon-se-quedan-sin-agua-738859.html"
GAR_TANDEO = ["https://mvsnoticias.com/nuevo-leon/2026/7/8/asi-sera-el-tandeo-de-agua-en-colonias-de-garcia-737791.html",
              "https://abcnoticias.mx/local/2026/7/7/garcia-mitigara-falta-de-agua-con-nuevos-tanques-tandeo-para-19-colonias-283642.html",
              "https://www.nmas.com.mx/nuevo-leon/sociedad/alternaran-suministro-de-agua-potable-en-garcia-que-dias-tendra-agua-mi-colonia/"]
# (id, fecha, tipo, url, municipio, [colonias listadas], nota)
EV = [
 ("E01","2026-07-07","TANDEO (calendario L-M-V) zona Capellanía",GAR_TANDEO[0],"García",
  ["Avance Popular","Bugambilias","Centro de García (parte alta)","Colinas del Río","La Cruz","Martín González","Miguel Hidalgo","Paseo de Capellanía","Riveras de Capellanía","José Páez"],
  "Anuncio AyD+municipio García; vigente hasta que terminen tanques (El Porvenir 2026-09-09: listos nov-2026)"),
 ("E02","2026-07-07","TANDEO (calendario M-J-S) zona Durazno",GAR_TANDEO[0],"García",
  ["Ampliación Los Nogales","Balcones de García","División del Norte","Fomerrey 192","Infonavit Los Nogales","Los Nogales","Martínez Domínguez","Mirador del Fraile","Punta Esmeralda","Villas del Mirador"],
  "Idem; ABC lista 'Ampliación Los Nogales El Polvorín' y 'Misión del Norte' en vez de 'División del Norte'"),
 ("E03","2026-07-18","Bombeo suspendido (falla CFE) Sistema Nueva Castilla: hasta 189 colonias",MVS_189,"García",
  ["Brisas Residencial","Las Brisas Residencial","Los Encinos Residencial","El Renacimiento","Hacienda el Renacimiento","Los Nogales","Infonavit Los Nogales","Paseo de las Minas","Miguel Hidalgo","Real de Capellanía","Villas del Álcali"],
  "Lista parcial relevante a nuestras 167 (la nota lista 117 colonias de García)"),
 ("E04","2026-07-18","Bombeo suspendido (falla CFE) Sistema Nueva Castilla: hasta 189 colonias",MVS_189,"General Escobedo",
  ["Alianza Real I y II","Fernando Amilpa","Hacienda San Miguel","Privadas de Camino Real","Portal de San Francisco","Praderas de San Francisco","Emiliano Zapata","Nueva Castilla","San Miguel del Parque","Nuevo León Estado de Progreso"],
  "La nota pone 'N.L. Edo. de Progreso' bajo El Carmen; nuestra colonia está en Escobedo (revisar)"),
 ("E05","2026-03-16","Baja presión/falta temporal (viento→CFE→bombeo; tanques bajos ~8 h)","https://mvsnoticias.com/nuevo-leon/2026/3/16/colonias-sin-agua-en-monterrey-la-zona-metropolitana-hoy-16-de-marzo-del-2026-726242.html","García",
  ["Ampliación Los Nogales (El Polvorín)","Balcones de García","Fomerrey 192, Los Nogales","Miguel Hidalgo","Nuevo Amanecer","Villas del Mirador"],"Aviso AyD vía MVS"),
 ("E06","2026-03-16","Baja presión/falta temporal (viento→CFE→bombeo; tanques bajos ~8 h)","https://mvsnoticias.com/nuevo-leon/2026/3/16/colonias-sin-agua-en-monterrey-la-zona-metropolitana-hoy-16-de-marzo-del-2026-726242.html","Santa Catarina",
  ["Hacienda Santa Catarina","Miguel Hidalgo","Puerta del Sol","Lázaro Cárdenas","Zimix","Jardines de Santa Catarina","Centro"],"Aviso AyD vía MVS (41 sectores en la lista)"),
 ("E07","2026-03-16","Reparación tubería general (corte)","https://mvsnoticias.com/nuevo-leon/2026/3/16/colonias-sin-agua-en-monterrey-la-zona-metropolitana-hoy-16-de-marzo-del-2026-726242.html","General Escobedo",["Ampl. Eulalio Villarreal"],"Corte puntual ~horas"),
 ("E08","2026-03-16","Reparación tubería general (corte)","https://mvsnoticias.com/nuevo-leon/2026/3/16/colonias-sin-agua-en-monterrey-la-zona-metropolitana-hoy-16-de-marzo-del-2026-726242.html","Monterrey",
  ["Santa Fe","Fresnos","Del Vidrio","Parque Regiomontano","Escamilla","Industrias del Hierro","Independencia"],"Corte puntual ~horas"),
 ("E09","2026-03-09","Reparación tubería general (corte)","https://mvsnoticias.com/nuevo-leon/2026/3/9/colonias-sin-agua-hoy-de-marzo-en-juarez-monterrey-garcia-escobedo-apodaca-santa-catarina-725501.html","Santa Catarina",["La Fama 1"],"Corte puntual ~horas"),
 ("E10","2026-03-09","Reparación tubería general (corte)","https://mvsnoticias.com/nuevo-leon/2026/3/9/colonias-sin-agua-hoy-de-marzo-en-juarez-monterrey-garcia-escobedo-apodaca-santa-catarina-725501.html","Monterrey",["Villa Alegre","Valle de Santa Lucía","1 Mayo","Cantú","Reforma"],"Corte puntual ~horas"),
 ("E11","2026-04-17","Cambio de medidores/válvulas (corte)","https://mvsnoticias.com/nuevo-leon/2026/4/17/colonias-sin-agua-hoy-en-monterrey-santa-catarina-apodaca-garcia-por-trabajos-de-ayd-729565.html","General Escobedo",["Villas de San Francisco"],"Visto en extracto de búsqueda de la nota; corte ~horas"),
 ("E12","2026-04-17","Cambio de medidores/válvulas (corte)","https://mvsnoticias.com/nuevo-leon/2026/4/17/colonias-sin-agua-hoy-en-monterrey-santa-catarina-apodaca-garcia-por-trabajos-de-ayd-729565.html","Apodaca",["Nueva Democracia","Paraje San José Los Ríos"],"Visto en extracto; corte ~horas"),
 ("E13","2026-05-09","Reparación tubería general (corte)","https://abcnoticias.mx/local/2026/5/9/cortes-de-agua-en-nl-afecta-varias-colonias-hoy-sabado-de-mayo-277991.html","Juárez",["Las Quintas","Praderas del Oriente","Los Ébanos","La Escondida"],"Cita cuenta X @ayd_monterrey; hasta 20:00 h"),
 ("E14","2026-05-09","Reparación tubería general (corte)","https://abcnoticias.mx/local/2026/5/9/cortes-de-agua-en-nl-afecta-varias-colonias-hoy-sabado-de-mayo-277991.html","Monterrey",["Colón","Miguel Nieto"],"hasta 17:00 h"),
 ("E15","2026-07-09","Corte programado 14 h (sustitución 31 m de tubería)","https://www.telediario.mx/comunidad/cortes-de-agua-escobedo-9-de-julio-2026-lista-colonias-afectadas","General Escobedo",
  ["Almara","Bosques de Quebec","Cantera","Centro","Don Lalo","Eucaliptos","Flores Magón","Jardines de Escobedo","Las Quintas","Las Palomas","Los Olivos","Monterreal","Privadas Diamante","Privadas San Jorge","Reden","Umara","Villa Alta"],"Aviso AyD vía Telediario/El Porvenir 2026-07-08"),
 ("E16","2026-09-02","Corte programado ~12 h (tubería 24\" límite Escobedo)","https://mvsnoticias.com/nuevo-leon/2026/9/2/mas-de-50-colonias-se-quedaran-sin-agua-en-apodaca-hoy-2-de-septiembre-744350.html","Apodaca",
  ["Los Fresnos","Los Amarantos","Jardines de Santa Rosa","Capellanía","Arboledas de Santa Rosa","Industrial Apodaca"],"Lista N+ de 54 colonias (aquí solo las con posible match)"),
 ("E17","2026-08-10","Falla eléctrica: bombeo Pozos Buenos Aires suspendido, >100 colonias (SIN lista)","https://abcnoticias.mx/local/2026/8/10/anuncian-cortes-de-agua-en-mas-de-100-colonias-de-santa-catarina-garcia-286547.html","Santa Catarina",[],
  "Sin lista de colonias; 2026-08-11 Quadratin: afectaciones persisten en 'zonas altas' de Santa Catarina y sur de García"),
]
# colonias de las 167 que pueden entrar por coincidencia de nombre en el municipio
cols = list(csv.DictReader(open(ROOT/"v2/data/colonias_v3.csv", encoding="utf-8")))
MUN_ALIAS = {"General Escobedo":"General Escobedo"}
def match(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb: return None
    if na == nb: return "exacto"
    if (na in nb or nb in na) and min(len(na), len(nb)) >= 6: return "parcial"
    return None
out_ev = []
with open(ROOT/"v2/data/sadm_agua_eventos_2026.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["id","fecha","tipo","url","municipio","n_colonias_extractadas","colonias_extractadas","nota"])
    for e in EV: w.writerow([e[0],e[1],e[2],e[3],e[4],len(e[5]),"; ".join(e[5]),e[6]])
hits = {}
# falsos positivos revisados a mano (coincidencia de subcadena sin ser la misma colonia) -> se descartan
EXCL = {("San Miguel Residencial","E04"), ("Los Nogales","E05"), ("Ampl Los Nogales ( El Polvorin )","E03")}
# match exacto tras normalizar pero con sector distinto -> degradar a parcial
DOWN = {("Villas de San Francisco 2Do Sector","E11")}
for e in EV:
    for c in cols:
        if c["municipio"] != e[4]: continue
        for nm in e[5]:
            m = match(c["colonia"], nm)
            if (c["colonia"], e[0]) in EXCL: continue
            if (c["colonia"], e[0]) in DOWN: m = "parcial"
            if m: hits.setdefault(c["cve_col"], []).append((e, nm, m))
# Zona azul (resto de Garcia: presion baja >18h) -> supuesto
for c in cols:
    if c["municipio"] == "García": hits.setdefault(c["cve_col"], []).append((("E18","2026-07-07","Zona azul García: suministro continuo pero baja presión >18:00",GAR_TANDEO[0],"García",[],""), "(resto de García)", "supuesto_zona"))
out = []
for c in cols:
    h = hits.get(c["cve_col"])
    if not h: continue
    tandeo = [x for x in h if x[0][0] in ("E01","E02")]
    ids = sorted({x[0][0] for x in h})
    exactos = [x for x in h if x[2] == "exacto"]
    if tandeo and any(x[2] == "exacto" for x in tandeo): nivel, ver = "ALTO (tandeo oficial)", "VERIFICADO (nombre exacto en lista de tandeo)"
    elif tandeo: nivel, ver = "ALTO (tandeo oficial)", "VERIFICADO nombre parcial; confirmar que es la misma colonia"
    elif exactos: nivel, ver = "MEDIO (corte/baja presión reportada)", "VERIFICADO nombre exacto; homonimia posible (confirmar polígono)"
    elif any(x[2] == "parcial" for x in h): nivel, ver = "MEDIO-BAJO", "SUPUESTO (nombre parcial)"
    else: nivel, ver = "BAJO (solo zona azul García)", "SUPUESTO (zona, no colonia)"
    out.append(dict(rank_base=c["rank_base"], cve_col=c["cve_col"], colonia=c["colonia"], municipio=c["municipio"], score_base=c["score_base"],
                    nivel=nivel, verificacion=ver, eventos=";".join(ids),
                    detalle=" | ".join(f"{x[0][1]} {x[0][2]} ← '{x[1]}' ({x[2]})" for x in h)[:600],
                    urls=" ".join(sorted({x[0][3] for x in h}))))
out.sort(key=lambda r: ({"A":0,"M":1,"B":2}[r["nivel"][0]], int(r["rank_base"])))
with open(ROOT/"v2/data/sadm_agua_colonias_match.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(len(out))
for r in out: print(r["nivel"][:5], r["rank_base"], r["colonia"], r["municipio"], r["eventos"], "|", r["detalle"][:140])
