// ==UserScript==
// @name         Purificadoras Scout SV (Street View)
// @namespace    https://casca-code.github.io/mapa-purificadoras/
// @version      1.7.3
// @description  Scout de campo sobre google.com/maps Street View. CERO Maps billing. v1.7.3: speed −/+ (sin range); sin blur HUD; routeBusy watchdog + destrabado; look-ahead cruce POV→salida; cobertura calles; auto-walk REQUIERE extensión. NO uses scout-sv.html.
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
   * Purificadoras Scout — Tampermonkey sobre Street View de consumidor (google.com/maps).
   * CERO Maps Platform API key / billing. Nunca llama Street View Static/JS API con key.
   * Sync primario: ntfy (mismo topic que index.html).
   * NO uses scout-sv.html (esa página SÍ pide key).
   * v1.1: auto-walk + picker colonia + trayecto OSM.
   * v1.2: prebaked roads + Overpass timeout + grid + fuzzy.
   * v1.2.1: trayecto persiste tras navigate; HUD sin falso “falta key”.
   * v1.3.0: walk = saltos URL map_action=pano (causaba pantalla negra).
   * v1.4.0: walk = flecha SV in-pano (click chevron / pointer / tecla); URL solo 1er punto trayecto o recovery raro.
   * v1.5.0: extensión Chrome = PRIMARY (requerida). Ext FIRST cada tick; giro Left/Right + ArrowUp; trayecto auto sin clicks; pace ~800ms.
   * v1.6.0: trayecto = cobertura total calles (grafo + Chinese Postman approx); steering turnDeg; U-turn dead-end; hop raro entre componentes.
   * v1.7.0: rota el POV hacia el bearing del trayecto ANTES de ArrowUp; poll heading URL; U-turn ~180° real; HUD POV cur→target.
   * v1.7.1: HUD slim left — hotkeys, colonia+Start, speed, progress, Pause/Stop; mini-map route+peg; clutter→⋯ menu.
   * v1.7.2: speed no auto-acelera (blur/ignore Arrow* en slider ante ext); look-ahead esquina |turn|≥35° → POV a bearing de SALIDA ~50 m antes; HUD ↳/↰.
   * v1.7.3: sin blur/restore HUD; speed = botones −/+ (nada focusable con Arrow*); routeBusy watchdog ~5s; POV hard timeout; destrabado si pose no cambia.
   */

  var NTFY_TOPIC = 'purif-zmm-campo-casca-v1';
  var LS_COMP = 'purificadoras_field_adds_v1';
  var LS_ANCLAS = 'purificadoras_anclas_v1';
  var LS_SESSION = 'purificadoras_scout_tm_session_v1';
  var LS_SPEED = 'purificadoras_scout_tm_speed_ms';
  var LS_ROUTE = 'purificadoras_scout_tm_route_v1';
  var LS_AUTOWALK = 'purif_scout_autowalk';
  var LS_AUTOWALK_META = 'purif_scout_autowalk_meta';
  var SCRIPT_VERSION = '1.7.3';
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
  var DEFAULT_AUTO_MS = 800; // v1.5 faster pace (~0.7–0.9s)
  var ROUTE_MS_MIN = 700;
  var ROUTE_MS_MAX = 2500;
  var FORWARD_M_MIN = 8;
  var FORWARD_M_MAX = 14;
  var STEP_M = 15; // sample waypoints every ~12–18 m along covering walk
  var MAX_ROUTE_PTS = 2500; // raise from 900 so medium colonias keep full coverage
  var SV_WAIT_MS = 4500;
  var DEAD_END_FAILS = 10; // auto-walk (no route) abort
  var ROUTE_DEAD_END_FAILS = 3; // trayecto: U-turn after N no-move ArrowUps
  var ROUTE_HOP_FAILS = 5; // trayecto: pano hop after N fails if next WP > HOP_DIST_M
  var HOP_DIST_M = 90; // component hop threshold
  var CONSEC_SV_FAILS = 3;
  var URL_RECOVERY_EVERY = 8; // rare URL jump after N flecha failures
  var NEAR_WP_M = 28; // haversine to advance trayecto index
  var LOOKAHEAD_NEAR_M = 22; // soft steer toward WP+1 when this close (legacy)
  var CORNER_LOOKAHEAD_M = 55; // v1.7.2: commit exit bearing this far before corner
  var CORNER_TURN_DEG = 35; // |turnDeg| at WP ≥ this → corner / multi-link
  var CORNER_EXTRA_BURSTS = 2; // stronger POV align at crossroads
  var EXT_TURN_THRESH = 18; // deg — ask extension to turn if |delta| above this
  var STRONG_TURN_DEG = 20; // |delta| above this → align POV before ArrowUp (v1.7)
  var POV_ALIGN_DEG = 20; // same threshold for alignPovToBearing
  var POV_POLL_MS = 800; // wait/poll URL heading after turn-only burst
  var POV_EXTRA_BURSTS = 2; // extra turn bursts if heading URL doesn't update
  var POV_CLOSE_DEG = 18; // stop aligning when |diff| under this
  var POV_HARD_TIMEOUT_MS = 3200; // v1.7.3: never hang forever waiting heading
  var EXT_STEP_TIMEOUT_MS = 5500;
  var ROUTE_BUSY_WATCHDOG_MS = 5500; // v1.7.3: always clear routeBusy
  var STUCK_POSE_N = 3; // unchanged pose after turn+↑ → unstick
  var SPEED_STEP_MS = 100;
  var WALK_MODE = "ext";
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
    route: null, // { name, points, i, paused, status, skipped, streetCount, edgeCount, capped }
    routeTimer: null,
    routeBusy: false,
    roadsFc: null,
    roadsLoading: null,
    trayectoBuilding: false,
    lastTrayectoError: null,
    walkMethod: 'flecha SV',
    flechaFailStreak: 0,
    urlRecoveryCount: 0,
    hopCount: 0,
    extAvailable: false,
    routeEntered: false, // first URL jump done for trayecto
    povHud: null, // brief 'POV 120°→85°'
    povHudUntil: 0,
    targetBearing: null,
    nextTurnHud: null, // '↳ der 90°' / '↰ izq'
    _routeBusyTimer: null,
    _lastUnstickToast: 0
  };

  try {
    var savedSpeed = Number(GM_getValue && GM_getValue(LS_SPEED, NaN));
    if (!isFinite(savedSpeed)) {
      try { savedSpeed = Number(localStorage.getItem(LS_SPEED)); } catch (e2) { savedSpeed = NaN; }
    }
    if (isFinite(savedSpeed) && savedSpeed >= ROUTE_MS_MIN && savedSpeed <= ROUTE_MS_MAX) state.autoMs = savedSpeed;
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

  function saveRoute() {
    try {
      if (!state.route) {
        try { sessionStorage.removeItem(LS_ROUTE); } catch (e0) {}
        try { if (typeof GM_setValue === 'function') GM_setValue(LS_ROUTE, ''); } catch (e1) {}
        return;
      }
      var payload = JSON.stringify({
        name: state.route.name,
        points: state.route.points,
        i: state.route.i,
        paused: !!state.route.paused,
        status: state.route.status || 'running',
        skipped: state.route.skipped || 0,
        failStreak: state.route.failStreak || 0,
        svFailStreak: state.route.svFailStreak || 0,
        flechaFailStreak: state.route.flechaFailStreak || 0,
        entered: !!state.route.entered,
        attemptCount: state.route.attemptCount || 0,
        lastNavI: state.route.lastNavI != null ? state.route.lastNavI : -1,
        savedAt: Date.now()
      });
      try { sessionStorage.setItem(LS_ROUTE, payload); } catch (e2) {}
      try { if (typeof GM_setValue === 'function') GM_setValue(LS_ROUTE, payload); } catch (e3) {}
    } catch (e) {}
  }

  function loadRoute() {
    try {
      var raw = null;
      try { raw = sessionStorage.getItem(LS_ROUTE); } catch (e0) {}
      if (!raw && typeof GM_getValue === 'function') {
        try { raw = GM_getValue(LS_ROUTE, ''); } catch (e1) {}
      }
      if (!raw) return null;
      var r = typeof raw === 'string' ? JSON.parse(raw) : raw;
      if (!r || !Array.isArray(r.points) || !r.points.length) return null;
      if (r.savedAt && (Date.now() - r.savedAt) > 6 * 60 * 60 * 1000) return null; // stale
      return r;
    } catch (e) { return null; }
  }

  function clearRoutePersist() {
    try { sessionStorage.removeItem(LS_ROUTE); } catch (e0) {}
    try { if (typeof GM_setValue === 'function') GM_setValue(LS_ROUTE, ''); } catch (e1) {}
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
    var mH = url.match(/,(-?[\d.]+)h,([\d.]+)t/i);
    if (mH) out.heading = Number(mH[1]); // prefer latest h,t even if set
    var mHead = url.match(/[?&#]heading=(-?[\d.]+)/i);
    if (mHead) out.heading = Number(mHead[1]);
    // Maps sometimes puts heading in !3e / nested data — last ,Xh, before t
    var mH2 = url.match(/,(-?[\d.]+)h,/i);
    if (mH2 && (out.heading == null || !isFinite(out.heading))) out.heading = Number(mH2[1]);
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
    // Also peek history.state / hash if href lagging (Maps SPA)
    try {
      if ((!p.heading || !isFinite(p.heading)) && location.hash) {
        var ph = parseFromUrl(location.origin + location.pathname + location.hash);
        if (ph.heading != null && isFinite(ph.heading)) p.heading = ph.heading;
        if (ph.lat != null) { p.lat = ph.lat; p.lng = ph.lng; }
      }
    } catch (eHash) {}
    var changed = false;
    if (p.lat != null && p.lng != null) {
      if (state.lat !== p.lat || state.lng !== p.lng) changed = true;
      state.lat = p.lat;
      state.lng = p.lng;
    }
    if (p.heading != null && isFinite(p.heading)) {
      if (state.heading !== p.heading) changed = true;
      state.heading = p.heading;
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
    drawMini();
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
    drawMini();
    toast('💬 Zona guardada');
  }

  function undoPin() {
    if (!state.sessionPins.length) { toast('Nada que deshacer'); return; }
    var f = state.sessionPins.pop();
    saveSession();
    unpersistFeature(f);
    drawMini();
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

  /* ---------- flecha SV walk (Space) — v1.4.0 ---------- */
  /* Goal: soft in-panorama steps (white chevron / road arrow), NEVER location.assign each tick.
   * Research 2025/2026 Maps SV DOM: forward chevrons are WebGL-only (canvas.widget-scene-canvas /
   * canvas.H1VXrf). No reliable aria-label="Forward" button. HTML rotate buttons DO exist
   * ("Rotate the view clockwise/counterclockwise"). Untrusted KeyboardEvent often ignored —
   * we still try click/pointer/key; Chrome extension/ (debugger ArrowUp) is the trusted fallback.
   * URL map_action=pano = black flash — only first trayecto point or rare recovery. */

  function routeIntervalMs() {
    var ms = Number(state.autoMs) || DEFAULT_AUTO_MS;
    if (ms < ROUTE_MS_MIN) ms = ROUTE_MS_MIN;
    if (ms > ROUTE_MS_MAX) ms = ROUTE_MS_MAX;
    return ms;
  }

  function persistAutoWalkFlag(on) {
    try {
      if (typeof GM_setValue === 'function') GM_setValue(LS_AUTOWALK, !!on);
    } catch (e) {}
  }

  function readAutoWalkFlag() {
    try {
      if (typeof GM_getValue === 'function') return !!GM_getValue(LS_AUTOWALK, false);
    } catch (e) {}
    return false;
  }

  function saveAutoWalkMeta(meta) {
    try {
      if (typeof GM_setValue === 'function') GM_setValue(LS_AUTOWALK_META, JSON.stringify(meta || {}));
    } catch (e) {}
  }

  function loadAutoWalkMeta() {
    try {
      if (typeof GM_getValue !== 'function') return null;
      var raw = GM_getValue(LS_AUTOWALK_META, '');
      if (!raw) return null;
      return typeof raw === 'string' ? JSON.parse(raw) : raw;
    } catch (e) { return null; }
  }

  function clearAutoWalkMeta() {
    try { if (typeof GM_setValue === 'function') GM_setValue(LS_AUTOWALK_META, ''); } catch (e) {}
  }

  function buildStreetViewUrl(lat, lng, heading) {
    var h = Math.round((heading != null && isFinite(heading)) ? heading : 0);
    return 'https://www.google.com/maps/@' + lat + ',' + lng + ',3a,75y,' + h + 'h,90t';
  }

  function buildStreetViewUrlPanoAction(lat, lng, heading) {
    var h = Math.round((heading != null && isFinite(heading)) ? heading : 0);
    return 'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=' +
      encodeURIComponent(lat + ',' + lng) +
      '&heading=' + encodeURIComponent(String(h)) +
      '&pitch=0&fov=75';
  }

  /** URL teleport — CAUSES black flash. Only for first trayecto entry or rare recovery. */
  function navigateToSv(lat, lng, heading, opt) {
    opt = opt || {};
    saveRoute();
    var url = buildStreetViewUrlPanoAction(lat, lng, heading);
    if (opt.softOnly) url = buildStreetViewUrl(lat, lng, heading);
    state.walkMethod = 'URL-pano ⚠';
    state._lastWalkMethod = 'URL-pano';
    if (!opt.silentWarn) {
      toast('⚠ Teletransporte URL (flash negro) — solo recuperación / entrada');
    }
    try { location.assign(url); }
    catch (e) { location.href = url; }
  }

  function forwardMeters() {
    return FORWARD_M_MIN + Math.random() * (FORWARD_M_MAX - FORWARD_M_MIN);
  }

  function angleDiffDeg(a, b) {
    var d = ((a - b + 540) % 360) - 180;
    return d;
  }

  function getSvCanvas() {
    var c = document.querySelector('canvas.widget-scene-canvas') ||
      document.querySelector('canvas.widget-scene-canvas, canvas[class*="scene"]') ||
      document.querySelector('[aria-label="Street View"] canvas, [aria-label="Vista de calle"] canvas') ||
      document.querySelector('[role="application"] canvas') ||
      document.querySelector('canvas');
    return c;
  }

  function focusSvSurface() {
    var app = document.querySelector('[aria-label="Street View"], [aria-label="Vista de calle"], [aria-label*="Street View"], [role="application"]');
    var canvas = getSvCanvas();
    try {
      if (app && app.focus) app.focus();
      if (canvas) {
        if (canvas.tabIndex < 0) canvas.tabIndex = 0;
        canvas.focus();
      }
    } catch (e) {}
    return canvas || app;
  }

  /** Find HTML overlays that might be navigation links / forward controls. */
  function findSvNavArrowEls(preferredHeading) {
    var hits = [];
    var nodes = document.querySelectorAll('button, a, [role="button"], [jsaction], [aria-label], div[tabindex]');
    var re = /forward|adelante|navigate|avanzar|move forward|go forward|siguiente|next pano|link arrow|flecha/i;
    var reBad = /zoom|rotate|clockwise|counter|back|atrás|close|search|menu|pegman|browse|expand|collapse|share/i;
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var aria = (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '');
      var js = el.getAttribute('jsaction') || '';
      var cls = String(el.className || '');
      if (reBad.test(aria)) continue;
      var score = 0;
      if (re.test(aria)) score += 50;
      if (/pano|forward|navigate|streetview\.link|scene\.link/i.test(js)) score += 30;
      if (/link|chevron|arrow|nav/i.test(cls)) score += 10;
      // Prefer elements in lower-center of viewport (where road chevrons sit)
      try {
        var r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2 || r.width > 400 || r.height > 400) continue;
        var cx = r.left + r.width / 2;
        var cy = r.top + r.height / 2;
        var vw = window.innerWidth || 1200;
        var vh = window.innerHeight || 800;
        if (cy < vh * 0.35 || cy > vh * 0.92) continue;
        if (cx < vw * 0.15 || cx > vw * 0.85) continue;
        // Prefer near horizontal center
        score += Math.max(0, 20 - Math.abs(cx - vw / 2) / 20);
        if (score > 0) hits.push({ el: el, score: score, cx: cx, cy: cy });
      } catch (e2) {}
    }
    hits.sort(function (a, b) { return b.score - a.score; });
    return hits;
  }

  function clickEl(el) {
    if (!el) return false;
    try {
      el.click();
      return true;
    } catch (e) {}
    try {
      var opts = { bubbles: true, cancelable: true, view: window };
      el.dispatchEvent(new MouseEvent('pointerdown', opts));
      el.dispatchEvent(new MouseEvent('mousedown', opts));
      el.dispatchEvent(new MouseEvent('pointerup', opts));
      el.dispatchEvent(new MouseEvent('mouseup', opts));
      el.dispatchEvent(new MouseEvent('click', opts));
      return true;
    } catch (e2) { return false; }
  }

  function pointerClickAt(x, y) {
    var el = document.elementFromPoint(x, y) || getSvCanvas() || document.body;
    var opts = {
      bubbles: true, cancelable: true, view: window,
      clientX: x, clientY: y, screenX: x, screenY: y,
      button: 0, buttons: 1, pointerId: 1, isPrimary: true, pointerType: 'mouse'
    };
    try {
      el.dispatchEvent(new PointerEvent('pointerdown', opts));
      el.dispatchEvent(new MouseEvent('mousedown', opts));
      el.dispatchEvent(new PointerEvent('pointerup', opts));
      el.dispatchEvent(new MouseEvent('mouseup', opts));
      el.dispatchEvent(new MouseEvent('click', opts));
      return true;
    } catch (e) {
      try {
        el.dispatchEvent(new MouseEvent('click', opts));
        return true;
      } catch (e2) { return false; }
    }
  }

  /** Click typical chevron screen zones (lower-center of SV canvas). */
  function clickChevronZones() {
    var canvas = getSvCanvas();
    var rect;
    if (canvas) rect = canvas.getBoundingClientRect();
    else rect = { left: 0, top: 0, width: window.innerWidth, height: window.innerHeight };
    var cx = rect.left + rect.width * 0.5;
    var points = [
      [cx, rect.top + rect.height * 0.62],
      [cx, rect.top + rect.height * 0.55],
      [cx, rect.top + rect.height * 0.68],
      [cx - 40, rect.top + rect.height * 0.60],
      [cx + 40, rect.top + rect.height * 0.60],
      [cx, rect.top + rect.height * 0.48]
    ];
    var ok = false;
    for (var i = 0; i < points.length; i++) {
      if (pointerClickAt(points[i][0], points[i][1])) ok = true;
    }
    return ok;
  }

  function dispatchArrowUp() {
    var target = focusSvSurface() || document.activeElement || document.body;
    var codes = [
      { key: 'ArrowUp', code: 'ArrowUp', keyCode: 38, which: 38 },
      { key: 'Up', code: 'ArrowUp', keyCode: 38, which: 38 }
    ];
    var ok = false;
    for (var i = 0; i < codes.length; i++) {
      var c = codes[i];
      try {
        var down = new KeyboardEvent('keydown', {
          key: c.key, code: c.code, keyCode: c.keyCode, which: c.which,
          bubbles: true, cancelable: true, view: window
        });
        var up = new KeyboardEvent('keyup', {
          key: c.key, code: c.code, keyCode: c.keyCode, which: c.which,
          bubbles: true, cancelable: true, view: window
        });
        target.dispatchEvent(down);
        document.dispatchEvent(down);
        window.dispatchEvent(down);
        target.dispatchEvent(up);
        document.dispatchEvent(up);
        ok = true;
      } catch (e) {}
    }
    return ok;
  }

  /* ---- Extension bridge (PRIMARY walk driver, v1.5) ---- */
  var _extPending = {};
  var _extSeq = 0;


  /* ---- v1.7.3: no HUD blur/disable around ext steps (was flickering speed bar) ---- */
  function toastDestrabado() {
    var now = Date.now();
    if (now - (state._lastUnstickToast || 0) < 4000) return;
    state._lastUnstickToast = now;
    toast('destrabado');
  }

  function clearRouteBusy() {
    if (state._routeBusyTimer) {
      clearTimeout(state._routeBusyTimer);
      state._routeBusyTimer = null;
    }
    state.routeBusy = false;
  }

  /** Set routeBusy with hard watchdog so routeTick never freezes forever. */
  function setRouteBusy(watchMs) {
    if (state._routeBusyTimer) {
      clearTimeout(state._routeBusyTimer);
      state._routeBusyTimer = null;
    }
    state.routeBusy = true;
    var ms = (watchMs != null && isFinite(watchMs)) ? Number(watchMs) : ROUTE_BUSY_WATCHDOG_MS;
    state._routeBusyTimer = setTimeout(function () {
      state._routeBusyTimer = null;
      if (!state.routeBusy) return;
      state.routeBusy = false;
      console.warn('[scout] routeBusy watchdog fired (' + ms + 'ms)');
      if (state.route && !state.route.paused) toastDestrabado();
    }, ms);
  }

  function extPost(type, extra) {
    extra = extra || {};
    var reqId = 'u' + (++_extSeq) + '_' + Date.now();
    return new Promise(function (resolve) {
      var settled = false;
      var timer = setTimeout(function () {
        if (settled) return;
        settled = true;
        delete _extPending[reqId];
        resolve({ ok: false, err: 'timeout' });
      }, EXT_STEP_TIMEOUT_MS);
      _extPending[reqId] = function (res) {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        delete _extPending[reqId];
        resolve(res || { ok: false, err: 'empty' });
      };
      try {
        var payload = Object.assign({ source: 'purif-scout', type: type, reqId: reqId, ts: Date.now() }, extra);
        window.postMessage(payload, '*');
        if (type === 'stepForward' || type === 'PURIF_SCOUT_FORWARD') {
          document.dispatchEvent(new CustomEvent('purif-scout-forward', { detail: { reqId: reqId } }));
        }
        if (type === 'step' || type === 'PURIF_SCOUT_STEP') {
          document.dispatchEvent(new CustomEvent('purif-scout-step', { detail: Object.assign({ reqId: reqId }, extra) }));
        }
        try {
          if (window.PURIF_SCOUT_EXT && typeof window.PURIF_SCOUT_EXT.step === 'function') {
            var api = window.PURIF_SCOUT_EXT;
            var p;
            if (type === 'ping') p = api.ping();
            else if (type === 'step' || type === 'PURIF_SCOUT_STEP') p = api.step(extra);
            else if (type === 'stepForward' || type === 'PURIF_SCOUT_FORWARD') p = api.stepForward(extra);
            else if (type === 'turnLeft') p = api.turnLeft(extra.count || 1);
            else if (type === 'turnRight') p = api.turnRight(extra.count || 1);
            if (p && p.then) {
              p.then(function (r) {
                if (_extPending[reqId]) _extPending[reqId]({ ok: !!(r && r.ok), err: (r && r.err) || null, version: r && r.version, detail: r && r.detail });
              });
            }
          }
        } catch (eApi) {}
      } catch (e) {
        settled = true;
        clearTimeout(timer);
        delete _extPending[reqId];
        resolve({ ok: false, err: String(e) });
      }
    });
  }

  function requestExtStep(opts) {
    opts = opts || {};
    return extPost('step', {
      turnDeg: opts.turnDeg,
      turnsLeft: opts.turnsLeft,
      turnsRight: opts.turnsRight,
      forward: opts.forward !== false,
      alsoW: !!opts.alsoW
    });
  }

  function requestExtArrowUp() {
    return extPost('stepForward', {});
  }

  function requestExtPing() {
    return extPost('ping', {});
  }

  function listenExtPing() {
    window.addEventListener('message', function (ev) {
      var d = ev && ev.data;
      if (!d || d.source !== 'purif-scout-ext') return;
      if (d.type === 'PURIF_SCOUT_EXT_READY') {
        state.extAvailable = true;
        state.extVersion = d.version || state.extVersion || '1.5';
        updateHud();
      }
      if (d.type === 'PURIF_SCOUT_STEP_DONE') {
        if (d.ok) {
          state.extAvailable = true;
          state.flechaFailStreak = 0;
          state.walkMethod = 'ext';
        }
        if (d.reqId && _extPending[d.reqId]) {
          _extPending[d.reqId]({ ok: !!d.ok, err: d.err || null, detail: d.detail || null, version: d.version || null });
        }
        updateHud();
      }
    });
    setTimeout(function () { requestExtPing(); }, 400);
    setTimeout(function () { requestExtPing(); }, 2000);
    setTimeout(function () { requestExtPing(); }, 5000);
  }

  function flashPovHud(fromH, toH) {
    var a = (fromH != null && isFinite(fromH)) ? Math.round(fromH) : '?';
    var b = (toH != null && isFinite(toH)) ? Math.round(toH) : '?';
    state.povHud = 'POV ' + a + '°→' + b + '°';
    state.targetBearing = (toH != null && isFinite(toH)) ? toH : null;
    state.povHudUntil = Date.now() + 2200;
    updateHud();
  }

  /** Poll Maps URL heading until closer to target or timeout. */
  function waitHeadingCloser(targetHeading, maxMs, startHeading) {
    return new Promise(function (resolve) {
      var start = Date.now();
      var max = maxMs != null ? maxMs : POV_POLL_MS;
      var best = null;
      var timer = setInterval(function () {
        refreshPose();
        var cur = state.heading;
        var diff = (cur != null && isFinite(cur) && targetHeading != null && isFinite(targetHeading))
          ? Math.abs(angleDiffDeg(targetHeading, cur))
          : null;
        if (diff != null) best = diff;
        var movedHeading = (startHeading != null && cur != null && isFinite(cur) &&
          Math.abs(angleDiffDeg(cur, startHeading)) >= 8);
        if (diff != null && diff <= POV_CLOSE_DEG) {
          clearInterval(timer);
          resolve({ ok: true, diff: diff, heading: cur });
          return;
        }
        if ((Date.now() - start) >= max) {
          clearInterval(timer);
          resolve({ ok: diff != null && diff <= POV_ALIGN_DEG + 10, diff: best, heading: cur, movedHeading: !!movedHeading });
        }
      }, 90);
    });
  }

  /**
   * Rotate POV to face trayecto bearing BEFORE stepping forward.
   * Uses extension step({turnDeg, forward:false}), polls URL heading, up to POV_EXTRA_BURSTS extras.
   */
  function alignPovToBearing(targetBearing, extraBursts) {
    return new Promise(function (resolve) {
      var settled = false;
      function finish(res) {
        if (settled) return;
        settled = true;
        if (hardTimer) clearTimeout(hardTimer);
        resolve(res);
      }
      var hardTimer = setTimeout(function () {
        // Heading poll failed / hung — caller still attempts one ↑
        finish({ ok: false, err: 'pov-timeout', heading: state.heading });
      }, POV_HARD_TIMEOUT_MS);

      refreshPose();
      if (targetBearing == null || !isFinite(targetBearing)) {
        finish({ ok: true, skipped: true });
        return;
      }
      if (!state.extAvailable) {
        rotateTowardHeading(targetBearing);
        finish({ ok: false, err: 'no-ext' });
        return;
      }
      var startH = state.heading;
      flashPovHud(startH, targetBearing);

      function oneBurst(remaining) {
        if (settled) return;
        refreshPose();
        var cur = state.heading;
        var turnDeg = 0;
        if (cur != null && isFinite(cur)) {
          turnDeg = angleDiffDeg(targetBearing, cur);
        } else {
          // Unknown heading — still send a burst toward target guess using last turn sign
          turnDeg = angleDiffDeg(targetBearing, startH != null ? startH : 0);
        }
        if (Math.abs(turnDeg) <= POV_ALIGN_DEG) {
          flashPovHud(cur, targetBearing);
          finish({ ok: true, diff: Math.abs(turnDeg), heading: cur });
          return;
        }
        flashPovHud(cur, targetBearing);
        var beforeH = cur;
        requestExtStep({ turnDeg: turnDeg, forward: false }).then(function () {
          if (settled) return null;
          return waitHeadingCloser(targetBearing, Math.min(POV_POLL_MS, 500), beforeH);
        }).then(function (res) {
          if (settled) return;
          refreshPose();
          var diff = (state.heading != null && isFinite(state.heading))
            ? Math.abs(angleDiffDeg(targetBearing, state.heading))
            : (res && res.diff);
          flashPovHud(state.heading, targetBearing);
          if (diff != null && diff <= POV_CLOSE_DEG) {
            finish({ ok: true, diff: diff, heading: state.heading });
            return;
          }
          // Heading didn't update or still far — extra turn bursts (max remaining)
          if (remaining > 0 && (diff == null || diff > POV_CLOSE_DEG)) {
            oneBurst(remaining - 1);
            return;
          }
          // Poll failed — still ok to attempt ↑ (caller does)
          finish({ ok: diff != null && diff <= POV_ALIGN_DEG + 15, diff: diff, heading: state.heading });
        }).catch(function (e) {
          finish({ ok: false, err: String(e) });
        });
      }

      var bursts = (extraBursts != null && isFinite(extraBursts)) ? Number(extraBursts) : POV_EXTRA_BURSTS;
      oneBurst(bursts);
    });
  }

    /** Rotate view using real HTML buttons (trusted .click works). */
  function rotateTowardHeading(targetHeading) {
    refreshPose();
    var cur = state.heading;
    if (cur == null || !isFinite(cur) || targetHeading == null || !isFinite(targetHeading)) return false;
    var diff = angleDiffDeg(targetHeading, cur);
    if (Math.abs(diff) < 25) return false;
    var wantClockwise = diff > 0;
    var labels = wantClockwise
      ? [/clockwise|horario|Rotate the view clockwise|Girar.*horario/i]
      : [/counterclockwise|antihorario|counter-clockwise|Rotate the view counterclockwise|Girar.*anti/i];
    var btns = document.querySelectorAll('button[aria-label]');
    var clicked = false;
    for (var i = 0; i < btns.length; i++) {
      var a = btns[i].getAttribute('aria-label') || '';
      for (var j = 0; j < labels.length; j++) {
        if (labels[j].test(a)) {
          clickEl(btns[i]);
          clicked = true;
          break;
        }
      }
      if (clicked) break;
    }
    return clicked;
  }

  function poseSnapshot() {
    refreshPose();
    return {
      lat: state.lat,
      lng: state.lng,
      heading: state.heading,
      href: location.href,
      key: poseKey()
    };
  }

  function poseChanged(before, minM) {
    refreshPose();
    if (!before) return false;
    if (before.href && location.href !== before.href) {
      // URL changed without full reload (SPA) — good
      if (state.lat != null && before.lat != null) {
        var d = haversineM(before.lat, before.lng, state.lat, state.lng);
        if (d >= (minM || 3)) return true;
      }
      // panoid token change
      if (/!1s([^!]+)/.test(location.href) && /!1s([^!]+)/.test(before.href)) {
        var a = (location.href.match(/!1s([^!]+)/) || [])[1];
        var b = (before.href.match(/!1s([^!]+)/) || [])[1];
        if (a && b && a !== b) return true;
      }
    }
    if (state.lat != null && before.lat != null) {
      if (haversineM(before.lat, before.lng, state.lat, state.lng) >= (minM || 3)) return true;
    }
    if (before.key && poseKey() && before.key !== poseKey()) return true;
    return false;
  }

  /**
   * One soft forward step. Returns Promise<boolean> moved.
   * preferredHeading: optional bearing to face before stepping (trayecto).
   * allowUrlRecovery: if true, after URL_RECOVERY_EVERY flecha fails, do one URL jump.
   */
  function waitPoseChange(before, minM, maxMs) {
    return new Promise(function (resolve) {
      var start = Date.now();
      var maxChecks = Math.max(6, Math.floor((maxMs || 1200) / 100));
      var checks = 0;
      var timer = setInterval(function () {
        checks++;
        if (poseChanged(before, minM || 2.5)) {
          clearInterval(timer);
          resolve(true);
          return;
        }
        if (checks >= maxChecks || (Date.now() - start) > (maxMs || 1200)) {
          clearInterval(timer);
          resolve(false);
        }
      }, 100);
    });
  }

  /**
   * One soft forward step. Extension FIRST (required for reliable move).
   * preferredHeading: bearing to face before stepping (trayecto).
   * allowUrlRecovery: rare URL jump after many fails.
   */
  function smoothStepForward(preferredHeading, allowUrlRecovery) {
    return new Promise(function (resolve) {
      refreshPose();
      if (!state.inSV && state.lat == null) {
        toast('Entra a Street View (peoncito)');
        resolve(false);
        return;
      }

      function afterMove(moved, method) {
        if (moved) {
          state.flechaFailStreak = 0;
          state.autoFailStreak = 0;
          state.walkMethod = method || (state.extAvailable ? 'ext' : 'flecha SV');
          updateHud();
          resolve(true);
          return;
        }
        state.flechaFailStreak = (state.flechaFailStreak || 0) + 1;
        if (state.flechaFailStreak % 2 === 1) {
          var dir = (state._autoRotateDir || 1) * -1;
          state._autoRotateDir = dir;
          if (state.extAvailable) {
            // Align a bit then Up (don't combine poorly)
            requestExtStep({ turnDeg: dir * 45, forward: false }).then(function () {
              return requestExtStep({ turnDeg: 0, forward: true });
            });
          } else {
            var base = (preferredHeading != null && isFinite(preferredHeading))
              ? preferredHeading
              : (state.heading || 0);
            rotateTowardHeading((base + dir * 45 + 360) % 360);
            clickChevronZones();
            dispatchArrowUp();
          }
        }

        if (allowUrlRecovery && state.flechaFailStreak > 0 &&
            state.flechaFailStreak % URL_RECOVERY_EVERY === 0 &&
            state.lat != null) {
          state.urlRecoveryCount = (state.urlRecoveryCount || 0) + 1;
          var h = (preferredHeading != null && isFinite(preferredHeading))
            ? preferredHeading
            : (state.heading || 0);
          var next = offsetLatLng(state.lat, state.lng, h, forwardMeters());
          toast('⚠ Recovery URL #' + state.urlRecoveryCount + ' (flash) tras ' + state.flechaFailStreak + ' fallos');
          navigateToSv(next.lat, next.lng, h);
          resolve(false);
          return;
        }

        if (state.flechaFailStreak >= DEAD_END_FAILS) {
          if (state.autoWalk) setAutoWalk(false);
          if (!state.extAvailable) {
            toast('⏹ INSTALA la extensión — sin ella Maps ignora la flecha');
          } else {
            toast('⏹ Sin avance tras ' + DEAD_END_FAILS + ' intentos — gira la vista o reanuda');
          }
        }
        updateHud();
        resolve(false);
      }

      function doForwardOnly() {
        var before = poseSnapshot();
        state.walkMethod = state.extAvailable ? 'ext' : 'ext?';
        state._lastWalkMethod = 'ext';
        updateHud();
        requestExtStep({ turnDeg: 0, forward: true }).then(function (res) {
          if (res && res.ok) {
            state.extAvailable = true;
            return waitPoseChange(before, 2.0, 1100).then(function (moved) {
              if (moved) { afterMove(true, 'ext'); return true; }
              return requestExtArrowUp().then(function () {
                return waitPoseChange(before, 2.0, 900).then(function (moved2) {
                  if (moved2) { afterMove(true, 'ext'); return true; }
                  return false;
                });
              });
            });
          }
          return false;
        }).then(function (done) {
          if (done) return;
          if (!state.extAvailable) {
            toast('⚠ Sin extensión — no camina solo. Instala extension/ (HUD rojo)');
          }
          if (preferredHeading != null && isFinite(preferredHeading)) {
            rotateTowardHeading(preferredHeading);
          }
          var arrows = findSvNavArrowEls(preferredHeading);
          if (arrows.length) clickEl(arrows[0].el);
          clickChevronZones();
          dispatchArrowUp();
          requestExtStep({ turnDeg: 0, forward: true }).then(function () {
            waitPoseChange(before, 2.5, 1000).then(function (moved) {
              afterMove(moved, moved && state.extAvailable ? 'ext' : 'fallback');
            });
          });
        }).catch(function () {
          afterMove(false, 'err');
        });
      }

      // v1.7: if POV far from trayecto bearing → rotate FIRST, then ArrowUp only
      var needAlign = false;
      var turnDeg = 0;
      if (preferredHeading != null && isFinite(preferredHeading) && state.heading != null && isFinite(state.heading)) {
        turnDeg = angleDiffDeg(preferredHeading, state.heading);
        if (Math.abs(turnDeg) > POV_ALIGN_DEG) needAlign = true;
        else if (Math.abs(turnDeg) < EXT_TURN_THRESH) turnDeg = 0;
      } else if (preferredHeading != null && isFinite(preferredHeading)) {
        needAlign = true;
      }

      if (needAlign && state.extAvailable) {
        alignPovToBearing(preferredHeading).then(function () {
          refreshPose();
          doForwardOnly();
        }).catch(function () {
          doForwardOnly();
        });
        return;
      }

      // Small/no turn: single step (ext may still apply tiny turnDeg if any)
      if (turnDeg && Math.abs(turnDeg) >= EXT_TURN_THRESH && state.extAvailable) {
        var before2 = poseSnapshot();
        state.walkMethod = 'ext';
        updateHud();
        requestExtStep({ turnDeg: turnDeg, forward: true }).then(function (res) {
          if (res && res.ok) {
            return waitPoseChange(before2, 2.0, 1100).then(function (moved) {
              if (moved) { afterMove(true, 'ext'); return true; }
              return false;
            });
          }
          return false;
        }).then(function (done) {
          if (!done) doForwardOnly();
        }).catch(function () { doForwardOnly(); });
        return;
      }

      doForwardOnly();
    });
  }


  function advanceOneStep() {
    // HUD ▶ Siguiente — one flecha SV step (or trayecto soft step)
    if (state.route && state.route.status === 'running') {
      if (state.route.paused) {
        state.route.paused = false;
        saveRoute();
      }
      var r = state.route;
      if (r.i >= r.points.length) {
        stopRoute('✅ Trayecto completo · ' + r.name);
        return;
      }
      refreshPose();
      var pt = r.points[r.i];
      var nxt = r.points[r.i + 1];
      var heading = nxt ? bearingDeg(pt.lat, pt.lng, nxt.lat, nxt.lng)
        : bearingDeg(state.lat || pt.lat, state.lng || pt.lng, pt.lat, pt.lng);
      if (state.lat != null && haversineM(state.lat, state.lng, pt.lat, pt.lng) < NEAR_WP_M) {
        r.i += 1;
        r.failStreak = 0;
        saveRoute();
        updateHud();
        if (r.i >= r.points.length) {
          stopRoute('✅ Trayecto completo · ' + r.name);
          return;
        }
        pt = r.points[r.i];
        nxt = r.points[r.i + 1];
        heading = nxt ? bearingDeg(pt.lat, pt.lng, nxt.lat, nxt.lng) : heading;
      }
      // Prefer heading toward current waypoint
      if (state.lat != null) {
        heading = bearingDeg(state.lat, state.lng, pt.lat, pt.lng);
      }
      setRouteBusy();
      setRouteStatus('manual ▶ punto ' + (r.i + 1) + '/' + r.points.length + ' · ext');
      saveRoute();
      smoothStepForward(heading, true).then(function () {
        clearRouteBusy();
        refreshPose();
        if (state.lat != null && haversineM(state.lat, state.lng, pt.lat, pt.lng) < NEAR_WP_M) {
          r.i += 1;
          r.failStreak = 0;
          saveRoute();
        }
        updateHud();
      });
      return;
    }
    if (!state.inSV && state.lat == null) {
      toast('Entra a Street View (arrastra el peoncito)');
      return;
    }
    smoothStepForward(state.heading, false);
  }

  function autoWalkTick() {
    if (!state.autoWalk || state.commentOpen) return;
    if (state.route && !state.route.paused) return;
    if (state._autoBusy) return;
    state._autoBusy = true;
    smoothStepForward(state.heading, true).then(function () {
      state._autoBusy = false;
      updateHud();
    }).catch(function () {
      state._autoBusy = false;
    });
  }

  function setAutoWalk(on) {
    state.autoWalk = !!on;
    if (!on) {
      state.autoFailStreak = 0;
      state.flechaFailStreak = 0;
    }
    if (state.autoTimer) {
      clearInterval(state.autoTimer);
      state.autoTimer = null;
    }
    if (state._autoResumeTimer) {
      clearTimeout(state._autoResumeTimer);
      state._autoResumeTimer = null;
    }
    // v1.4: do NOT persist auto-walk across reloads for URL chaining — Space walk stays in-page
    persistAutoWalkFlag(false);
    clearAutoWalkMeta();
    if (state.autoWalk) {
      if (state.commentOpen) {
        state.autoWalk = false;
        toast('Cierra el comentario antes de auto-walk');
        updateHud();
        return;
      }
      if (state.route && !state.route.paused) {
        state.autoWalk = false;
        toast('Pausa el trayecto antes de auto-walk (Space)');
        updateHud();
        return;
      }
      if (!state.inSV) {
        state.autoWalk = false;
        toast('Entra a Street View (peoncito) para flecha SV');
        updateHud();
        return;
      }
      state.walkMethod = 'flecha SV';
      if (!state.extAvailable) toast('⚠ Sin extensión — auto-walk no se moverá');
      state.autoTimer = setInterval(autoWalkTick, state.autoMs);
      setTimeout(autoWalkTick, 250);
      toast('▶ Auto-walk ON · ext (' + (state.autoMs / 1000).toFixed(1) + 's) — sin flash URL');
    } else {
      toast('⏸ Auto-walk OFF');
    }
    updateHud();
  }

  function resumeAutoWalkFromPersist() {
    // v1.4: Space walk no longer survives URL reloads (by design). Clear stale v1.3 flags.
    if (readAutoWalkFlag()) {
      persistAutoWalkFlag(false);
      clearAutoWalkMeta();
    }
    return false;
  }

  function setAutoMs(ms, fromUser) {
    ms = Math.max(ROUTE_MS_MIN, Math.min(ROUTE_MS_MAX, Number(ms) || DEFAULT_AUTO_MS));
    // Snap to slider step 100
    ms = Math.round(ms / 100) * 100;
    if (ms < ROUTE_MS_MIN) ms = ROUTE_MS_MIN;
    if (ms > ROUTE_MS_MAX) ms = ROUTE_MS_MAX;
    if (ms === state.autoMs && !fromUser) {
      syncSpeedUi();
      return;
    }
    state.autoMs = ms;
    try { if (typeof GM_setValue === 'function') GM_setValue(LS_SPEED, ms); } catch (e) {}
    try { localStorage.setItem(LS_SPEED, String(ms)); } catch (e2) {}
    syncSpeedUi();
    if (state.autoWalk && state.autoTimer) {
      clearInterval(state.autoTimer);
      state.autoTimer = setInterval(autoWalkTick, state.autoMs);
    }
    if (state.route && !state.route.paused && state.routeTimer) {
      clearInterval(state.routeTimer);
      state.routeTimer = setInterval(routeTick, routeIntervalMs());
    }
  }

  function syncSpeedUi() {
    var lab = document.getElementById('purif-scout-speed-label');
    if (lab) lab.textContent = (state.autoMs / 1000).toFixed(1) + 's';
  }

  /** − = slower (↑ ms), + = faster (↓ ms). Buttons never take ArrowLeft focus. */
  function bumpAutoMs(dir) {
    // dir +1 → faster (lower ms), dir -1 → slower (higher ms)
    setAutoMs(state.autoMs - (dir * SPEED_STEP_MS), true);
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
          'User-Agent': 'PurificadorasScout/1.3 (CASCA-code; field scout)'
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

    var MAX_PTS = MAX_ROUTE_PTS;
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

  /**
   * Full street-coverage walk (Chinese Postman approximation on undirected multigraph).
   * 1) Clip OSM ways to colonia polygon → atomic edges between snapped nodes.
   * 2) Per connected component: pair odd-degree nodes (greedy shortest paths) → Eulerian.
   * 3) Hierholzer circuit → sample waypoints every STEP_M.
   * Returns { points, streetCount, edgeCount, capped }.
   */
  
  /** Precompute turnDeg / exitBearing at each WP (bearing in→out). Deterministic steering. */
  function annotateRouteTurns(points) {
    if (!points || points.length < 2) return points;
    for (var i = 0; i < points.length; i++) {
      var prev = points[i - 1];
      var cur = points[i];
      var nxt = points[i + 1];
      var inB = null, outB = null, turn = 0;
      if (prev) inB = bearingDeg(prev.lat, prev.lng, cur.lat, cur.lng);
      if (nxt) outB = bearingDeg(cur.lat, cur.lng, nxt.lat, nxt.lng);
      if (inB != null && outB != null) turn = angleDiffDeg(outB, inB);
      cur.turnDeg = turn;
      cur.inBearing = inB;
      cur.exitBearing = outB != null ? outB : inB;
      cur.isCorner = Math.abs(turn) >= CORNER_TURN_DEG;
    }
    return points;
  }

  function formatNextTurnHud(turnDeg) {
    if (turnDeg == null || !isFinite(turnDeg) || Math.abs(turnDeg) < CORNER_TURN_DEG) return null;
    var abs = Math.round(Math.abs(turnDeg));
    if (turnDeg > 0) return '↳ der ' + abs + '°';
    return '↰ izq ' + abs + '°';
  }

function waysToCoveragePoints(elements, geom) {
    var NODE_PREC = 5; // ~1.1 m snap
    var ways = [];
    (elements || []).forEach(function (el) {
      if (!el || el.type !== 'way' || !el.geometry || el.geometry.length < 2) return;
      var hw = (el.tags && el.tags.highway) || '';
      if (hw === 'service' && el.tags && /parking|driveway/i.test(el.tags.service || '')) return;
      var coords = [];
      for (var i = 0; i < el.geometry.length; i++) {
        var g = el.geometry[i];
        if (pointInPolygon(g.lon, g.lat, geom)) coords.push([g.lon, g.lat]);
        else if (coords.length >= 2) {
          ways.push(coords);
          coords = [];
        } else coords = [];
      }
      if (coords.length >= 2) ways.push(coords);
    });
    if (!ways.length) return { points: [], streetCount: 0, edgeCount: 0, capped: false };

    function nodeKey(lng, lat) {
      return roundCoord(lng, NODE_PREC) + ',' + roundCoord(lat, NODE_PREC);
    }
    function roundCoord(x, p) {
      var m = Math.pow(10, p);
      return Math.round(x * m) / m;
    }
    function parseKey(k) {
      var sp = k.split(',');
      return { lng: Number(sp[0]), lat: Number(sp[1]) };
    }

    var adj = {}; // nodeKey -> [{v, eid}]
    var edges = []; // {a,b,coords:[[lng,lat],...], len}

    function addAdj(u, v, eid) {
      if (!adj[u]) adj[u] = [];
      adj[u].push({ v: v, eid: eid });
    }

    for (var wi = 0; wi < ways.length; wi++) {
      var w = ways[wi];
      for (var j = 0; j < w.length - 1; j++) {
        var aLng = w[j][0], aLat = w[j][1];
        var bLng = w[j + 1][0], bLat = w[j + 1][1];
        var a = nodeKey(aLng, aLat);
        var b = nodeKey(bLng, bLat);
        if (a === b) continue;
        var len = haversineM(aLat, aLng, bLat, bLng);
        if (len < 0.4) continue;
        var eid = edges.length;
        edges.push({
          a: a,
          b: b,
          coords: [[aLng, aLat], [bLng, bLat]],
          len: len
        });
        addAdj(a, b, eid);
        addAdj(b, a, eid);
      }
    }
    if (!edges.length) return { points: [], streetCount: ways.length, edgeCount: 0, capped: false };

    // Connected components
    var seen = {};
    var comps = [];
    Object.keys(adj).forEach(function (n) {
      if (seen[n]) return;
      var stack = [n];
      seen[n] = true;
      var nodes = [];
      while (stack.length) {
        var u = stack.pop();
        nodes.push(u);
        (adj[u] || []).forEach(function (e) {
          if (!seen[e.v]) { seen[e.v] = true; stack.push(e.v); }
        });
      }
      comps.push(nodes);
    });
    // Longer components first (main street network before stubs)
    comps.sort(function (A, B) { return B.length - A.length; });

    function dijkstra(compSet, start) {
      var dist = {};
      var prev = {};
      dist[start] = 0;
      // binary-ish heap via sorted insert is fine for colonia size
      var pq = [{ d: 0, u: start }];
      function pushPq(item) {
        pq.push(item);
        var i = pq.length - 1;
        while (i > 0) {
          var p = (i - 1) >> 1;
          if (pq[p].d <= pq[i].d) break;
          var tmp = pq[p]; pq[p] = pq[i]; pq[i] = tmp;
          i = p;
        }
      }
      function popPq() {
        var top = pq[0];
        var last = pq.pop();
        if (!pq.length) return top;
        pq[0] = last;
        var i = 0;
        for (;;) {
          var l = i * 2 + 1, r = l + 1, sm = i;
          if (l < pq.length && pq[l].d < pq[sm].d) sm = l;
          if (r < pq.length && pq[r].d < pq[sm].d) sm = r;
          if (sm === i) break;
          var t2 = pq[i]; pq[i] = pq[sm]; pq[sm] = t2;
          i = sm;
        }
        return top;
      }
      while (pq.length) {
        var cur = popPq();
        if (cur.d !== dist[cur.u]) continue;
        var nbrs = adj[cur.u] || [];
        for (var ni = 0; ni < nbrs.length; ni++) {
          var v = nbrs[ni].v;
          if (!compSet[v]) continue;
          var eid = nbrs[ni].eid;
          var nd = cur.d + edges[eid].len;
          if (dist[v] == null || nd < dist[v]) {
            dist[v] = nd;
            prev[v] = { u: cur.u, eid: eid };
            pushPq({ d: nd, u: v });
          }
        }
      }
      return { dist: dist, prev: prev };
    }

    function reconstruct(prev, start, goal) {
      var out = [];
      var u = goal;
      while (u !== start) {
        if (!prev[u]) return null;
        out.push(prev[u].eid);
        u = prev[u].u;
      }
      out.reverse();
      return out;
    }

    var walkLngLat = []; // continuous covering polyline [lng,lat]
    var totalEdges = 0;

    for (var ci = 0; ci < comps.length; ci++) {
      var comp = comps[ci];
      var compSet = {};
      for (var ci2 = 0; ci2 < comp.length; ci2++) compSet[comp[ci2]] = true;

      var compEids = [];
      for (var ei = 0; ei < edges.length; ei++) {
        if (compSet[edges[ei].a] && compSet[edges[ei].b]) compEids.push(ei);
      }
      totalEdges += compEids.length;
      if (!compEids.length) continue;

      var deg = {};
      for (var di = 0; di < compEids.length; di++) {
        var ed = edges[compEids[di]];
        deg[ed.a] = (deg[ed.a] || 0) + 1;
        deg[ed.b] = (deg[ed.b] || 0) + 1;
      }
      var odds = [];
      for (var oi = 0; oi < comp.length; oi++) {
        if ((deg[comp[oi]] || 0) % 2 === 1) odds.push(comp[oi]);
      }

      // Greedy odd-pairing via shortest paths (CPP approximation)
      var duplicateEids = [];
      var rem = odds.slice();
      while (rem.length >= 2) {
        var s = rem.shift();
        var dj = dijkstra(compSet, s);
        var best = null;
        var bestD = Infinity;
        for (var ri = 0; ri < rem.length; ri++) {
          var t = rem[ri];
          if (dj.dist[t] != null && dj.dist[t] < bestD) {
            bestD = dj.dist[t];
            best = t;
          }
        }
        if (best == null) break;
        rem.splice(rem.indexOf(best), 1);
        var path = reconstruct(dj.prev, s, best);
        if (path && path.length) {
          for (var pi = 0; pi < path.length; pi++) duplicateEids.push(path[pi]);
        }
      }

      // Multigraph instances for Hierholzer
      var instances = []; // eid per instance
      var multi = {}; // node -> [instIdx]
      function addInst(eid) {
        var e = edges[eid];
        var ii = instances.length;
        instances.push(eid);
        if (!multi[e.a]) multi[e.a] = [];
        if (!multi[e.b]) multi[e.b] = [];
        multi[e.a].push(ii);
        multi[e.b].push(ii);
      }
      for (var ae = 0; ae < compEids.length; ae++) addInst(compEids[ae]);
      for (var de = 0; de < duplicateEids.length; de++) addInst(duplicateEids[de]);

      var usedInst = [];
      for (var ui = 0; ui < instances.length; ui++) usedInst[ui] = false;

      var startNode = comp[0];
      for (var so = 0; so < odds.length; so++) {
        if (compSet[odds[so]]) { startNode = odds[so]; break; }
      }

      var stack = [startNode];
      var nodeCircuit = [];
      while (stack.length) {
        var u = stack[stack.length - 1];
        var advanced = false;
        var bag = multi[u] || [];
        while (bag.length) {
          var ii = bag.pop();
          if (usedInst[ii]) continue;
          usedInst[ii] = true;
          var eid2 = instances[ii];
          var e2 = edges[eid2];
          var v = (u === e2.a) ? e2.b : e2.a;
          stack.push(v);
          advanced = true;
          break;
        }
        if (!advanced) nodeCircuit.push(stack.pop());
      }
      nodeCircuit.reverse();

      // Playback: bag of oriented coords keyed by directed pair
      var orientBag = {};
      function pushOrient(eid) {
        var e = edges[eid];
        var kFwd = e.a + '>' + e.b;
        var kRev = e.b + '>' + e.a;
        if (!orientBag[kFwd]) orientBag[kFwd] = [];
        if (!orientBag[kRev]) orientBag[kRev] = [];
        orientBag[kFwd].push(e.coords);
        orientBag[kRev].push([e.coords[1], e.coords[0]]);
      }
      for (var pe = 0; pe < compEids.length; pe++) pushOrient(compEids[pe]);
      for (var pd = 0; pd < duplicateEids.length; pd++) pushOrient(duplicateEids[pd]);

      var segCoords = [];
      for (var ni = 0; ni < nodeCircuit.length - 1; ni++) {
        var na = nodeCircuit[ni];
        var nb = nodeCircuit[ni + 1];
        var key = na + '>' + nb;
        var lst = orientBag[key];
        if (!lst || !lst.length) continue;
        var coords = lst.pop();
        if (!segCoords.length) {
          for (var c0 = 0; c0 < coords.length; c0++) segCoords.push(coords[c0]);
        } else {
          for (var c1 = 1; c1 < coords.length; c1++) segCoords.push(coords[c1]);
        }
      }

      // Append component walk (gap = component hop later in routeTick)
      if (segCoords.length >= 2) {
        if (!walkLngLat.length) {
          for (var s0 = 0; s0 < segCoords.length; s0++) walkLngLat.push(segCoords[s0]);
        } else {
          // mark discontinuity: still append; hop logic handles large jumps
          for (var s1 = 0; s1 < segCoords.length; s1++) walkLngLat.push(segCoords[s1]);
        }
      }
    }

    if (walkLngLat.length < 2) {
      return { points: [], streetCount: ways.length, edgeCount: totalEdges, capped: false };
    }

    var samples = samplePolyline(walkLngLat, STEP_M);
    var points = [];
    var last = null;
    for (var si = 0; si < samples.length; si++) {
      var pt = samples[si];
      if (!pointInPolygon(pt.lng, pt.lat, geom)) continue;
      if (last && haversineM(last.lat, last.lng, pt.lat, pt.lng) < STEP_M * 0.4) continue;
      points.push(pt);
      last = pt;
    }

    var capped = false;
    if (points.length > MAX_ROUTE_PTS) {
      capped = true;
      var stride = Math.ceil(points.length / MAX_ROUTE_PTS);
      var thinned = [];
      for (var t = 0; t < points.length; t += stride) thinned.push(points[t]);
      var lastPt = points[points.length - 1];
      if (thinned.length && (thinned[thinned.length - 1].lat !== lastPt.lat || thinned[thinned.length - 1].lng !== lastPt.lng)) {
        thinned.push(lastPt);
      }
      points = thinned;
    }

    annotateRouteTurns(points);

    return {
      points: points,
      streetCount: ways.length,
      edgeCount: totalEdges,
      capped: capped
    };
  }

  function showSvEntryHelp(lat, lng, heading) {
    var link = buildStreetViewUrlPanoAction(lat, lng, heading);
    setRouteStatus('⚠ Sin Street View cerca — peoncito en google.com/maps · NO scout-sv');
    toast('⚠ Arrastra el peoncito a la calle (google.com/maps)');
    state.lastTrayectoError = 'Sin SV en punto. Abre: ' + link;
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
    clearRouteBusy();
    if (state.route) {
      state.route.paused = true;
      state.route.status = 'stopped';
      saveRoute();
    }
    clearRoutePersist();
    state.route = null;
    if (msg) toast(msg);
    updateHud();
  }

  function startRoute(points, name, meta) {
    meta = meta || {};
    if (!points || !points.length) {
      toast('Sin calles OSM en esta colonia');
      return;
    }
    if (state.autoWalk) setAutoWalk(false);
    var streetCount = meta.streetCount || 0;
    var edgeCount = meta.edgeCount || 0;
    var capped = !!meta.capped;
    state.route = {
      name: name || 'colonia',
      points: points,
      i: 0,
      paused: false,
      status: 'running',
      skipped: 0,
      failStreak: 0,
      svFailStreak: 0,
      flechaFailStreak: 0,
      deadEndFails: 0,
      hopFails: 0,
      hopCount: 0,
      streetCount: streetCount,
      edgeCount: edgeCount,
      capped: capped,
      entered: false // first point uses one URL jump to enter colonia SV
    };
    state.routeEntered = false;
    state.hopCount = 0;
    saveRoute();
    if (state.routeTimer) clearInterval(state.routeTimer);
    var iv = routeIntervalMs();
    state.routeTimer = setInterval(routeTick, iv);
    var callesLabel = streetCount ? (streetCount + ' calles') : (edgeCount ? edgeCount + ' tramos' : 'calles');
    var hudLine = 'Trayecto: ' + points.length + ' pts · ~' + callesLabel + ' · cobertura colonia';
    if (capped) hudLine += ' · cap ' + MAX_ROUTE_PTS;
    toast('🛣 ' + hudLine);
    setRouteStatus(hudLine + ' · ' + name);
    if (!state.extAvailable) toast('⚠ Sin extensión — el trayecto no avanzará hasta instalarla');
    updateHud();
    routeTick();
  }

  function resumeRouteFromPersist() {
    var r = loadRoute();
    if (!r || r.status !== 'running') return false;
    state.route = r;
    if (r.svFailStreak == null) r.svFailStreak = 0;
    if (r.flechaFailStreak == null) r.flechaFailStreak = 0;
    clearRouteBusy();
    state.routeEntered = !!r.entered;
    if (state.routeTimer) clearInterval(state.routeTimer);
    if (!r.paused) {
      var iv = routeIntervalMs();
      state.routeTimer = setInterval(routeTick, iv);
      setRouteStatus('reanudado · punto ' + Math.min(r.i + 1, r.points.length) + '/' + r.points.length + ' · ext · ' + r.name);
      // If we just landed from the one-time URL entry, settle then continue with flecha
      setTimeout(function () {
        refreshPose();
        var rt = state.route;
        if (!rt || rt.paused) return;
        if (rt.i < rt.points.length) {
          var pt0 = rt.points[rt.i];
          var near = state.lat != null && haversineM(state.lat, state.lng, pt0.lat, pt0.lng) < NEAR_WP_M * 1.6;
          if (near) {
            rt.entered = true;
            state.routeEntered = true;
            rt.i += 1;
            rt.failStreak = 0;
            rt.svFailStreak = 0;
            rt.flechaFailStreak = 0;
            saveRoute();
            setRouteStatus('punto ' + Math.min(rt.i + 1, rt.points.length) + '/' + rt.points.length + ' · ext · ' + rt.name);
            updateHud();
          } else if (rt.entered) {
            // Soft resume mid-route — keep walking flecha toward current WP
            state.routeEntered = true;
          } else {
            // Entry URL may have failed — mark and let routeTick retry entry once
            state.routeEntered = false;
            rt.entered = false;
          }
        }
        routeTick();
      }, 1200);
    } else {
      setRouteStatus('PAUSA · punto ' + Math.min(r.i + 1, r.points.length) + '/' + r.points.length);
    }
    updateHud();
    return true;
  }

  function routeProgressLabel(r) {
    if (!r || !r.points || !r.points.length) return '';
    var i = Math.min(r.i, r.points.length);
    var n = r.points.length;
    var pct = Math.round((i / n) * 100);
    var calles = r.streetCount ? (r.streetCount + ' calles') : 'calles';
    return (r.name || 'colonia') + ' · ' + i + '/' + n + ' (' + pct + '%) · ' + calles;
  }

  function routeSteerHeading(r, pt, next) {
    // v1.7.2: prefer EXIT bearing of upcoming corner (commit turn early), not "toward next point"
    // which oscillates between left/right link options at SV intersections.
    var heading;
    var corner = null;
    var cornerDist = Infinity;
    if (r && r.points && state.lat != null) {
      // Look ahead up to ~3 WPs / CORNER_LOOKAHEAD_M for a marked corner
      var maxK = Math.min(r.points.length - 1, (r.i != null ? r.i : 0) + 3);
      var startI = (r.i != null ? r.i : 0);
      for (var k = startI; k <= maxK; k++) {
        var cand = r.points[k];
        if (!cand || !cand.isCorner) continue;
        var d = haversineM(state.lat, state.lng, cand.lat, cand.lng);
        if (d <= CORNER_LOOKAHEAD_M && d < cornerDist) {
          corner = cand;
          cornerDist = d;
        }
      }
    }
    if (corner && corner.exitBearing != null && isFinite(corner.exitBearing)) {
      state.nextTurnHud = formatNextTurnHud(corner.turnDeg);
      return corner.exitBearing;
    }
    // Precomputed exit on current WP when close
    if (pt && pt.exitBearing != null && isFinite(pt.exitBearing) && state.lat != null) {
      var distPt = haversineM(state.lat, state.lng, pt.lat, pt.lng);
      if (distPt < CORNER_LOOKAHEAD_M && pt.isCorner) {
        state.nextTurnHud = formatNextTurnHud(pt.turnDeg);
        return pt.exitBearing;
      }
      if (distPt < LOOKAHEAD_NEAR_M && next) {
        state.nextTurnHud = formatNextTurnHud(pt.turnDeg);
        return (pt.exitBearing != null) ? pt.exitBearing : bearingDeg(state.lat, state.lng, next.lat, next.lng);
      }
    }
    state.nextTurnHud = (pt && pt.isCorner) ? formatNextTurnHud(pt.turnDeg) : null;
    if (state.lat != null) {
      var dist = haversineM(state.lat, state.lng, pt.lat, pt.lng);
      if (dist < LOOKAHEAD_NEAR_M && next) {
        heading = bearingDeg(state.lat, state.lng, next.lat, next.lng);
      } else {
        heading = bearingDeg(state.lat, state.lng, pt.lat, pt.lng);
      }
    } else if (next) {
      heading = bearingDeg(pt.lat, pt.lng, next.lat, next.lng);
    } else {
      heading = state.heading || 0;
    }
    return heading;
  }

  /** U-turn ~180° POV change via extension (no ArrowUp), then ready for forward. */
  function doUTurnBurst() {
    refreshPose();
    var start = state.heading;
    var target = (start != null && isFinite(start)) ? ((start + 180) % 360) : null;
    flashPovHud(start, target != null ? target : ((start || 0) + 180));
    // Ext v1.5.1: ~9°/key, MAX 24 → one -180 burst is enough; settle + poll; extra if stuck
    return requestExtStep({ turnDeg: -180, forward: false }).then(function () {
      if (target == null) {
        return requestExtStep({ turnDeg: -90, forward: false });
      }
      return waitHeadingCloser(target, POV_POLL_MS, start).then(function (res) {
        refreshPose();
        var diff = (state.heading != null && target != null)
          ? Math.abs(angleDiffDeg(target, state.heading))
          : 999;
        flashPovHud(state.heading, target);
        if (diff > 35) {
          var rem = angleDiffDeg(target, state.heading || start || 0);
          return requestExtStep({ turnDeg: rem, forward: false }).then(function () {
            return waitHeadingCloser(target, POV_POLL_MS, state.heading);
          });
        }
        return res;
      });
    });
  }

  function routeTick() {
    if (!state.route || state.route.paused || state.routeBusy) return;
    if (state.commentOpen) return;
    var r = state.route;
    if (r.i >= r.points.length) {
      stopRoute('✅ Trayecto completo · ' + r.name);
      setRouteStatus('Completo · ' + r.points.length + ' pts · skip ' + (r.skipped || 0) + ' · hops ' + (r.hopCount || 0));
      return;
    }
    var pt = r.points[r.i];
    var next = r.points[r.i + 1];
    refreshPose();

    // Already near waypoint → advance index (no teleport)
    if (state.lat != null && haversineM(state.lat, state.lng, pt.lat, pt.lng) < NEAR_WP_M) {
      r.i += 1;
      r.failStreak = 0;
      r.svFailStreak = 0;
      r.flechaFailStreak = 0;
      r.deadEndFails = 0;
      r.hopFails = 0;
      r.entered = true;
      state.routeEntered = true;
      saveRoute();
      setRouteStatus(routeProgressLabel(r));
      updateHud();
      return;
    }

    // ONE-TIME URL entry to first colonia point (only way we intentionally flash)
    if (!r.entered && !state.routeEntered) {
      var entryHeading = next ? bearingDeg(pt.lat, pt.lng, next.lat, next.lng) : (state.heading || 0);
      r.entered = true;
      state.routeEntered = true;
      saveRoute();
      setRouteBusy(2000);
      setRouteStatus('entrada URL (1×) · luego cobertura calles · ' + r.name);
      updateHud();
      toast('Entrada colonia: 1 salto URL, luego camina todas las calles');
      navigateToSv(pt.lat, pt.lng, entryHeading, { silentWarn: false });
      setTimeout(function () { clearRouteBusy(); }, 1500);
      return;
    }

    var heading = routeSteerHeading(r, pt, next);
    var turnDelta = 0;
    if (state.heading != null && isFinite(state.heading) && isFinite(heading)) {
      turnDelta = angleDiffDeg(heading, state.heading);
    }
    var distToWp = (state.lat != null) ? haversineM(state.lat, state.lng, pt.lat, pt.lng) : Infinity;

    // Guard: never overlap ticks without a clear path
    if (state.routeBusy) return;
    setRouteBusy();
    setRouteStatus(routeProgressLabel(r) + (state.extAvailable ? ' · ext' : ' · SIN EXT'));
    saveRoute();
    updateHud();

    function afterStep(moved) {
      clearRouteBusy();
      refreshPose();
      if (!state.route || state.route !== r) return;
      if (state.lat != null && haversineM(state.lat, state.lng, pt.lat, pt.lng) < NEAR_WP_M) {
        r.i += 1;
        r.failStreak = 0;
        r.svFailStreak = 0;
        r.flechaFailStreak = 0;
        r.deadEndFails = 0;
        r.hopFails = 0;
        r.stuckPose = 0;
        r._unstickUturn = false;
        saveRoute();
        setRouteStatus(routeProgressLabel(r));
        updateHud();
        return;
      }
      if (!moved) {
        r.flechaFailStreak = (r.flechaFailStreak || 0) + 1;
        r.failStreak = (r.failStreak || 0) + 1;
        r.deadEndFails = (r.deadEndFails || 0) + 1;
        r.hopFails = (r.hopFails || 0) + 1;
        r.stuckPose = (r.stuckPose || 0) + 1;

        // v1.7.3: pose unchanged for N steps after turn+↑ → U-turn once, then skip WP
        if (r.stuckPose >= STUCK_POSE_N) {
          r.stuckPose = 0;
          if (!r._unstickUturn && state.extAvailable) {
            r._unstickUturn = true;
            r.deadEndFails = 0;
            toastDestrabado();
            setRouteBusy();
            doUTurnBurst().then(function () {
              clearRouteBusy();
              saveRoute();
              updateHud();
            }).catch(function () { clearRouteBusy(); });
            return;
          }
          // Already tried U-turn — skip waypoint and continue
          r._unstickUturn = false;
          r.skipped = (r.skipped || 0) + 1;
          r.i += 1;
          r.flechaFailStreak = 0;
          r.deadEndFails = 0;
          toastDestrabado();
          setRouteStatus('destrabado · skip · ' + routeProgressLabel(r));
          saveRoute();
          updateHud();
          return;
        }

        // Dead-end: ArrowUp didn't move → U-turn, stay on covering path (includes reverse)
        if (r.deadEndFails >= ROUTE_DEAD_END_FAILS && state.extAvailable) {
          r.deadEndFails = 0;
          setRouteBusy();
          toast('↩ Calle sin salida — U-turn');
          doUTurnBurst().then(function () {
            clearRouteBusy();
            saveRoute();
            updateHud();
          }).catch(function () { clearRouteBusy(); });
          return;
        }

        // Component hop: next WP far + stuck ≥5 → ONE pano jump
        if (r.hopFails >= ROUTE_HOP_FAILS && distToWp > HOP_DIST_M) {
          r.hopFails = 0;
          r.deadEndFails = 0;
          r.stuckPose = 0;
          r.hopCount = (r.hopCount || 0) + 1;
          state.hopCount = r.hopCount;
          var hopH = next ? bearingDeg(pt.lat, pt.lng, next.lat, next.lng) : heading;
          toast('otra calle');
          setRouteStatus('hop → otra calle · ' + routeProgressLabel(r));
          saveRoute();
          navigateToSv(pt.lat, pt.lng, hopH, { silentWarn: true });
          return;
        }

        // Soft skip only after many fails when already close-ish (avoid skipping whole streets)
        if (r.flechaFailStreak >= 10 && distToWp < HOP_DIST_M) {
          r.skipped = (r.skipped || 0) + 1;
          r.i += 1;
          r.flechaFailStreak = 0;
          r.deadEndFails = 0;
          r.stuckPose = 0;
          setRouteStatus('skip · ' + routeProgressLabel(r));
          toast('Skip punto (flecha no avanza)');
        }
        saveRoute();
        updateHud();
      } else {
        r.flechaFailStreak = 0;
        r.deadEndFails = 0;
        r.hopFails = 0;
        r.stuckPose = 0;
        r._unstickUturn = false;
        saveRoute();
      }
    }

    // v1.7.2: face EXIT bearing early at corners; stronger bursts at multi-link turns
    var cornerCommit = false;
    var extra = POV_EXTRA_BURSTS;
    if (state.lat != null && pt) {
      var dCorner = haversineM(state.lat, state.lng, pt.lat, pt.lng);
      if (pt.isCorner && Math.abs(pt.turnDeg || 0) >= CORNER_TURN_DEG && dCorner <= CORNER_LOOKAHEAD_M) {
        cornerCommit = true;
        extra = POV_EXTRA_BURSTS + CORNER_EXTRA_BURSTS;
        if (pt.exitBearing != null && isFinite(pt.exitBearing)) heading = pt.exitBearing;
        state.nextTurnHud = formatNextTurnHud(pt.turnDeg);
      } else if (next && next.isCorner && Math.abs(next.turnDeg || 0) >= CORNER_TURN_DEG) {
        var dNext = haversineM(state.lat, state.lng, next.lat, next.lng);
        if (dNext <= CORNER_LOOKAHEAD_M) {
          cornerCommit = true;
          extra = POV_EXTRA_BURSTS + CORNER_EXTRA_BURSTS;
          if (next.exitBearing != null && isFinite(next.exitBearing)) heading = next.exitBearing;
          state.nextTurnHud = formatNextTurnHud(next.turnDeg);
        }
      }
    }
    if (state.heading != null && isFinite(state.heading) && isFinite(heading)) {
      turnDelta = angleDiffDeg(heading, state.heading);
    }

    if ((cornerCommit || Math.abs(turnDelta) > STRONG_TURN_DEG) && state.extAvailable) {
      flashPovHud(state.heading, heading);
      alignPovToBearing(heading, extra).then(function () {
        // POV may have timed out — still attempt one ↑ and advance logic
        return smoothStepForward(heading, false);
      }).then(afterStep).catch(function () {
        clearRouteBusy();
      });
      return;
    }

    if (isFinite(heading)) flashPovHud(state.heading, heading);
    smoothStepForward(heading, true).then(afterStep).catch(function () {
      clearRouteBusy();
    });
  }

  function waitArrive(pt, r, heading) {
    // Kept as no-op stub — v1.4 trayecto no longer waits on URL reload per tick.
    // Soft flecha steps resolve via smoothStepForward promise in routeTick.
    return;
  }

  function toggleRoutePause() {
    if (!state.route) return false;
    state.route.paused = !state.route.paused;
    if (state.route.paused) {
      clearRouteBusy();
      toast('⏸ Trayecto pausado');
      setRouteStatus('PAUSA · punto ' + Math.min(state.route.i + 1, state.route.points.length) + '/' + state.route.points.length);
    } else {
      clearRouteBusy();
      toast('▶ Trayecto reanudado · ext');
      if (!state.routeTimer) state.routeTimer = setInterval(routeTick, routeIntervalMs());
      setTimeout(routeTick, 200);
    }
    saveRoute();
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

    function finishOk(cover, source) {
      state.trayectoBuilding = false;
      setRetryVisible(false);
      var pts = (cover && cover.points) ? cover.points : (cover || []);
      var meta = {
        streetCount: (cover && cover.streetCount) || 0,
        edgeCount: (cover && cover.edgeCount) || 0,
        capped: !!(cover && cover.capped),
        source: source
      };
      if (!pts.length) {
        showTrayectoError('Sin puntos de cobertura en ' + name);
        return;
      }
      var calles = meta.streetCount ? ('~' + meta.streetCount + ' calles') : 'cobertura colonia';
      var line = 'Trayecto: ' + pts.length + ' pts · ' + calles + ' · cobertura colonia';
      if (meta.capped) line += ' · cap ' + MAX_ROUTE_PTS;
      setRouteStatus(line + ' · ' + source + ' · ' + name);
      startRoute(pts, name, meta);
    }

    function tryLiveOverpass() {
      setRouteStatus('Consultando OSM Overpass…');
      // Hard ceiling ~22s across mirrors — never infinite "consultando…"
      return withHardTimeout(
        overpassHighways(bbox),
        22000,
        'overpass-total'
      ).then(function (data) {
        var cover = waysToCoveragePoints(data.elements || [], geom);
        if (cover.points.length >= MIN_ROUTE_PTS) {
          finishOk(cover, 'Overpass');
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
        finishOk({ points: pts, streetCount: 0, edgeCount: 0, capped: pts.length >= MAX_ROUTE_PTS }, 'rejilla ' + GRID_STEP_M + 'm');
        toast('⚠ Sin calles OSM — usando rejilla (' + reason + ')');
        return;
      }
      state.trayectoBuilding = false;
      showTrayectoError('No se pudo armar trayecto (' + reason + '). Reintentar.');
    }

    // 1) Prebaked roads (preferred — no live Overpass)
    loadPrebakedRoads().then(function (fc) {
      var elements = geojsonRoadsToElements(fc, bbox);
      var cover = waysToCoveragePoints(elements, geom);
      if (cover.points.length >= MIN_ROUTE_PTS) {
        finishOk(cover, 'prebaked');
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
      '#purif-scout-left{position:fixed;top:64px;left:10px;width:240px;max-width:240px;',
      'display:flex;flex-direction:column;gap:6px;pointer-events:none}',
      '#purif-scout-hud{pointer-events:auto;background:rgba(28,25,23,.9);color:#e7e5e4;',
      'padding:8px 9px;border-radius:10px;font-size:11px;line-height:1.3;',
      'box-shadow:0 6px 18px rgba(0,0,0,.32);backdrop-filter:blur(5px);',
      'border:1px solid rgba(255,255,255,.06)}',
      '#purif-scout-hud b{color:#fff;font-weight:700}',
      '#purif-scout-hud .top{display:flex;align-items:center;justify-content:space-between;',
      'gap:6px;margin-bottom:4px}',
      '#purif-scout-hud .ext-dot{display:inline-flex;align-items:center;gap:5px;',
      'font:600 10px/1 system-ui;opacity:.9}',
      '#purif-scout-hud .ext-dot i{width:8px;height:8px;border-radius:50%;display:inline-block;',
      'box-shadow:0 0 0 2px rgba(0,0,0,.25)}',
      '#purif-scout-hud .ext-dot.ok i{background:#22c55e}',
      '#purif-scout-hud .ext-dot.bad i{background:#ef4444;animation:purif-pulse 1.4s ease infinite}',
      '@keyframes purif-pulse{0%,100%{opacity:1}50%{opacity:.55}}',
      '#purif-scout-hud .menu-wrap{position:relative}',
      '#purif-scout-hud .menu-btn{border:0;background:transparent;color:#a8a29e;cursor:pointer;',
      'font:700 14px/1 system-ui;padding:2px 6px;border-radius:6px}',
      '#purif-scout-hud .menu-btn:hover{background:rgba(255,255,255,.08);color:#fff}',
      '#purif-scout-hud .menu{display:none;position:absolute;right:0;top:100%;margin-top:2px;',
      'min-width:132px;background:#1c1917;border:1px solid #44403c;border-radius:8px;',
      'padding:4px;box-shadow:0 8px 20px rgba(0,0,0,.45);z-index:5}',
      '#purif-scout-hud .menu.open{display:block}',
      '#purif-scout-hud .menu button{display:block;width:100%;text-align:left;border:0;',
      'background:transparent;color:#e7e5e4;padding:7px 8px;border-radius:6px;',
      'font:600 11px/1.2 system-ui;cursor:pointer}',
      '#purif-scout-hud .menu button:hover{background:rgba(255,255,255,.08)}',
      '#purif-scout-hud .keys{margin:0 0 6px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,.08)}',
      '#purif-scout-hud .row{margin:1px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
      '#purif-scout-hud kbd{display:inline-block;min-width:1.25em;text-align:center;',
      'padding:0 4px;margin-right:3px;border-radius:3px;background:#7a0177;color:#fff;',
      'font:700 10px/1.35 ui-monospace,Menlo,monospace}',
      '#purif-scout-hud kbd.sec{background:#44403c}',
      '#purif-scout-hud .tray label{display:block;font-size:9px;opacity:.7;margin:3px 0 2px;',
      'text-transform:uppercase;letter-spacing:.03em}',
      '#purif-scout-hud input[type="search"],#purif-scout-hud select{',
      'width:100%;border-radius:7px;border:1px solid #44403c;background:#0c0a09;color:#e7e5e4;',
      'padding:5px 7px;font:11px/1.2 system-ui;margin-bottom:3px}',
      '#purif-scout-hud button.primary{pointer-events:auto;cursor:pointer;border:0;border-radius:8px;',
      'padding:9px 10px;font:700 12px/1.2 system-ui;background:#7a0177;color:#fff;width:100%;margin:4px 0 2px}',
      '#purif-scout-hud button.primary:hover{filter:brightness(1.07)}',
      '#purif-scout-hud .speed-row{display:flex;align-items:center;gap:5px;margin:2px 0}',
      '#purif-scout-hud .speed-row label{margin:0;flex:0 0 auto;text-transform:none;',
      'letter-spacing:0;font-size:10px;opacity:.8}',
      '#purif-scout-hud .speed-row button{pointer-events:auto;cursor:pointer;border:0;border-radius:6px;',
      'width:28px;height:24px;padding:0;font:700 14px/1 system-ui;background:#292524;color:#e7e5e4;',
      'flex:0 0 auto}',
      '#purif-scout-hud .speed-row button:hover{filter:brightness(1.1)}',
      '#purif-scout-hud .speed-row span{flex:0 0 auto;font:600 10px/1 ui-monospace,Menlo,monospace;opacity:.85;min-width:2.6em;text-align:center}',
      '#purif-scout-hud .route-status{font-size:10px;margin:4px 0 2px;color:#f9a8d4;',
      'min-height:1.15em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
      '#purif-scout-hud .acts{display:flex;gap:5px;margin-top:2px}',
      '#purif-scout-hud .acts button{pointer-events:auto;cursor:pointer;border:0;border-radius:7px;',
      'padding:5px 8px;font:600 10px/1 system-ui;background:#292524;color:#e7e5e4;flex:1}',
      '#purif-scout-hud .acts button:hover{filter:brightness(1.08)}',
      '#purif-scout-hud .acts button.danger{background:#7f1d1d;color:#fecaca}',
      '#purif-scout-mini{pointer-events:auto;width:100%;height:150px;border-radius:10px;',
      'overflow:hidden;box-shadow:0 6px 18px rgba(0,0,0,.32);',
      'border:1px solid rgba(255,255,255,.08);background:#d6d0c2}',
      '#purif-scout-mini .head{display:flex;align-items:center;justify-content:space-between;',
      'padding:3px 7px;background:rgba(28,25,23,.9);color:#e7e5e4;font:600 9px/1.2 system-ui}',
      '#purif-scout-mini .head a{color:#f9a8d4;text-decoration:none;font-weight:700}',
      '#purif-scout-mini canvas{display:block;width:100%;height:calc(100% - 18px);background:#d6d0c2}',
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
      '#purif-scout-root.hidden-ui #purif-scout-left{display:none}'
    ].join('');
    (document.head || document.documentElement).appendChild(css);
  }

  function buildUi() {
    if (document.getElementById('purif-scout-root')) return;
    injectCss();
    var root = document.createElement('div');
    root.id = 'purif-scout-root';
    root.innerHTML = [
      '<div id="purif-scout-left">',
      '  <div id="purif-scout-hud">',
      '    <div class="top">',
      '      <span class="ext-dot bad" id="purif-scout-ext-status" title="Estado extensión"><i></i><span>ext</span></span>',
      '      <div class="menu-wrap">',
      '        <button type="button" class="menu-btn" id="purif-scout-more" title="Más" aria-haspopup="true">⋯</button>',
      '        <div class="menu" id="purif-scout-menu" role="menu">',
      '          <button type="button" id="purif-scout-export" role="menuitem">Export</button>',
      '          <button type="button" id="purif-scout-sync" role="menuitem">Sync ntfy</button>',
      '          <button type="button" id="purif-scout-next" role="menuitem">Paso ▶</button>',
      '          <button type="button" id="purif-scout-retry-route" role="menuitem" style="display:none">Reintentar</button>',
      '          <button type="button" id="purif-scout-hide" role="menuitem">Ocultar</button>',
      '        </div>',
      '      </div>',
      '    </div>',
      '    <div class="keys">',
      '      <div class="row"><kbd>M</kbd><b>Modelorama</b> · <kbd>S</kbd><b>Semáforo</b></div>',
      '      <div class="row"><kbd class="sec">Y</kbd>Comp · <kbd class="sec">E</kbd>Express · <kbd class="sec">P</kbd>Iglesia</div>',
      '      <div class="row"><kbd class="sec">I</kbd>Escuela · <kbd class="sec">H</kbd>Hosp · <kbd>C</kbd>Coment</div>',
      '      <div class="row"><kbd class="sec">Space</kbd>Pausa/Start · <kbd class="sec">Z</kbd>Undo</div>',
      '    </div>',
      '    <div class="tray">',
      '      <label>Colonia</label>',
      '      <input type="search" id="purif-scout-col-filter" placeholder="Buscar colonia…" autocomplete="off" />',
      '      <select id="purif-scout-colonia"><option value="">— cargando… —</option></select>',
      '      <button type="button" class="primary" id="purif-scout-start-route">▶ Start trayecto</button>',
      '      <div class="speed-row">',
      '        <label>Velocidad</label>',
      '        <button type="button" id="purif-scout-speed-down" tabindex="-1" title="Más lento (−)">−</button>',
      '        <span id="purif-scout-speed-label">' + (state.autoMs / 1000).toFixed(1) + 's</span>',
      '        <button type="button" id="purif-scout-speed-up" tabindex="-1" title="Más rápido (+)">+</button>',
      '      </div>',
      '      <div class="route-status" id="purif-scout-route-status"></div>',
      '      <div class="acts">',
      '        <button type="button" id="purif-scout-pause-route">Pausa</button>',
      '        <button type="button" class="danger" id="purif-scout-stop-route">Stop</button>',
      '      </div>',
      '    </div>',
      '  </div>',
      '  <div id="purif-scout-mini">',
      '    <div class="head"><span>Recorrido</span><a id="purif-scout-openmap" href="' + MAP_BASE + '" target="_blank" rel="noopener">mapa</a></div>',
      '    <canvas id="purif-scout-canvas" width="220" height="132"></canvas>',
      '  </div>',
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

    var menu = document.getElementById('purif-scout-menu');
    var moreBtn = document.getElementById('purif-scout-more');
    function closeMenu() { if (menu) menu.classList.remove('open'); }
    moreBtn.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      menu.classList.toggle('open');
    });
    document.addEventListener('click', function (e) {
      if (!menu || !menu.classList.contains('open')) return;
      if (menu.contains(e.target) || moreBtn.contains(e.target)) return;
      closeMenu();
    }, true);

    document.getElementById('purif-scout-export').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation(); closeMenu(); downloadExport();
    });
    document.getElementById('purif-scout-sync').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation(); closeMenu(); syncAllNtfy();
    });
    document.getElementById('purif-scout-hide').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation(); closeMenu();
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
    document.getElementById('purif-scout-next').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation(); closeMenu();
      advanceOneStep();
    });
    document.getElementById('purif-scout-retry-route').addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation(); closeMenu();
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
    // v1.7.3: −/+ buttons only — no <input type="range"> (ArrowLeft cannot touch speed)
    var speedDown = document.getElementById('purif-scout-speed-down');
    var speedUp = document.getElementById('purif-scout-speed-up');
    if (speedDown) {
      speedDown.addEventListener('click', function (e) {
        e.preventDefault(); e.stopPropagation();
        bumpAutoMs(-1); // slower = higher ms
        try { speedDown.blur(); } catch (err) {}
      });
    }
    if (speedUp) {
      speedUp.addEventListener('click', function (e) {
        e.preventDefault(); e.stopPropagation();
        bumpAutoMs(1); // faster = lower ms
        try { speedUp.blur(); } catch (err) {}
      });
    }
    syncSpeedUi();
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
    var extEl = document.getElementById('purif-scout-ext-status');
    var link = document.getElementById('purif-scout-openmap');
    var pauseBtn = document.getElementById('purif-scout-pause-route');
    if (!extEl) return;

    if (state.extAvailable) {
      extEl.className = 'ext-dot ok';
      extEl.title = 'ext OK · camina solo';
      extEl.innerHTML = '<i></i><span>ext OK</span>';
    } else {
      extEl.className = 'ext-dot bad';
      extEl.title = 'INSTALA extensión — sin ella no se mueve';
      extEl.innerHTML = '<i></i><span>ext</span>';
    }

    // One-line progress only (no badge / POV / lat spam)
    var rs = document.getElementById('purif-scout-route-status');
    if (rs && state.route && state.route.status === 'running') {
      var prog = routeProgressLabel(state.route);
      var turnBit = state.nextTurnHud ? (' · ' + state.nextTurnHud) : '';
      rs.textContent = (state.route.paused ? '⏸ ' : '▶ ') + prog + turnBit + (state.extAvailable ? '' : ' · sin ext');
    } else if (rs && state.route && state.route.status === 'stopped') {
      if (!rs.textContent) rs.textContent = 'Detenido';
    } else if (rs && !state.route && !state.trayectoBuilding && !state.lastTrayectoError) {
      if (!state.inSV) rs.textContent = 'Peoncito → Street View';
      else if (!rs.textContent || rs.textContent.indexOf('Peoncito') === 0) rs.textContent = '';
    }

    if (pauseBtn && state.route) {
      pauseBtn.textContent = state.route.paused ? 'Reanudar' : 'Pausa';
    } else if (pauseBtn) {
      pauseBtn.textContent = 'Pausa';
    }

    if (link && state.lat != null && state.lng != null) {
      link.href = MAP_BASE + '#map=' + Math.max(16, 17) + '/' + state.lat.toFixed(5) + '/' + state.lng.toFixed(5);
    }
    drawMini();
  }

  function drawMini() {
    var canvas = document.getElementById('purif-scout-canvas');
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext('2d');
    var w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#d6d0c2';
    ctx.fillRect(0, 0, w, h);

    var clat = state.lat != null ? state.lat : 25.836;
    var clng = state.lng != null ? state.lng : -100.371;
    var spanLat = 0.0035;
    var spanLng = 0.0035;

    // Fit to trayecto route when active (wire state.route.points)
    var pts = (state.route && state.route.points) ? state.route.points : null;
    if (pts && pts.length) {
      var minLat = Infinity, maxLat = -Infinity, minLng = Infinity, maxLng = -Infinity;
      for (var i = 0; i < pts.length; i++) {
        var p0 = pts[i];
        if (p0.lat < minLat) minLat = p0.lat;
        if (p0.lat > maxLat) maxLat = p0.lat;
        if (p0.lng < minLng) minLng = p0.lng;
        if (p0.lng > maxLng) maxLng = p0.lng;
      }
      if (state.lat != null) {
        if (state.lat < minLat) minLat = state.lat;
        if (state.lat > maxLat) maxLat = state.lat;
        if (state.lng < minLng) minLng = state.lng;
        if (state.lng > maxLng) maxLng = state.lng;
      }
      var pad = 0.0004;
      minLat -= pad; maxLat += pad; minLng -= pad; maxLng += pad;
      clat = (minLat + maxLat) / 2;
      clng = (minLng + maxLng) / 2;
      spanLat = Math.max((maxLat - minLat) / 2, 0.0008);
      spanLng = Math.max((maxLng - minLng) / 2, 0.0008);
      var aspect = w / h;
      if (spanLng / spanLat < aspect) spanLng = spanLat * aspect;
      else spanLat = spanLng / aspect;
    }

    function xy(lat, lng) {
      var x = ((lng - (clng - spanLng)) / (2 * spanLng)) * w;
      var y = ((clat + spanLat - lat) / (2 * spanLat)) * h;
      return { x: x, y: y };
    }

    ctx.strokeStyle = 'rgba(0,0,0,.07)';
    ctx.lineWidth = 1;
    for (var g = 1; g < 4; g++) {
      ctx.beginPath();
      ctx.moveTo((w / 4) * g, 0); ctx.lineTo((w / 4) * g, h); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, (h / 4) * g); ctx.lineTo(w, (h / 4) * g); ctx.stroke();
    }

    if (pts && pts.length) {
      ctx.beginPath();
      for (var j = 0; j < pts.length; j++) {
        var pxy = xy(pts[j].lat, pts[j].lng);
        if (j === 0) ctx.moveTo(pxy.x, pxy.y); else ctx.lineTo(pxy.x, pxy.y);
      }
      ctx.strokeStyle = 'rgba(122,1,119,.55)';
      ctx.lineWidth = 2;
      ctx.lineJoin = 'round';
      ctx.stroke();

      var ki = Math.min(state.route.i, pts.length - 1);
      if (ki > 0) {
        ctx.beginPath();
        for (var k = 0; k <= ki; k++) {
          var dxy = xy(pts[k].lat, pts[k].lng);
          if (k === 0) ctx.moveTo(dxy.x, dxy.y); else ctx.lineTo(dxy.x, dxy.y);
        }
        ctx.strokeStyle = 'rgba(122,1,119,.9)';
        ctx.lineWidth = 2.5;
        ctx.stroke();
      }

      var cur = pts[ki];
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
        coords.forEach(function (c, ii) {
          var pt = xy(c[1], c[0]);
          if (ii === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        });
        ctx.strokeStyle = COMMENT_COLOR;
        ctx.lineWidth = 3;
        ctx.stroke();
      } else if (g2.type === 'Point') {
        var c = g2.coordinates;
        var pt = xy(c[1], c[0]);
        var col = '#64748b';
        for (var key in SCOUT_HOTKEYS) {
          if (key === 'U') continue;
          var hk = SCOUT_HOTKEYS[key];
          if (hk.kind === p.kind && hk.layer === p.layer) {
            if (p.kind === 'otro' && hk.nota_raw && p.nota_raw === hk.nota_raw) { col = hk.color; break; }
            if (p.kind !== 'otro') { col = hk.color; break; }
          }
        }
        if (p.layer === 'competencia') col = '#0f766e';
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
    });

    // Current peg + heading
    var peg = xy(clat, clng);
    if (state.lat != null && state.lng != null) peg = xy(state.lat, state.lng);
    var rad = ((state.heading || 0) - 90) * Math.PI / 180;
    ctx.save();
    ctx.translate(peg.x, peg.y);
    ctx.rotate(rad + Math.PI / 2);
    ctx.beginPath();
    ctx.moveTo(0, -9);
    ctx.lineTo(6, 7);
    ctx.lineTo(0, 3.5);
    ctx.lineTo(-6, 7);
    ctx.closePath();
    ctx.fillStyle = '#7a0177';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1.4;
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
      // Colonia selected, no active route → auto-build + start trayecto
      if (!state.route && selectedFeatureFromUi()) {
        ev.preventDefault();
        ev.stopPropagation();
        buildTrayectoForSelection();
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
    listenExtPing();
    refreshPose();
    document.addEventListener('keydown', onKeyDown, true);
    loadColonias().catch(function () {});
    var resumed = resumeRouteFromPersist();
    var resumedWalk = false;
    if (!resumed) {
      resumedWalk = resumeAutoWalkFromPersist();
    }
    if (resumed) {
      toast('Scout v' + SCRIPT_VERSION + ' · reanudando trayecto · ext');
    } else if (resumedWalk) {
      toast('Scout v' + SCRIPT_VERSION + ' · reanudando auto-walk · ext');
    } else {
      toast('Scout v' + SCRIPT_VERSION + ' · ext · google.com/maps');
    }
    updateHud();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
