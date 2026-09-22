# Extensión Chrome — Purificadoras Scout v1.6.1 (**REQUERIDA**)

Sin esta extensión **el auto-walk no se mueve**. Google Maps Street View ignora clicks/teclas sintéticas (*untrusted*). Solo `chrome.debugger` envía `ArrowUp` / `ArrowLeft` / `ArrowRight` confiables.

Companion del userscript Tampermonkey: **Purificadoras Scout v1.9.0+** (cobertura calles + **rota POV antes de avanzar**; la extensión es el pasito Left/Right/Up confiable).

---

## Instalación en 5 pasos (haz esto PRIMERO)

1. **Descarga** el zip:  
   https://github.com/CASCA-code/mapa-purificadoras/raw/main/extension-dist/purificadoras-scout-ext.zip  
   (o clona el repo y usa la carpeta `extension/`)
2. Descomprime el zip en una carpeta fija (ej. `~/purificadoras-scout-ext`).
3. Abre Chrome → `chrome://extensions` → activa **Modo de desarrollador**.
4. Pulsa **Cargar descomprimida** → elige esa carpeta (debe verse `manifest.json`).
5. Abre **[Google Maps](https://www.google.com/maps)** → Street View (peoncito). El HUD del userscript debe ponerse **verde: «ext OK»** y el chip `v… · ext 1.6.1` (amarillo = zip viejo → Recargar).

Luego actualiza el userscript y elige colonia → **Start trayecto**.

---

## Changelog corto

- **v1.6.1:** bump de versión para que el HUD del userscript detecte zip desactualizado (`EXPECT_EXT`). Misma API/bridge que 1.6.0.
- **v1.6.0:** un burst debugger por step; origin check; timeout 12s; ~9°/key; settle 320 ms.

## ¿Qué hace?

- Escucha al userscript (**postMessage + reqId** primario; CustomEvent solo legacy). `PURIF_SCOUT_EXT.step({turnDeg})` también usa postMessage por debajo.
- **v1.6.1:** un burst debugger por step lógico; origin check en content script; timeout inject 12s alineado con userscript.
- Adjunta el debugger a la pestaña de Maps, dispara teclas confiables, **desadjunta** al terminar el burst (banner amarillo breve).
- **v1.6.1:** ~9° por tecla de giro; si `|turnDeg|≥12` envía **solo giros**, espera ~320 ms (POV settle), **luego** ArrowUp — un solo attach para turn+wait+Up. `forward:false` = solo rotar POV. Backup: drag horizontal del mouse en el centro del viewport si `|turnDeg|` grande.
- Teclas: `ArrowUp` (avanzar), `ArrowLeft` / `ArrowRight` (rumbo), opcional `KeyW`.

### API

```js
await PURIF_SCOUT_EXT.step({ turnDeg: -30 }); // negativo = izquierda
await PURIF_SCOUT_EXT.step({ turnDeg: -90, forward: false }); // solo POV
PURIF_SCOUT_EXT.stepForward();
PURIF_SCOUT_EXT.turnLeft(2);
PURIF_SCOUT_EXT.turnRight(1);
PURIF_SCOUT_EXT.ping();
```

También `postMessage` (`source: 'purif-scout'`, types: `step` / `stepForward` / `turnLeft` / `turnRight` / `ping`).

---

## Banner amarillo

Chrome muestra «debugging this browser» mientras el debugger está adjunto. En v1.5 se adjunta **solo durante cada paso** y se suelta después.

## Seguridad

- No envía datos a servidores externos.
- Solo despacha teclas en pestañas de Google Maps.
- No lee el panorama ni los pines.

## Userscript

https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js

Docs: `docs/SCOUT_USERSCRIPT.md`
