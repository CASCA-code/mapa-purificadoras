#!/usr/bin/env python3
"""Offline: OSM major roads WITH tags (oneway, name, ref, lanes, junction) -> /workspace/downloads/osm_vias_oneway_raw.json"""
import json, sys, urllib.parse, urllib.request
B = "25.52,-100.70,25.92,-100.00"
Q = f'[out:json][timeout:240];way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified)(_link)?$"]({B});out tags geom;'
MIRRORS = ["https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter",
           "https://overpass.private.coffee/api/interpreter"]
for m in MIRRORS:
    try:
        req = urllib.request.Request(m, data=urllib.parse.urlencode({"data": Q}).encode(), headers={"User-Agent": "mapa-purificadoras/1.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=300).read())
        json.dump(d, open("/workspace/downloads/osm_vias_oneway_raw.json", "w")); print(m, len(d["elements"])); sys.exit(0)
    except Exception as e:
        print(m, e, file=sys.stderr)
sys.exit("all mirrors failed")
