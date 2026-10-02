#!/usr/bin/env python3
"""Dias de calor (Tmax >= 35 / >= 40 C) por mes, Monterrey (25.67,-100.31), 2021-2026.
Fuente: Open-Meteo Historical Weather API (archive-api.open-meteo.com, sin llave; reanalisis, celda ~9-11 km, NO estacion).
Uso: python3 scripts/clima_dias_calor_mty.py [--fetch]   (--fetch descarga a /workspace/downloads/om_raw.json; 1 sola peticion)
Escribe data/clima_mty_dias_calor.csv. No toca rankings."""
import json, os, sys, urllib.request, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/workspace/downloads/om_raw.json"
URL = ("https://archive-api.open-meteo.com/v1/archive?latitude=25.67&longitude=-100.31&start_date=2021-01-01&end_date=2026-09-30"
       "&daily=temperature_2m_max,temperature_2m_min&timezone=America%2FMexico_City")
if "--fetch" in sys.argv or not os.path.exists(RAW):
    req = urllib.request.Request(URL, headers={"User-Agent": "purificador-research/1.0"})
    open(RAW, "wb").write(urllib.request.urlopen(req, timeout=60).read())
j = json.load(open(RAW)); d = j["daily"]
df = pd.DataFrame({"fecha": pd.to_datetime(d["time"]), "tmax": d["temperature_2m_max"], "tmin": d["temperature_2m_min"]})
assert df.tmax.notna().all()
df["anio"] = df.fecha.dt.year; df["mes"] = df.fecha.dt.month
g = df.groupby(["anio", "mes"])
out = g.agg(dias_con_dato=("tmax", "size"), tmax_media_c=("tmax", "mean"), tmax_max_c=("tmax", "max"), tmin_media_c=("tmin", "mean"),
            dias_ge35=("tmax", lambda s: int((s >= 35).sum())), dias_ge40=("tmax", lambda s: int((s >= 40).sum()))).reset_index()
out["dias_mes"] = out.apply(lambda r: pd.Period(f"{int(r.anio)}-{int(r.mes):02d}").days_in_month, axis=1)
out["mes_completo"] = out.dias_con_dato == out.dias_mes
out["pct_dias_ge35"] = (100 * out.dias_ge35 / out.dias_con_dato).round(1)
for c in ["tmax_media_c", "tmax_max_c", "tmin_media_c"]: out[c] = out[c].round(1)
out["fuente"] = "Open-Meteo archive (reanalisis; celda %.3f,%.3f elev %sm); lat/lon pedidos 25.67,-100.31" % (j["latitude"], j["longitude"], j.get("elevation"))
out.to_csv(f"{ROOT}/data/clima_mty_dias_calor.csv", index=False)
print(out.to_string())
# climatologia por mes (solo meses completos)
c = out[out.mes_completo].groupby("mes").agg(n_anios=("anio", "count"), d35_media=("dias_ge35", "mean"), d40_media=("dias_ge40", "mean"), tmax_media=("tmax_media_c", "mean")).round(1)
print(c)
print(df.groupby("anio").apply(lambda x: pd.Series({"n": len(x), "d35": int((x.tmax >= 35).sum()), "d40": int((x.tmax >= 40).sum()), "tmax_max": x.tmax.max(), "fecha_max": str(x.loc[x.tmax.idxmax(), "fecha"].date())})))
c.to_csv("/workspace/downloads/clima_climatologia_mes.csv")
