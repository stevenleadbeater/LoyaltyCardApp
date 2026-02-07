// SVG barcode renderer for both 1D (Code128) and 2D (QR) barcodes

/**
 * Render a 1D barcode as an SVG string.
 * @param {number[]} bars - Array of bar/space widths from Code128 encoder
 * @param {object} options
 * @param {number} [options.height=100] - Bar height in pixels
 * @param {number} [options.moduleWidth=2] - Width of 1 module in pixels
 * @param {number} [options.quietZone=20] - Quiet zone width in pixels
 * @returns {string} SVG markup
 */
function renderBarcode1D(bars, options = {}) {
  const {
    height = 100,
    moduleWidth = 2,
    quietZone = 20,
  } = options;

  const totalModules = bars.reduce((s, w) => s + w, 0);
  const barcodeWidth = totalModules * moduleWidth;
  const svgWidth = barcodeWidth + quietZone * 2;
  const svgHeight = height;

  let x = quietZone;
  const rects = [];

  for (let i = 0; i < bars.length; i++) {
    const w = bars[i] * moduleWidth;
    if (i % 2 === 0) {
      // Even indices are bars (black)
      rects.push(`<rect x="${x}" y="0" width="${w}" height="${height}" fill="#000"/>`);
    }
    x += w;
  }

  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${svgWidth} ${svgHeight}" `,
    `width="100%" height="100%" preserveAspectRatio="xMidYMid meet">`,
    `<rect width="${svgWidth}" height="${svgHeight}" fill="#fff"/>`,
    ...rects,
    `</svg>`,
  ].join('');
}

/**
 * Render a 2D code (QR/DataMatrix) as an SVG string.
 * @param {boolean[][]} matrix - 2D boolean array (true = dark module)
 * @param {object} options
 * @param {number} [options.moduleSize=8] - Size of each module in pixels
 * @param {number} [options.quietZone=32] - Quiet zone width in pixels
 * @returns {string} SVG markup
 */
function render2D(matrix, options = {}) {
  const {
    moduleSize = 8,
    quietZone = 32,
  } = options;

  const size = matrix.length;
  const svgSize = size * moduleSize + quietZone * 2;

  const rects = [];
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (matrix[r][c]) {
        const x = quietZone + c * moduleSize;
        const y = quietZone + r * moduleSize;
        rects.push(`<rect x="${x}" y="${y}" width="${moduleSize}" height="${moduleSize}" fill="#000"/>`);
      }
    }
  }

  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${svgSize} ${svgSize}" `,
    `width="100%" height="100%" preserveAspectRatio="xMidYMid meet">`,
    `<rect width="${svgSize}" height="${svgSize}" fill="#fff"/>`,
    ...rects,
    `</svg>`,
  ].join('');
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { renderBarcode1D, render2D };
}
