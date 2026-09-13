# Ubicarme (GPS en el mapa web)

Fecha: 2026-09-12  
URL: https://casca-code.github.io/mapa-purificadoras/

## Qué hace

Con el website abierto en el teléfono:

1. Botón **Ubicarme** pide permiso de ubicación al navegador.
2. `watchPosition` mantiene un pin azul en vivo (+ círculo de precisión).
3. Point-in-polygon contra colonias del estudio → ficha: colonia, municipio, rank, `score_100`, Demanda\*, Comp\*, Anclas\*, Canibal\*.
4. Fuera de polígonos → “Fuera de colonias del estudio”.

Todo es **client-side** (no se sube el GPS a un servidor).

## Requisitos

- Abrir por **HTTPS** (GitHub Pages). `file://` suele fallar o limitar geolocation.
- Aceptar el permiso de ubicación en Safari/Chrome.

## Qué no hace (aún)

- No manda la ubicación en vivo al chat de Grok Bot / Purificador.
- No guarda notas de campo automáticamente (siguiente iteración si Nicolás lo pide).
