#!/usr/bin/env python3
"""Barrio anchors for ZMM from INEGI DENUE bulk CSV (Nuevo León, free, no token).

Usage:
  python3 scripts/fetch_denue_anclas_barrio_zmm.py            # downloads zip if missing
  DENUE_ZIP=/path/denue_19_csv.zip python3 scripts/fetch_denue_anclas_barrio_zmm.py

Source: https://www.inegi.org.mx/contenidos/masiva/denue/denue_19_csv.zip
  (~21 MB zip, ~211k rows NL; cached at $DENUE_ZIP or /tmp/denue_19_csv.zip; NOT committed)

Writes:
  data/denue_anclas_barrio_zmm.geojson  (raw DENUE source, clipped to ZMM bbox)

SCIAN → kind:
  311830           tortilleria   (elaboración de tortillas de maíz y molienda de nixtamal)
  461110           abarrotes     (abarrotes, ultramarinos y misceláneas)
  461211, 461212   deposito      (vinos y licores / cerveza — depósitos)
  462112           abarrotes     (minisupers) minus big chains (Oxxo/7-Eleven/Six/Extra/… already in places_anclas)
  464111           farmacia      (farmacias sin minisúper)
  522110/522210/466112/523122/522452 whose name ~ AZTECA|BIENESTAR|ELEKTRA → banco_prestamo

Why bulk instead of DENUE API: no INEGI token in repo/.env; bulk CSV is the same
data, one download, no rate limits. Consumed by scripts/build_anclas_barrio_zmm.py.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
import urllib.request
import zipfile
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from _anclas_common import DATA, in_clip, now_utc, point, write_fc, zmm_clip  # noqa: E402

URL = "https://www.inegi.org.mx/contenidos/masiva/denue/denue_19_csv.zip"
ZIP = os.environ.get("DENUE_ZIP", "/tmp/denue_19_csv.zip")
OUT = os.path.join(DATA, "denue_anclas_barrio_zmm.geojson")

SCIAN = {
    "311830": "tortilleria",
    "461110": "abarrotes",
    "461211": "deposito",
    "461212": "deposito",
    "462112": "abarrotes",
    "464111": "farmacia",
}
BANK_CODES = {"522110", "522210", "466112", "523122", "522452"}
BANK_RE = re.compile(r"AZTECA|BIENESTAR|ELEKTRA|BANSEFI", re.I)
CHAIN_RE = re.compile(
    r"OXXO|7.?ELEVEN|SEVEN|CIRCLE ?K|\bSIX\b|MODELORAMA|TIENDA EXTRA|\bEXTRA\b|SORIANA|AURRERA|"
    r"WAL.?MART|\bHEB\b|H-E-B|CHEDRAUI|FRESKO|CITY MARKET|SMART|KIOSKO|GASOLINERA",
    re.I,
)


def open_csv():
    if not os.path.isfile(ZIP):
        print(f"downloading {URL} → {ZIP}")
        urllib.request.urlretrieve(URL, ZIP)
    z = zipfile.ZipFile(ZIP)
    name = next(n for n in z.namelist() if n.startswith("conjunto_de_datos/") and n.endswith(".csv"))
    return io.TextIOWrapper(z.open(name), encoding="latin-1", newline="")


def main() -> int:
    clip = zmm_clip()
    feats, c, dropped_chain = [], Counter(), 0
    for row in csv.DictReader(open_csv()):
        code = row["codigo_act"]
        name = (row["nom_estab"] or "").strip()
        full = f"{name} {row.get('raz_social') or ''}"
        kind = SCIAN.get(code)
        sub = code
        if code in BANK_CODES:
            m = BANK_RE.search(full)
            kind = "banco_prestamo" if m else None
            sub = m.group(0).lower() if m else code
        if not kind:
            continue
        if code == "462112" and CHAIN_RE.search(full):
            dropped_chain += 1
            continue
        try:
            lat, lon = float(row["latitud"]), float(row["longitud"])
        except ValueError:
            continue
        if not in_clip(lon, lat, clip):
            continue
        c[kind] += 1
        feats.append(
            point(
                lon,
                lat,
                {
                    "kind": kind,
                    "name": name.title(),
                    "fuente": "denue",
                    "denue_id": row["id"],
                    "scian": code,
                    "sub": sub,
                    "per_ocu": row["per_ocu"],
                    "mun": row["municipio"],
                },
            )
        )
    feats.sort(key=lambda f: (f["properties"]["kind"], f["properties"]["denue_id"]))
    write_fc(
        OUT,
        feats,
        "denue_anclas_barrio_zmm",
        {
            "fuente": "INEGI DENUE bulk CSV (Nuevo León)",
            "url": URL,
            "fetched_at": now_utc(),
            "clip_bbox": list(clip),
            "counts_by_kind": dict(c),
            "dropped_chain_minisuper": dropped_chain,
        },
    )
    print(dict(c), "dropped chains", dropped_chain, "→", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
