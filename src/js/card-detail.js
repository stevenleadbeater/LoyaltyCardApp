// Card detail fullscreen barcode display

/**
 * Create the card detail overlay element.
 * @param {import('./store').Card} card
 * @param {object} deps - Injected dependencies
 * @param {object} deps.code128 - Code128 encoder
 * @param {object} deps.qr - QR encoder
 * @param {object} deps.renderer - Barcode SVG renderer
 * @param {object} deps.brightness - Brightness manager
 * @returns {HTMLElement} The overlay element
 */
function createCardDetail(card, deps) {
  const { code128, qr, renderer, brightness } = deps;

  const overlay = document.createElement('div');
  overlay.className = 'card-detail-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-label', `${card.name} barcode`);

  // Card name
  const nameEl = document.createElement('h2');
  nameEl.className = 'card-detail-name';
  nameEl.textContent = card.name;

  // Barcode container
  const barcodeContainer = document.createElement('div');
  barcodeContainer.className = 'card-detail-barcode';

  let svgMarkup;
  try {
    if (card.barcodeType === 'qr') {
      const { matrix } = qr.encode(card.barcodeData);
      svgMarkup = renderer.render2D(matrix);
    } else {
      const bars = code128.encode(card.barcodeData);
      svgMarkup = renderer.renderBarcode1D(bars);
    }
  } catch (err) {
    svgMarkup = `<div class="barcode-error">Unable to render barcode: ${err.message}</div>`;
  }

  barcodeContainer.innerHTML = svgMarkup;

  // Barcode data text (for reference)
  const dataEl = document.createElement('p');
  dataEl.className = 'card-detail-data';
  dataEl.textContent = card.barcodeData;

  // Close button
  const closeBtn = document.createElement('button');
  closeBtn.className = 'card-detail-close';
  closeBtn.textContent = 'Tap to close';
  closeBtn.setAttribute('aria-label', 'Close barcode view');

  overlay.appendChild(nameEl);
  overlay.appendChild(barcodeContainer);
  overlay.appendChild(dataEl);
  overlay.appendChild(closeBtn);

  return overlay;
}

/**
 * Open the card detail fullscreen barcode view.
 * @param {import('./store').Card} card
 * @param {object} deps
 * @returns {Promise<void>}
 */
async function openCardDetail(card, deps) {
  const { brightness } = deps;
  const overlay = createCardDetail(card, deps);
  document.body.appendChild(overlay);

  // Maximize brightness for scanning
  await brightness.maximizeBrightness(overlay);

  // Force repaint then show
  overlay.offsetHeight; // eslint-disable-line no-unused-expressions
  overlay.classList.add('visible');

  return new Promise((resolve) => {
    function close() {
      overlay.classList.remove('visible');
      brightness.restoreBrightness(overlay).then(() => {
        overlay.remove();
        resolve();
      });
    }

    overlay.querySelector('.card-detail-close').addEventListener('click', close);
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });

    document.addEventListener('keydown', function onKey(e) {
      if (e.key === 'Escape') {
        document.removeEventListener('keydown', onKey);
        close();
      }
    });

    // Re-acquire wake lock if page becomes visible again
    document.addEventListener('visibilitychange', async () => {
      if (document.visibilityState === 'visible' && overlay.parentNode) {
        await brightness.requestWakeLock();
      }
    });
  });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { createCardDetail, openCardDetail };
}
