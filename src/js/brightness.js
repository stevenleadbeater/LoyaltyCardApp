// Screen brightness management using Wake Lock API and Fullscreen API

let wakeLock = null;

/**
 * Request a screen wake lock to prevent the display from dimming.
 * @returns {Promise<boolean>} true if lock acquired
 */
async function requestWakeLock() {
  if (!('wakeLock' in navigator)) return false;
  try {
    wakeLock = await navigator.wakeLock.request('screen');
    wakeLock.addEventListener('release', () => { wakeLock = null; });
    return true;
  } catch {
    return false;
  }
}

/**
 * Release the wake lock.
 */
async function releaseWakeLock() {
  if (wakeLock) {
    await wakeLock.release();
    wakeLock = null;
  }
}

/**
 * Enter fullscreen mode on the given element.
 * @param {HTMLElement} element
 * @returns {Promise<boolean>} true if fullscreen entered
 */
async function enterFullscreen(element) {
  try {
    if (element.requestFullscreen) {
      await element.requestFullscreen();
    } else if (element.webkitRequestFullscreen) {
      await element.webkitRequestFullscreen();
    }
    return true;
  } catch {
    return false;
  }
}

/**
 * Exit fullscreen mode.
 */
async function exitFullscreen() {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else if (document.webkitFullscreenElement) {
      document.webkitExitFullscreen();
    }
  } catch {
    // ignore
  }
}

/**
 * Maximize screen brightness for barcode scanning.
 * Requests wake lock and sets the element to bright white background.
 * @param {HTMLElement} element - The container element
 * @returns {Promise<void>}
 */
async function maximizeBrightness(element) {
  await requestWakeLock();
  await enterFullscreen(element);
  element.classList.add('max-brightness');
}

/**
 * Restore normal screen state.
 * @param {HTMLElement} element - The container element
 * @returns {Promise<void>}
 */
async function restoreBrightness(element) {
  await releaseWakeLock();
  await exitFullscreen();
  element.classList.remove('max-brightness');
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    requestWakeLock, releaseWakeLock,
    enterFullscreen, exitFullscreen,
    maximizeBrightness, restoreBrightness,
  };
}
