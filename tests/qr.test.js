const {
  encode, selectVersion, encodeData, generateEC, rsEncode,
  rsGeneratorPoly, gfMul, GF_EXP, GF_LOG, CAPACITY, EC_PARAMS,
  getFormatBits, getVersionBits,
} = require('../src/js/barcode/qr');

describe('GF(256) arithmetic', () => {
  test('EXP and LOG tables are consistent', () => {
    for (let i = 0; i < 255; i++) {
      const exp = GF_EXP[i];
      expect(GF_LOG[exp]).toBe(i);
    }
  });

  test('EXP[0] = 1 (alpha^0 = 1)', () => {
    expect(GF_EXP[0]).toBe(1);
  });

  test('EXP[1] = 2 (alpha^1 = 2)', () => {
    expect(GF_EXP[1]).toBe(2);
  });

  test('EXP[8] = 29 (alpha^8 = x^4+x^3+x^2+1)', () => {
    expect(GF_EXP[8]).toBe(29);
  });

  test('multiplication is commutative', () => {
    expect(gfMul(5, 7)).toBe(gfMul(7, 5));
    expect(gfMul(100, 200)).toBe(gfMul(200, 100));
  });

  test('multiplication by 0 gives 0', () => {
    expect(gfMul(0, 42)).toBe(0);
    expect(gfMul(42, 0)).toBe(0);
  });

  test('multiplication by 1 gives identity', () => {
    expect(gfMul(1, 42)).toBe(42);
    expect(gfMul(42, 1)).toBe(42);
  });
});

describe('Reed-Solomon encoding', () => {
  test('generator polynomial has correct degree', () => {
    const poly = rsGeneratorPoly(10);
    expect(poly.length).toBe(11); // degree 10 = 11 coefficients
  });

  test('generator polynomial starts with 1', () => {
    const poly = rsGeneratorPoly(7);
    expect(poly[0]).toBe(1);
  });

  test('RS encode produces correct number of EC codewords', () => {
    const data = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17];
    const ec = rsEncode(data, 10);
    expect(ec.length).toBe(10);
  });
});

describe('QR version selection', () => {
  test('selects version 1 for short data', () => {
    expect(selectVersion(10)).toBe(1);
    expect(selectVersion(14)).toBe(1);
  });

  test('selects version 2 for medium data', () => {
    expect(selectVersion(15)).toBe(2);
    expect(selectVersion(26)).toBe(2);
  });

  test('selects higher versions for longer data', () => {
    expect(selectVersion(100)).toBe(6);
    expect(selectVersion(200)).toBe(10);
  });

  test('throws for data too long', () => {
    expect(() => selectVersion(300)).toThrow('Data too long');
  });
});

describe('Data encoding', () => {
  test('encodes to correct number of codewords', () => {
    const codewords = encodeData('Hello', 1);
    // V1 M: 16 data codewords
    expect(codewords.length).toBe(16);
  });

  test('starts with byte mode indicator', () => {
    const codewords = encodeData('A', 1);
    // First byte: mode (0100) + count MSB (4 bits of 8-bit count for 1 char = 0000)
    // = 0100 0000 = 0x40
    // Wait: mode=0100, count=00000001
    // bits: 0100 0000 0001 ...
    // first byte: 01000000 = 0x40
    expect(codewords[0]).toBe(0x40);
  });

  test('padding bytes alternate 0xEC and 0x11', () => {
    const codewords = encodeData('A', 1);
    // After mode(4) + count(8) + data(8) = 20 bits = 2.5 bytes → 3 bytes used
    // Remaining 13 bytes should be padding
    // Byte 3: 0x10 (last 4 bits of 'A' + 4 bits of terminator)
    // Then: EC 11 EC 11 ...
    const paddingStart = 3; // after mode+count+data+terminator
    for (let i = paddingStart; i < codewords.length; i++) {
      const expected = (i - paddingStart) % 2 === 0 ? 0xEC : 0x11;
      expect(codewords[i]).toBe(expected);
    }
  });
});

describe('Format bits', () => {
  test('format bits are 15 bits wide', () => {
    for (let mask = 0; mask < 8; mask++) {
      const bits = getFormatBits(mask);
      expect(bits).toBeLessThan(1 << 15);
      expect(bits).toBeGreaterThanOrEqual(0);
    }
  });

  test('different masks produce different format bits', () => {
    const seen = new Set();
    for (let mask = 0; mask < 8; mask++) {
      const bits = getFormatBits(mask);
      expect(seen.has(bits)).toBe(false);
      seen.add(bits);
    }
  });
});

describe('Version bits', () => {
  test('returns 0 for versions < 7', () => {
    for (let v = 1; v <= 6; v++) {
      expect(getVersionBits(v)).toBe(0);
    }
  });

  test('returns 18-bit value for versions >= 7', () => {
    for (let v = 7; v <= 10; v++) {
      const bits = getVersionBits(v);
      expect(bits).toBeLessThan(1 << 18);
      expect(bits).toBeGreaterThan(0);
    }
  });
});

describe('QR encode (full)', () => {
  test('generates correct size matrix for version 1', () => {
    const { matrix, size, version } = encode('Hello');
    expect(version).toBe(1);
    expect(size).toBe(21);
    expect(matrix.length).toBe(21);
    matrix.forEach(row => expect(row.length).toBe(21));
  });

  test('generates correct size for version 2', () => {
    const { matrix, size, version } = encode('Hello, World! 1234567');
    expect(version).toBe(2);
    expect(size).toBe(25);
  });

  test('matrix contains only booleans', () => {
    const { matrix } = encode('Test');
    matrix.forEach(row => {
      row.forEach(cell => expect(typeof cell).toBe('boolean'));
    });
  });

  test('finder patterns are present', () => {
    const { matrix } = encode('Test');
    // Top-left finder pattern: first 7 rows/cols should have the pattern
    // Top-left corner should be dark
    expect(matrix[0][0]).toBe(true);
    expect(matrix[0][6]).toBe(true);
    expect(matrix[6][0]).toBe(true);
    expect(matrix[6][6]).toBe(true);
    // Inside the finder: row 0, col 1-5 should be dark
    expect(matrix[0][1]).toBe(true);
    expect(matrix[0][2]).toBe(true);
    expect(matrix[0][3]).toBe(true);
    expect(matrix[0][4]).toBe(true);
    expect(matrix[0][5]).toBe(true);
    // White border inside: row 1, col 1 should be white
    expect(matrix[1][1]).toBe(false);
  });

  test('produces different output for different input', () => {
    const { matrix: m1 } = encode('Hello');
    const { matrix: m2 } = encode('World');
    let different = false;
    for (let r = 0; r < m1.length && !different; r++) {
      for (let c = 0; c < m1[r].length && !different; c++) {
        if (m1[r][c] !== m2[r][c]) different = true;
      }
    }
    expect(different).toBe(true);
  });

  test('throws on empty string', () => {
    expect(() => encode('')).toThrow('Text cannot be empty');
  });

  test('handles long data requiring higher version', () => {
    const longText = 'A'.repeat(100);
    const { version, size } = encode(longText);
    expect(version).toBeGreaterThanOrEqual(5);
    expect(size).toBe(17 + version * 4);
  });
});
