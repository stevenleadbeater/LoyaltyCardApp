"""Render barcodes as Cairo surfaces for display on screen.

Supports common 1D barcode formats using pure Python encoding.
"""

import cairo
import math

# EAN/UPC encoding tables
_L_PATTERNS = {
    "0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101",
    "4": "0100011", "5": "0110001", "6": "0101111", "7": "0111011",
    "8": "0110111", "9": "0001011",
}
_G_PATTERNS = {
    "0": "0100111", "1": "0110011", "2": "0011011", "3": "0100001",
    "4": "0011101", "5": "0111001", "6": "0000101", "7": "0010001",
    "8": "0001001", "9": "0010111",
}
_R_PATTERNS = {
    "0": "1110010", "1": "1100110", "2": "1101100", "3": "1000010",
    "4": "1011100", "5": "1001110", "6": "1010000", "7": "1000100",
    "8": "1001000", "9": "1110100",
}
# First digit parity for EAN-13
_FIRST_DIGIT_PARITY = {
    "0": "LLLLLL", "1": "LLGLGG", "2": "LLGGLG", "3": "LLGGGL",
    "4": "LGLLGG", "5": "LGGLLG", "6": "LGGGLL", "7": "LGLGLG",
    "8": "LGLGGL", "9": "LGGLGL",
}

# Code 39 character set
_CODE39_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"
_CODE39_PATTERNS = {
    "0": "nnnwwnwnn", "1": "wnnwnnnnw", "2": "nnwwnnnnw", "3": "wnwwnnnn",
    "4": "nnnwwnnnw", "5": "wnnwwnnn", "6": "nnwwwnnn", "7": "nnnwnnwnw",
    "8": "wnnwnnwnn", "9": "nnwwnnwnn", "A": "wnnnnwnnw", "B": "nnwnnwnnw",
    "C": "wnwnnwnnn", "D": "nnnnwwnnw", "E": "wnnnwwnnn", "F": "nnwnwwnnn",
    "G": "nnnnnwwnw", "H": "wnnnnwwnn", "I": "nnwnnwwnn", "J": "nnnnwwwnn",
    "K": "wnnnnnnww", "L": "nnwnnnnww", "M": "wnwnnnnwn", "N": "nnnnwnnww",
    "O": "wnnnwnnwn", "P": "nnwnwnnwn", "Q": "nnnnnnwww", "R": "wnnnnnwwn",
    "S": "nnwnnnwwn", "T": "nnnnwnwwn", "U": "wwnnnnnnw", "V": "nwwnnnnnw",
    "W": "wwwnnnnnn", "X": "nwnnwnnnw", "Y": "wwnnwnnnn", "Z": "nwwnwnnnn",
    "-": "nwnnnnwnw", ".": "wwnnnnwnn", " ": "nwwnnnwnn", "$": "nwnwnwnnn",
    "/": "nwnwnnnwn", "+": "nwnnnwnwn", "%": "nnnwnwnwn", "*": "nwnnwnwnn",
}

# Code 128 encoding
_CODE128_START_B = 104
_CODE128_VALUES_B = {}
for i in range(95):
    _CODE128_VALUES_B[chr(32 + i)] = i
_CODE128_VALUES_B["\x00"] = 95  # FNC 3, etc.

_CODE128_PATTERNS = [
    "11011001100", "11001101100", "11001100110", "10010011000", "10010001100",
    "10001001100", "10011001000", "10011000100", "10001100100", "11001001000",
    "11001000100", "11000100100", "10110011100", "10011011100", "10011001110",
    "10111001100", "10011101100", "10011100110", "11001110010", "11001011100",
    "11001001110", "11011100100", "11001110100", "11101101110", "11101001100",
    "11100101100", "11100100110", "11101100100", "11100110100", "11100110010",
    "11011011000", "11011000110", "11000110110", "10100011000", "10001011000",
    "10001000110", "10110001000", "10001101000", "10001100010", "11010001000",
    "11000101000", "11000100010", "10110111000", "10110001110", "10001101110",
    "10111011000", "10111000110", "10001110110", "11101110110", "11010001110",
    "11000101110", "11011101000", "11011100010", "11011101110", "11101011000",
    "11101000110", "11100010110", "11101101000", "11101100010", "11100011010",
    "11101111010", "11001000010", "11110001010", "10100110000", "10100001100",
    "10010110000", "10010000110", "10000101100", "10000100110", "10110010000",
    "10110000100", "10011010000", "10011000010", "10000110100", "10000110010",
    "11000010010", "11001010000", "11110111010", "11000010100", "10001111010",
    "10100111100", "10010111100", "10010011110", "10111100100", "10011110100",
    "10011110010", "11110100100", "11110010100", "11110010010", "11011011110",
    "11011110110", "11110110110", "10101111000", "10100011110", "10001011110",
    "10111101000", "10111100010", "11110101000", "11110100010", "10111011110",
    "10111101110", "11101011110", "11110101110", "11010000100", "11010010000",
    "11010011100", "1100011101011",
]


def _encode_ean13(digits):
    """Return a binary string of bar/space modules for EAN-13."""
    parity = _FIRST_DIGIT_PARITY[digits[0]]
    bits = "101"  # start guard
    for i in range(6):
        d = digits[1 + i]
        if parity[i] == "L":
            bits += _L_PATTERNS[d]
        else:
            bits += _G_PATTERNS[d]
    bits += "01010"  # center guard
    for i in range(6):
        bits += _R_PATTERNS[digits[7 + i]]
    bits += "101"  # end guard
    return bits


def _encode_ean8(digits):
    """Return a binary string of bar/space modules for EAN-8."""
    bits = "101"
    for i in range(4):
        bits += _L_PATTERNS[digits[i]]
    bits += "01010"
    for i in range(4):
        bits += _R_PATTERNS[digits[4 + i]]
    bits += "101"
    return bits


