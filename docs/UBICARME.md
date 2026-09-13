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

## Fix 2026-09-12

- Al tocar **Ubicarme** se llama `getCurrentPosition` (dispara el diálogo Allow) y luego `watchPosition`.
- Si falla por timeout, reintenta sin alta precisión.
- Capas de contexto/competencia arrancan **apagadas**; no bloquean el GPS.
- Si dijiste Deny antes: en Chrome Android → candado de la URL → Permisos → Ubicación → Permitir.

## iPhone (2026-09-12)

**No hace falta Trust Developer** (eso es para apps firmadas, no para este website).

Si no sale el aviso de ubicación:

1. Abre el mapa en **Safari** (copia el link; no lo abras desde el navegador interno de WhatsApp/IG).
2. iPhone **Ajustes → Privacidad y seguridad → Localización** → ON.
3. En esa lista, **Safari Websites** (o Safari) → **Preguntar** o **Mientras se use la app**.
4. Vuelve a https://casca-code.github.io/mapa-purificadoras/ → **Ubicarme** → **Permitir**.
5. Si antes tocaste No permitir: Ajustes → Safari → Avanzado → Datos de sitios web → borra `github.io`, o en Localización → Safari cambia a Preguntar.


## Nombre fuera del estudio

Reverse Nominatim para nombre; score solo en estudio.
