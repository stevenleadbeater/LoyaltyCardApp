const { encode, totalWidth, PATTERNS, STOP_PATTERN, START_B } = require('../src/js/barcode/code128');

describe('Code128B encoder', () => {
  test('encodes a simple string', () => {
    const bars = encode('A');
    expect(Array.isArray(bars)).toBe(true);
    expect(bars.length).toBeGreaterThan(0);
    // All widths should be 1-4
    bars.forEach(w => {
      expect(w).toBeGreaterThanOrEqual(1);
      expect(w).toBeLessThanOrEqual(4);
    });
  });

  test('starts with START_B pattern', () => {
    const bars = encode('A');
    const startPattern = PATTERNS[START_B];
    const startWidths = startPattern.split('').map(Number);
    expect(bars.slice(0, 6)).toEqual(startWidths);
  });

  test('ends with STOP pattern', () => {
    const bars = encode('A');
    const stopWidths = STOP_PATTERN.split('').map(Number);
    expect(bars.slice(-7)).toEqual(stopWidths);
  });

  test('total width is correct for single character', () => {
    // START_B (11) + 'A' (11) + checksum (11) + STOP (13) = 46
    const bars = encode('A');
    expect(totalWidth(bars)).toBe(46);
  });

  test('total width scales with text length', () => {
    const bars1 = encode('A');
    const bars5 = encode('ABCDE');
    // Each additional character adds 11 modules
    expect(totalWidth(bars5) - totalWidth(bars1)).toBe(4 * 11);
  });

  test('checksum is correctly calculated', () => {
    // For "A": START_B=104, A=33
    // checksum = (104 + 1*33) % 103 = 137 % 103 = 34
    const bars = encode('A');
    const checksumPattern = PATTERNS[34];
    const checksumWidths = checksumPattern.split('').map(Number);
    // Checksum is the second-to-last symbol (before STOP)
    const checksumStart = bars.length - 7 - 6;
    expect(bars.slice(checksumStart, checksumStart + 6)).toEqual(checksumWidths);
  });

  test('encodes digits', () => {
    const bars = encode('1234567890');
    expect(Array.isArray(bars)).toBe(true);
    expect(bars.length).toBeGreaterThan(0);
  });

  test('encodes special characters', () => {
    const bars = encode('Hello, World!');
    expect(Array.isArray(bars)).toBe(true);
  });

  test('throws on empty string', () => {
    expect(() => encode('')).toThrow('Text cannot be empty');
  });

  test('throws on null/undefined', () => {
    expect(() => encode(null)).toThrow();
    expect(() => encode(undefined)).toThrow();
  });

  test('throws on unsupported characters', () => {
    expect(() => encode('\x00')).toThrow('not supported');
    expect(() => encode('\x7F')).toThrow('not supported');
  });

  test('all patterns have correct module width sum', () => {
    PATTERNS.forEach((pattern, idx) => {
      const sum = pattern.split('').reduce((s, c) => s + parseInt(c, 10), 0);
      expect(sum).toBe(11);
    });
  });

  test('stop pattern has correct module width sum', () => {
    const sum = STOP_PATTERN.split('').reduce((s, c) => s + parseInt(c, 10), 0);
    expect(sum).toBe(13);
  });

  test('bars alternate between bar and space', () => {
    const bars = encode('Test');
    // Total elements: START(6) + 4 chars(24) + checksum(6) + STOP(7) = 43
    expect(bars.length).toBe(43);
  });

  test('encodes all printable ASCII', () => {
    let text = '';
    for (let i = 32; i <= 126; i++) text += String.fromCharCode(i);
    const bars = encode(text);
    expect(Array.isArray(bars)).toBe(true);
  });
});
