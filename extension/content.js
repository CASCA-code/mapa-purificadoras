/* Bridge v1.6.1: page/userscript ↔ extension background (trusted debugger keys).
 * Primary: window.postMessage + reqId (one debugger burst per logical step).
 * CustomEvent = legacy only when reqId absent. Exposes PURIF_SCOUT_EXT via postMessage. */
(function () {
  'use strict';

  var EXT_SOURCE = 'purif-scout-ext';
  var PAGE_SOURCE = 'purif-scout';

  function postToPage(payload) {
    try {
      window.postMessage(Object.assign({ source: EXT_SOURCE, ts: Date.now() }, payload), '*');
    } catch (e) {}
  }

  function readyPing() {
    postToPage({
      type: 'PURIF_SCOUT_EXT_READY',
      version: (chrome.runtime.getManifest && chrome.runtime.getManifest().version) || '1.6.1',
      api: ['step', 'stepForward', 'turnLeft', 'turnRight', 'ping']
    });
  }

  function callBg(msg) {
    return new Promise(function (resolve) {
      try {
        chrome.runtime.sendMessage(msg, function (res) {
          var err = (chrome.runtime.lastError && chrome.runtime.lastError.message) || null;
          if (err) resolve({ ok: false, err: err });
          else resolve(res || { ok: false, err: 'no response' });
        });
      } catch (e) {
        resolve({ ok: false, err: String(e) });
      }
    });
  }

  function replyDone(reqType, res, reqId) {
    postToPage({
      type: 'PURIF_SCOUT_STEP_DONE',
      reqType: reqType || null,
      reqId: reqId || null,
      ok: !!(res && res.ok),
      err: (res && res.err) || null,
      detail: (res && res.detail) || null,
      version: (res && res.version) || null
    });
  }

  function handlePageMsg(d) {
    if (!d || d.source !== PAGE_SOURCE) return;
    var t = d.type;
    var reqId = d.reqId || null;

    if (t === 'PURIF_SCOUT_PING' || t === 'ping') {
      callBg({ type: 'ping' }).then(function (res) {
        postToPage({
          type: 'PURIF_SCOUT_EXT_READY',
          version: (res && res.version) || null,
          api: (res && res.api) || null,
          reqId: reqId,
          ok: !!(res && res.ok)
        });
        replyDone('ping', res, reqId);
      });
      return;
    }

    if (t === 'PURIF_SCOUT_FORWARD' || t === 'stepForward') {
      callBg({ type: 'stepForward', alsoW: !!d.alsoW }).then(function (res) {
        replyDone('stepForward', res, reqId);
      });
      return;
    }

    if (t === 'turnLeft' || t === 'PURIF_SCOUT_TURN_LEFT') {
      callBg({ type: 'turnLeft', count: d.count || 1 }).then(function (res) {
        replyDone('turnLeft', res, reqId);
      });
      return;
    }

    if (t === 'turnRight' || t === 'PURIF_SCOUT_TURN_RIGHT') {
      callBg({ type: 'turnRight', count: d.count || 1 }).then(function (res) {
        replyDone('turnRight', res, reqId);
      });
      return;
    }

    if (t === 'step' || t === 'PURIF_SCOUT_STEP') {
      // Preserve forward:false for POV-only rotate (no ArrowUp)
      var fwd = (d.forward === false) ? false : true;
      callBg({
        type: 'step',
        turnDeg: d.turnDeg,
        turnsLeft: d.turnsLeft,
        turnsRight: d.turnsRight,
        forward: fwd,
        alsoW: !!d.alsoW
      }).then(function (res) {
        replyDone('step', res, reqId);
      });
      return;
    }
  }

  // v1.6.1: primary channel = postMessage with reqId (userscript must NOT also fire CustomEvent)
  window.addEventListener('message', function (ev) {
    try {
      var o = ev && ev.origin;
      if (o && o !== 'null' && o.indexOf('google.') < 0 && o.indexOf('chrome-extension://') !== 0) {
        // ignore non-Maps origins; Maps tab origin is google.*
        return;
      }
    } catch (eO) {}
    handlePageMsg(ev && ev.data);
  });

  // Legacy CustomEvent ONLY if an old userscript still dispatches (no postMessage).
  // Current userscript v1.8+ uses postMessage exclusively — do not double-fire.
  document.addEventListener('purif-scout-forward', function (ev) {
    var detail = (ev && ev.detail) || {};
    if (detail && detail.reqId) return; // paired with postMessage — ignore
    handlePageMsg({ source: PAGE_SOURCE, type: 'stepForward' });
  });
  document.addEventListener('purif-scout-step', function (ev) {
    var detail = (ev && ev.detail) || {};
    if (detail && detail.reqId) return; // paired with postMessage — ignore
    handlePageMsg(Object.assign({ source: PAGE_SOURCE, type: 'step' }, detail));
  });

  // Inject page-world API: window.PURIF_SCOUT_EXT.step({turnDeg})
  function injectPageApi() {
    var s = document.createElement('script');
    s.textContent = [
      '(function(){',
      '  if (window.PURIF_SCOUT_EXT && window.PURIF_SCOUT_EXT._v) return;',
      '  var seq = 0;',
      '  function send(type, extra) {',
      '    var reqId = "p" + (++seq) + "_" + Date.now();',
      '    return new Promise(function(resolve){',
      '      var done = false;',
      '      function onMsg(ev){',
      '        var d = ev && ev.data;',
      '        if (!d || d.source !== "purif-scout-ext") return;',
      '        if (d.type !== "PURIF_SCOUT_STEP_DONE" && d.type !== "PURIF_SCOUT_EXT_READY") return;',
      '        if (d.reqId && d.reqId !== reqId) return;',
      '        if (!d.reqId && d.type === "PURIF_SCOUT_EXT_READY" && type !== "ping") return;',
      '        done = true;',
      '        window.removeEventListener("message", onMsg);',
      '        resolve({ ok: !!d.ok || d.type === "PURIF_SCOUT_EXT_READY", err: d.err || null, version: d.version || null, detail: d.detail || null });',
      '      }',
      '      window.addEventListener("message", onMsg);',
      '      var payload = Object.assign({ source: "purif-scout", type: type, reqId: reqId, ts: Date.now() }, extra || {});',
      '      window.postMessage(payload, "*");',
      '      setTimeout(function(){ if (!done) { window.removeEventListener("message", onMsg); resolve({ ok: false, err: "timeout" }); } }, 12000);',
      '    });',
      '  }',
      '  window.PURIF_SCOUT_EXT = {',
      '    _v: "1.6.1",',
      '    ping: function(){ return send("ping"); },',
      '    stepForward: function(opts){ return send("stepForward", opts || {}); },',
      '    turnLeft: function(count){ return send("turnLeft", { count: count || 1 }); },',
      '    turnRight: function(count){ return send("turnRight", { count: count || 1 }); },',
      '    step: function(opts){ opts = opts || {}; return send("step", opts); }',
      '  };',
      '  try { window.postMessage({ source: "purif-scout", type: "ping", ts: Date.now() }, "*"); } catch(e) {}',
      '})();'
    ].join(String.fromCharCode(10));
    (document.documentElement || document.head || document.body).appendChild(s);
    s.remove();
  }

  try { injectPageApi(); } catch (e) {}
  readyPing();
  setTimeout(readyPing, 800);
  setTimeout(readyPing, 2500);
})();
