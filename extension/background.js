/* Purificadoras Scout v1.6.1 — trusted SV keys via chrome.debugger (MV3).
 * PRIMARY walk driver: ArrowUp / ArrowLeft / ArrowRight (+ optional KeyW).
 * v1.5.1: stronger POV turns — more keys per deg, turn burst + settle BEFORE ArrowUp,
 * optional mouse-drag backup; one attach for turn+wait+Up (no mid-step detach).
 */

// Shared budget with userscript EXT_STEP_TIMEOUT_MS (12s) / ROUTE_BUSY_WATCHDOG_MS (15s):
// attach + turn keys + POV_SETTLE_MS + ArrowUp must fit under userscript step timeout.
const ATTACH_TIMEOUT_MS = 8000;
const DEG_PER_TURN_KEY = 9; // ~8–10°: more Left/Right presses for same turnDeg
const MAX_TURN_KEYS = 24; // allow ~180°+ at 9°/key
const POV_SETTLE_MS = 320; // wait after turn keys so Maps applies POV before Up
const MOUSE_DRAG_BACKUP_MIN_DEG = 50; // horizontal drag backup when |turnDeg| large
const PX_PER_DEG_DRAG = 3.5;

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

function sendCommand(tabId, method, params) {
  return new Promise((resolve) => {
    chrome.debugger.sendCommand({ tabId }, method, params || {}, (result) => {
      const err = chrome.runtime.lastError && chrome.runtime.lastError.message;
      resolve({ ok: !err, err: err || null, result: result || null });
    });
  });
}

/**
 * Backup POV rotate: horizontal mouse drag on viewport center.
 * Maps SV: drag right → camera turns left (negative heading).
 * Used when |turnDeg| is large after key burst. Documented in extension README.
 */
async function mouseDragRotate(tabId, turnDeg) {
  const layout = await sendCommand(tabId, 'Page.getLayoutMetrics', {});
  let w = 1200;
  let h = 800;
  try {
    const css = layout.result && (layout.result.cssVisualViewport || layout.result.visualViewport || layout.result.layoutViewport);
    if (css) {
      w = css.clientWidth || css.width || w;
      h = css.clientHeight || css.height || h;
    }
  } catch (e) {}
  const cx = Math.round(w / 2);
  const cy = Math.round(h / 2);
  // drag direction opposite to desired turn (positive turnDeg = right = drag left)
  const dx = Math.round(-turnDeg * PX_PER_DEG_DRAG);
  const capped = Math.max(-420, Math.min(420, dx));
  if (Math.abs(capped) < 12) return { ok: true, skipped: true };

  const down = await sendCommand(tabId, 'Input.dispatchMouseEvent', {
    type: 'mousePressed',
    x: cx,
    y: cy,
    button: 'left',
    buttons: 1,
    clickCount: 1
  });
  if (!down.ok) return down;

  const steps = 6;
  for (let i = 1; i <= steps; i++) {
    const x = cx + Math.round((capped * i) / steps);
    await sendCommand(tabId, 'Input.dispatchMouseEvent', {
      type: 'mouseMoved',
      x: x,
      y: cy,
      button: 'left',
      buttons: 1
    });
    await sleep(16);
  }

  const up = await sendCommand(tabId, 'Input.dispatchMouseEvent', {
    type: 'mouseReleased',
    x: cx + capped,
    y: cy,
    button: 'left',
    buttons: 0,
    clickCount: 1
  });
  return { ok: up.ok, err: up.err, dx: capped };
}

/**
 * Attach once, run async work while attached, then detach.
 * Keeps debugger attached across turn burst + settle + ArrowUp.
 */
function withDebugger(tabId, workFn) {
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
        const msg = String((e && e.message) || e);
        if (!/already attached/i.test(msg)) {
          clearTimeout(timer);
          done(false, msg);
          return;
        }
      }

      try {
        const detail = await workFn(tabId);
        clearTimeout(timer);
        await sleep(50);
        done(true, null, detail);
      } catch (e) {
        clearTimeout(timer);
        done(false, String((e && e.message) || e));
      }
    };

    run().catch((e) => {
      clearTimeout(timer);
      done(false, String((e && e.message) || e));
    });
  });
}

