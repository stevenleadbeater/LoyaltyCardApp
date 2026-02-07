// QR Code generator (versions 1-10, ECC level M, byte mode)

// --- Galois Field GF(256) arithmetic ---
// Primitive polynomial: x^8 + x^4 + x^3 + x^2 + 1 (0x11D)

const GF_EXP = new Uint8Array(256);
const GF_LOG = new Uint8Array(256);

(function initGF() {
  let x = 1;
  for (let i = 0; i < 255; i++) {
    GF_EXP[i] = x;
    GF_LOG[x] = i;
    x <<= 1;
    if (x >= 256) x ^= 0x11D;
  }
  GF_EXP[255] = GF_EXP[0];
})();

function gfMul(a, b) {
  if (a === 0 || b === 0) return 0;
  return GF_EXP[(GF_LOG[a] + GF_LOG[b]) % 255];
}

function polyMul(p1, p2) {
  const result = new Array(p1.length + p2.length - 1).fill(0);
  for (let i = 0; i < p1.length; i++) {
    for (let j = 0; j < p2.length; j++) {
      result[i + j] ^= gfMul(p1[i], p2[j]);
    }
  }
  return result;
}

function rsGeneratorPoly(n) {
  let poly = [1];
  for (let i = 0; i < n; i++) {
    poly = polyMul(poly, [1, GF_EXP[i]]);
  }
  return poly;
}

function rsEncode(data, numEC) {
  const gen = rsGeneratorPoly(numEC);
  const padded = new Array(data.length + numEC).fill(0);
  for (let i = 0; i < data.length; i++) padded[i] = data[i];
  for (let i = 0; i < data.length; i++) {
    const coef = padded[i];
    if (coef !== 0) {
      for (let j = 0; j < gen.length; j++) {
        padded[i + j] ^= gfMul(gen[j], coef);
      }
    }
  }
  return padded.slice(data.length);
}

// --- QR parameters ---

// ECC Level M parameters: [totalCodewords, ecPerBlock, blocksG1, dataG1, blocksG2, dataG2]
const EC_PARAMS = [
  null, // no version 0
  [26, 10, 1, 16, 0, 0],   // V1
  [44, 16, 1, 28, 0, 0],   // V2
  [70, 26, 1, 44, 0, 0],   // V3
  [100, 18, 2, 32, 0, 0],  // V4
  [134, 24, 2, 43, 0, 0],  // V5
  [172, 16, 4, 27, 0, 0],  // V6
  [196, 18, 4, 31, 0, 0],  // V7
  [242, 22, 2, 38, 2, 39], // V8
  [292, 22, 3, 36, 2, 37], // V9
  [346, 26, 4, 43, 1, 44], // V10
];

// Byte mode capacity for ECC M
const CAPACITY = [0, 14, 26, 42, 62, 84, 106, 122, 152, 180, 213];

// Alignment pattern center positions per version
const ALIGNMENT_POSITIONS = [
  null, // V0
  [],           // V1
  [6, 18],      // V2
  [6, 22],      // V3
  [6, 26],      // V4
  [6, 30],      // V5
  [6, 34],      // V6
  [6, 22, 38],  // V7
  [6, 24, 42],  // V8
  [6, 26, 46],  // V9
  [6, 28, 50],  // V10
];

// --- Data encoding ---

function selectVersion(dataLength) {
  for (let v = 1; v <= 10; v++) {
    if (dataLength <= CAPACITY[v]) return v;
  }
  throw new Error(`Data too long for QR versions 1-10 (max ${CAPACITY[10]} bytes)`);
}

function encodeData(text, version) {
  const params = EC_PARAMS[version];
  const totalDataCodewords = params[2] * params[3] + params[4] * params[5];
  const bits = [];

  function pushBits(value, count) {
    for (let i = count - 1; i >= 0; i--) {
      bits.push((value >> i) & 1);
    }
  }

  // Mode indicator: byte mode = 0100
  pushBits(0b0100, 4);

  // Character count
  const countBits = version <= 9 ? 8 : 16;
  pushBits(text.length, countBits);

  // Data bytes
  for (let i = 0; i < text.length; i++) {
    pushBits(text.charCodeAt(i), 8);
  }

  // Terminator (up to 4 zero bits)
  const totalBits = totalDataCodewords * 8;
  const terminatorLen = Math.min(4, totalBits - bits.length);
  for (let i = 0; i < terminatorLen; i++) bits.push(0);

  // Pad to byte boundary
  while (bits.length % 8 !== 0) bits.push(0);

  // Pad bytes (alternating 0xEC, 0x11)
  const padBytes = [0xEC, 0x11];
  let padIdx = 0;
  while (bits.length < totalBits) {
    pushBits(padBytes[padIdx], 8);
    padIdx = (padIdx + 1) % 2;
  }

  // Convert to bytes
  const codewords = [];
  for (let i = 0; i < bits.length; i += 8) {
    let byte = 0;
    for (let j = 0; j < 8; j++) byte = (byte << 1) | bits[i + j];
    codewords.push(byte);
  }

  return codewords;
}

