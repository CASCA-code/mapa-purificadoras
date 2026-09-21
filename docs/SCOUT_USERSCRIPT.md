# Scout Userscript (Tampermonkey) — Street View sin billing

Actualizado: 2026-09-21 (**v1.5.0**)

> **Camino primario para Nicolás.** Corre **sobre** Google Maps de consumidor (`https://www.google.com/maps` Street View).  
> **Cero** Google Cloud / Maps Platform API key / hold de facturación.  
> **Usa siempre `google.com/maps` + peoncito.** No abras `scout-sv.html` (esa página sí pide key/billing).  
> Mapillary: abandonado.

## Instalación (5 pasos — hazlos en orden)

### 1) Extensión Chrome (**REQUERIDA** — sin ella no camina)

Los clicks/teclas sintéticos del userscript son *untrusted* y Maps los ignora. Solo `chrome.debugger` (ArrowUp / Left / Right) mueve el panorama con suavidad.

1. Descarga el zip:  
   https://github.com/CASCA-code/mapa-purificadoras/raw/main/extension-dist/purificadoras-scout-ext.zip  
   (o usa la carpeta `extension/` del repo)
2. Descomprime en una carpeta fija.
3. Chrome → `chrome://extensions` → **Modo de desarrollador** ON.
4. **Cargar descomprimida** → elige esa carpeta (debe verse `manifest.json`).
5. Abre Maps → Street View. El HUD debe ponerse **verde: «ext OK · camina solo»**. Si está rojo, la extensión no está activa.

Detalle: [`extension/README.md`](../extension/README.md).

### 2) Userscript Tampermonkey

1. Instala **[Tampermonkey](https://www.tampermonkey.net/)**.
2. **Utilidades** → **Instalar desde URL**:

   ```
   https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js
   ```

3. Confirma permisos (`ntfy.sh`, Maps, Pages, Overpass, raw GitHub).

### 3) Entra a Street View

Abre **[Google Maps](https://www.google.com/maps)** → arrastra el **peoncito** a una calle de la ZMM.

### 4) Elige colonia

En el HUD: busca / elige colonia (prioriza **General Escobedo**).

### 5) Start trayecto — camina solo

Pulsa **Start trayecto**. El script:

1. Arma puntos desde calles prebaked (`data/roads_zmm.geojson`) / Overpass / rejilla.
2. Entra **1 vez** al inicio con URL (puede flash negro).
3. Luego **loop automático** sin que hagas clic: extensión gira Left/Right hacia el waypoint + ArrowUp.
4. Avanza el índice cuando haversine está cerca. **Space** = pausa/reanudar.
5. Progreso visible: `colonia · i/n · ext`.

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

## Extensión = requerida (no opcional)

| | Userscript solo | Userscript + extensión |
|---|---|---|
| Auto-walk / trayecto | ❌ Maps ignora teclas/clicks sintéticos | ✅ ArrowUp/Left/Right confiables |
| HUD | Rojo «INSTALA extensión» | Verde «ext OK · camina solo» |
| Banner amarillo Chrome | — | Breve al adjuntar debugger (normal; se suelta tras cada paso) |

API página: `PURIF_SCOUT_EXT.step({turnDeg})`, `stepForward()`, `turnLeft(n)`, `turnRight(n)`, `ping()`.

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
| **Space** | Sin trayecto: Auto-walk ON/OFF. Con trayecto: pausa/reanuda |
| **Z** / **Backspace** | Deshacer último pin |

ntfy sync sin cambios (`purif-zmm-campo-casca-v1`).

## Limitaciones

- Hay que estar en **Street View**.
- Sin extensión el panorama **no avanza** (HUD rojo).
- Entrada/recovery URL = flash negro (avisado).
- Colonias grandes se muestrean (máx. ~900 pts).

## Relacionado

- Extensión: `extension/` · zip: `extension-dist/purificadoras-scout-ext.zip`
- Script: `userscripts/purificadoras-scout.user.js`
- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
