#!/usr/bin/env python3
"""(i) Sensibilidad score_base con termino de densidad de viviendas y (ii) banda de confianza Monte-Carlo por colonia.
MODELO, no pronostico. Solo archivos locales (sin red). NO modifica colonias_v3.csv ni nada existente.
Salidas nuevas: v2/data/colonias_v3_sensibilidad_densidad.csv, v2/data/colonias_v3_banda_confianza.csv, /workspace/downloads/banda_confianza_stats.json
Reproducible: semilla fija. python3 scripts/banda_confianza_densidad.py"""
import json, os
import numpy as np, pandas as pd
from scipy.stats import spearmanr
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = "/home/box/geo/inegi_purificador/datos"
SEED, NDRAW = 20261002, 4000
W_D, W_A, W_C = .40, .30, .30
v = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv")
c = pd.read_csv(f"{GEO}/colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv")[["cve_col", "viv_hab_censo_est"]]
gp = {f["properties"]["cve_col"]: f["properties"] for f in json.load(open(f"{GEO}/colonias167_conapo_geom.geojson"))["features"]}
cg = {f["properties"]["cve_col"]: f["properties"] for f in json.load(open(f"{ROOT}/data/colonias.geojson"))["features"]}
d = v.merge(c, on="cve_col", validate="1:1")
d["area_km2"] = d.cve_col.map(lambda k: float(gp[k]["area_km2"]))
d["pob_exact"] = d.cve_col.map(lambda k: float(cg[k]["pob_conapo"]))
d["viv_est"] = d.pob_exact / 3.6
d["viv_ha_censo"] = d.viv_hab_censo_est / (d.area_km2 * 100)       # viviendas habitadas por ha (MODELO)
assert len(d) == 167 and d.area_km2.gt(0).all()

