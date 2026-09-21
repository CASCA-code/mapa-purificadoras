/* Purificadoras Scout — trusted ArrowUp via chrome.debugger (MV3).
 * Shows the yellow "debugging" banner briefly while attached.
 * Only used when the Tampermonkey userscript requests a forward step
 * and synthetic KeyboardEvents are ignored by Maps. */

const ATTACH_TIMEOUT_MS = 4000;

function sendArrowUp(tabId) {
  return new Promise((resolve) => {
    const target = { tabId };
    let finished = false;
    const done = (ok, err) => {
      if (finished) return;
      finished = true;
      try { chrome.debugger.detach(target, () => {}); } catch (e) {}
      resolve({ ok: !!ok, err: err || null });
    };
    const timer = setTimeout(() => done(false, 'timeout'), ATTACH_TIMEOUT_MS);

    chrome.debugger.attach(target, '1.3', () => {
      if (chrome.runtime.lastError) {
        clearTimeout(timer);
        done(false, chrome.runtime.lastError.message);
        return;
      }
      const base = {
        type: 'keyDown',
        windowsVirtualKeyCode: 38,
        nativeVirtualKeyCode: 38,
        code: 'ArrowUp',
        key: 'ArrowUp',
        text: '',
        unmodifiedText: '',
        modifiers: 0
      };
      chrome.debugger.sendCommand(target, 'Input.dispatchKeyEvent', base, () => {
        chrome.debugger.sendCommand(
          target,
          'Input.dispatchKeyEvent',
          Object.assign({}, base, { type: 'keyUp' }),
          () => {
            clearTimeout(timer);
            const err = chrome.runtime.lastError && chrome.runtime.lastError.message;
            // brief pause so Maps registers the key before detach
            setTimeout(() => done(!err, err || null), 80);
          }
        );
      });
    });
  });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || msg.type !== 'PURIF_SCOUT_FORWARD') return;
  const tabId = sender.tab && sender.tab.id;
  if (tabId == null) {
    sendResponse({ ok: false, err: 'no tab' });
    return true;
  }
  sendArrowUp(tabId).then(sendResponse);
  return true; // async
});
