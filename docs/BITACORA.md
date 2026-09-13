# Bitácora Purificadoras

## 2026-09-12 (layout móvil)

- Mapa a pantalla casi completa en teléfono.
- Sidebar “Colonia objetivo” → bottom sheet **Capas y ranking** (colapsado; tocas para abrir).
- Ficha GPS compacta arriba (fuera del estudio = 2 líneas).

## 2026-09-12 (tarde)

- Default del mapa: **solo colonias score ON**; competencia, anclas (OSM + retail/bancos), etiquetas **OFF** (el usuario prende lo que quiere ver).
- Ubicarme: `getCurrentPosition` al tocar (dispara Allow) + `watchPosition`; reintento sin high-accuracy; mensajes de error por código; meta Permissions-Policy.

## 2026-09-12

- Default del mapa: **solo colonias score ON**; competencia, anclas (OSM + retail/bancos), etiquetas **OFF** (el usuario prende lo que quiere ver).
- Ubicarme: `getCurrentPosition` al tocar (dispara Allow) + `watchPosition`; reintento sin high-accuracy; mensajes de error por código; meta Permissions-Policy.

- Publicado mapa v2 en GitHub Pages: https://casca-code.github.io/mapa-purificadoras/
- Anclas retail/bancos (118 pts) + pesos en Anclas\*; capas A/S/C/B/Z.
- Ubicarme (GPS vivo + ficha rank) en el HTML.
- Top 10 v2 estable tras anclas nuevas.
- Tarifas SADM documentadas (Croc, ósmosis, doméstica vs comercial).
- Standing ops: actualizar MDs del folder y push a GitHub tras cada avance, sin pedir ok de público.
- Descartado: casas abandonadas, capa haitianos.

## Regla permanente

Después de cada conversación con avance: actualizar MD(s) aquí y en `version2/`, commit + push al repo `CASCA-code/mapa-purificadoras` (y copiar HTML a Pages).