def _encode_upca(digits):
    """Return a binary string of bar/space modules for UPC-A."""
    bits = "101"
    for i in range(6):
        bits += _L_PATTERNS[digits[i]]
    bits += "01010"
    for i in range(6):
        bits += _R_PATTERNS[digits[6 + i]]
    bits += "101"
    return bits


def _encode_code39(data):
    """Return a list of (width, is_bar) tuples for Code 39."""
    narrow = 1
    wide = 3
    chars = "*" + data.upper() + "*"
    elements = []
    for ci, ch in enumerate(chars):
        if ci > 0:
            elements.append((narrow, False))  # inter-character gap
        pat = _CODE39_PATTERNS.get(ch, _CODE39_PATTERNS["0"])
        for i, p in enumerate(pat):
            w = wide if p == "w" else narrow
            is_bar = (i % 2 == 0)
            elements.append((w, is_bar))
    return elements


def _encode_code128(data):
    """Return a binary string for Code 128 (character set B)."""
    values = [_CODE128_START_B]
    for ch in data:
        v = _CODE128_VALUES_B.get(ch)
        if v is None:
            v = 0
        values.append(v)
    # Checksum
    total = values[0]
    for i, v in enumerate(values[1:], 1):
        total += i * v
    values.append(total % 103)
    values.append(106)  # stop
    bits = ""
    for v in values:
        bits += _CODE128_PATTERNS[v]
    return bits


def _encode_itf(digits):
    """Return a list of (width, is_bar) tuples for ITF (Interleaved 2 of 5)."""
    narrow = 1
    wide = 3
    _ITF_PATTERNS = {
        "0": "nnwwn", "1": "wnnnw", "2": "nwnnw", "3": "wwnnn",
        "4": "nnwnw", "5": "wnwnn", "6": "nwwnn", "7": "nnnww",
        "8": "wnnwn", "9": "nwnwn",
    }
    # Start pattern
    elements = [(narrow, True), (narrow, False), (narrow, True), (narrow, False)]
    # Encode pairs
    for i in range(0, len(digits), 2):
        bar_pat = _ITF_PATTERNS[digits[i]]
        space_pat = _ITF_PATTERNS[digits[i + 1]]
        for j in range(5):
            bw = wide if bar_pat[j] == "w" else narrow
            sw = wide if space_pat[j] == "w" else narrow
            elements.append((bw, True))
            elements.append((sw, False))
    # Stop pattern
    elements.extend([(wide, True), (narrow, False), (narrow, True)])
    return elements


def render_barcode(barcode_format, barcode_value, width=320, height=160):
    """Render a barcode to a Cairo ImageSurface.

    Returns a cairo.ImageSurface or None if the format is unsupported.
    """
    fmt_lower = barcode_format.lower().replace(" ", "").replace("-", "")

    if fmt_lower in ("ean13",):
        return _render_binary_barcode(_encode_ean13(barcode_value), barcode_value, width, height)
    elif fmt_lower in ("ean8",):
        return _render_binary_barcode(_encode_ean8(barcode_value), barcode_value, width, height)
    elif fmt_lower in ("upca",):
        return _render_binary_barcode(_encode_upca(barcode_value), barcode_value, width, height)
    elif fmt_lower in ("code128",):
        return _render_binary_barcode(_encode_code128(barcode_value), barcode_value, width, height)
    elif fmt_lower in ("code39",):
        return _render_element_barcode(_encode_code39(barcode_value), barcode_value, width, height)
    elif fmt_lower in ("itf",):
        return _render_element_barcode(_encode_itf(barcode_value), barcode_value, width, height)
    elif fmt_lower in ("codabar",):
        # Codabar uses same structure as Code 39
        return _render_element_barcode(_encode_code39(barcode_value), barcode_value, width, height)

    return None


def _render_binary_barcode(bits, text, width, height):
    """Render a barcode from a binary string (1=bar, 0=space)."""
    padding = 20
    text_height = 20
    bar_height = height - padding * 2 - text_height

    n_modules = len(bits)
    avail_width = width - padding * 2
    module_width = avail_width / n_modules

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # White background
    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0, 0, width, height)
    ctx.fill()

    # Draw bars
    ctx.set_source_rgb(0, 0, 0)
    for i, bit in enumerate(bits):
        if bit == "1":
            x = padding + i * module_width
            ctx.rectangle(x, padding, module_width, bar_height)
            ctx.fill()

    # Draw text below barcode
    ctx.set_font_size(12)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    extents = ctx.text_extents(text)
    text_x = (width - extents.width) / 2
    text_y = height - padding / 2
    ctx.move_to(text_x, text_y)
    ctx.show_text(text)

    return surface


def _render_element_barcode(elements, text, width, height):
    """Render a barcode from a list of (width, is_bar) tuples."""
    padding = 20
    text_height = 20
    bar_height = height - padding * 2 - text_height

    total_units = sum(w for w, _ in elements)
    avail_width = width - padding * 2
    unit_width = avail_width / total_units

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # White background
    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0, 0, width, height)
    ctx.fill()

    # Draw bars
    ctx.set_source_rgb(0, 0, 0)
    x = padding
    for w, is_bar in elements:
        px_width = w * unit_width
        if is_bar:
            ctx.rectangle(x, padding, px_width, bar_height)
            ctx.fill()
        x += px_width

    # Draw text below
    ctx.set_font_size(12)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    extents = ctx.text_extents(text)
    text_x = (width - extents.width) / 2
    text_y = height - padding / 2
    ctx.move_to(text_x, text_y)
    ctx.show_text(text)

    return surface
