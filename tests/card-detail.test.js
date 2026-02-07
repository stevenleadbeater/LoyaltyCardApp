/**
 * @jest-environment jsdom
 */

const { createCardDetail } = require('../src/js/card-detail');

// Mock dependencies
const mockCode128 = {
  encode: jest.fn().mockReturnValue([2, 1, 1, 2, 1, 4]),
};
const mockQr = {
  encode: jest.fn().mockReturnValue({
    matrix: [[true, false], [false, true]],
    size: 2,
    version: 1,
  }),
};
const mockRenderer = {
  renderBarcode1D: jest.fn().mockReturnValue('<svg><rect/></svg>'),
  render2D: jest.fn().mockReturnValue('<svg><rect/></svg>'),
};
const mockBrightness = {
  maximizeBrightness: jest.fn().mockResolvedValue(),
  restoreBrightness: jest.fn().mockResolvedValue(),
  requestWakeLock: jest.fn().mockResolvedValue(true),
};

const deps = {
  code128: mockCode128,
  qr: mockQr,
  renderer: mockRenderer,
  brightness: mockBrightness,
};

describe('Card detail view', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('creates overlay element', () => {
    const card = { id: '1', name: 'Test Card', barcodeData: '12345', barcodeType: 'code128' };
    const overlay = createCardDetail(card, deps);
    expect(overlay.className).toBe('card-detail-overlay');
  });

  test('has dialog role', () => {
    const card = { id: '1', name: 'Test Card', barcodeData: '12345', barcodeType: 'code128' };
    const overlay = createCardDetail(card, deps);
    expect(overlay.getAttribute('role')).toBe('dialog');
  });

  test('displays card name', () => {
    const card = { id: '1', name: 'Coffee Rewards', barcodeData: '12345', barcodeType: 'code128' };
    const overlay = createCardDetail(card, deps);
    const name = overlay.querySelector('.card-detail-name');
    expect(name.textContent).toBe('Coffee Rewards');
  });

  test('displays barcode data text', () => {
    const card = { id: '1', name: 'Test', barcodeData: '9876543210', barcodeType: 'code128' };
    const overlay = createCardDetail(card, deps);
    const data = overlay.querySelector('.card-detail-data');
    expect(data.textContent).toBe('9876543210');
  });

  test('renders Code128 barcode for code128 type', () => {
    const card = { id: '1', name: 'Test', barcodeData: '12345', barcodeType: 'code128' };
    createCardDetail(card, deps);
    expect(mockCode128.encode).toHaveBeenCalledWith('12345');
    expect(mockRenderer.renderBarcode1D).toHaveBeenCalled();
  });

  test('renders QR code for qr type', () => {
    const card = { id: '1', name: 'Test', barcodeData: 'https://example.com', barcodeType: 'qr' };
    createCardDetail(card, deps);
    expect(mockQr.encode).toHaveBeenCalledWith('https://example.com');
    expect(mockRenderer.render2D).toHaveBeenCalled();
  });

  test('shows error message on barcode encoding failure', () => {
    const failCode128 = { encode: jest.fn().mockImplementation(() => { throw new Error('Bad data'); }) };
    const card = { id: '1', name: 'Test', barcodeData: '\x00', barcodeType: 'code128' };
    const overlay = createCardDetail(card, { ...deps, code128: failCode128 });
    const error = overlay.querySelector('.barcode-error');
    expect(error).not.toBeNull();
    expect(error.textContent).toContain('Bad data');
  });

  test('has close button', () => {
    const card = { id: '1', name: 'Test', barcodeData: '12345', barcodeType: 'code128' };
    const overlay = createCardDetail(card, deps);
    const closeBtn = overlay.querySelector('.card-detail-close');
    expect(closeBtn).not.toBeNull();
    expect(closeBtn.textContent).toBe('Tap to close');
  });

  test('has aria-label with card name', () => {
    const card = { id: '1', name: 'Grocery Plus', barcodeData: '12345', barcodeType: 'code128' };
    const overlay = createCardDetail(card, deps);
    expect(overlay.getAttribute('aria-label')).toBe('Grocery Plus barcode');
  });

  test('contains barcode container', () => {
    const card = { id: '1', name: 'Test', barcodeData: '12345', barcodeType: 'code128' };
    const overlay = createCardDetail(card, deps);
    const container = overlay.querySelector('.card-detail-barcode');
    expect(container).not.toBeNull();
    expect(container.innerHTML).toContain('<svg');
  });
});
