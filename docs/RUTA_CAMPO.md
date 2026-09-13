# Ruta de campo (mapa)

## Qué hace
Panel **ruta** en el rail del mapa Version 2:

1. Elige municipio (o todos) y Top 5/8/9, o marca colonias a mano (top 40 del filtro).
2. **Cargar top** / **+ colonia fijada** / **Armar ruta**.
3. Dibuja circuito en el mapa (casa → paradas numeradas → casa).
4. **Abrir en Google Maps** (origin = destination = casa).

## Casa (depósito)
Violeta 116, Colonia Los Colorines, San Pedro Garza García, N.L.  
Pin aproximado en mapa: Calle Violeta OSM (~25.63028, -100.34602). Maps geocodifica la dirección completa.

## Motor
- Paradas = centroides de polígonos CONAPO del ranking v2 (no inventa scores).
- Orden: nearest-neighbor + 2-opt sobre distancia haversine (línea recta).
- Google Maps aplica el ruteo real por calles.
- Tope **9** waypoints (límite práctico del link `maps/dir`).

## No hace (aún)
- Matrices de tiempo real / tráfico (Routes API).
- Punto de visita exacto en calle (solo centroide).
- Más de 9 paradas en un solo link (partir en 2 vueltas).
