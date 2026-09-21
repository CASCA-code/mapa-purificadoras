# Scout Userscript (Tampermonkey) — Street View sin billing

Actualizado: 2026-09-21 (**v1.7.2**)

> **Camino primario para Nicolás.** Corre **sobre** Google Maps de consumidor (`https://www.google.com/maps` Street View).  
> **Cero** Google Cloud / Maps Platform API key / hold de facturación.  
> **Usa siempre `google.com/maps` + peoncito.** No abras `scout-sv.html` (esa página sí pide key/billing).  
> Mapillary: abandonado.

## División de roles (product truth)

| Pieza | Qué hace |
|---|---|
| **Extensión Chrome** | Solo el **pasito** confiable: `ArrowLeft` / `ArrowRight` / `ArrowUp` vía `chrome.debugger` (`step({turnDeg})`). Sin ella Maps ignora teclas sintéticas. |
| **Userscript** | El **mapa de todas las calles** de la colonia + **giros**: arma un trayecto que cubre cada calle OSM del polígono y dirige la extensión hacia cada waypoint. |

## Instalación (5 pasos — hazlos en orden)

### 1) Extensión Chrome (**REQUERIDA** — sin ella no camina)

Los clicks/teclas sintéticos del userscript son *untrusted* y Maps los ignora. Solo `chrome.debugger` (ArrowUp / Left / Right) mueve el panorama con suavidad.

1. Descarga el zip:  
   https://github.com/CASCA-code/mapa-purificadoras/raw/main/extension-dist/purificadoras-scout-ext.zip  
   (o usa la carpeta `extension/` del repo)
2. Descomprime en una carpeta fija.
3. Chrome → `chrome://extensions` → **Modo de desarrollador** ON.
4. **Cargar descomprimida** → elige esa carpeta (debe verse `manifest.json`).
5. Abre Maps → Street View. El HUD muestra un **punto verde «ext OK»** (o rojo si falta la extensión).

Detalle: [`extension/README.md`](../extension/README.md).

### 2) Userscript Tampermonkey

