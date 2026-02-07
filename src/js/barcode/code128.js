// Code128B barcode encoder
// Encodes ASCII 32-126 as a series of bar/space widths

// Bar patterns for Code128 values 0-106
// Each string represents alternating bar and space widths (6 digits, sum = 11)
const PATTERNS = [
  '212222', '222122', '222221', '121223', '121322', '131222', '122213', '122312',
  '132212', '221213', '221312', '231212', '112232', '122132', '122231', '113222',
  '123122', '123221', '223211', '221132', '221231', '213212', '223112', '312131',
  '311222', '321122', '321221', '312212', '322112', '322211', '212123', '212321',
  '232121', '111323', '131123', '131321', '112313', '132113', '132311', '211313',
  '231113', '231311', '112133', '112331', '132131', '113123', '113321', '133121',
  '313121', '211331', '231131', '213113', '213311', '213131', '311123', '311321',
  '331121', '312113', '312311', '332111', '314111', '221411', '431111', '111224',
  '111422', '121124', '121421', '141122', '141221', '112214', '112412', '122114',
  '122411', '142112', '142211', '241211', '221114', '413111', '241112', '134111',
  '111242', '121142', '121241', '114212', '124112', '124211', '411212', '421112',
  '421211', '212141', '214121', '412121', '111143', '111341', '131141', '114113',
  '114311', '411113', '411311', '113141', '114131', '311141', '411131', '211412',
  '211214', '211232',
];

const STOP_PATTERN = '2331112';
const START_B = 104;

/**
 * Encode text as Code128B barcode.
 * @param {string} text - ASCII text to encode (characters 32-126)
 * @returns {number[]} Array of bar/space widths (alternating black/white starting with black)
 */
function encode(text) {
  if (!text || text.length === 0) {
    throw new Error('Text cannot be empty');
  }

  const values = [START_B];
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i);
    if (code < 32 || code > 126) {
      throw new Error(`Character '${text[i]}' (code ${code}) not supported in Code128B`);
    }
    values.push(code - 32);
  }

  // Checksum: (start + sum(position * value)) mod 103
  let checksum = values[0];
  for (let i = 1; i < values.length; i++) {
    checksum += i * values[i];
  }
  checksum = checksum % 103;
  values.push(checksum);

  // Convert values to bar/space widths
  const bars = [];
  for (const value of values) {
    const pattern = PATTERNS[value];
    for (let j = 0; j < pattern.length; j++) {
      bars.push(parseInt(pattern[j], 10));
    }
  }

  // Append stop pattern (7 elements)
  for (let j = 0; j < STOP_PATTERN.length; j++) {
    bars.push(parseInt(STOP_PATTERN[j], 10));
  }

  return bars;
}

/**
 * Calculate the total module width of the encoded barcode.
 * @param {number[]} bars - Array of bar/space widths
 * @returns {number} Total width in modules
 */
function totalWidth(bars) {
  return bars.reduce((sum, w) => sum + w, 0);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { encode, totalWidth, PATTERNS, STOP_PATTERN, START_B };
}
