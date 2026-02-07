"""Barcode format definitions and validation for loyalty card app."""

import re
from enum import Enum


class BarcodeFormat(Enum):
    """Supported barcode formats."""
    EAN_13 = "EAN-13"
    EAN_8 = "EAN-8"
    UPC_A = "UPC-A"
    CODE_128 = "Code 128"
    CODE_39 = "Code 39"
    QR_CODE = "QR Code"
    DATA_MATRIX = "DataMatrix"
    PDF_417 = "PDF417"
    CODABAR = "Codabar"
    ITF = "ITF"


# Formats grouped by type for UI display
FORMAT_1D = [
    BarcodeFormat.EAN_13,
    BarcodeFormat.EAN_8,
    BarcodeFormat.UPC_A,
    BarcodeFormat.CODE_128,
    BarcodeFormat.CODE_39,
    BarcodeFormat.CODABAR,
    BarcodeFormat.ITF,
]

FORMAT_2D = [
    BarcodeFormat.QR_CODE,
    BarcodeFormat.DATA_MATRIX,
    BarcodeFormat.PDF_417,
]


def _luhn_check(digits: str) -> bool:
    """Verify a numeric string passes the Luhn checksum (used by EAN/UPC)."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 3
        total += n
    return total % 10 == 0


# Code 39 valid character set
_CODE39_CHARS = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%")

# Codabar valid character set
_CODABAR_CHARS = set("0123456789-$:/.+ABCD")


def validate_barcode(fmt: BarcodeFormat, value: str) -> str | None:
    """Validate a barcode value for the given format.

    Returns None if valid, or an error message string if invalid.
    """
    if not value:
        return "Barcode value cannot be empty"

    match fmt:
        case BarcodeFormat.EAN_13:
            return _validate_ean13(value)
        case BarcodeFormat.EAN_8:
            return _validate_ean8(value)
        case BarcodeFormat.UPC_A:
            return _validate_upc_a(value)
        case BarcodeFormat.CODE_128:
            return _validate_code128(value)
        case BarcodeFormat.CODE_39:
            return _validate_code39(value)
        case BarcodeFormat.QR_CODE:
            return _validate_qr(value)
        case BarcodeFormat.DATA_MATRIX:
            return _validate_data_matrix(value)
        case BarcodeFormat.PDF_417:
            return _validate_pdf417(value)
        case BarcodeFormat.CODABAR:
            return _validate_codabar(value)
        case BarcodeFormat.ITF:
            return _validate_itf(value)


def _validate_ean13(value: str) -> str | None:
    if not value.isdigit():
        return "EAN-13 must contain only digits"
    if len(value) != 13:
        return "EAN-13 must be exactly 13 digits"
    if not _luhn_check(value):
        return "EAN-13 check digit is invalid"
    return None


def _validate_ean8(value: str) -> str | None:
    if not value.isdigit():
        return "EAN-8 must contain only digits"
    if len(value) != 8:
        return "EAN-8 must be exactly 8 digits"
    if not _luhn_check(value):
        return "EAN-8 check digit is invalid"
    return None


def _validate_upc_a(value: str) -> str | None:
    if not value.isdigit():
        return "UPC-A must contain only digits"
    if len(value) != 12:
        return "UPC-A must be exactly 12 digits"
    if not _luhn_check(value):
        return "UPC-A check digit is invalid"
    return None


def _validate_code128(value: str) -> str | None:
    if len(value) > 80:
        return "Code 128 value is too long (max 80 characters)"
    for ch in value:
        if ord(ch) < 0 or ord(ch) > 127:
            return "Code 128 supports only ASCII characters (0-127)"
    return None


def _validate_code39(value: str) -> str | None:
    upper = value.upper()
    for ch in upper:
        if ch not in _CODE39_CHARS:
            return f"Code 39 does not support character '{ch}'"
    if len(upper) > 80:
        return "Code 39 value is too long (max 80 characters)"
    return None


def _validate_qr(value: str) -> str | None:
    encoded = value.encode("utf-8")
    if len(encoded) > 4296:
        return "QR Code data is too large (max 4296 bytes)"
    return None


def _validate_data_matrix(value: str) -> str | None:
    encoded = value.encode("utf-8")
    if len(encoded) > 2335:
        return "DataMatrix data is too large (max 2335 bytes)"
    return None


def _validate_pdf417(value: str) -> str | None:
    encoded = value.encode("utf-8")
    if len(encoded) > 1850:
        return "PDF417 data is too large (max 1850 bytes)"
    return None


def _validate_codabar(value: str) -> str | None:
    upper = value.upper()
    for ch in upper:
        if ch not in _CODABAR_CHARS:
            return f"Codabar does not support character '{ch}'"
    if len(upper) < 3:
        return "Codabar must be at least 3 characters (start + data + stop)"
    if upper[0] not in "ABCD" or upper[-1] not in "ABCD":
        return "Codabar must start and end with A, B, C, or D"
    return None


def _validate_itf(value: str) -> str | None:
    if not value.isdigit():
        return "ITF must contain only digits"
    if len(value) % 2 != 0:
        return "ITF must have an even number of digits"
    if len(value) < 2:
        return "ITF must be at least 2 digits"
    if len(value) > 80:
        return "ITF is too long (max 80 digits)"
    return None