async function dispatchKeyList(tabId, keys) {
  const results = [];
  for (let i = 0; i < keys.length; i++) {
    const r = await dispatchOneKey(tabId, keys[i]);
    results.push({ key: keys[i], ok: r.ok, err: r.err });
    if (!r.ok) {
      const err = new Error(r.err || 'key failed');
      err.partial = results;
      throw err;
    }
    if (i < keys.length - 1) await sleep(45);
  }
  return results;
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
  const turnDeg = msg.turnDeg != null && isFinite(Number(msg.turnDeg)) ? Number(msg.turnDeg) : 0;
  const turnKeys = [];
  if (turnDeg) turnKeys.push.apply(turnKeys, turnKeysFromDeg(turnDeg));
  if (msg.turnsLeft > 0) {
    for (let i = 0; i < Math.min(MAX_TURN_KEYS, msg.turnsLeft | 0); i++) turnKeys.push('ArrowLeft');
  }
  if (msg.turnsRight > 0) {
    for (let i = 0; i < Math.min(MAX_TURN_KEYS, msg.turnsRight | 0); i++) turnKeys.push('ArrowRight');
  }

  const wantForward = msg.forward !== false;
  const absTurn = Math.abs(turnDeg) || (turnKeys.length ? turnKeys.length * DEG_PER_TURN_KEY : 0);

  // forward:false + no meaningful turn → noop (do not force ArrowUp)
  if (!turnKeys.length && !wantForward) {
    return Promise.resolve({ ok: true, err: null, detail: { keys: [], note: 'noop' } });
  }

  // No turn, just forward — simple burst
  if (!turnKeys.length && wantForward) {
    const keys = ['ArrowUp'];
    if (msg.alsoW) keys.push('KeyW');
    return withDebugger(tabId, async (tid) => {
      const results = await dispatchKeyList(tid, keys);
      return { keys: results, phase: 'forward-only' };
    });
  }

  // Turn (+ optional forward): ONE attach for turn → settle → Up
  return withDebugger(tabId, async (tid) => {
    const detail = { keys: [], mouseDrag: null, settledMs: 0, phase: 'turn' };
    detail.keys = await dispatchKeyList(tid, turnKeys);

    // Optional mouse-drag backup for large POV changes
    if (absTurn >= MOUSE_DRAG_BACKUP_MIN_DEG) {
      try {
        detail.mouseDrag = await mouseDragRotate(tid, turnDeg || (turnKeys[0] === 'ArrowLeft' ? -absTurn : absTurn));
        detail.phase = 'turn+mouse';
      } catch (e) {
        detail.mouseDrag = { ok: false, err: String(e) };
      }
    }

    if (wantForward && absTurn >= 12) {
      await sleep(POV_SETTLE_MS);
      detail.settledMs = POV_SETTLE_MS;
      const fwd = ['ArrowUp'];
      if (msg.alsoW) fwd.push('KeyW');
      const fwdResults = await dispatchKeyList(tid, fwd);
      detail.keys = detail.keys.concat(fwdResults);
      detail.phase = 'turn-settle-forward';
    } else if (wantForward) {
      const fwd = ['ArrowUp'];
      if (msg.alsoW) fwd.push('KeyW');
      const fwdResults = await dispatchKeyList(tid, fwd);
      detail.keys = detail.keys.concat(fwdResults);
      detail.phase = 'turn-forward';
    } else {
      detail.phase = 'turn-only';
      await sleep(70);
    }
    return detail;
  });
}

function sendKeyBurst(tabId, keys) {
  if (!keys || !keys.length) {
    return Promise.resolve({ ok: true, err: null, detail: { keys: [] } });
  }
  return withDebugger(tabId, async (tid) => {
    const results = await dispatchKeyList(tid, keys);
    await sleep(70);
    return { keys: results };
  });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.type) return;

  if (msg.type === 'PURIF_SCOUT_PING' || msg.type === 'ping') {
    sendResponse({
      ok: true,
      version: chrome.runtime.getManifest().version,
      ext: 'purif-scout',
      api: ['step', 'stepForward', 'turnLeft', 'turnRight', 'ping'],
      degPerTurnKey: DEG_PER_TURN_KEY,
      povSettleMs: POV_SETTLE_MS,
      mouseDragBackup: true
    });
    return true;
  }

  const tabId = sender.tab && sender.tab.id != null ? sender.tab.id : msg.tabId;
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
