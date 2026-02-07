"""Tests for barcode scanner format mapping and logic."""

import pytest

from loyalty_card_app.barcode_scanner import ZBAR_FORMAT_MAP, map_zbar_format
from loyalty_card_app.barcode_formats import BarcodeFormat


class TestZbarFormatMapping:
    """Test that zbar type strings map correctly to BarcodeFormat."""

    def test_ean13(self):
        assert map_zbar_format("EAN-13") == BarcodeFormat.EAN_13

    def test_ean8(self):
        assert map_zbar_format("EAN-8") == BarcodeFormat.EAN_8

    def test_upc_a(self):
        assert map_zbar_format("UPC-A") == BarcodeFormat.UPC_A

    def test_code128(self):
        assert map_zbar_format("CODE-128") == BarcodeFormat.CODE_128

    def test_code128_alt(self):
        assert map_zbar_format("Code-128") == BarcodeFormat.CODE_128

    def test_code39(self):
        assert map_zbar_format("CODE-39") == BarcodeFormat.CODE_39

    def test_code39_alt(self):
        assert map_zbar_format("Code-39") == BarcodeFormat.CODE_39

    def test_qr_code(self):
        assert map_zbar_format("QR-Code") == BarcodeFormat.QR_CODE

    def test_codabar(self):
        assert map_zbar_format("CODABAR") == BarcodeFormat.CODABAR

    def test_codabar_alt(self):
        assert map_zbar_format("Codabar") == BarcodeFormat.CODABAR

    def test_itf(self):
        assert map_zbar_format("I2/5") == BarcodeFormat.ITF

    def test_unknown_returns_none(self):
        assert map_zbar_format("UNKNOWN-FORMAT") is None

    def test_empty_string_returns_none(self):
        assert map_zbar_format("") is None


class TestFormatMapCoverage:
    """Verify that all expected zbar formats are in the map."""

    def test_all_standard_formats_present(self):
        expected_zbar_types = [
            "EAN-13", "EAN-8", "UPC-A", "CODE-128",
            "CODE-39", "QR-Code", "CODABAR", "I2/5",
        ]
        for zbar_type in expected_zbar_types:
            assert zbar_type in ZBAR_FORMAT_MAP, f"Missing mapping for {zbar_type}"

    def test_all_mapped_values_are_valid_formats(self):
        for zbar_type, fmt in ZBAR_FORMAT_MAP.items():
            assert isinstance(fmt, BarcodeFormat), (
                f"{zbar_type} maps to {fmt} which is not a BarcodeFormat"
            )
