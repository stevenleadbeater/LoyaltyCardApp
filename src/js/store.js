// Card data store using localStorage

const STORAGE_KEY = 'loyalty_cards';

/**
 * @typedef {Object} Card
 * @property {string} id - Unique card identifier
 * @property {string} name - Card/store name
 * @property {string} barcodeData - Raw barcode data string
 * @property {string} barcodeType - 'code128' | 'qr'
 * @property {string} [color] - Optional accent color
 */

/**
 * Get all stored cards.
 * @returns {Card[]}
 */
function getCards() {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : getSampleCards();
  } catch {
    return getSampleCards();
  }
}

/**
 * Get a single card by ID.
 * @param {string} id
 * @returns {Card|null}
 */
function getCard(id) {
  const cards = getCards();
  return cards.find(c => c.id === id) || null;
}

/**
 * Save cards to storage.
 * @param {Card[]} cards
 */
function saveCards(cards) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cards));
}

/**
 * Default sample cards for first-run experience.
 * @returns {Card[]}
 */
function getSampleCards() {
  return [
    {
      id: 'sample-1',
      name: 'Coffee House Rewards',
      barcodeData: '6789012345',
      barcodeType: 'code128',
      color: '#6B4226',
    },
    {
      id: 'sample-2',
      name: 'Grocery Plus',
      barcodeData: '4567890123456',
      barcodeType: 'code128',
      color: '#2E7D32',
    },
    {
      id: 'sample-3',
      name: 'Bookstore Club',
      barcodeData: 'https://example.com/member/12345',
      barcodeType: 'qr',
      color: '#1565C0',
    },
  ];
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getCards, getCard, saveCards, getSampleCards, STORAGE_KEY };
}
