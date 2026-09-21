/* Bridge: userscript postMessage ↔ extension background debugger ArrowUp */
(function () {
  'use strict';

  function readyPing() {
    try {
      window.postMessage({ source: 'purif-scout-ext', type: 'PURIF_SCOUT_EXT_READY', ts: Date.now() }, '*');
    } catch (e) {}
  }

  readyPing();
  setTimeout(readyPing, 1500);

  window.addEventListener('message', function (ev) {
    var d = ev && ev.data;
    if (!d || d.source !== 'purif-scout') return;
    if (d.type !== 'PURIF_SCOUT_FORWARD') return;
    try {
      chrome.runtime.sendMessage({ type: 'PURIF_SCOUT_FORWARD', ts: d.ts || Date.now() }, function (res) {
        window.postMessage({
          source: 'purif-scout-ext',
          type: 'PURIF_SCOUT_STEP_DONE',
          ok: !!(res && res.ok),
          err: (res && res.err) || (chrome.runtime.lastError && chrome.runtime.lastError.message) || null,
          ts: Date.now()
        }, '*');
      });
    } catch (e) {
      window.postMessage({
        source: 'purif-scout-ext',
        type: 'PURIF_SCOUT_STEP_DONE',
        ok: false,
        err: String(e),
        ts: Date.now()
      }, '*');
    }
  });

  document.addEventListener('purif-scout-forward', function () {
    window.postMessage({ source: 'purif-scout', type: 'PURIF_SCOUT_FORWARD', ts: Date.now() }, '*');
  });
})();
