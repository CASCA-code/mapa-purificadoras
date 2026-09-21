// ==UserScript==
// @name         Purificadoras Scout SV (Street View)
// @namespace    https://casca-code.github.io/mapa-purificadoras/
// @version      1.2.0
// @description  Scout de campo sobre Google Maps Street View (sin Maps Platform / sin billing). Hotkeys + trayecto por colonia (prebaked OSM + Overpass fallback). Para Nicolás / Purificadoras ZMM.
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
// @connect      raw.githubusercontent.com
// @connect      overpass-api.de
// @connect      overpass.kumi.systems
// @connect      overpass.openstreetmap.ru
// @connect      router.project-osrm.org
// @run-at       document-idle
// @noframes
// ==/UserScript==

/* eslint-disable no-undef */
(function () {
  'use strict';

  /*
   * Purificadoras Scout — Tampermonkey sobre Street View de consumidor.
   * Sin API key de Maps Platform. Sync primario: ntfy (mismo topic que index.html).
   * v1.1: auto-walk robusto + picker de colonia + trayecto OSM (Overpass) sin billing.
   * v1.2: prebaked roads_zmm.geojson + Overpass hard-timeout/mirrors + grid fallback + fuzzy colonia.
   */

  var NTFY_TOPIC = 'purif-zmm-campo-casca-v1';
  var LS_COMP = 'purificadoras_field_adds_v1';
  var LS_ANCLAS = 'purificadoras_anclas_v1';
  var LS_SESSION = 'purificadoras_scout_tm_session_v1';
  var LS_SPEED = 'purificadoras_scout_tm_speed_ms';
  var MAP_BASE = 'https://casca-code.github.io/mapa-purificadoras/';
  var COLONIAS_URLS = [
    MAP_BASE + 'data/colonias.geojson',
    'https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/data/colonias.geojson'
  ];
  var OVERPASS_URLS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.openstreetmap.ru/api/interpreter'
  ];
  var ROADS_URLS = [
    MAP_BASE + 'data/roads_zmm.geojson',
    'https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/data/roads_zmm.geojson'
  ];
  var OVERPASS_HARD_MS = 12000; // per mirror — never hang on "consultando…"
  var OVERPASS_QUERY_TIMEOUT = 15;
  var GRID_STEP_M = 50;
  var MIN_ROUTE_PTS = 4;
  var COMMENT_HALF_M = 30;
  var COMMENT_COLOR = '#db2777';
  var DEFAULT_AUTO_MS = 1400;
  var STEP_M = 20;
  var SV_WAIT_MS = 5500;
  var DEAD_END_FAILS = 4;
  var FUENTE = 'scout_userscript';
  var ESCOBEDO = 'General Escobedo';

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
    autoMs: DEFAULT_AUTO_MS,
    autoFailStreak: 0,
    autoLastPose: null,
    sessionPins: [],
    commentOpen: false,
    colonias: [],
    coloniasLoaded: false,
    coloniasLoading: false,
    selectedColonia: null,
    route: null, // { name, points:[{lat,lng}], i, paused, status, skipped }
    routeTimer: null,
    routeBusy: false,
    roadsFc: null,
    roadsLoading: null,
    trayectoBuilding: false,
    lastTrayectoError: null
  };

  try {
    var savedSpeed = Number(GM_getValue && GM_getValue(LS_SPEED, DEFAULT_AUTO_MS));
    if (isFinite(savedSpeed) && savedSpeed >= 600 && savedSpeed <= 5000) state.autoMs = savedSpeed;
  } catch (e) {}

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
    toast._tm = setTimeout(function () { el.classList.remove('show'); }, 2200);
  }

  function offsetLatLng(lat, lng, headingDeg, meters) {
    var R = 6378137;
    var rad = headingDeg * Math.PI / 180;
    var dLat = (meters * Math.cos(rad)) / R;
    var dLng = (meters * Math.sin(rad)) / (R * Math.cos(lat * Math.PI / 180));
    return { lat: lat + dLat * 180 / Math.PI, lng: lng + dLng * 180 / Math.PI };
  }

  function haversineM(aLat, aLng, bLat, bLng) {
    var R = 6371000;
    var toR = Math.PI / 180;
    var dLat = (bLat - aLat) * toR;
    var dLng = (bLng - aLng) * toR;
    var s = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(aLat * toR) * Math.cos(bLat * toR) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(s)));
  }

  function bearingDeg(aLat, aLng, bLat, bLng) {
    var toR = Math.PI / 180;
    var y = Math.sin((bLng - aLng) * toR) * Math.cos(bLat * toR);
    var x = Math.cos(aLat * toR) * Math.sin(bLat * toR) -
      Math.sin(aLat * toR) * Math.cos(bLat * toR) * Math.cos((bLng - aLng) * toR);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  }

  function pointInRing(lng, lat, ring) {
    var inside = false;
    for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      var xi = ring[i][0], yi = ring[i][1];
      var xj = ring[j][0], yj = ring[j][1];
      var intersect = ((yi > lat) !== (yj > lat)) &&
        (lng < (xj - xi) * (lat - yi) / ((yj - yi) || 1e-12) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }

  function pointInPolygon(lng, lat, geom) {
    if (!geom) return false;
    var polys = geom.type === 'Polygon' ? [geom.coordinates]
      : geom.type === 'MultiPolygon' ? geom.coordinates : null;
    if (!polys) return false;
    for (var p = 0; p < polys.length; p++) {
      var rings = polys[p];
      if (!rings || !rings.length) continue;
      if (!pointInRing(lng, lat, rings[0])) continue;
      var hole = false;
      for (var h = 1; h < rings.length; h++) {
        if (pointInRing(lng, lat, rings[h])) { hole = true; break; }
      }
      if (!hole) return true;
    }
    return false;
  }

  function geomBbox(geom) {
    var minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
    function walk(c) {
      if (!c) return;
      if (typeof c[0] === 'number') {
        minLng = Math.min(minLng, c[0]); maxLng = Math.max(maxLng, c[0]);
        minLat = Math.min(minLat, c[1]); maxLat = Math.max(maxLat, c[1]);
        return;
      }
      for (var i = 0; i < c.length; i++) walk(c[i]);
    }
    walk(geom && geom.coordinates);
    return { south: minLat, west: minLng, north: maxLat, east: maxLng };
  }

  function gmRequest(opts) {
    return new Promise(function (resolve, reject) {
      if (typeof GM_xmlhttpRequest !== 'function') {
        reject(new Error('GM_xmlhttpRequest unavailable'));
        return;
      }
      GM_xmlhttpRequest({
        method: opts.method || 'GET',
        url: opts.url,
        headers: opts.headers || {},
        data: opts.data || null,
        timeout: opts.timeout || 60000,
        onload: function (res) {
          if (res.status >= 200 && res.status < 300) resolve(res);
          else reject(new Error('HTTP ' + res.status + ' ' + opts.url));
        },
        onerror: function () { reject(new Error('network ' + opts.url)); },
        ontimeout: function () { reject(new Error('timeout ' + opts.url)); }
      });
    });
  }

  function fetchTextFirst(urls) {
    var i = 0;
    function next() {
      if (i >= urls.length) return Promise.reject(new Error('all urls failed'));
      var url = urls[i++];
      return gmRequest({ url: url, method: 'GET', timeout: 45000 })
        .then(function (res) { return res.responseText; })
        .catch(function () { return next(); });
    }
    return next();
  }

  function withHardTimeout(promise, ms, label) {
    return new Promise(function (resolve, reject) {
      var settled = false;
      var timer = setTimeout(function () {
        if (settled) return;
        settled = true;
        reject(new Error('timeout duro ' + ms + 'ms' + (label ? ' · ' + label : '')));
      }, ms);
      promise.then(function (v) {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(v);
      }, function (err) {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        reject(err);
      });
    });
  }

  function normalizeText(s) {
    return String(s || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function fuzzyScore(query, blob) {
    var q = normalizeText(query);
    var b = normalizeText(blob);
    if (!q) return 1;
    if (b.indexOf(q) >= 0) return 100;
    var tokens = q.split(' ').filter(function (t) { return t.length >= 2; });
    if (!tokens.length) return b.indexOf(q) >= 0 ? 50 : 0;
    var hit = 0;
    for (var i = 0; i < tokens.length; i++) {
      if (b.indexOf(tokens[i]) >= 0) hit++;
    }
    var ratio = hit / tokens.length;
    // Prefer Escobedo / common aliases lightly via caller sort; score is match quality
    return Math.round(ratio * 80) + (hit === tokens.length ? 15 : 0);
  }

  /* ---------- URL / Street View parse ---------- */
  function parseFromUrl(href) {
    var url = href || location.href;
    var out = { inSV: false, lat: null, lng: null, heading: null };

    var mSv = url.match(/@(-?\d+\.?\d*),(-?\d+\.?\d*),(\d+(?:\.\d+)?)a,([\d.]+)y,([\d.]+)h,([\d.]+)t/i);
    if (mSv) {
      out.inSV = true;
      out.lat = Number(mSv[1]);
      out.lng = Number(mSv[2]);
      out.heading = Number(mSv[5]);
      return out;
    }

    var mMap = url.match(/@(-?\d+\.?\d*),(-?\d+\.?\d*),([\d.]+)z/i);
    if (mMap) {
      out.lat = Number(mMap[1]);
      out.lng = Number(mMap[2]);
    }

    var m34 = url.match(/!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)/);
    if (m34) {
      out.lat = Number(m34[1]);
      out.lng = Number(m34[2]);
    }

    if (/!1e1/.test(url) || /\/data=!3m\d+!1e1/.test(url) || /3a,[\d.]+y,/.test(url) || /map_action=pano/i.test(url)) {
      out.inSV = true;
    }
    var mH = url.match(/,([\d.]+)h,([\d.]+)t/i);
    if (mH && out.heading == null) out.heading = Number(mH[1]);
    var mHead = url.match(/[?&]heading=(-?[\d.]+)/i);
    if (mHead && out.heading == null) out.heading = Number(mHead[1]);
    var mVp = url.match(/[?&]viewpoint=(-?\d+\.?\d*),(-?\d+\.?\d*)/i);
    if (mVp) {
      out.lat = Number(mVp[1]);
      out.lng = Number(mVp[2]);
      out.inSV = true;
    }

    if (!out.inSV) {
      try {
        if (document.querySelector('canvas.widget-scene-canvas, button[jsaction*="streetview"], [aria-label*="Street View"], [aria-label*="Pegman"]')) {
          if (out.lat != null) out.inSV = true;
        }
      } catch (e) {}
    }
    if (!out.inSV && /street.?view|vista\s+de\s+calle/i.test(document.title || '')) {
      out.inSV = true;
    }
    return out;
  }

  function poseKey() {
    if (state.lat == null || state.lng == null) return '';
    return state.lat.toFixed(5) + ',' + state.lng.toFixed(5);
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
    if (/@[^/]+,\d+(?:\.\d+)?a,/.test(location.href) || /map_action=pano/i.test(location.href)) {
      state.inSV = true;
    }
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
    setInterval(refreshPose, 800);
  }

  /* ---------- ntfy sync (PRIMARY) ---------- */
  function silentSync(payload) {
    var body = JSON.stringify(payload);
    var url = 'https://ntfy.sh/' + NTFY_TOPIC;
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
          onerror: function () {}
        });
        return true;
      } catch (e) {}
    }
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
    var key = destKeyForFeature(feat);
    var arr = loadLS(key);
    var id = (feat.properties || {}).id;
    arr = arr.filter(function (x) { return (x.properties || {}).id !== id; });
    arr.push(feat);
    saveLS(key, arr);
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

  /* ---------- auto-forward (Space) — improved ---------- */
  function fireKey(code, key, keyCode) {
    var targets = [];
    try {
      var canvas = document.querySelector('canvas.widget-scene-canvas, canvas[class*="scene"], canvas');
      if (canvas) targets.push(canvas);
    } catch (e) {}
    targets.push(document.activeElement || document.body);
    targets.push(document.body);
    targets.push(document.documentElement);
    targets.push(window);

    var seen = [];
    targets.forEach(function (t) {
      if (!t || seen.indexOf(t) >= 0) return;
      seen.push(t);
      try {
        if (t.focus && t !== window) t.focus({ preventScroll: true });
      } catch (e0) {}
      ['keydown', 'keypress', 'keyup'].forEach(function (type) {
        try {
          var ev = new KeyboardEvent(type, {
            key: key, code: code, keyCode: keyCode, which: keyCode,
            bubbles: true, cancelable: true, view: window
          });
          try { Object.defineProperty(ev, 'keyCode', { get: function () { return keyCode; } }); } catch (e1) {}
          try { Object.defineProperty(ev, 'which', { get: function () { return keyCode; } }); } catch (e2) {}
          t.dispatchEvent(ev);
        } catch (e3) {}
      });
    });
  }

  function clickForwardUi() {
    var sels = [
      'button[aria-label*="Forward" i]',
      'button[aria-label*="Adelante" i]',
      'button[aria-label*="forward" i]',
      'button[aria-label*="Siguiente" i]',
      'button[aria-label*="Next" i]',
      'button[jsaction*="forward"]',
      '[role="button"][aria-label*="Forward" i]',
      '[role="button"][aria-label*="Adelante" i]',
      'button[data-tooltip*="Forward" i]',
      'button[data-tooltip*="Adelante" i]'
    ];
    for (var i = 0; i < sels.length; i++) {
      var el = null;
      try { el = document.querySelector(sels[i]); } catch (e) {}
      if (el && typeof el.click === 'function') {
        try { el.click(); return 'btn:' + sels[i]; } catch (e2) {}
      }
    }
    // SVG / path chevrons near bottom of SV chrome
    try {
      var candidates = document.querySelectorAll('[jsaction*="pane.streetview"], [jsaction*="streetview"], button');
      for (var j = 0; j < candidates.length; j++) {
        var c = candidates[j];
        var al = ((c.getAttribute('aria-label') || '') + ' ' + (c.getAttribute('data-tooltip') || '')).toLowerCase();
        if (/forward|adelante|siguiente|next|avancer/.test(al)) {
          c.click();
          return 'aria-scan';
        }
      }
    } catch (e3) {}

    try {
      var canvas = document.querySelector('canvas.widget-scene-canvas, canvas[class*="scene"]');
      if (canvas) {
        var r = canvas.getBoundingClientRect();
        var spots = [
          [0.5, 0.42],
          [0.5, 0.38],
          [0.5, 0.55],
          [0.5, 0.62]
        ];
        for (var s = 0; s < spots.length; s++) {
          var x = r.left + r.width * spots[s][0];
          var y = r.top + r.height * spots[s][1];
          ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(function (type) {
            try {
              canvas.dispatchEvent(new MouseEvent(type, {
                bubbles: true, cancelable: true, view: window,
                clientX: x, clientY: y, button: 0
              }));
            } catch (e4) {}
          });
        }
        return 'canvas-hotspot';
      }
    } catch (e5) {}
    return null;
  }

  function waitPoseChange(prevKey, timeoutMs) {
    return new Promise(function (resolve) {
      var start = Date.now();
      var iv = setInterval(function () {
        refreshPose();
        var now = poseKey();
        if (now && now !== prevKey) {
          clearInterval(iv);
          resolve(true);
          return;
        }
        if (Date.now() - start >= timeoutMs) {
          clearInterval(iv);
          resolve(false);
        }
      }, 180);
    });
  }

  function stepForwardAsync() {
    if (state.commentOpen) return Promise.resolve(false);
    if (state.route && !state.route.paused) return Promise.resolve(false);
    if (!state.inSV) return Promise.resolve(false);

    var prev = poseKey();
    // Method A: ArrowUp on canvas/document (works when SV has keyboard focus)
    fireKey('ArrowUp', 'ArrowUp', 38);
    return waitPoseChange(prev, Math.min(900, state.autoMs * 0.55)).then(function (ok) {
      if (ok) { state._lastWalkMethod = 'ArrowUp'; return true; }
      // Method B: click forward UI / canvas link arrow
      prev = poseKey();
      var how = clickForwardUi();
      return waitPoseChange(prev, Math.min(1100, state.autoMs * 0.7)).then(function (ok2) {
        if (ok2) { state._lastWalkMethod = how || 'click'; return true; }
        // Method C: retry ArrowUp once more after brief pause
        prev = poseKey();
        fireKey('ArrowUp', 'ArrowUp', 38);
        return waitPoseChange(prev, 700).then(function (ok3) {
          if (ok3) state._lastWalkMethod = 'ArrowUp-retry';
          return ok3;
        });
      });
    });
  }

  function autoWalkTick() {
    if (!state.autoWalk || state.commentOpen) return;
    if (state.route && !state.route.paused) return;
    if (state._autoBusy) return;
    state._autoBusy = true;
    stepForwardAsync().then(function (moved) {
      state._autoBusy = false;
      if (moved) {
        state.autoFailStreak = 0;
        updateHud();
      } else {
        state.autoFailStreak = (state.autoFailStreak || 0) + 1;
        updateHud();
        if (state.autoFailStreak >= DEAD_END_FAILS) {
          setAutoWalk(false);
          toast('⏹ Auto-walk: callejón sin salida / sin avance');
        }
      }
    }).catch(function () { state._autoBusy = false; });
  }

  function setAutoWalk(on) {
    state.autoWalk = !!on;
    state.autoFailStreak = 0;
    if (state.autoTimer) {
      clearInterval(state.autoTimer);
      state.autoTimer = null;
    }
    if (state.autoWalk) {
      // Don't steal focus from comment / HUD inputs
      if (state.commentOpen) {
        state.autoWalk = false;
        toast('Cierra el comentario antes de auto-walk');
        updateHud();
        return;
      }
      state.autoTimer = setInterval(autoWalkTick, state.autoMs);
      setTimeout(autoWalkTick, 120);
      toast('▶ Auto-walk ON (' + (state.autoMs / 1000).toFixed(1) + 's)');
    } else {
      toast('⏸ Auto-walk OFF');
    }
    updateHud();
  }

  function setAutoMs(ms) {
    ms = Math.max(600, Math.min(5000, Number(ms) || DEFAULT_AUTO_MS));
    state.autoMs = ms;
    try { if (typeof GM_setValue === 'function') GM_setValue(LS_SPEED, ms); } catch (e) {}
    if (state.autoWalk) {
      setAutoWalk(false);
      setAutoWalk(true);
    }
    if (state.route && !state.route.paused && state.routeTimer) {
      // restart route interval with new speed
      clearInterval(state.routeTimer);
      state.routeTimer = setInterval(routeTick, state.autoMs);
    }
    updateHud();
  }

  /* ---------- colonias + route builder ---------- */
  function coloniaLabel(ft) {
    var p = ft.properties || {};
    var mun = p.municipio || '';
    var col = p.colonia || p.colonia_raw || '?';
    var rank = p.rank != null ? '#' + p.rank + ' · ' : '';
    return rank + col + ' (' + mun + ')';
  }

  function sortColonias(list) {
    return list.slice().sort(function (a, b) {
      var am = (a.properties || {}).municipio || '';
      var bm = (b.properties || {}).municipio || '';
      var ae = am === ESCOBEDO ? 0 : 1;
      var be = bm === ESCOBEDO ? 0 : 1;
      if (ae !== be) return ae - be;
      var ar = Number((a.properties || {}).rank) || 9999;
      var br = Number((b.properties || {}).rank) || 9999;
      if (ar !== br) return ar - br;
      return String((a.properties || {}).colonia || '').localeCompare(String((b.properties || {}).colonia || ''), 'es');
    });
  }

  function loadColonias() {
    if (state.coloniasLoaded || state.coloniasLoading) {
      return Promise.resolve(state.colonias);
    }
    state.coloniasLoading = true;
    setRouteStatus('Cargando colonias…');
    return fetchTextFirst(COLONIAS_URLS).then(function (txt) {
      var geo = JSON.parse(txt);
      var feats = (geo && geo.features) || [];
      state.colonias = sortColonias(feats);
      state.coloniasLoaded = true;
      state.coloniasLoading = false;
      fillColoniaSelect('');
      setRouteStatus(state.colonias.length + ' colonias listas');
      return state.colonias;
    }).catch(function (err) {
      state.coloniasLoading = false;
      setRouteStatus('Error colonias: ' + (err && err.message || err));
      toast('No se pudieron cargar colonias');
      throw err;
    });
  }

  function fillColoniaSelect(filter) {
    var sel = document.getElementById('purif-scout-colonia');
    if (!sel) return;
    var q = String(filter || '').trim();
    var list = state.colonias;
    if (q) {
      var scored = [];
      for (var i = 0; i < list.length; i++) {
        var ft = list[i];
        var p = ft.properties || {};
        var blob = [p.colonia, p.colonia_raw, p.municipio, p.cve_col, String(p.rank || '')].join(' ');
        var sc = fuzzyScore(q, blob);
        // Alias: "unidad san francisco" / "san francisco" → villas
        var nq = normalizeText(q);
        var nb = normalizeText(blob);
        if (nq.indexOf('san francisco') >= 0 && nb.indexOf('san francisco') >= 0) sc = Math.max(sc, 90);
        if (nq.indexOf('topo') >= 0 && nb.indexOf('topo chico') >= 0) sc = Math.max(sc, 88);
        if (nq.indexOf('pedregal') >= 0 && nb.indexOf('pedregal') >= 0) sc = Math.max(sc, 88);
        if (sc >= 40) scored.push({ ft: ft, sc: sc });
      }
      scored.sort(function (a, b) {
        if (b.sc !== a.sc) return b.sc - a.sc;
        var am = (a.ft.properties || {}).municipio || '';
        var bm = (b.ft.properties || {}).municipio || '';
        var ae = am === ESCOBEDO ? 0 : 1;
        var be = bm === ESCOBEDO ? 0 : 1;
        if (ae !== be) return ae - be;
        return (Number((a.ft.properties || {}).rank) || 9999) - (Number((b.ft.properties || {}).rank) || 9999);
      });
      list = scored.map(function (x) { return x.ft; });
    }
    list = (q ? list : sortColonias(list)).slice(0, 120);
    var prev = sel.value;
    sel.innerHTML = '';
    var opt0 = document.createElement('option');
    opt0.value = '';
    opt0.textContent = list.length ? ('— elegir colonia (' + list.length + ') —') : '— sin resultados —';
    sel.appendChild(opt0);
    list.forEach(function (ft, idx) {
      var p = ft.properties || {};
      var opt = document.createElement('option');
      opt.value = String(p.cve_col || idx);
      opt.textContent = coloniaLabel(ft);
      opt._feat = ft;
      sel.appendChild(opt);
    });
    // restore if still present
    if (prev) {
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === prev) { sel.selectedIndex = i; break; }
      }
    }
  }

  function selectedFeatureFromUi() {
    var sel = document.getElementById('purif-scout-colonia');
    if (!sel || !sel.value) return null;
    var opt = sel.options[sel.selectedIndex];
    if (opt && opt._feat) return opt._feat;
    var cve = sel.value;
    for (var i = 0; i < state.colonias.length; i++) {
      if (String((state.colonias[i].properties || {}).cve_col) === cve) return state.colonias[i];
    }
    return null;
  }

  function samplePolyline(coords, stepM) {
    // coords: [[lng,lat], ...]
    var out = [];
    if (!coords || coords.length < 2) return out;
    var carry = 0;
    out.push({ lat: coords[0][1], lng: coords[0][0] });
    for (var i = 1; i < coords.length; i++) {
      var a = coords[i - 1];
      var b = coords[i];
      var seg = haversineM(a[1], a[0], b[1], b[0]);
      if (seg < 1e-3) continue;
      var dist = carry;
      while (dist + stepM <= seg) {
        dist += stepM;
        var t = dist / seg;
        out.push({
          lat: a[1] + (b[1] - a[1]) * t,
          lng: a[0] + (b[0] - a[0]) * t
        });
      }
      carry = seg - dist;
      if (carry < 0) carry = 0;
    }
    var last = coords[coords.length - 1];
    var prev = out[out.length - 1];
    if (!prev || haversineM(prev.lat, prev.lng, last[1], last[0]) > stepM * 0.4) {
      out.push({ lat: last[1], lng: last[0] });
    }
    return out;
  }

  function overpassHighways(bbox) {
    var q = '[out:json][timeout:' + OVERPASS_QUERY_TIMEOUT + '][maxsize:33554432];\n' +
      'way["highway"~"^(primary|secondary|tertiary|residential|unclassified|living_street|service)$"](' +
      bbox.south + ',' + bbox.west + ',' + bbox.north + ',' + bbox.east + ');\n' +
      'out geom;';
    var body = 'data=' + encodeURIComponent(q);
    var i = 0;
    function next() {
      if (i >= OVERPASS_URLS.length) return Promise.reject(new Error('Overpass falló en todos los mirrors'));
      var url = OVERPASS_URLS[i++];
      var host = url.replace(/^https?:\/\//, '').split('/')[0];
      setRouteStatus('OSM Overpass ' + i + '/' + OVERPASS_URLS.length + ' · ' + host + '…');
      var req = gmRequest({
        method: 'POST',
        url: url,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'User-Agent': 'PurificadorasScout/1.2 (CASCA-code; field scout)'
        },
        data: body,
        timeout: OVERPASS_HARD_MS
      }).then(function (res) {
        return JSON.parse(res.responseText);
      });
      return withHardTimeout(req, OVERPASS_HARD_MS + 1500, host).catch(function (err) {
        console.warn('[scout] Overpass mirror fail', host, err && err.message);
        return next();
      });
    }
    return next();
  }

  function loadPrebakedRoads() {
    if (state.roadsFc) return Promise.resolve(state.roadsFc);
    if (state.roadsLoading) return state.roadsLoading;
    setRouteStatus('Cargando calles prebaked…');
    state.roadsLoading = fetchTextFirst(ROADS_URLS).then(function (txt) {
      var fc = JSON.parse(txt);
      state.roadsFc = fc;
      state.roadsLoading = null;
      return fc;
    }).catch(function (err) {
      state.roadsLoading = null;
      throw err;
    });
    return state.roadsLoading;
  }

  function geojsonRoadsToElements(fc, bbox) {
    var elements = [];
    var feats = (fc && fc.features) || [];
    for (var i = 0; i < feats.length; i++) {
      var f = feats[i];
      var g = f && f.geometry;
      if (!g || g.type !== 'LineString' || !g.coordinates || g.coordinates.length < 2) continue;
      var coords = g.coordinates;
      var minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity;
      for (var c = 0; c < coords.length; c++) {
        var lon = coords[c][0], lat = coords[c][1];
        if (lon < minLng) minLng = lon;
        if (lon > maxLng) maxLng = lon;
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
      }
      if (maxLng < bbox.west || minLng > bbox.east || maxLat < bbox.south || minLat > bbox.north) continue;
      var geom = [];
      for (var k = 0; k < coords.length; k++) {
        geom.push({ lon: coords[k][0], lat: coords[k][1] });
      }
      elements.push({
        type: 'way',
        geometry: geom,
        tags: { highway: (f.properties && f.properties.highway) || 'residential' }
      });
    }
    return elements;
  }

  function densifyPolygonFallback(geom, stepM) {
    var step = stepM || GRID_STEP_M;
    var bbox = geomBbox(geom);
    var points = [];
    var last = null;

    function pushPt(lat, lng) {
      if (!pointInPolygon(lng, lat, geom)) return;
      if (last && haversineM(last.lat, last.lng, lat, lng) < step * 0.4) return;
      var pt = { lat: lat, lng: lng };
      points.push(pt);
      last = pt;
    }

    // 1) densify outer ring(s)
    var rings = [];
    if (geom.type === 'Polygon') rings = [geom.coordinates[0]];
    else if (geom.type === 'MultiPolygon') {
      for (var p = 0; p < geom.coordinates.length; p++) rings.push(geom.coordinates[p][0]);
    }
    for (var r = 0; r < rings.length; r++) {
      var samples = samplePolyline(rings[r], step);
      for (var s = 0; s < samples.length; s++) pushPt(samples[s].lat, samples[s].lng);
    }

    // 2) grid inside bbox (~40–60 m)
    var lat0 = bbox.south;
    var mPerDegLat = 111320;
    var mPerDegLng = 111320 * Math.cos(((bbox.south + bbox.north) / 2) * Math.PI / 180);
    var dLat = step / mPerDegLat;
    var dLng = step / Math.max(mPerDegLng, 1e-6);
    var row = 0;
    for (var lat = bbox.south; lat <= bbox.north + 1e-12; lat += dLat, row++) {
      var colOff = (row % 2) * (dLng * 0.5); // slight stagger
      for (var lng = bbox.west + colOff; lng <= bbox.east + 1e-12; lng += dLng) {
        pushPt(lat, lng);
      }
    }

    var MAX_PTS = 900;
    if (points.length > MAX_PTS) {
      var stride = Math.ceil(points.length / MAX_PTS);
      var thinned = [];
      for (var t = 0; t < points.length; t += stride) thinned.push(points[t]);
      points = thinned;
    }
    return points;
  }

  function setRetryVisible(show) {
    var btn = document.getElementById('purif-scout-retry-route');
    if (btn) btn.style.display = show ? '' : 'none';
  }

  function showTrayectoError(msg) {
    state.lastTrayectoError = msg || 'Error armando trayecto';
    setRouteStatus('❌ ' + state.lastTrayectoError);
    setRetryVisible(true);
    toast(state.lastTrayectoError);
  }

  function waysToCoveragePoints(elements, geom) {
    var ways = [];
    (elements || []).forEach(function (el) {
      if (!el || el.type !== 'way' || !el.geometry || el.geometry.length < 2) return;
      var hw = (el.tags && el.tags.highway) || '';
      // skip parking aisles / driveways-heavy if service+parking
      if (hw === 'service' && el.tags && /parking|driveway/i.test(el.tags.service || '')) return;
      var coords = [];
      for (var i = 0; i < el.geometry.length; i++) {
        var g = el.geometry[i];
        if (pointInPolygon(g.lon, g.lat, geom)) coords.push([g.lon, g.lat]);
        else if (coords.length >= 2) {
          ways.push({ coords: coords, len: 0 });
          coords = [];
        } else coords = [];
      }
      if (coords.length >= 2) ways.push({ coords: coords, len: 0 });
    });
    ways.forEach(function (w) {
      var len = 0;
      for (var i = 1; i < w.coords.length; i++) {
        len += haversineM(w.coords[i - 1][1], w.coords[i - 1][0], w.coords[i][1], w.coords[i][0]);
      }
      w.len = len;
    });
    ways.sort(function (a, b) { return b.len - a.len; });

    // Order ways into a walkable sequence (greedy endpoint chaining)
    var remaining = ways.slice();
    var ordered = [];
    if (!remaining.length) return [];
    ordered.push(remaining.shift());
    while (remaining.length) {
      var cur = ordered[ordered.length - 1];
      var end = cur.coords[cur.coords.length - 1];
      var bestI = 0, bestD = Infinity, bestRev = false;
      for (var i = 0; i < remaining.length; i++) {
        var w = remaining[i];
        var d0 = haversineM(end[1], end[0], w.coords[0][1], w.coords[0][0]);
        var d1 = haversineM(end[1], end[0], w.coords[w.coords.length - 1][1], w.coords[w.coords.length - 1][0]);
        if (d0 < bestD) { bestD = d0; bestI = i; bestRev = false; }
        if (d1 < bestD) { bestD = d1; bestI = i; bestRev = true; }
      }
      var pick = remaining.splice(bestI, 1)[0];
      if (bestRev) pick.coords = pick.coords.slice().reverse();
      ordered.push(pick);
    }

    var points = [];
    var last = null;
    ordered.forEach(function (w) {
      var samples = samplePolyline(w.coords, STEP_M);
      samples.forEach(function (pt) {
        if (!pointInPolygon(pt.lng, pt.lat, geom)) return;
        if (last && haversineM(last.lat, last.lng, pt.lat, pt.lng) < STEP_M * 0.45) return;
        points.push(pt);
        last = pt;
      });
    });
    // Cap very large colonias so trayecto stays usable
    var MAX_PTS = 900;
    if (points.length > MAX_PTS) {
      var stride = Math.ceil(points.length / MAX_PTS);
      var thinned = [];
      for (var t = 0; t < points.length; t += stride) thinned.push(points[t]);
      if (thinned[thinned.length - 1] !== points[points.length - 1]) thinned.push(points[points.length - 1]);
      points = thinned;
    }
    return points;
  }

  function buildStreetViewUrl(lat, lng, heading) {
    var h = (heading != null && isFinite(heading)) ? heading : 0;
    // Official Maps URLs (no API key / no billing) — preferred 2026
    return 'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=' +
      encodeURIComponent(lat + ',' + lng) +
      '&heading=' + encodeURIComponent(String(Math.round(h))) +
      '&pitch=0&fov=75';
  }

  function navigateToSv(lat, lng, heading) {
    var url = buildStreetViewUrl(lat, lng, heading);
    // Same-tab navigation keeps Tampermonkey running
    try {
      location.assign(url);
    } catch (e) {
      location.href = url;
    }
  }

  function setRouteStatus(msg) {
    var el = document.getElementById('purif-scout-route-status');
    if (el) el.textContent = msg || '';
  }

  function stopRoute(msg) {
    if (state.routeTimer) {
      clearInterval(state.routeTimer);
      state.routeTimer = null;
    }
    state.routeBusy = false;
    if (state.route) {
      state.route.paused = true;
      state.route.status = 'stopped';
    }
    if (msg) toast(msg);
    updateHud();
  }

  function startRoute(points, name) {
    if (!points || !points.length) {
      toast('Sin calles OSM en esta colonia');
      return;
    }
    // Pause local auto-walk — trayecto drives via URL
    if (state.autoWalk) setAutoWalk(false);
    state.route = {
      name: name || 'colonia',
      points: points,
      i: 0,
      paused: false,
      status: 'running',
      skipped: 0
    };
    if (state.routeTimer) clearInterval(state.routeTimer);
    state.routeTimer = setInterval(routeTick, state.autoMs);
    toast('🛣 Trayecto: ' + points.length + ' pts · ' + name);
    setRouteStatus('punto 1/' + points.length + ' · ' + name);
    updateHud();
    // kick immediately
    routeTick();
  }

  function routeTick() {
    if (!state.route || state.route.paused || state.routeBusy) return;
    if (state.commentOpen) return;
    var r = state.route;
    if (r.i >= r.points.length) {
      stopRoute('✅ Trayecto completo · ' + r.name);
      setRouteStatus('Completo · ' + r.points.length + ' pts · skip ' + r.skipped);
      return;
    }
    var pt = r.points[r.i];
    var next = r.points[r.i + 1];
    var heading = next ? bearingDeg(pt.lat, pt.lng, next.lat, next.lng) : (state.heading || 0);
    var targetKey = pt.lat.toFixed(5) + ',' + pt.lng.toFixed(5);
    state.routeBusy = true;
    setRouteStatus('punto ' + (r.i + 1) + '/' + r.points.length + ' · ' + r.name);
    updateHud();
    navigateToSv(pt.lat, pt.lng, heading);

    var start = Date.now();
    var check = setInterval(function () {
      refreshPose();
      var okSv = state.inSV;
      var near = state.lat != null && haversineM(state.lat, state.lng, pt.lat, pt.lng) < 55;
      var urlSv = /map_action=pano|,\d+(?:\.\d+)?a,/.test(location.href);
      if ((okSv || urlSv) && (near || poseKey())) {
        // Accept snap even if slightly offset (SV nearest pano)
        clearInterval(check);
        state.routeBusy = false;
        r.i += 1;
        updateHud();
        return;
      }
      if (Date.now() - start > SV_WAIT_MS) {
        clearInterval(check);
        r.skipped += 1;
        r.i += 1;
        state.routeBusy = false;
        setRouteStatus('skip SV · punto ' + r.i + '/' + r.points.length + ' · ' + r.name);
        updateHud();
      }
    }, 250);
  }

  function toggleRoutePause() {
    if (!state.route) return false;
    state.route.paused = !state.route.paused;
    if (state.route.paused) {
      toast('⏸ Trayecto pausado');
      setRouteStatus('PAUSA · punto ' + Math.min(state.route.i + 1, state.route.points.length) + '/' + state.route.points.length);
    } else {
      toast('▶ Trayecto reanudado');
      if (!state.routeTimer) state.routeTimer = setInterval(routeTick, state.autoMs);
      setTimeout(routeTick, 100);
    }
    updateHud();
    return true;
  }

  function buildTrayectoForSelection() {
    var ft = selectedFeatureFromUi();
    if (!ft) {
      toast('Elige una colonia');
      return;
    }
    if (state.trayectoBuilding) {
      toast('Ya se está armando el trayecto…');
      return;
    }
    state.selectedColonia = ft;
    var p = ft.properties || {};
    var name = (p.colonia_raw || p.colonia || '?') + ' · ' + (p.municipio || '');
    var geom = ft.geometry;
    if (!geom) { toast('Colonia sin geometría'); return; }
    var bbox = geomBbox(geom);
    var pad = 0.0003;
    bbox = {
      south: bbox.south - pad,
      west: bbox.west - pad,
      north: bbox.north + pad,
      east: bbox.east + pad
    };

    state.trayectoBuilding = true;
    state.lastTrayectoError = null;
    setRetryVisible(false);
    setRouteStatus('Armando trayecto…');
    toast('Generando trayecto…');

    function finishOk(pts, source) {
      state.trayectoBuilding = false;
      setRetryVisible(false);
      setRouteStatus(pts.length + ' pts · ' + source + ' · ' + name);
      if (!pts.length) {
        showTrayectoError('Sin puntos de cobertura en ' + name);
        return;
      }
      startRoute(pts, name);
    }

    function tryLiveOverpass() {
      setRouteStatus('Consultando OSM Overpass…');
      // Hard ceiling ~22s across mirrors — never infinite "consultando…"
      return withHardTimeout(
        overpassHighways(bbox),
        22000,
        'overpass-total'
      ).then(function (data) {
        var pts = waysToCoveragePoints(data.elements || [], geom);
        if (pts.length >= MIN_ROUTE_PTS) {
          finishOk(pts, 'Overpass');
          return true;
        }
        return false;
      }).catch(function (err) {
        console.warn('[scout] Overpass failed', err && err.message);
        return false;
      });
    }

    function useGridFallback(reason) {
      setRouteStatus('Fallback rejilla / borde…');
      var pts = densifyPolygonFallback(geom, GRID_STEP_M);
      if (pts.length >= MIN_ROUTE_PTS) {
        finishOk(pts, 'rejilla ' + GRID_STEP_M + 'm');
        toast('⚠ Sin calles OSM — usando rejilla (' + reason + ')');
        return;
      }
      state.trayectoBuilding = false;
      showTrayectoError('No se pudo armar trayecto (' + reason + '). Reintentar.');
    }

    // 1) Prebaked roads (preferred — no live Overpass)
    loadPrebakedRoads().then(function (fc) {
      var elements = geojsonRoadsToElements(fc, bbox);
      var pts = waysToCoveragePoints(elements, geom);
      if (pts.length >= MIN_ROUTE_PTS) {
        finishOk(pts, 'prebaked');
        return null;
      }
      // 2) Live Overpass optional refresh
      return tryLiveOverpass().then(function (ok) {
        if (!ok) useGridFallback('sin vías en polígono');
      });
    }).catch(function () {
      // prebake missing → Overpass → grid
      return tryLiveOverpass().then(function (ok) {
        if (!ok) useGridFallback('prebake+Overpass fallaron');
      });
    }).catch(function (err) {
      state.trayectoBuilding = false;
      showTrayectoError('Error: ' + (err && err.message || err));
    });
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
      'font-size:12px;line-height:1.35;max-width:300px;box-shadow:0 8px 24px rgba(0,0,0,.35);',
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
      '#purif-scout-hud button.primary{background:#7a0177;color:#fff}',
      '#purif-scout-hud button.danger{background:#9f1239;color:#fff}',
      '#purif-scout-hud .tray{margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.12)}',
      '#purif-scout-hud .tray label{display:block;font-size:10px;opacity:.8;margin:4px 0 2px}',
      '#purif-scout-hud input[type="search"],#purif-scout-hud select,#purif-scout-hud input[type="range"]{',
      'width:100%;border-radius:8px;border:1px solid #57534e;background:#1c1917;color:#efe9db;',
      'padding:6px 8px;font:12px/1.2 system-ui}',
      '#purif-scout-hud input[type="range"]{padding:0;height:22px}',
      '#purif-scout-hud .route-status{font-size:11px;margin-top:6px;color:#f9a8d4;min-height:1.2em}',
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
      '  <div class="row"><kbd class="sec">Space</kbd>Auto / pausa trayecto · <kbd class="sec">Z</kbd>Deshacer</div>',
      '  <div class="meta" id="purif-scout-meta">—</div>',
      '  <div class="tray">',
      '    <label>Colonia (Escobedo + ZMM)</label>',
      '    <input type="search" id="purif-scout-col-filter" placeholder="Buscar colonia…" autocomplete="off" />',
      '    <select id="purif-scout-colonia"><option value="">— cargando… —</option></select>',
      '    <label>Velocidad auto / trayecto: <span id="purif-scout-speed-label">1.4s</span></label>',
      '    <input type="range" id="purif-scout-speed" min="600" max="4000" step="100" value="' + state.autoMs + '" />',
      '    <div class="acts">',
      '      <button type="button" class="primary" id="purif-scout-start-route">Start trayecto</button>',
      '      <button type="button" id="purif-scout-pause-route">Pausa</button>',
      '      <button type="button" class="danger" id="purif-scout-stop-route">Stop</button>',
      '      <button type="button" id="purif-scout-retry-route" style="display:none;background:#b45309;color:#fff">Reintentar</button>',
      '    </div>',
      '    <div class="route-status" id="purif-scout-route-status"></div>',
      '  </div>',
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

    document.getElementById('purif-scout-col-filter').addEventListener('input', function (e) {
      fillColoniaSelect(e.target.value);
    });
    document.getElementById('purif-scout-start-route').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      buildTrayectoForSelection();
    });
    document.getElementById('purif-scout-retry-route').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      setRetryVisible(false);
      buildTrayectoForSelection();
    });
    document.getElementById('purif-scout-pause-route').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      if (!state.route) { toast('No hay trayecto'); return; }
      toggleRoutePause();
    });
    document.getElementById('purif-scout-stop-route').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      stopRoute('Trayecto detenido');
      setRouteStatus('Detenido');
    });
    document.getElementById('purif-scout-speed').addEventListener('input', function (e) {
      var ms = Number(e.target.value);
      var lab = document.getElementById('purif-scout-speed-label');
      if (lab) lab.textContent = (ms / 1000).toFixed(1) + 's';
      setAutoMs(ms);
    });
    var lab0 = document.getElementById('purif-scout-speed-label');
    if (lab0) lab0.textContent = (state.autoMs / 1000).toFixed(1) + 's';
  }

  function openComment() {
    // Pause motions so we don't steal focus from the textarea
    if (state.autoWalk) setAutoWalk(false);
    if (state.route && !state.route.paused) toggleRoutePause();
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
    if (state.route && state.route.status === 'running') {
      badge.textContent = state.route.paused
        ? ('Trayecto ⏸ ' + Math.min(state.route.i + 1, state.route.points.length) + '/' + state.route.points.length)
        : ('Trayecto ▶ ' + Math.min(state.route.i + 1, state.route.points.length) + '/' + state.route.points.length);
      badge.className = 'badge ' + (state.route.paused ? 'warn' : 'on');
    } else if (state.inSV) {
      badge.textContent = state.autoWalk ? ('SV · auto ▶' + (state._lastWalkMethod ? ' · ' + state._lastWalkMethod : '')) : 'Street View';
      badge.className = 'badge on';
    } else {
      badge.textContent = 'No SV — arrastra peoncito';
      badge.className = 'badge warn';
    }
    var lat = state.lat != null ? state.lat.toFixed(6) : '—';
    var lng = state.lng != null ? state.lng.toFixed(6) : '—';
    var h = (state.heading != null && isFinite(state.heading)) ? Math.round(state.heading) + '°' : '—';
    var extra = '';
    if (state.route) {
      extra = ' · ' + state.route.name + ' ' + Math.min(state.route.i, state.route.points.length) + '/' + state.route.points.length;
      if (state.route.skipped) extra += ' skip' + state.route.skipped;
    }
    meta.textContent = lat + ', ' + lng + ' · h ' + h + ' · ' + state.sessionPins.length + ' pin(es)' + extra;
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

    var clat = state.lat != null ? state.lat : 25.836;
    var clng = state.lng != null ? state.lng : -100.371;
    var span = 0.004;
    function xy(lat, lng) {
      var x = ((lng - (clng - span)) / (2 * span)) * w;
      var y = ((clat + span - lat) / (2 * span)) * h;
      return { x: x, y: y };
    }

    ctx.strokeStyle = 'rgba(0,0,0,.08)';
    ctx.lineWidth = 1;
    for (var g = 1; g < 4; g++) {
      ctx.beginPath();
      ctx.moveTo((w / 4) * g, 0); ctx.lineTo((w / 4) * g, h); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, (h / 4) * g); ctx.lineTo(w, (h / 4) * g); ctx.stroke();
    }

    // route preview
    if (state.route && state.route.points && state.route.points.length) {
      ctx.beginPath();
      state.route.points.forEach(function (pt, i) {
        var pxy = xy(pt.lat, pt.lng);
        if (i === 0) ctx.moveTo(pxy.x, pxy.y); else ctx.lineTo(pxy.x, pxy.y);
      });
      ctx.strokeStyle = 'rgba(122,1,119,.45)';
      ctx.lineWidth = 2;
      ctx.stroke();
      var cur = state.route.points[Math.min(state.route.i, state.route.points.length - 1)];
      if (cur) {
        var cxy = xy(cur.lat, cur.lng);
        ctx.beginPath();
        ctx.arc(cxy.x, cxy.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#f472b6';
        ctx.fill();
      }
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
  function isTypingTarget(el) {
    if (!el) return false;
    var tag = (el.tagName || '').toUpperCase();
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
    if (el.isContentEditable) return true;
    return false;
  }

  function onKeyDown(ev) {
    if (isTypingTarget(ev.target)) return;
    if (state.commentOpen) {
      if (ev.key === 'Escape') { closeComment(); ev.preventDefault(); }
      // Never steal keys (incl. Space) while comment dialog is open
      return;
    }

    if (ev.code === 'Space' || ev.key === ' ') {
      if (state.route && state.route.status === 'running') {
        ev.preventDefault();
        ev.stopPropagation();
        toggleRoutePause();
        return;
      }
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
    loadColonias().catch(function () {});
    toast('Scout Purificadoras v1.1 · sin API key');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
