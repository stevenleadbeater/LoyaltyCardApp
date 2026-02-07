// Loyalty Card App - Main entry point

import * as code128 from './barcode/code128.js';
import * as qr from './barcode/qr.js';
import * as renderer from './barcode/renderer.js';
import * as brightness from './brightness.js';
import * as store from './store.js';
import { openCardDetail } from './card-detail.js';

const deps = { code128, qr, renderer, brightness };

function renderCardList() {
  const cards = store.getCards();
  const list = document.getElementById('card-list');
  if (!list) return;

  list.innerHTML = '';

  cards.forEach(card => {
    const item = document.createElement('button');
    item.className = 'card-item';
    item.setAttribute('aria-label', `Open ${card.name}`);
    if (card.color) {
      item.style.borderLeftColor = card.color;
    }

    const name = document.createElement('span');
    name.className = 'card-item-name';
    name.textContent = card.name;

    const type = document.createElement('span');
    type.className = 'card-item-type';
    type.textContent = card.barcodeType === 'qr' ? 'QR' : 'Barcode';

    item.appendChild(name);
    item.appendChild(type);

    item.addEventListener('click', () => {
      openCardDetail(card, deps);
    });

    list.appendChild(item);
  });
}

function init() {
  renderCardList();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
