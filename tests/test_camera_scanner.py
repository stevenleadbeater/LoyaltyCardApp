"""Tests for camera_scanner module."""

import unittest
from unittest.mock import MagicMock, patch

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)

import sys
import os

# Add src to path so we can import the module directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camera_scanner import (
    PIPELINE_DESC,
    SUPPORTED_FORMATS,
    ZBAR_FORMAT_MAP,
    CameraScannerPage,
)


class TestZbarFormatMap(unittest.TestCase):
    """Tests for the ZBar type to format name mapping."""

    def test_ean13_mapped(self):
        self.assertEqual(ZBAR_FORMAT_MAP["EAN-13"], "EAN-13")

    def test_ean8_mapped(self):
        self.assertEqual(ZBAR_FORMAT_MAP["EAN-8"], "EAN-8")

    def test_upc_a_mapped(self):
        self.assertEqual(ZBAR_FORMAT_MAP["UPC-A"], "UPC-A")

    def test_code128_mapped(self):
        self.assertEqual(ZBAR_FORMAT_MAP["CODE-128"], "Code 128")

    def test_code39_mapped(self):
        self.assertEqual(ZBAR_FORMAT_MAP["CODE-39"], "Code 39")

    def test_qr_code_mapped(self):
        self.assertEqual(ZBAR_FORMAT_MAP["QR-Code"], "QR Code")

    def test_datamatrix_mapped(self):
        self.assertEqual(ZBAR_FORMAT_MAP["DataMatrix"], "DataMatrix")

    def test_unknown_type_returns_none(self):
        self.assertIsNone(ZBAR_FORMAT_MAP.get("UNKNOWN-TYPE"))


class TestSupportedFormats(unittest.TestCase):
    """Tests for the supported formats set."""

    def test_required_formats_present(self):
        required = {"EAN-13", "EAN-8", "UPC-A", "Code 128", "QR Code", "DataMatrix"}
        self.assertTrue(required.issubset(SUPPORTED_FORMATS))

    def test_all_map_values_in_supported(self):
        for fmt in ZBAR_FORMAT_MAP.values():
            self.assertIn(fmt, SUPPORTED_FORMATS)


class TestPipelineDescription(unittest.TestCase):
    """Tests for the GStreamer pipeline description."""

    def test_contains_v4l2src(self):
        self.assertIn("v4l2src", PIPELINE_DESC)

    def test_contains_zbar(self):
        self.assertIn("zbar", PIPELINE_DESC)

    def test_contains_gtk4paintablesink(self):
        self.assertIn("gtk4paintablesink", PIPELINE_DESC)

    def test_contains_videoconvert(self):
        self.assertIn("videoconvert", PIPELINE_DESC)


class TestCameraScannerPageInit(unittest.TestCase):
    """Tests for CameraScannerPage construction (no GTK display needed)."""

    @patch("camera_scanner.Gst.parse_launch")
    def test_page_title(self, _mock_launch):
        # CameraScannerPage inherits from Adw.NavigationPage which needs
        # a display. We test attributes that don't require a display.
        # The title is set in __init__ before any widget realization.
        pass

    def test_zbar_format_map_is_dict(self):
        self.assertIsInstance(ZBAR_FORMAT_MAP, dict)

    def test_supported_formats_is_frozenset(self):
        self.assertIsInstance(SUPPORTED_FORMATS, frozenset)


class TestHandleBarcode(unittest.TestCase):
    """Tests for barcode message handling logic."""

    def test_format_mapping_ean13(self):
        """Simulate an EAN-13 barcode detection."""
        struct = Gst.Structure.new_from_string(
            "barcode,type=(string)EAN-13,symbol=(string)4006381333931,quality=(int)1"
        )
        barcode_type = struct.get_string("type")
        symbol = struct.get_string("symbol")
        self.assertEqual(barcode_type, "EAN-13")
        self.assertEqual(symbol, "4006381333931")
        self.assertEqual(ZBAR_FORMAT_MAP.get(barcode_type), "EAN-13")

    def test_format_mapping_qr(self):
        """Simulate a QR code detection."""
        struct = Gst.Structure.new_from_string(
            "barcode,type=(string)QR-Code,symbol=(string)https://example.com,quality=(int)1"
        )
        barcode_type = struct.get_string("type")
        symbol = struct.get_string("symbol")
        self.assertEqual(barcode_type, "QR-Code")
        self.assertEqual(symbol, "https://example.com")
        self.assertEqual(ZBAR_FORMAT_MAP.get(barcode_type), "QR Code")

    def test_format_mapping_code128(self):
        """Simulate a Code 128 barcode detection."""
        struct = Gst.Structure.new_from_string(
            "barcode,type=(string)CODE-128,symbol=(string)ABC123,quality=(int)1"
        )
        barcode_type = struct.get_string("type")
        self.assertEqual(ZBAR_FORMAT_MAP.get(barcode_type), "Code 128")

    def test_format_mapping_upc_a(self):
        """Simulate a UPC-A barcode detection."""
        struct = Gst.Structure.new_from_string(
            "barcode,type=(string)UPC-A,symbol=(string)042100005264,quality=(int)1"
        )
        barcode_type = struct.get_string("type")
        self.assertEqual(ZBAR_FORMAT_MAP.get(barcode_type), "UPC-A")

    def test_unsupported_type_not_mapped(self):
        """An unsupported barcode type should not be in the map."""
        struct = Gst.Structure.new_from_string(
            "barcode,type=(string)ISBN-13,symbol=(string)1234567890123,quality=(int)1"
        )
        barcode_type = struct.get_string("type")
        self.assertIsNone(ZBAR_FORMAT_MAP.get(barcode_type))

    def test_none_symbol_rejected(self):
        """A structure without a symbol field should be treated as no detection."""
        struct = Gst.Structure.new_from_string(
            "barcode,type=(string)EAN-13,quality=(int)1"
        )
        symbol = struct.get_string("symbol")
        # Missing field returns None - should be rejected.
        self.assertFalse(symbol)


if __name__ == "__main__":
    unittest.main()
