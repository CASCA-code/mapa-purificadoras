# Extensión Chrome — Purificadoras Scout v1.5 (**REQUERIDA**)

Sin esta extensión **el auto-walk no se mueve**. Google Maps Street View ignora clicks/teclas sintéticas (*untrusted*). Solo `chrome.debugger` envía `ArrowUp` / `ArrowLeft` / `ArrowRight` confiables.

Companion del userscript Tampermonkey: **Purificadoras Scout v1.5+**.

---

## Instalación en 5 pasos (haz esto PRIMERO)

1. **Descarga** el zip:  
   https://github.com/CASCA-code/mapa-purificadoras/raw/main/extension-dist/purificadoras-scout-ext.zip  
   (o clona el repo y usa la carpeta `extension/`)
2. Descomprime el zip en una carpeta fija (ej. `~/purificadoras-scout-ext`).
3. Abre Chrome → `chrome://extensions` → activa **Modo de desarrollador**.
4. Pulsa **Cargar descomprimida** → elige esa carpeta (debe verse `manifest.json`).
5. Abre **[Google Maps](https://www.google.com/maps)** → Street View (peoncito). El HUD del userscript debe ponerse **verde: «ext OK · camina solo»**.

Luego actualiza el userscript y elige colonia → **Start trayecto**.

---

## ¿Qué hace?

- Escucha al userscript (`postMessage` / `PURIF_SCOUT_EXT.step({turnDeg})`).
- Adjunta el debugger a la pestaña de Maps, dispara teclas confiables, **desadjunta** al terminar el burst (banner amarillo breve).
- Teclas: `ArrowUp` (avanzar), `ArrowLeft` / `ArrowRight` (rumbo), opcional `KeyW`.

### API

```js
await PURIF_SCOUT_EXT.step({ turnDeg: -30 }); // negativo = izquierda
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
