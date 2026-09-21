# Extensión Chrome — flecha SV (fallback Scout)

Companion opcional del userscript Tampermonkey **Purificadoras Scout v1.4+**.

## ¿Para qué?

Google Maps Street View **ignora** `KeyboardEvent` / clicks sintéticos *untrusted*.
Las flechas blancas del camino están dibujadas en WebGL (no hay botón HTML "Forward").

El userscript intenta:
1. Click en overlays DOM si existen
2. Pointer clicks en la zona típica del chevron
3. `ArrowUp` sintético al canvas
4. Pedir a **esta extensión** un `ArrowUp` **confiable** vía `chrome.debugger`

Solo necesitas la extensión si el auto-walk del userscript **no avanza** solo.

## Instalación (Chrome / Edge)

1. Abre `chrome://extensions`
2. Activa **Modo de desarrollador**
3. **Cargar descomprimida** → elige esta carpeta `extension/`
4. Confirma permisos (debugger + Maps)
5. Abre `https://www.google.com/maps` → Street View (peoncito)
6. El HUD del userscript puede mostrar que la extensión está lista
7. Al usar **Space** / **▶ Siguiente**, si el userscript pide ayuda, Chrome mostrará
   un banner amarillo breve ("debugging this browser") — es normal y se quita solo

## Seguridad

- No envía datos a servidores externos
- Solo despacha `ArrowUp` en pestañas de Google Maps
- No lee el contenido del panorama ni pines

## Relación con el userscript

Instala primero:
https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js

Docs: `docs/SCOUT_USERSCRIPT.md`
