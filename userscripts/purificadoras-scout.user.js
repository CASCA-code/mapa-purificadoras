// ==UserScript==
// @name         Purificadoras Scout SV (Street View)
// @namespace    https://casca-code.github.io/mapa-purificadoras/
// @version      1.0.0
// @description  Scout de campo sobre Google Maps Street View (sin Maps Platform / sin billing). Hotkeys → ntfy + export. Para Nicolás / Purificadoras ZMM.
// @author       CASCA-code
// @match        https://www.google.com/maps*
// @match        https://maps.google.com/*
// @match        https://www.google.com.mx/maps*
// @match        https://maps.google.com.mx/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_download
// @connect      ntfy.sh
// @connect      casca-code.github.io
// @run-at       document-idle
// @noframes
// ==/UserScript==

/* eslint-disable no-undef */
(function () {
  'use strict';

  /*
   * Purificadoras Scout — Tampermonkey sobre Street View de consumidor.
   * Sin API key de Maps Platform. Sync primario: ntfy (mismo topic que index.html).
   * localStorage en google.com NO se comparte con casca-code.github.io.
   */

  var NTFY_TOPIC = 'purif-zmm-campo-casca-v1';
  var LS_COMP = 'purificadoras_field_adds_v1';
  var LS_ANCLAS = 'purificadoras_anclas_v1';
  var LS_SESSION = 'purificadoras_scout_tm_session_v1';
  var MAP_BASE = 'https://casca-code.github.io/mapa-purificadoras/';
  var COMMENT_HALF_M = 30;
  var COMMENT_COLOR = '#db2777';
  var AUTO_MS = 1400;
  var FUENTE = 'scout_userscript';

  var SCOUT_HOTKEYS = {
    M: { kind: 'modelorama', layer: 'ancla_campo', name: 'Modelorama', label: 'Modelorama', color: '#ca8a04', primary: true },
    S: { kind: 'otro', layer: 'ancla_campo', name: 'Semáforo', nota_raw: 'Semáforo', label: 'Semáforo', color: '#64748b', primary: true },
    Y: { kind: 'purificadora', layer: 'competencia', name: 'Purificadora', label: 'Competencia / purificadora', color: '#0f766e' },
    E: { kind: 'express', layer: 'ancla_campo', name: 'Express', label: 'Express', color: '#ea580c' },
    P: { kind: 'iglesia', layer: 'ancla_campo', name: 'Iglesia', label: 'Iglesia', color: '#7c3aed' },
    I: { kind: 'escuela', layer: 'ancla_campo', name: 'Escuela', label: 'Escuela', color: '#2563eb' },
    H: { kind: 'otro', layer: 'ancla_campo', name: 'Hospital / otro', label: 'Hospital / otro', color: '#64748b' }
  };
  SCOUT_HOTKEYS.U = Object.assign({}, SCOUT_HOTKEYS.M, { label: 'Modelorama (alias U)' });

  var state = {
    inSV: false,
    lat: null,
    lng: null,
    heading: 0,
    autoWalk: false,
    autoTimer: null,
    sessionPins: [],
    commentOpen: false
  };

  /* ---------- utils ---------- */
  function uuid(prefix) {
    return prefix + '_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
  }
  function loadLS(key) {
    try { return JSON.parse(localStorage.getItem(key) || '[]'); }
    catch (e) { return []; }
  }
  function saveLS(key, arr) {
    try { localStorage.setItem(key, JSON.stringify(arr)); }
    catch (e) { /* quota / private mode */ }
  }
  function loadSession() {
    try {
      var raw = localStorage.getItem(LS_SESSION);
      if (raw) {
        var arr = JSON.parse(raw);
        if (Array.isArray(arr)) state.sessionPins = arr;
      }
    } catch (e) {}
  }
  function saveSession() {
    try { localStorage.setItem(LS_SESSION, JSON.stringify(state.sessionPins)); }
    catch (e) {}
  }

  function toast(msg) {
    var el = document.getElementById('purif-scout-toast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toast._tm);
    toast._tm = setTimeout(function () { el.classList.remove('show'); }, 2000);
  }

  function offsetLatLng(lat, lng, headingDeg, meters) {
    var R = 6378137;
    var rad = headingDeg * Math.PI / 180;
    var dLat = (meters * Math.cos(rad)) / R;
    var dLng = (meters * Math.sin(rad)) / (R * Math.cos(lat * Math.PI / 180));
    return { lat: lat + dLat * 180 / Math.PI, lng: lng + dLng * 180 / Math.PI };
  }

  /* ---------- URL / Street View parse ---------- */
  function parseFromUrl(href) {
    var url = href || location.href;
    var out = { inSV: false, lat: null, lng: null, heading: null };

    // Classic SV: /@lat,lng,3a,Yy,Hh,Tt
    var mSv = url.match(/@(-?\d+\.?\d*),(-?\d+\.?\d*),(\d+(?:\.\d+)?)a,([\d.]+)y,([\d.]+)h,([\d.]+)t/i);
    if (mSv) {
      out.inSV = true;
      out.lat = Number(mSv[1]);
      out.lng = Number(mSv[2]);
      out.heading = Number(mSv[5]);
      return out;
    }

    // Map center /@lat,lng,zoomz — not SV by itself
    var mMap = url.match(/@(-?\d+\.?\d*),(-?\d+\.?\d*),([\d.]+)z/i);
    if (mMap) {
      out.lat = Number(mMap[1]);
      out.lng = Number(mMap[2]);
    }

    // data=!3dLAT!4dLNG (common in SV / place URLs)
    var m34 = url.match(/!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)/);
    if (m34) {
      out.lat = Number(m34[1]);
      out.lng = Number(m34[2]);
    }

    // Street View markers in path
    if (/!1e1/.test(url) || /\/data=!3m\d+!1e1/.test(url) || /3a,[\d.]+y,/.test(url)) {
      out.inSV = true;
    }
    // Heading elsewhere: Nh before t, or !5d / !6d rarely
    var mH = url.match(/,([\d.]+)h,([\d.]+)t/i);
    if (mH && out.heading == null) out.heading = Number(mH[1]);

    // DOM heuristic: SV canvas / pegman active
    if (!out.inSV) {
      try {
        if (document.querySelector('canvas.widget-scene-canvas, button[jsaction*="streetview"], [aria-label*="Street View"], [aria-label*="Pegman"]')) {
          // weak signal — only if we already have coords looking like ZMM-ish or any
          if (out.lat != null) out.inSV = true;
        }
      } catch (e) {}
    }

    // Title / hash with streetview
    if (!out.inSV && /street.?view|vista\s+de\s+calle/i.test(document.title || '')) {
      out.inSV = true;
    }

    return out;
  }

  function refreshPose() {
    var p = parseFromUrl(location.href);
    var changed = false;
    if (p.lat != null && p.lng != null) {
      if (state.lat !== p.lat || state.lng !== p.lng) changed = true;
      state.lat = p.lat;
      state.lng = p.lng;
    }
    if (p.heading != null && isFinite(p.heading)) {
      state.heading = p.heading;
      changed = true;
    }
    if (p.inSV !== state.inSV) {
      state.inSV = p.inSV;
      changed = true;
    }
    // Extra: if URL has 3a pattern we're definitely in SV
    if (/@[^/]+,\d+(?:\.\d+)?a,/.test(location.href)) state.inSV = true;

    if (changed) updateHud();
    return p;
  }

  function hookHistory() {
    var wrap = function (type) {
      var orig = history[type];
      return function () {
        var ret = orig.apply(this, arguments);
        setTimeout(refreshPose, 30);
        return ret;
      };
    };
    try {
      history.pushState = wrap('pushState');
      history.replaceState = wrap('replaceState');
    } catch (e) {}
    window.addEventListener('popstate', function () { setTimeout(refreshPose, 30); });
    // Google often mutates URL without events — poll lightly
    setInterval(refreshPose, 800);
  }

  /* ---------- ntfy sync (PRIMARY) ---------- */
  function silentSync(payload) {
    var body = JSON.stringify(payload);
    var url = 'https://ntfy.sh/' + NTFY_TOPIC;

    // GM_xmlhttpRequest bypasses page CSP (preferred)
    if (typeof GM_xmlhttpRequest === 'function') {
      try {
        GM_xmlhttpRequest({
          method: 'POST',
          url: url,
          headers: {
            'Content-Type': 'application/json',
            'Title': payload.action || 'scout',
            'Tags': 'round_pushpin'
          },
          data: body,
          onload: function () {},
          onerror: function () { /* silent */ }
        });
        return true;
      } catch (e) {}
    }

    // Fallback fetch (may fail under Maps CSP)
    try {
      if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }))) {
        return true;
      }
    } catch (e) {}
    try {
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Title': payload.action || 'scout', 'Tags': 'round_pushpin' },
        body: body,
        mode: 'cors',
        keepalive: true
      }).catch(function () {});
      return true;
    } catch (e2) {
      return false;
    }
  }

  function destKeyForFeature(f) {
    var p = f.properties || {};
    if (p.layer === 'competencia' || p.kind === 'purificadora') return LS_COMP;
    return LS_ANCLAS;
  }

  function persistFeature(feat) {
    // Best-effort LS on google.com (NOT shared with Pages — backup only)
    var key = destKeyForFeature(feat);
    var arr = loadLS(key);
    var id = (feat.properties || {}).id;
    arr = arr.filter(function (x) { return (x.properties || {}).id !== id; });
    arr.push(feat);
    saveLS(key, arr);
    // PRIMARY sync path
    silentSync({ action: 'upsert', feature: feat });
  }

  function unpersistFeature(feat) {
    if (!feat) return;
    var key = destKeyForFeature(feat);
    var id = (feat.properties || {}).id;
    var arr = loadLS(key).filter(function (x) { return (x.properties || {}).id !== id; });
    saveLS(key, arr);
    if (id) silentSync({ action: 'delete', id: id, layer: (feat.properties || {}).layer || '' });
  }

  function makeFeature(def, lat, lng) {
    var isComp = def.layer === 'competencia';
    return {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [lng, lat] },
      properties: {
        id: uuid(isComp ? 'fa' : 'ancla'),
        kind: def.kind,
        name: def.name || def.label,
        nota_raw: def.nota_raw || '',
        accuracy_m: null,
        ts: new Date().toISOString(),
        fuente: FUENTE,
        status: 'inbox',
        layer: def.layer,
        pano_id: null
      }
    };
  }

  function makeCommentFeature(text, lat, lng, heading) {
    var a = offsetLatLng(lat, lng, heading, -COMMENT_HALF_M);
    var b = offsetLatLng(lat, lng, heading, COMMENT_HALF_M);
    return {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [[a.lng, a.lat], [lng, lat], [b.lng, b.lat]]
      },
      properties: {
        id: uuid('cz'),
        kind: 'comentario_zona',
        name: (text || '').slice(0, 80) || 'Comentario zona',
        nota_raw: text || '',
        comentario: text || '',
        accuracy_m: null,
        ts: new Date().toISOString(),
        fuente: FUENTE,
        status: 'inbox',
        layer: 'comentario_zona',
        heading: heading,
        pano_id: null
      }
    };
  }

  function needPose() {
    if (!state.inSV) {
      toast('Entra a Street View (arrastra el peoncito)');
      return false;
    }
    if (state.lat == null || state.lng == null) {
      toast('Sin coords aún — mueve un poco la vista');
      return false;
    }
    return true;
  }

  function dropPin(def) {
    if (!needPose()) return;
    var feat = makeFeature(def, state.lat, state.lng);
    state.sessionPins.push(feat);
    saveSession();
    persistFeature(feat);
    paintMiniPins();
    toast('📍 ' + (def.label || def.name));
  }

  function dropComment(text) {
    if (!needPose()) return;
    var t = String(text || '').trim();
    if (!t) { toast('Escribe un comentario'); return; }
    var feat = makeCommentFeature(t, state.lat, state.lng, state.heading || 0);
    state.sessionPins.push(feat);
    saveSession();
    persistFeature(feat);
    paintMiniPins();
    toast('💬 Zona guardada');
  }

  function undoPin() {
    if (!state.sessionPins.length) { toast('Nada que deshacer'); return; }
    var f = state.sessionPins.pop();
    saveSession();
    unpersistFeature(f);
    paintMiniPins();
    toast('Deshecho: ' + ((f.properties && f.properties.name) || 'pin'));
  }

  function downloadExport() {
    var comp = [];
    var anclas = [];
    state.sessionPins.forEach(function (f) {
      var layer = (f.properties || {}).layer;
      if (layer === 'competencia') comp.push(f);
      else anclas.push(f);
    });
    var payload = {
      exported_at: new Date().toISOString(),
      fuente: FUENTE,
      keys: {
        purificadoras_field_adds_v1: comp,
        purificadoras_anclas_v1: anclas
      }
    };
    var text = JSON.stringify(payload, null, 2);
    var d = new Date();
    var stamp = d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0');
    var name = 'purif-scout-tm-' + stamp + '.json';
    try {
      if (typeof GM_download === 'function') {
        GM_download({ url: 'data:application/json;charset=utf-8,' + encodeURIComponent(text), name: name });
        toast('JSON exportado');
        return;
      }
    } catch (e) {}
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
    a.download = name;
    document.documentElement.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 400);
    toast('JSON exportado');
  }

  function syncAllNtfy() {
    if (!state.sessionPins.length) { toast('Sin pines'); return; }
    var n = 0;
    state.sessionPins.forEach(function (f) {
      silentSync({ action: 'upsert', feature: f });
      n++;
    });
    toast('Sync ntfy: ' + n + ' upsert(s)');
  }

  /* ---------- auto-forward (Space) ---------- */
  function fireKey(code, key, keyCode) {
    var opts = { key: key, code: code, keyCode: keyCode, which: keyCode, bubbles: true, cancelable: true, view: window };
    try {
      document.dispatchEvent(new KeyboardEvent('keydown', opts));
      document.dispatchEvent(new KeyboardEvent('keyup', opts));
    } catch (e) {}
    try {
      window.dispatchEvent(new KeyboardEvent('keydown', opts));
    } catch (e2) {}
  }

  function clickForwardUi() {
    // Best-effort: click visible forward / next arrow in SV chrome
    var sels = [
      'button[aria-label*="Forward" i]',
      'button[aria-label*="Adelante" i]',
      'button[aria-label*="forward" i]',
      'button[jsaction*="forward"]',
      '[data-tooltip*="Forward" i]',
      '.widget-minimap-shim' // don't click this
    ];
    for (var i = 0; i < sels.length; i++) {
      if (sels[i].indexOf('minimap') >= 0) continue;
      var el = document.querySelector(sels[i]);
      if (el && typeof el.click === 'function') {
        try { el.click(); return true; } catch (e) {}
      }
    }
    // Click center-top of canvas (often the link arrow hotspot)
    try {
      var canvas = document.querySelector('canvas.widget-scene-canvas, canvas[class*="scene"]');
      if (canvas) {
        var r = canvas.getBoundingClientRect();
        var x = r.left + r.width / 2;
        var y = r.top + r.height * 0.42;
        ['mousedown', 'mouseup', 'click'].forEach(function (type) {
          canvas.dispatchEvent(new MouseEvent(type, {
            bubbles: true, cancelable: true, view: window,
            clientX: x, clientY: y, button: 0
          }));
        });
        return true;
      }
    } catch (e) {}
    return false;
  }

  function stepForward() {
    if (!state.inSV) return;
    fireKey('ArrowUp', 'ArrowUp', 38);
    clickForwardUi();
  }

  function setAutoWalk(on) {
    state.autoWalk = !!on;
    if (state.autoTimer) {
      clearInterval(state.autoTimer);
      state.autoTimer = null;
    }
    if (state.autoWalk) {
      state.autoTimer = setInterval(stepForward, AUTO_MS);
      toast('▶ Auto-walk ON');
    } else {
      toast('⏸ Auto-walk OFF');
    }
    updateHud();
  }

  /* ---------- UI ---------- */
  function injectCss() {
    if (document.getElementById('purif-scout-css')) return;
    var css = document.createElement('style');
    css.id = 'purif-scout-css';
    css.textContent = [
      '#purif-scout-root{all:initial;position:fixed;z-index:2147483646;pointer-events:none;',
      'font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:#1f1a14}',
      '#purif-scout-root *{box-sizing:border-box;font-family:inherit}',
      '#purif-scout-hud{position:fixed;top:72px;left:12px;pointer-events:auto;',
      'background:rgba(33,29,23,.92);color:#efe9db;padding:10px 12px;border-radius:12px;',
      'font-size:12px;line-height:1.35;max-width:260px;box-shadow:0 8px 24px rgba(0,0,0,.35);',
      'backdrop-filter:blur(6px)}',
      '#purif-scout-hud b{color:#fff}',
      '#purif-scout-hud .row{margin:2px 0}',
      '#purif-scout-hud kbd{display:inline-block;min-width:1.4em;text-align:center;',
      'padding:1px 5px;margin-right:4px;border-radius:4px;background:#7a0177;color:#fff;',
      'font:700 11px/1.4 ui-monospace,Menlo,monospace}',
      '#purif-scout-hud kbd.sec{background:#44403c}',
      '#purif-scout-hud .meta{opacity:.75;font-size:11px;margin-top:6px}',
      '#purif-scout-hud .badge{display:inline-block;padding:2px 7px;border-radius:999px;',
      'font-size:10px;font-weight:700;margin-bottom:6px}',
      '#purif-scout-hud .badge.on{background:#0f766e;color:#fff}',
      '#purif-scout-hud .badge.off{background:#57534e;color:#e7e5e4}',
      '#purif-scout-hud .badge.warn{background:#b45309;color:#fff}',
      '#purif-scout-hud .acts{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}',
      '#purif-scout-hud button{pointer-events:auto;cursor:pointer;border:0;border-radius:8px;',
      'padding:6px 8px;font:600 11px/1 system-ui;background:#f5efe3;color:#1f1a14}',
      '#purif-scout-hud button:hover{filter:brightness(1.06)}',
      '#purif-scout-mini{position:fixed;left:12px;bottom:12px;width:200px;height:168px;',
      'pointer-events:auto;border-radius:12px;overflow:hidden;',
      'box-shadow:0 8px 28px rgba(0,0,0,.4);border:2px solid #fffdf8;background:#e7e2d7}',
      '#purif-scout-mini .head{display:flex;align-items:center;justify-content:space-between;',
      'padding:4px 8px;background:rgba(33,29,23,.88);color:#efe9db;font:600 10px/1.2 system-ui}',
      '#purif-scout-mini .head a{color:#f9a8d4;text-decoration:none;font-weight:700}',
      '#purif-scout-mini canvas{display:block;width:100%;height:calc(100% - 22px);background:#d6d0c2}',
      '#purif-scout-toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(12px);',
      'background:rgba(33,29,23,.94);color:#fff;padding:10px 16px;border-radius:999px;',
      'font:600 13px/1.2 system-ui;opacity:0;pointer-events:none;transition:opacity .18s,transform .18s;',
      'z-index:2147483647;max-width:90vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
      '#purif-scout-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}',
      '#purif-scout-comment{display:none;position:fixed;inset:0;z-index:2147483647;',
      'background:rgba(0,0,0,.45);pointer-events:auto;align-items:center;justify-content:center}',
      '#purif-scout-comment.show{display:flex}',
      '#purif-scout-comment .card{background:#fffdf8;color:#1f1a14;border-radius:14px;',
      'padding:16px;width:min(360px,92vw);box-shadow:0 16px 40px rgba(0,0,0,.35)}',
      '#purif-scout-comment h2{margin:0 0 6px;font:700 16px/1.2 system-ui}',
      '#purif-scout-comment p{margin:0 0 10px;font-size:12px;color:#736b5e}',
      '#purif-scout-comment textarea{width:100%;min-height:72px;padding:8px;border:1px solid #e4ddcc;',
      'border-radius:8px;resize:vertical;font:14px/1.4 system-ui}',
      '#purif-scout-comment .btns{display:flex;gap:8px;margin-top:10px}',
      '#purif-scout-comment button{cursor:pointer;border:0;border-radius:8px;padding:9px 12px;',
      'font:600 13px system-ui}',
      '#purif-scout-comment .ok{background:#7a0177;color:#fff}',
      '#purif-scout-comment .cancel{background:#ebe5d8;color:#1f1a14}',
      '#purif-scout-root.hidden-ui #purif-scout-hud,',
      '#purif-scout-root.hidden-ui #purif-scout-mini{display:none}'
    ].join('');
    (document.head || document.documentElement).appendChild(css);
  }

  function buildUi() {
    if (document.getElementById('purif-scout-root')) return;
    injectCss();
    var root = document.createElement('div');
    root.id = 'purif-scout-root';
    root.innerHTML = [
      '<div id="purif-scout-hud">',
      '  <div class="badge off" id="purif-scout-badge">Mapa</div>',
      '  <div class="row"><kbd>M</kbd><b>Modelorama</b></div>',
      '  <div class="row"><kbd>S</kbd><b>Semáforo</b></div>',
      '  <div class="row"><kbd class="sec">Y</kbd>Comp · <kbd class="sec">E</kbd>Express · <kbd class="sec">P</kbd>Iglesia</div>',
      '  <div class="row"><kbd class="sec">I</kbd>Escuela · <kbd class="sec">H</kbd>Hospital · <kbd>C</kbd>Comentario</div>',
      '  <div class="row"><kbd class="sec">Space</kbd>Auto-walk · <kbd class="sec">Z</kbd>Deshacer</div>',
      '  <div class="meta" id="purif-scout-meta">—</div>',
      '  <div class="acts">',
      '    <button type="button" id="purif-scout-export" title="Descargar JSON sesión">Export</button>',
      '    <button type="button" id="purif-scout-sync" title="Reenviar upserts ntfy">Sync ntfy</button>',
      '    <button type="button" id="purif-scout-hide" title="Ocultar HUD">Ocultar</button>',
      '  </div>',
      '</div>',
      '<div id="purif-scout-mini">',
      '  <div class="head"><span>Scout peg</span><a id="purif-scout-openmap" href="' + MAP_BASE + '" target="_blank" rel="noopener">Abrir mapa</a></div>',
      '  <canvas id="purif-scout-canvas" width="196" height="146"></canvas>',
      '</div>',
      '<div id="purif-scout-toast" role="status" aria-live="polite"></div>',
      '<div id="purif-scout-comment" role="dialog" aria-modal="true">',
      '  <div class="card">',
      '    <h2>Comentario de zona</h2>',
      '    <p>Línea ~60 m según el heading actual. Se sincroniza por ntfy al mapa principal.</p>',
      '    <textarea id="purif-scout-comment-text" maxlength="500" placeholder="ej. buen flujo / semáforo lento / fachada viable…"></textarea>',
      '    <div class="btns">',
      '      <button type="button" class="ok" id="purif-scout-comment-ok">Guardar</button>',
      '      <button type="button" class="cancel" id="purif-scout-comment-cancel">Cancelar</button>',
      '    </div>',
      '  </div>',
      '</div>'
    ].join('');
    document.documentElement.appendChild(root);

    document.getElementById('purif-scout-export').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation(); downloadExport();
    });
    document.getElementById('purif-scout-sync').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation(); syncAllNtfy();
    });
    document.getElementById('purif-scout-hide').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      root.classList.add('hidden-ui');
      toast('HUD oculto — recarga o F5 para verlo');
    });
    document.getElementById('purif-scout-comment-ok').addEventListener('click', function () {
      var t = (document.getElementById('purif-scout-comment-text').value || '').trim();
      closeComment();
      dropComment(t);
    });
    document.getElementById('purif-scout-comment-cancel').addEventListener('click', closeComment);
  }

  function openComment() {
    state.commentOpen = true;
    var gate = document.getElementById('purif-scout-comment');
    var ta = document.getElementById('purif-scout-comment-text');
    if (gate) gate.classList.add('show');
    if (ta) { ta.value = ''; setTimeout(function () { try { ta.focus(); } catch (e) {} }, 40); }
  }
  function closeComment() {
    state.commentOpen = false;
    var gate = document.getElementById('purif-scout-comment');
    if (gate) gate.classList.remove('show');
  }

  function updateHud() {
    var badge = document.getElementById('purif-scout-badge');
    var meta = document.getElementById('purif-scout-meta');
    var link = document.getElementById('purif-scout-openmap');
    if (!badge || !meta) return;
    if (state.inSV) {
      badge.textContent = state.autoWalk ? 'SV · auto ▶' : 'Street View';
      badge.className = 'badge ' + (state.autoWalk ? 'on' : 'on');
    } else {
      badge.textContent = 'No SV — arrastra peoncito';
      badge.className = 'badge warn';
    }
    var lat = state.lat != null ? state.lat.toFixed(6) : '—';
    var lng = state.lng != null ? state.lng.toFixed(6) : '—';
    var h = (state.heading != null && isFinite(state.heading)) ? Math.round(state.heading) + '°' : '—';
    meta.textContent = lat + ', ' + lng + ' · h ' + h + ' · ' + state.sessionPins.length + ' pin(es)';
    if (link && state.lat != null && state.lng != null) {
      link.href = MAP_BASE + '#map=' + Math.max(16, 17) + '/' + state.lat.toFixed(5) + '/' + state.lng.toFixed(5);
    }
    paintMiniPins();
  }

  function paintMiniPins() {
    var canvas = document.getElementById('purif-scout-canvas');
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext('2d');
    var w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#d6d0c2';
    ctx.fillRect(0, 0, w, h);

    // Simple local mercator around current pose
    var clat = state.lat != null ? state.lat : 25.836;
    var clng = state.lng != null ? state.lng : -100.371;
    var span = 0.004; // ~400 m
    function xy(lat, lng) {
      var x = ((lng - (clng - span)) / (2 * span)) * w;
      var y = ((clat + span - lat) / (2 * span)) * h;
      return { x: x, y: y };
    }

    // grid
    ctx.strokeStyle = 'rgba(0,0,0,.08)';
    ctx.lineWidth = 1;
    for (var g = 1; g < 4; g++) {
      ctx.beginPath();
      ctx.moveTo((w / 4) * g, 0); ctx.lineTo((w / 4) * g, h); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, (h / 4) * g); ctx.lineTo(w, (h / 4) * g); ctx.stroke();
    }

    state.sessionPins.forEach(function (f) {
      var p = f.properties || {};
      var g2 = f.geometry;
      if (!g2) return;
      if (g2.type === 'LineString') {
        var coords = g2.coordinates || [];
        if (coords.length < 2) return;
        ctx.beginPath();
        coords.forEach(function (c, i) {
          var pt = xy(c[1], c[0]);
          if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        });
        ctx.strokeStyle = COMMENT_COLOR;
        ctx.lineWidth = 3;
        ctx.stroke();
      } else if (g2.type === 'Point') {
        var c = g2.coordinates;
        var pt = xy(c[1], c[0]);
        var col = '#64748b';
        for (var k in SCOUT_HOTKEYS) {
          if (k === 'U') continue;
          var hk = SCOUT_HOTKEYS[k];
          if (hk.kind === p.kind && hk.layer === p.layer) {
            if (p.kind === 'otro' && hk.nota_raw && p.nota_raw === hk.nota_raw) { col = hk.color; break; }
            if (p.kind !== 'otro') { col = hk.color; break; }
          }
        }
        if (p.layer === 'competencia') col = '#0f766e';
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    });

    // peg + heading
    var peg = xy(clat, clng);
    var rad = ((state.heading || 0) - 90) * Math.PI / 180;
    ctx.save();
    ctx.translate(peg.x, peg.y);
    ctx.rotate(rad + Math.PI / 2);
    ctx.beginPath();
    ctx.moveTo(0, -10);
    ctx.lineTo(7, 8);
    ctx.lineTo(0, 4);
    ctx.lineTo(-7, 8);
    ctx.closePath();
    ctx.fillStyle = '#7a0177';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();
  }

  /* ---------- hotkeys ---------- */
  function onKeyDown(ev) {
    var tag = (ev.target && ev.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (ev.target && ev.target.isContentEditable)) return;
    if (state.commentOpen) {
      if (ev.key === 'Escape') { closeComment(); ev.preventDefault(); }
      return;
    }

    if (ev.code === 'Space' || ev.key === ' ') {
      // Only hijack Space while in SV so Maps search isn't broken on map view
      if (!state.inSV) return;
      ev.preventDefault();
      ev.stopPropagation();
      setAutoWalk(!state.autoWalk);
      return;
    }
    if (ev.key === 'Backspace' || ev.key === 'z' || ev.key === 'Z') {
      if (!state.inSV && !state.sessionPins.length) return;
      if (ev.key === 'Backspace') ev.preventDefault();
      undoPin();
      return;
    }
    var key = (ev.key || '').toUpperCase();
    if (key === 'C') {
      if (!state.inSV) return;
      ev.preventDefault();
      if (!needPose()) return;
      openComment();
      return;
    }
    if (SCOUT_HOTKEYS[key]) {
      if (!state.inSV) return;
      ev.preventDefault();
      dropPin(SCOUT_HOTKEYS[key]);
    }
  }

  /* ---------- boot ---------- */
  function boot() {
    loadSession();
    buildUi();
    hookHistory();
    refreshPose();
    document.addEventListener('keydown', onKeyDown, true);
    toast('Scout Purificadoras listo · sin API key');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
