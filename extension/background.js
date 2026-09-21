/* Purificadoras Scout v1.5 — trusted SV keys via chrome.debugger (MV3).
 * PRIMARY walk driver: ArrowUp / ArrowLeft / ArrowRight (+ optional KeyW).
 * Attach → dispatch key(s) → detach after each burst (limits yellow banner spam).
 */

const ATTACH_TIMEOUT_MS = 5000;
const DEG_PER_TURN_KEY = 15; // approx Maps SV heading change per ArrowLeft/Right
const MAX_TURN_KEYS = 8;

const KEY_DEFS = {
  ArrowUp: { windowsVirtualKeyCode: 38, nativeVirtualKeyCode: 38, code: 'ArrowUp', key: 'ArrowUp' },
  ArrowLeft: { windowsVirtualKeyCode: 37, nativeVirtualKeyCode: 37, code: 'ArrowLeft', key: 'ArrowLeft' },
  ArrowRight: { windowsVirtualKeyCode: 39, nativeVirtualKeyCode: 39, code: 'ArrowRight', key: 'ArrowRight' },
  KeyW: { windowsVirtualKeyCode: 87, nativeVirtualKeyCode: 87, code: 'KeyW', key: 'w', text: 'w', unmodifiedText: 'w' }
};

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function dispatchOneKey(tabId, keyName) {
  const def = KEY_DEFS[keyName];
  if (!def) return Promise.resolve({ ok: false, err: 'unknown key ' + keyName });
  const target = { tabId };
  const base = Object.assign(
    {
      type: 'keyDown',
      text: '',
      unmodifiedText: '',
      modifiers: 0
    },
    def
  );

  return new Promise((resolve) => {
    chrome.debugger.sendCommand(target, 'Input.dispatchKeyEvent', base, () => {
      const errDown = chrome.runtime.lastError && chrome.runtime.lastError.message;
      if (errDown) {
        resolve({ ok: false, err: errDown });
        return;
      }
      chrome.debugger.sendCommand(
        target,
        'Input.dispatchKeyEvent',
        Object.assign({}, base, { type: 'keyUp', text: '', unmodifiedText: '' }),
        () => {
          const errUp = chrome.runtime.lastError && chrome.runtime.lastError.message;
          resolve({ ok: !errUp, err: errUp || null });
        }
      );
    });
  });
}

/**
 * Attach once, send a burst of keys, detach. One yellow banner flash per call.
 * keys: string[] of KEY_DEFS names
 */
function sendKeyBurst(tabId, keys) {
  return new Promise((resolve) => {
    const target = { tabId };
    let finished = false;
    const done = (ok, err, detail) => {
      if (finished) return;
      finished = true;
      try {
        chrome.debugger.detach(target, () => {});
      } catch (e) {}
      resolve({ ok: !!ok, err: err || null, detail: detail || null });
    };
    const timer = setTimeout(() => done(false, 'timeout'), ATTACH_TIMEOUT_MS);

    const run = async () => {
      try {
        await new Promise((res, rej) => {
          chrome.debugger.attach(target, '1.3', () => {
            if (chrome.runtime.lastError) rej(new Error(chrome.runtime.lastError.message));
            else res();
          });
        });
      } catch (e) {
        // Already attached is fine — reuse
        const msg = String(e && e.message || e);
        if (!/already attached/i.test(msg)) {
          clearTimeout(timer);
          done(false, msg);
          return;
        }
      }

      const results = [];
      for (let i = 0; i < keys.length; i++) {
        const r = await dispatchOneKey(tabId, keys[i]);
        results.push({ key: keys[i], ok: r.ok, err: r.err });
        if (!r.ok) {
          clearTimeout(timer);
          // brief settle then detach
          await sleep(60);
          done(false, r.err, { keys: results });
          return;
        }
        // small gap so Maps registers each key
        if (i < keys.length - 1) await sleep(45);
      }
      clearTimeout(timer);
      await sleep(70);
      done(true, null, { keys: results });
    };

    run().catch((e) => {
      clearTimeout(timer);
      done(false, String(e && e.message || e));
    });
  });
}

function turnKeysFromDeg(turnDeg) {
  const deg = Number(turnDeg) || 0;
  if (!isFinite(deg) || Math.abs(deg) < 12) return [];
  const n = Math.min(MAX_TURN_KEYS, Math.max(1, Math.round(Math.abs(deg) / DEG_PER_TURN_KEY)));
  const key = deg < 0 ? 'ArrowLeft' : 'ArrowRight';
  const out = [];
  for (let i = 0; i < n; i++) out.push(key);
  return out;
}

function handleStep(tabId, msg) {
  const keys = [];
  if (msg.turnDeg != null && isFinite(Number(msg.turnDeg))) {
    keys.push.apply(keys, turnKeysFromDeg(Number(msg.turnDeg)));
  }
  if (msg.turnsLeft > 0) {
    for (let i = 0; i < Math.min(MAX_TURN_KEYS, msg.turnsLeft | 0); i++) keys.push('ArrowLeft');
  }
  if (msg.turnsRight > 0) {
    for (let i = 0; i < Math.min(MAX_TURN_KEYS, msg.turnsRight | 0); i++) keys.push('ArrowRight');
  }
  // Always end with a forward step unless forward===false
  if (msg.forward !== false) {
    keys.push('ArrowUp');
    if (msg.alsoW) keys.push('KeyW');
  }
  if (!keys.length) keys.push('ArrowUp');
  return sendKeyBurst(tabId, keys);
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.type) return;

  if (msg.type === 'PURIF_SCOUT_PING' || msg.type === 'ping') {
    sendResponse({
      ok: true,
      version: chrome.runtime.getManifest().version,
      ext: 'purif-scout',
      api: ['step', 'stepForward', 'turnLeft', 'turnRight', 'ping']
    });
    return true;
  }

  const tabId = (sender.tab && sender.tab.id) != null ? sender.tab.id : msg.tabId;
  if (tabId == null) {
    sendResponse({ ok: false, err: 'no tab' });
    return true;
  }

  const t = msg.type;

  if (t === 'PURIF_SCOUT_FORWARD' || t === 'stepForward') {
    sendKeyBurst(tabId, msg.alsoW ? ['ArrowUp', 'KeyW'] : ['ArrowUp']).then(sendResponse);
    return true;
  }
  if (t === 'turnLeft' || t === 'PURIF_SCOUT_TURN_LEFT') {
    const n = Math.min(MAX_TURN_KEYS, Math.max(1, (msg.count | 0) || 1));
    const keys = [];
    for (let i = 0; i < n; i++) keys.push('ArrowLeft');
    sendKeyBurst(tabId, keys).then(sendResponse);
    return true;
  }
  if (t === 'turnRight' || t === 'PURIF_SCOUT_TURN_RIGHT') {
    const n = Math.min(MAX_TURN_KEYS, Math.max(1, (msg.count | 0) || 1));
    const keys = [];
    for (let i = 0; i < n; i++) keys.push('ArrowRight');
    sendKeyBurst(tabId, keys).then(sendResponse);
    return true;
  }
  if (t === 'step' || t === 'PURIF_SCOUT_STEP') {
    handleStep(tabId, msg).then(sendResponse);
    return true;
  }

  return false;
});
