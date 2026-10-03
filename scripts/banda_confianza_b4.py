#!/usr/bin/env python3
"""Banda de confianza (p10/p50/p90 de puesto, prob_top30) RECALCULADA con la formula B4 nueva (0.45/0.45/0.10, 0 comp => competencia excluida (renormalizado), con comp => max(renorm., completa)).
MODELO de sensibilidad, no pronostico. Misma metodologia y semilla que scripts/banda_confianza_densidad.py (docs/BANDA_CONFIANZA.md),
solo cambian la formula y los pesos. Offline. Escribe SOLO b4/data/colonias_b4_banda.csv (no toca v2/).
Entradas (solo lectura): v2/data/colonias_v3.csv, data/colonias.geojson, /home/box/geo/inegi_purificador/datos/* (viviendas Censo, ya en disco)."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b4_formula as F
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = "/home/box/geo/inegi_purificador/datos"
SEED, NDRAW = 20261002, 4000
v = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv")
c = pd.read_csv(f"{GEO}/colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv")[["cve_col", "viv_hab_censo_est"]]
cg = {f["properties"]["cve_col"]: f["properties"] for f in json.load(open(f"{ROOT}/data/colonias.geojson"))["features"]}
d = v.merge(c, on="cve_col", validate="1:1")
d["viv_est"] = d.cve_col.map(lambda k: float(cg[k]["pob_conapo"])) / 3.6
assert len(d) == 167

def pct_rank(vals, zero_is_zero=False):   # identica a build_v3_rating.py
    x = np.asarray(vals, float); order = x.argsort(kind="stable"); ranks = np.empty(len(x)); sv = x[order]; i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sv[j + 1] == sv[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0; i = j + 1
    r = ranks / (len(x) - 1)
    if zero_is_zero: r[x == 0] = 0.0
    return r
def rank_desc(s): return pd.Series(np.asarray(s)).rank(ascending=False, method="first").astype(int).values
def cb(P, n): return np.where(n > 0, np.minimum(P, F.CAP_P) / F.CAP_P, 0.0)
def sc(wd, wa, wc, D_, a_, P_, n_):   # 0 comp -> renormalizado; con comp -> max(renormalizado, formula completa)
    base = 100 * (wd * D_ + wa * a_) / (wd + wa)
    return np.where(n_ > 0, np.maximum(base, 100 * (wd * D_ + wa * a_ + wc * cb(P_, n_))), base)

D = d.D_star.values; anc = d.anclas_pond.values; cnt = d.comp_n_300m.values.astype(float)
vE, vC = d.viv_est.values, d.viv_hab_censo_est.values
# control: reproducir score B4 del base
s0 = sc(F.W_D, F.W_A, F.W_C, D, pct_rank(anc / (vE / 1000)), pct_rank(cnt / (vE / 1000), True), cnt)
s_ref = np.array([F.score(a, b, c_, n) for a, b, c_, n in zip(d.D_star, d.A_star, d.C_star, d.comp_n_300m)])
print("repro B4 base: max dif score vs columnas v3 redondeadas", float(np.abs(s0 - s_ref).max()))
rate = cnt / (vE / 1000); pool_all = rate.copy(); pool_pos = rate[cnt > 0]; zero = cnt == 0
rng = np.random.default_rng(SEED)
def mc(pool, nd):
    R = np.empty((nd, len(d)), dtype=np.int16)
    for k in range(nd):
        w = np.array([F.W_D, F.W_A, F.W_C]) * rng.uniform(0.7, 1.3, 3); w = w / w.sum()   # pesos +-30 %, renormalizados
        viv = vC + rng.uniform(0, 1, len(d)) * (vE - vC)                                   # viviendas entre Censo y pob/3.6
        n = cnt.copy(); n[zero] = rng.choice(pool, zero.sum()) * (viv[zero] / 1000)         # 0 competidores = desconocido (si sale >0 solo SUMA bono)
        a = pct_rank(anc / (viv / 1000)); P = pct_rank(n / (viv / 1000), True)
        R[k] = rank_desc(sc(w[0], w[1], w[2], D, a, P, n))
    return R
R = mc(pool_all, NDRAW); Rp = mc(pool_pos, NDRAW)
d["rank_p10"], d["rank_p50"], d["rank_p90"] = [np.round(np.percentile(R, q, axis=0)).astype(int) for q in (10, 50, 90)]
d["ancho_banda"] = d.rank_p90 - d.rank_p10
d["prob_top10"] = (R <= 10).mean(0).round(3); d["prob_top30"] = (R <= 30).mean(0).round(3); d["prob_top30_estres"] = (Rp <= 30).mean(0).round(3)
d["comp_cero_desconocido"] = zero
W1, W2 = 30, 60     # mismas reglas de confianza que docs/BANDA_CONFIANZA.md
d["banda"] = d.ancho_banda.map(lambda w: "estrecha" if w <= W1 else ("media" if w <= W2 else "ancha"))
def conf(r):
    pts = {"estrecha": 2, "media": 1, "ancha": 0}[r.banda] - (1 if r.cobertura_campo == "sin encuesta" else 0)
    return ["baja", "media", "alta"][max(0, pts)]
d["confianza"] = d.apply(conf, axis=1)
d["rank_b4_ref"] = rank_desc(s_ref)
cols = ["cve_col", "colonia", "municipio", "rank_p10", "rank_p50", "rank_p90", "ancho_banda", "banda", "confianza", "prob_top10", "prob_top30", "prob_top30_estres", "comp_cero_desconocido"]
d[cols].sort_values("rank_p50").to_csv(f"{ROOT}/b4/data/colonias_b4_banda.csv", index=False)
print("confianza", d.confianza.value_counts().to_dict(), "banda", d.banda.value_counts().to_dict(), "ancho mediana", float(d.ancho_banda.median()))