1. Instala **[Tampermonkey](https://www.tampermonkey.net/)**.
2. **Utilidades** → **Instalar desde URL**:

   ```
   https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js?v=172
   ```
   Si Tampermonkey no toma el cambio: **Reinstall** desde esa URL (no solo Update).

3. Confirma permisos (`ntfy.sh`, Maps, Pages, Overpass, raw GitHub).

### 3) Entra a Street View

Abre **[Google Maps](https://www.google.com/maps)** → arrastra el **peoncito** a una calle de la ZMM.

### 4) Elige colonia

En el HUD: busca / elige colonia (prioriza **General Escobedo**).

### 5) Start trayecto — cubre **todas** las calles

Pulsa **▶ Start trayecto** (acción principal). El script:

1. Carga calles prebaked (`data/roads_zmm.geojson`) recortadas al polígono de la colonia (Overpass / rejilla solo si falta).
2. Arma un **grafo** de tramos (nodos en intersecciones / extremos).
3. Calcula un paseo que **cubre cada arista al menos una vez** (aproximación Chinese Postman / Hierholzer; si hay nodos de grado impar, duplica caminos cortos).
4. Muestrea waypoints cada ~15 m (cap ~2500 pts en colonias muy grandes; el HUD lo anuncia).
5. HUD antes de caminar: `Trayecto: N pts · ~X calles · cobertura colonia`.
6. Entra **1 vez** al inicio con URL (puede flash negro).
7. Luego **loop automático**: **v1.7+ rota el POV hacia el trayecto antes de avanzar** (poll heading URL; luego ArrowUp). **v1.7.2:** ~55 m antes de un cruce con giro ≥35° alinea al bearing de **salida** del trayecto (evita quedarse entre link izq/der de SV).
8. Callejón sin salida: si ArrowUp no mueve 2–3 veces → U-turn POV ~180° real (sin Up), luego sigue el path.
9. Componente lejano: solo si el siguiente punto está >90 m **y** falla ≥5 veces → **un** salto `map_action=pano` (“otra calle”), luego vuelve a flecha.
10. **Space** = pausa/reanuda el trayecto. Si hay colonia elegida y aún no hay ruta → Space arma y arranca el trayecto.
11. Progreso: `colonia · i/n (p%) · calles`.

Pace default ~800 ms (slider 700–2500).

---

## Qué es

Extensión de usuarios (Tampermonkey) + **extensión Chrome companion (requerida para walk)** que, en Street View del Maps normal, deja marcar pines / comentarios de zona con las mismas teclas que Scout SV.

- Human-in-the-loop en el **marcado** (M/S/Y/…/C); el **desplazamiento** del trayecto es automático vía extensión.
- No scrapea negocios ni cachea imagery — solo GeoJSON (coords + props).
- Sync **primario: ntfy** (el userscript en `google.com` **no** comparte `localStorage` con Pages).

## Historial corto

- **v1.3:** walk URL-pano → pantalla negra cada paso.
- **v1.4:** walk flecha SV in-pano; extensión era fallback opcional (insuficiente: untrusted falla).
- **v1.5:** extensión = **PRIMARY / requerida**. Cada tick llama extensión primero (`step({turnDeg})`). Trayecto automático de punta a punta. Pace más rápido (~800 ms).
- **v1.6:** trayecto = **cobertura total de calles** (grafo + Chinese Postman), no “solo ArrowUp en una avenida”. Steering con giros fuertes, U-turn en dead-ends, hop raro entre componentes.
- **v1.7:** rota el POV hacia el trayecto antes de avanzar (ext 1.5.1: más teclas/°, settle 320 ms, mouse-drag backup).
- **v1.7.1:** HUD slim (hotkeys → colonia → Start → speed → progress → Pause/Stop + mini-mapa del recorrido; Export/Sync en ⋯).
- **v1.7.2:** speed ya no “acelera solo” (ArrowLeft/Right de la extensión ya no mueven el `<input type="range">`: blur/disable HUD antes de cada step, `tabindex=-1`, `preventDefault`+`stopImmediatePropagation` en flechas). Look-ahead en cruces: ~55 m antes de esquina con `|turn|≥35°` alinea POV al **bearing de salida** del trayecto (no al link SV ambiguo); HUD `↳ der` / `↰ izq`.

## Extensión = requerida (no opcional)

| | Userscript solo | Userscript + extensión |
|---|---|---|
| Auto-walk / trayecto | ❌ Maps ignora teclas/clicks sintéticos | ✅ ArrowUp/Left/Right confiables |
| HUD | Punto rojo «ext» | Punto verde «ext OK» |
| Banner amarillo Chrome | — | Breve al adjuntar debugger (normal; se suelta tras cada paso) |

API página: `PURIF_SCOUT_EXT.step({turnDeg, forward:false})` (POV-only) / `step({turnDeg})`, `stepForward()`, `turnLeft(n)`, `turnRight(n)`, `ping()`.

## Hotkeys (igual que Scout SV)

| Tecla | Qué marca |
|---|---|
| **M** | Modelorama |
| **S** | Semáforo |
| **Y** | Competencia / purificadora |
| **E** | Express |
| **P** | Iglesia |
| **I** | Escuela |
| **H** | Hospital / otro |
| **U** | Alias Modelorama |
| **C** | Comentario de zona (~60 m) |
| **Space** | Con trayecto: pausa/reanuda. Con colonia y sin ruta: Start trayecto. Sin ambos: Auto-walk ON/OFF |
| **Z** / **Backspace** | Deshacer último pin |

ntfy sync sin cambios (`purif-zmm-campo-casca-v1`).

## Limitaciones

- Hay que estar en **Street View**.
- Sin extensión el panorama **no avanza** (HUD rojo).
- Entrada/recovery URL = flash negro (avisado).
- Colonias muy grandes se capan a ~2500 pts (HUD: `cap 2500`); la cobertura sigue siendo por calles, no una sola avenida.
- Componentes OSM desconectados pueden requerir un hop pano ocasional (“otra calle”).

## Relacionado

- Extensión: `extension/` · zip: `extension-dist/purificadoras-scout-ext.zip`
- Script: `userscripts/purificadoras-scout.user.js`
- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