def pct_rank(vals, zero_is_zero=False):          # identica a build_v3_rating.py (rangos promedio, 0..1)
    x = np.asarray(vals, float); order = x.argsort(kind="stable"); ranks = np.empty(len(x)); sv = x[order]; i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sv[j + 1] == sv[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0; i = j + 1
    r = ranks / (len(x) - 1)
    if zero_is_zero: r[x == 0] = 0.0
    return r
def rank_desc(s):  # 1 = mejor; desempate estable por orden de fila
    return pd.Series(np.asarray(s)).rank(ascending=False, method="first").astype(int).values

# ---------- reproduccion del base ----------
D = d.D_star.values
A0 = pct_rank(d.anclas_pond / (d.viv_est / 1000)); C0 = pct_rank(d.comp_n_300m / (d.viv_est / 1000), True)
s0 = 100 * (W_D * D + W_A * A0 + W_C * (1 - C0))
rep_diff = float(np.abs(s0 - d.score_base).max()); rep_rk = int((rank_desc(s0) != d.rank_base).sum())
print("reproduccion base: max dif score", rep_diff, "rangos distintos", rep_rk)

# ======================= (i) densidad =======================
Dens = pct_rank(d.viv_ha_censo)
d["dens_star"] = Dens.round(4)
res = {}
def variant(w, mode):
    if mode == "DA":    # el peso de densidad sale de Demanda y Anclas en proporcion a su peso (C intacto)
        wd, wa, wc = W_D - w * W_D / (W_D + W_A), W_A - w * W_A / (W_D + W_A), W_C
    else:               # sale de los tres en proporcion
        wd, wa, wc = W_D * (1 - w), W_A * (1 - w), W_C * (1 - w)
    return 100 * (wd * D + wa * A0 + wc * (1 - C0) + w * Dens), (wd, wa, wc)
rows = []
for mode in ("DA", "ALL"):
    for w in (0.05, 0.10, 0.20, 0.30):
        if mode == "ALL" and w not in (0.10, 0.20): continue
        s, (wd, wa, wc) = variant(w, mode); r = rank_desc(s)
        key = f"{mode}_{int(w*100):02d}"; d[f"score_dens_{key}"] = s.round(2); d[f"rank_dens_{key}"] = r
        t = lambda col, n: set(d.loc[d[col] <= n, "cve_col"])
        b10, n10 = t("rank_base", 10), set(d.loc[r <= 10, "cve_col"]); b30, n30 = t("rank_base", 30), set(d.loc[r <= 30, "cve_col"])
        mv = np.abs(d.rank_base.values - r)
        res[key] = dict(modo=mode, w_dens=w, w_D=round(wd, 4), w_A=round(wa, 4), w_C=round(wc, 4),
                        spearman_score=float(spearmanr(d.score_base, s)[0]), spearman_rank=float(spearmanr(d.rank_base, r)[0]),
                        top10_comun=len(b10 & n10), top30_comun=len(b30 & n30), mov_gt10=int((mv > 10).sum()), mov_mediano=float(np.median(mv)), mov_max=int(mv.max()),
                        entran10=sorted(n10 - b10), salen10=sorted(b10 - n10))
d_out = d[["cve_col", "colonia", "municipio", "rank_base", "score_base", "area_km2", "viv_hab_censo_est", "viv_ha_censo", "dens_star"] +
          [c_ for c_ in d.columns if c_.startswith("score_dens_") or c_.startswith("rank_dens_")]].sort_values("rank_base")
d_out["viv_ha_censo"] = d_out.viv_ha_censo.round(2); d_out["viv_hab_censo_est"] = d_out.viv_hab_censo_est.round(1)
d_out["etiqueta"] = "MODELO (viv Censo 2020 por traslape colonia-AGEB / area poligono CONAPO); sensibilidad, no reemplaza score_base"
d_out.to_csv(f"{ROOT}/v2/data/colonias_v3_sensibilidad_densidad.csv", index=False)

# ======================= (ii) banda de confianza (Monte-Carlo) =======================
rng = np.random.default_rng(SEED)
N = len(d); anc = d.anclas_pond.values; cnt = d.comp_n_300m.values.astype(float)
vE, vC = d.viv_est.values, d.viv_hab_censo_est.values
rate_obs_all = cnt / (vE / 1000)                      # tasa observada /1000 viv (base)
pool_all = rate_obs_all.copy(); pool_pos = rate_obs_all[cnt > 0]
zero = cnt == 0
def mc(pool, nd):
    R = np.empty((nd, N), dtype=np.int16)
    for k in range(nd):
        w = np.array([W_D, W_A, W_C]) * rng.uniform(0.7, 1.3, 3); w = w / w.sum()       # pesos +-30 %, renormalizados
        u = rng.uniform(0, 1, N); viv = vC + u * (vE - vC)                              # viviendas entre Censo y pob/3.6
        n = cnt.copy()                                                                  # competencia: 0 = desconocido
        n[zero] = rng.choice(pool, zero.sum()) * (viv[zero] / 1000)                      # tasa empirica x viviendas
        a = pct_rank(anc / (viv / 1000)); cc = pct_rank(n / (viv / 1000), True)          # misma regla del base: n=0 -> C*=0
        s = 100 * (w[0] * D + w[1] * a + w[2] * (1 - cc))
        R[k] = rank_desc(s)
    return R
R = mc(pool_all, NDRAW)
Rp = mc(pool_pos, NDRAW)
# control: MC solo pesos (sin viviendas ni competencia) -> cuanta incertidumbre viene de cada fuente
def mc_only(w_on, viv_on, comp_on, nd=1500):
    out = np.empty((nd, N), dtype=np.int16)
    for k in range(nd):
        w = np.array([W_D, W_A, W_C]) * (rng.uniform(0.7, 1.3, 3) if w_on else 1); w = w / w.sum()
        viv = vC + rng.uniform(0, 1, N) * (vE - vC) if viv_on else vE
        n = cnt.copy()
        if comp_on: n[zero] = rng.choice(pool_all, zero.sum()) * (viv[zero] / 1000)
        a = pct_rank(anc / (viv / 1000)); cc = pct_rank(n / (viv / 1000), True)
        out[k] = rank_desc(100 * (w[0] * D + w[1] * a + w[2] * (1 - cc)))
    return out
src = {}
for name, args in {"solo_pesos": (1, 0, 0), "solo_viviendas": (0, 1, 0), "solo_competencia_cero": (0, 0, 1), "todo": (1, 1, 1)}.items():
    Rx = mc_only(*args); w_ = np.percentile(Rx, 90, axis=0) - np.percentile(Rx, 10, axis=0)
    src[name] = dict(ancho_mediano=float(np.median(w_)), ancho_medio=float(w_.mean()), ancho_max=float(w_.max()))
p10, p50, p90 = [np.percentile(R, q, axis=0) for q in (10, 50, 90)]
q10, q90 = np.percentile(Rp, 10, axis=0), np.percentile(Rp, 90, axis=0)
d["rank_p10"] = np.round(p10).astype(int); d["rank_p50"] = np.round(p50).astype(int); d["rank_p90"] = np.round(p90).astype(int)
d["ancho_banda"] = d.rank_p90 - d.rank_p10
d["rank_p10_estres"] = np.round(q10).astype(int); d["rank_p90_estres"] = np.round(q90).astype(int)
d["prob_top10"] = (R <= 10).mean(0).round(3); d["prob_top30"] = (R <= 30).mean(0).round(3)
d["prob_top30_estres"] = (Rp <= 30).mean(0).round(3)
d["comp_cero_desconocido"] = zero
# ---- etiqueta de confianza (reglas fijas, ver docs/BANDA_CONFIANZA.md) ----
W1, W2 = 30, 60     # ancho (p90-p10) en rangos: <=30 estrecha; 31-60 media; >60 ancha
def band(wid): return "estrecha" if wid <= W1 else ("media" if wid <= W2 else "ancha")
d["banda"] = d.ancho_banda.map(band)
def conf(r):
    # puntos por banda (estrecha 2 / media 1 / ancha 0) menos 1 si no hay ninguna marca Scout en la colonia (piso 0)
    pts_ = {"estrecha": 2, "media": 1, "ancha": 0}[r.banda] - (1 if r.cobertura_campo == "sin encuesta" else 0)
    return ["baja", "media", "alta"][max(0, pts_)]
d["confianza"] = d.apply(conf, axis=1)
d["etiqueta"] = "MODELO: banda de sensibilidad (pesos +-30%, viviendas Censo<->pob/3.6, 0 competidores = desconocido); NO es pronostico ni intervalo estadistico"
cols = ["cve_col", "colonia", "municipio", "rank_base", "score_base", "rank_p10", "rank_p50", "rank_p90", "ancho_banda", "banda", "confianza",
        "prob_top10", "prob_top30", "rank_p10_estres", "rank_p90_estres", "prob_top30_estres", "comp_n_300m", "comp_cero_desconocido", "cobertura_campo", "scout_marks", "etiqueta"]
out = d.sort_values("rank_base")[cols]; out.to_csv(f"{ROOT}/v2/data/colonias_v3_banda_confianza.csv", index=False)
stats = dict(repro=dict(max_dif=rep_diff, rangos_distintos=rep_rk), dens=res, ndraw=NDRAW, seed=SEED, fuentes_ancho=src,
             ancho=dict(mediana=float(d.ancho_banda.median()), media=float(d.ancho_banda.mean()), max=int(d.ancho_banda.max()), min=int(d.ancho_banda.min())),
             confianza=d.confianza.value_counts().to_dict(), banda=d.banda.value_counts().to_dict(),
             spearman_rank_p50=float(spearmanr(d.rank_base, d.rank_p50)[0]),
             spearman_dens_vs_score=float(spearmanr(d.viv_ha_censo, d.score_base)[0]))
json.dump(stats, open("/workspace/downloads/banda_confianza_stats.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v_ for k, v_ in stats.items() if k != "dens"}, indent=1, ensure_ascii=False))
for k, r_ in res.items(): print(k, {a: b for a, b in r_.items() if a not in ("entran10", "salen10")}, r_["entran10"], r_["salen10"])
