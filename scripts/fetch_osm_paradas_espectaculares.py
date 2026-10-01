#!/usr/bin/env python3
"""Offline build step: OSM Overpass (free) -> /workspace/downloads/osm_paradas_raw.json
Metro/Metrorrey stations, BRT/Transmetro, bus stops (incl. direction/ref/route_ref/network)."""
import json, sys, urllib.parse, urllib.request
B = "25.52,-100.70,25.92,-100.00"
Q = f'''[out:json][timeout:240];
(
 nwr["railway"~"^(station|subway_entrance|halt|tram_stop)$"]({B});
 nwr["station"~"^(subway|light_rail)$"]({B});
 nwr["public_transport"~"^(stop_position|platform|station)$"]({B});
 nwr["highway"="bus_stop"]({B});
 nwr["amenity"="bus_station"]({B});
);
out center tags;'''
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter"]
OUT = "/workspace/downloads/osm_paradas_raw.json"
for m in MIRRORS:
    try:
        req = urllib.request.Request(m, data=urllib.parse.urlencode({"data": Q}).encode(), headers={"User-Agent": "mapa-purificadoras/1.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=300).read())
        json.dump(d, open(OUT, "w")); print(m, len(d["elements"])); sys.exit(0)
    except Exception as e:
        print(m, e, file=sys.stderr)
sys.exit("all mirrors failed")