// --- Error correction and interleaving ---

function generateEC(dataCodewords, version) {
  const params = EC_PARAMS[version];
  const [, ecPerBlock, blocksG1, dataG1, blocksG2, dataG2] = params;

  const dataBlocks = [];
  const ecBlocks = [];
  let offset = 0;

  for (let i = 0; i < blocksG1; i++) {
    const block = dataCodewords.slice(offset, offset + dataG1);
    dataBlocks.push(block);
    ecBlocks.push(rsEncode(block, ecPerBlock));
    offset += dataG1;
  }
  for (let i = 0; i < blocksG2; i++) {
    const block = dataCodewords.slice(offset, offset + dataG2);
    dataBlocks.push(block);
    ecBlocks.push(rsEncode(block, ecPerBlock));
    offset += dataG2;
  }

  // Interleave data codewords
  const result = [];
  const maxDataLen = Math.max(dataG1, dataG2 || 0);
  for (let i = 0; i < maxDataLen; i++) {
    for (const block of dataBlocks) {
      if (i < block.length) result.push(block[i]);
    }
  }

  // Interleave EC codewords
  for (let i = 0; i < ecPerBlock; i++) {
    for (const block of ecBlocks) {
      if (i < block.length) result.push(block[i]);
    }
  }

  return result;
}

// --- Matrix construction ---

function createMatrix(version) {
  const size = 17 + version * 4;
  const matrix = Array.from({ length: size }, () => new Int8Array(size)); // 0 = unset
  const reserved = Array.from({ length: size }, () => new Uint8Array(size)); // 1 = reserved
  return { matrix, reserved, size };
}

function placeFinderPattern(m, row, col) {
  for (let r = -1; r <= 7; r++) {
    for (let c = -1; c <= 7; c++) {
      const mr = row + r, mc = col + c;
      if (mr < 0 || mr >= m.size || mc < 0 || mc >= m.size) continue;
      let val;
      if (r === -1 || r === 7 || c === -1 || c === 7) {
        val = 0; // separator (white)
      } else if (r === 0 || r === 6 || c === 0 || c === 6) {
        val = 1; // border (black)
      } else if (r >= 2 && r <= 4 && c >= 2 && c <= 4) {
        val = 1; // center (black)
      } else {
        val = 0; // inner white
      }
      m.matrix[mr][mc] = val ? 1 : -1;
      m.reserved[mr][mc] = 1;
    }
  }
}

function placeAlignmentPattern(m, row, col) {
  for (let r = -2; r <= 2; r++) {
    for (let c = -2; c <= 2; c++) {
      const mr = row + r, mc = col + c;
      if (m.reserved[mr][mc]) continue;
      let val;
      if (r === -2 || r === 2 || c === -2 || c === 2) {
        val = 1;
      } else if (r === 0 && c === 0) {
        val = 1;
      } else {
        val = 0;
      }
      m.matrix[mr][mc] = val ? 1 : -1;
      m.reserved[mr][mc] = 1;
    }
  }
}

function placeTimingPatterns(m) {
  for (let i = 8; i < m.size - 8; i++) {
    if (!m.reserved[6][i]) {
      m.matrix[6][i] = (i % 2 === 0) ? 1 : -1;
      m.reserved[6][i] = 1;
    }
    if (!m.reserved[i][6]) {
      m.matrix[i][6] = (i % 2 === 0) ? 1 : -1;
      m.reserved[i][6] = 1;
    }
  }
}

function reserveFormatArea(m) {
  // Around top-left finder
  for (let i = 0; i <= 8; i++) {
    if (!m.reserved[8][i]) m.reserved[8][i] = 1;
    if (!m.reserved[i][8]) m.reserved[i][8] = 1;
  }
  // Around top-right finder
  for (let i = 0; i <= 7; i++) {
    if (!m.reserved[8][m.size - 1 - i]) m.reserved[8][m.size - 1 - i] = 1;
  }
  // Around bottom-left finder
  for (let i = 0; i <= 7; i++) {
    if (!m.reserved[m.size - 1 - i][8]) m.reserved[m.size - 1 - i][8] = 1;
  }
  // Dark module
  m.matrix[m.size - 8][8] = 1;
  m.reserved[m.size - 8][8] = 1;
}

function reserveVersionArea(m, version) {
  if (version < 7) return;
  for (let i = 0; i < 6; i++) {
    for (let j = 0; j < 3; j++) {
      m.reserved[i][m.size - 11 + j] = 1;
      m.reserved[m.size - 11 + j][i] = 1;
    }
  }
}

