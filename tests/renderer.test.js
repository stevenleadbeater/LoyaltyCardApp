const { renderBarcode1D, render2D } = require('../src/js/barcode/renderer');

describe('1D barcode renderer', () => {
  const sampleBars = [2, 1, 1, 2, 1, 4, 2, 3, 3, 1, 1, 1, 2];

  test('returns valid SVG string', () => {
    const svg = renderBarcode1D(sampleBars);
    expect(svg).toContain('<svg');
    expect(svg).toContain('</svg>');
    expect(svg).toContain('xmlns="http://www.w3.org/2000/svg"');
  });

  test('contains black rects for bars', () => {
    const svg = renderBarcode1D(sampleBars);
    expect(svg).toContain('fill="#000"');
  });

  test('contains white background rect', () => {
    const svg = renderBarcode1D(sampleBars);
    expect(svg).toContain('fill="#fff"');
  });

  test('respects custom height option', () => {
    const svg = renderBarcode1D(sampleBars, { height: 200 });
    expect(svg).toContain('height="200"');
  });

  test('respects custom moduleWidth option', () => {
    const svg1 = renderBarcode1D(sampleBars, { moduleWidth: 1 });
    const svg2 = renderBarcode1D(sampleBars, { moduleWidth: 4 });
    // Different module widths should produce different viewBox widths
    expect(svg1).not.toBe(svg2);
  });

  test('only even-indexed bars produce rects', () => {
    // Simple bars: [1, 1] = one black bar of width 1, one space of width 1
    const svg = renderBarcode1D([1, 1]);
    const rects = svg.match(/<rect[^/]*fill="#000"/g);
    // Should have 1 black rect (index 0)
    expect(rects.length).toBe(1);
  });

  test('uses preserveAspectRatio for scaling', () => {
    const svg = renderBarcode1D(sampleBars);
    expect(svg).toContain('preserveAspectRatio');
  });
});

describe('2D code renderer', () => {
  const sampleMatrix = [
    [true, false, true],
    [false, true, false],
    [true, false, true],
  ];

  test('returns valid SVG string', () => {
    const svg = render2D(sampleMatrix);
    expect(svg).toContain('<svg');
    expect(svg).toContain('</svg>');
  });

  test('contains correct number of dark modules', () => {
    const svg = render2D(sampleMatrix);
    const rects = svg.match(/<rect[^/]*fill="#000"/g);
    // 5 dark modules in sample matrix
    expect(rects.length).toBe(5);
  });

  test('respects custom moduleSize', () => {
    const svg = render2D(sampleMatrix, { moduleSize: 16 });
    expect(svg).toContain('width="16"');
    expect(svg).toContain('height="16"');
  });

  test('handles empty matrix', () => {
    const svg = render2D([]);
    expect(svg).toContain('<svg');
  });

  test('handles single-cell matrix', () => {
    const svg = render2D([[true]]);
    const rects = svg.match(/<rect[^/]*fill="#000"/g);
    expect(rects.length).toBe(1);
  });
});
