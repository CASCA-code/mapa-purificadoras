#!/usr/bin/env python3
"""Sensibilidad del margen mensual por estacion a un factor estacional de calor (PARAMETRO, k SUPUESTO).
Entradas: data/clima_mty_dias_calor.csv, data/sadm_tarifas_sep2026_cat2_cat6.csv, v2/data/colonias_v3.csv (solo lectura).
Salidas: data/calor_sensibilidad_mensual.csv, /workspace/downloads/calor_sens_stats.json. Sin red. NO recalcula ni escribe v3."""
import csv, json, math, os
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L_GARR, PRECIO, GARR_DIA, DIAS, RENTA, OTROS = 19.0, 12.0, 30, 30, 1000.0, (0.30, 0.85)   # = scripts/unit_economics_reconciliado.py
NIC_AGUA, REC = 2.50, 0.80
T = {int(r["m3_mes"]): r for r in csv.DictReader(open(f"{ROOT}/data/sadm_tarifas_sep2026_cat2_cat6.csv"))}
def agua_cat(garr_mes, cat, rec=REC):
    n = math.ceil(garr_mes * L_GARR / 1000 / rec - 1e-9); r = T[n]
    return float(r[f"{cat}_valor_consumo_mxn"]) + float(r[f"{cat}_cargo_fijo_mxn"])
CASOS = {"BASE $2.50 plano": lambda g: NIC_AGUA * g,
         "Cat. 2 @ 80 %": lambda g: agua_cat(g, "cat2"),
         "Cat. 6 @ 80 %": lambda g: agua_cat(g, "cat6")}
# climatologia: promedio de dias >=35 C por mes calendario (solo meses completos)
c = pd.read_csv(f"{ROOT}/data/clima_mty_dias_calor.csv"); c = c[c.mes_completo == True]
m = c.groupby("mes").agg(n_anios=("anio", "nunique"), d35=("dias_ge35", "mean"), dias=("dias_mes", "mean")).reset_index()
m["frac35"] = m.d35 / m.dias
KS = (0.0, 0.1, 0.2)
rows = []
for caso, fa in CASOS.items():
    for norm in ("base_sin_calor", "media_anual_30"):
        for k in KS:
            f = 1 + k * m.frac35.values
            sc = 1.0 if norm == "base_sin_calor" else 1.0 / f.mean()        # media_anual_30: el promedio simple de los 12 factores = 1
            for i, mes in enumerate(m.mes):
                fac = f[i] * sc; gd = GARR_DIA * fac; gm = gd * DIAS
                ing = gm * PRECIO; agua = fa(gm)
                rows.append(dict(caso_agua=caso, normalizacion=norm, k=k, mes=int(mes), n_anios=int(m.n_anios[i]), d35_media=round(m.d35[i], 2), frac_dias_ge35=round(m.frac35[i], 3),
                                 factor=round(fac, 4), garr_dia=round(gd, 2), garr_mes=round(gm, 1), ingreso_mxn=round(ing, 0), agua_mxn=round(agua, 0), renta_mxn=RENTA,
                                 margen_peor_mxn=round(ing - RENTA - agua - OTROS[1] * gm, 0), margen_mejor_mxn=round(ing - RENTA - agua - OTROS[0] * gm, 0),
                                 etiqueta="k = SUPUESTO (sin dato de ventas MTY); clima VERIFICADO (Open-Meteo); tarifas OFICIAL SADM sep-2026; demas = ESTIMADO"))
out = pd.DataFrame(rows); out.to_csv(f"{ROOT}/data/calor_sensibilidad_mensual.csv", index=False)
# ranking: D* uniforme
d = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv")
mm = lambda s: (s - s.min()) / (s.max() - s.min())
chk = (0.40 * d.D_star + 0.30 * d.A_star + 0.30 * (1 - d.C_star)) * 100
res = dict(chk_score_base_maxdiff=float((chk - d.score_base).abs().max()))
base_rank = d.score_base.rank(ascending=False, method="first")
for lab, fx in (("k0.2_ago", 1 + 0.2 * float(m.frac35[7])), ("k0.2_ene", 1.0)):
    Ds = mm(d.D_star * fx); sc = (0.40 * Ds + 0.30 * d.A_star + 0.30 * (1 - d.C_star)) * 100
    res[lab] = dict(f=round(fx, 4), D_maxdiff=float((Ds - d.D_star).abs().max()), score_maxdiff=float((sc - chk).abs().max()), rank_changes=int((sc.rank(ascending=False, method="first") != chk.rank(ascending=False, method="first")).sum()))
# sin renormalizar min-max (D* ya normalizado se multiplica por f): efecto = subir el peso de demanda 0.40 -> 0.40*f
Dm = d.D_star * (1 + 0.2 * float(m.frac35[7])); sc2 = (0.40 * Dm + 0.30 * d.A_star + 0.30 * (1 - d.C_star)) * 100
r1 = chk.rank(ascending=False, method="first"); r2 = sc2.rank(ascending=False, method="first")
res["sin_renormalizar_ago_k02"] = dict(rank_changes=int((r1 != r2).sum()), spearman=float(r1.corr(r2, method="spearman")), top30_cambia=int((set(r1[r1 <= 30].index) != set(r2[r2 <= 30].index))))
res["meses"] = m[["mes", "n_anios", "d35", "frac35"]].round(3).to_dict("records")
json.dump(res, open("/workspace/downloads/calor_sens_stats.json", "w"), indent=1)
print(json.dumps(res, indent=1))