function placeFunctionPatterns(m, version) {
  placeFinderPattern(m, 0, 0);
  placeFinderPattern(m, 0, m.size - 7);
  placeFinderPattern(m, m.size - 7, 0);

  const alignPos = ALIGNMENT_POSITIONS[version];
  if (alignPos.length > 0) {
    for (const row of alignPos) {
      for (const col of alignPos) {
        // Skip if overlapping finder patterns
        if (row <= 8 && col <= 8) continue;
        if (row <= 8 && col >= m.size - 8) continue;
        if (row >= m.size - 8 && col <= 8) continue;
        placeAlignmentPattern(m, row, col);
      }
    }
  }

  placeTimingPatterns(m);
  reserveFormatArea(m);
  reserveVersionArea(m, version);
}

// --- Data placement ---

function placeData(m, dataBits) {
  let bitIdx = 0;
  let col = m.size - 1;
  let upward = true;

  while (col >= 0) {
    // Skip timing pattern column
    if (col === 6) col--;

    const rowStart = upward ? m.size - 1 : 0;
    const rowEnd = upward ? -1 : m.size;
    const rowStep = upward ? -1 : 1;

    for (let row = rowStart; row !== rowEnd; row += rowStep) {
      for (let dc = 0; dc <= 1; dc++) {
        const c = col - dc;
        if (c < 0) continue;
        if (m.reserved[row][c]) continue;
        if (bitIdx < dataBits.length) {
          m.matrix[row][c] = dataBits[bitIdx] ? 1 : -1;
        } else {
          m.matrix[row][c] = -1; // padding (white)
        }
        bitIdx++;
      }
    }

    col -= 2;
    upward = !upward;
  }
}

// --- Masking ---

const MASK_FUNCTIONS = [
  (r, c) => (r + c) % 2 === 0,
  (r, c) => r % 2 === 0,
  (r, c) => c % 3 === 0,
  (r, c) => (r + c) % 3 === 0,
  (r, c) => (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0,
  (r, c) => ((r * c) % 2) + ((r * c) % 3) === 0,
  (r, c) => (((r * c) % 2) + ((r * c) % 3)) % 2 === 0,
  (r, c) => (((r + c) % 2) + ((r * c) % 3)) % 2 === 0,
];

function applyMask(m, maskIdx) {
  const fn = MASK_FUNCTIONS[maskIdx];
  for (let r = 0; r < m.size; r++) {
    for (let c = 0; c < m.size; c++) {
      if (m.reserved[r][c]) continue;
      if (fn(r, c)) {
        m.matrix[r][c] = m.matrix[r][c] === 1 ? -1 : 1;
      }
    }
  }
}

function calcPenalty(m) {
  let penalty = 0;
  const s = m.size;

  function isDark(r, c) {
    return m.matrix[r][c] === 1;
  }

  // Rule 1: runs of 5+ same color in row/col
  for (let r = 0; r < s; r++) {
    let count = 1;
    for (let c = 1; c < s; c++) {
      if (isDark(r, c) === isDark(r, c - 1)) {
        count++;
      } else {
        if (count >= 5) penalty += count - 2;
        count = 1;
      }
    }
    if (count >= 5) penalty += count - 2;
  }
  for (let c = 0; c < s; c++) {
    let count = 1;
    for (let r = 1; r < s; r++) {
      if (isDark(r, c) === isDark(r - 1, c)) {
        count++;
      } else {
        if (count >= 5) penalty += count - 2;
        count = 1;
      }
    }
    if (count >= 5) penalty += count - 2;
  }

  // Rule 2: 2x2 blocks of same color
  for (let r = 0; r < s - 1; r++) {
    for (let c = 0; c < s - 1; c++) {
      const v = isDark(r, c);
      if (v === isDark(r, c + 1) && v === isDark(r + 1, c) && v === isDark(r + 1, c + 1)) {
        penalty += 3;
      }
    }
  }

  // Rule 3: finder-like patterns
  const pattern1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0];
  const pattern2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1];
  for (let r = 0; r < s; r++) {
    for (let c = 0; c <= s - 11; c++) {
      let match1 = true, match2 = true;
      for (let k = 0; k < 11; k++) {
        const d = isDark(r, c + k) ? 1 : 0;
        if (d !== pattern1[k]) match1 = false;
        if (d !== pattern2[k]) match2 = false;
      }
      if (match1) penalty += 40;
      if (match2) penalty += 40;
    }
  }
  for (let c = 0; c < s; c++) {
    for (let r = 0; r <= s - 11; r++) {
      let match1 = true, match2 = true;
      for (let k = 0; k < 11; k++) {
        const d = isDark(r + k, c) ? 1 : 0;
        if (d !== pattern1[k]) match1 = false;
        if (d !== pattern2[k]) match2 = false;
      }
      if (match1) penalty += 40;
      if (match2) penalty += 40;
    }
  }

  // Rule 4: proportion of dark modules
  let darkCount = 0;
  for (let r = 0; r < s; r++) {
    for (let c = 0; c < s; c++) {
      if (isDark(r, c)) darkCount++;
    }
  }
  const percentage = (darkCount * 100) / (s * s);
  const prevFive = Math.floor(percentage / 5) * 5;
  const nextFive = prevFive + 5;
  penalty += Math.min(
    Math.abs(prevFive - 50) / 5,
    Math.abs(nextFive - 50) / 5
  ) * 10;

  return penalty;
}

// --- Format and version info ---

function bchEncode(data, poly, dataBits, totalBits) {
  let d = data << (totalBits - dataBits);
  const polyLen = totalBits - dataBits + 1;
  for (let i = dataBits - 1; i >= 0; i--) {
    if (d & (1 << (i + totalBits - dataBits))) {
      d ^= poly << i;
    }
  }
  return (data << (totalBits - dataBits)) | d;
}

function getFormatBits(maskIdx) {
  // ECC M = 00, mask pattern = maskIdx (3 bits)
  const data = (0b00 << 3) | maskIdx;
  let encoded = bchEncode(data, 0b10100110111, 5, 15);
  encoded ^= 0b101010000010010;
  return encoded;
}

function getVersionBits(version) {
  if (version < 7) return 0;
  return bchEncode(version, 0b1111100100101, 6, 18);
}

function placeFormatInfo(m, maskIdx) {
  const bits = getFormatBits(maskIdx);

  // Positions around top-left finder (horizontal then vertical)
  const hPositions = [
    [8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5],
    [8, 7], [8, 8],
    [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8],
  ];

  for (let i = 0; i < 15; i++) {
    const bit = (bits >> i) & 1;
    const [r, c] = hPositions[i];
    m.matrix[r][c] = bit ? 1 : -1;
  }

  // Second copy: bottom-left (vertical) and top-right (horizontal)
  for (let i = 0; i < 7; i++) {
    const bit = (bits >> i) & 1;
    m.matrix[m.size - 1 - i][8] = bit ? 1 : -1;
  }
  for (let i = 7; i < 15; i++) {
    const bit = (bits >> i) & 1;
    m.matrix[8][m.size - 15 + i] = bit ? 1 : -1;
  }
}

function placeVersionInfo(m, version) {
  if (version < 7) return;
  const bits = getVersionBits(version);
  for (let i = 0; i < 18; i++) {
    const bit = (bits >> i) & 1;
    const r = Math.floor(i / 3);
    const c = m.size - 11 + (i % 3);
    m.matrix[r][c] = bit ? 1 : -1;
    m.matrix[c][r] = bit ? 1 : -1;
  }
}

// --- Main encode function ---

/**
 * Generate a QR code matrix from text.
 * @param {string} text - Text to encode
 * @returns {{ matrix: boolean[][], size: number, version: number }}
 *   matrix[row][col] = true for dark module, false for light
 */
function encode(text) {
  if (!text || text.length === 0) {
    throw new Error('Text cannot be empty');
  }

  const version = selectVersion(text.length);
  const dataCodewords = encodeData(text, version);
  const finalCodewords = generateEC(dataCodewords, version);

  // Convert to bit array
  const dataBits = [];
  for (const byte of finalCodewords) {
    for (let i = 7; i >= 0; i--) {
      dataBits.push((byte >> i) & 1);
    }
  }

  // Try all 8 masks, pick lowest penalty
  let bestMask = 0;
  let bestPenalty = Infinity;
  let bestMatrix = null;

  for (let maskIdx = 0; maskIdx < 8; maskIdx++) {
    const m = createMatrix(version);
    placeFunctionPatterns(m, version);
    placeData(m, dataBits);
    applyMask(m, maskIdx);
    placeFormatInfo(m, maskIdx);
    placeVersionInfo(m, version);

    const penalty = calcPenalty(m);
    if (penalty < bestPenalty) {
      bestPenalty = penalty;
      bestMask = maskIdx;
      bestMatrix = m;
    }
  }

  // Convert to boolean matrix
  const result = [];
  for (let r = 0; r < bestMatrix.size; r++) {
    const row = [];
    for (let c = 0; c < bestMatrix.size; c++) {
      row.push(bestMatrix.matrix[r][c] === 1);
    }
    result.push(row);
  }

  return { matrix: result, size: bestMatrix.size, version };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    encode, selectVersion, encodeData, generateEC, rsEncode,
    rsGeneratorPoly, gfMul, GF_EXP, GF_LOG, CAPACITY, EC_PARAMS,
    getFormatBits, getVersionBits,
  };
}
