"""Tests for barcode format validation."""

import pytest

from loyalty_card_app.barcode_formats import BarcodeFormat, validate_barcode


class TestEmptyInput:
    def test_empty_string_rejected(self):
        for fmt in BarcodeFormat:
            assert validate_barcode(fmt, "") is not None


class TestEAN13:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.EAN_13, "4006381333931") is None

    def test_wrong_length(self):
        err = validate_barcode(BarcodeFormat.EAN_13, "400638133393")
        assert "13 digits" in err

    def test_non_digit(self):
        err = validate_barcode(BarcodeFormat.EAN_13, "400638133393A")
        assert "digits" in err

    def test_bad_check_digit(self):
        err = validate_barcode(BarcodeFormat.EAN_13, "4006381333932")
        assert "check digit" in err

    def test_all_zeros(self):
        assert validate_barcode(BarcodeFormat.EAN_13, "0000000000000") is None


class TestEAN8:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.EAN_8, "96385074") is None

    def test_wrong_length(self):
        err = validate_barcode(BarcodeFormat.EAN_8, "9638507")
        assert "8 digits" in err

    def test_non_digit(self):
        err = validate_barcode(BarcodeFormat.EAN_8, "9638507x")
        assert "digits" in err

    def test_bad_check_digit(self):
        err = validate_barcode(BarcodeFormat.EAN_8, "96385075")
        assert "check digit" in err


class TestUPCA:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.UPC_A, "042100005264") is None

    def test_wrong_length(self):
        err = validate_barcode(BarcodeFormat.UPC_A, "04210000526")
        assert "12 digits" in err

    def test_bad_check_digit(self):
        err = validate_barcode(BarcodeFormat.UPC_A, "042100005265")
        assert "check digit" in err


class TestCode128:
    def test_valid_alphanumeric(self):
        assert validate_barcode(BarcodeFormat.CODE_128, "Hello123") is None

    def test_valid_with_special(self):
        assert validate_barcode(BarcodeFormat.CODE_128, "TEST-123/ABC") is None

    def test_too_long(self):
        err = validate_barcode(BarcodeFormat.CODE_128, "A" * 81)
        assert "too long" in err

    def test_non_ascii(self):
        err = validate_barcode(BarcodeFormat.CODE_128, "Héllo")
        assert "ASCII" in err


class TestCode39:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.CODE_39, "HELLO-123") is None

    def test_lowercase_accepted(self):
        # Code 39 is case-insensitive; we uppercase internally
        assert validate_barcode(BarcodeFormat.CODE_39, "hello") is None

    def test_invalid_char(self):
        err = validate_barcode(BarcodeFormat.CODE_39, "HELLO@123")
        assert "does not support" in err

    def test_special_chars(self):
        assert validate_barcode(BarcodeFormat.CODE_39, "-. $/+%") is None


class TestQRCode:
    def test_valid_short(self):
        assert validate_barcode(BarcodeFormat.QR_CODE, "hello") is None

    def test_valid_url(self):
        assert validate_barcode(BarcodeFormat.QR_CODE, "https://example.com") is None

    def test_valid_unicode(self):
        assert validate_barcode(BarcodeFormat.QR_CODE, "日本語テスト") is None

    def test_too_large(self):
        err = validate_barcode(BarcodeFormat.QR_CODE, "A" * 4297)
        assert "too large" in err

    def test_at_limit(self):
        assert validate_barcode(BarcodeFormat.QR_CODE, "A" * 4296) is None


class TestDataMatrix:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.DATA_MATRIX, "DM-TEST-123") is None

    def test_too_large(self):
        err = validate_barcode(BarcodeFormat.DATA_MATRIX, "A" * 2336)
        assert "too large" in err


class TestPDF417:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.PDF_417, "PDF417-DATA") is None

    def test_too_large(self):
        err = validate_barcode(BarcodeFormat.PDF_417, "A" * 1851)
        assert "too large" in err


class TestCodabar:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.CODABAR, "A12345B") is None

    def test_missing_start_stop(self):
        err = validate_barcode(BarcodeFormat.CODABAR, "12345")
        assert "start and end" in err

    def test_invalid_char(self):
        err = validate_barcode(BarcodeFormat.CODABAR, "A123@5B")
        assert "does not support" in err

    def test_too_short(self):
        err = validate_barcode(BarcodeFormat.CODABAR, "AB")
        assert "at least 3" in err

    def test_all_start_stop_codes(self):
        for s in "ABCD":
            for e in "ABCD":
                assert validate_barcode(BarcodeFormat.CODABAR, f"{s}1{e}") is None


class TestITF:
    def test_valid(self):
        assert validate_barcode(BarcodeFormat.ITF, "1234567890") is None

    def test_odd_length(self):
        err = validate_barcode(BarcodeFormat.ITF, "12345")
        assert "even" in err

    def test_non_digit(self):
        err = validate_barcode(BarcodeFormat.ITF, "12AB56")
        assert "digits" in err

    def test_minimum_length(self):
        assert validate_barcode(BarcodeFormat.ITF, "12") is None

    def test_too_short(self):
        err = validate_barcode(BarcodeFormat.ITF, "1")
        # Single digit is odd, so "even" error
        assert err is not None

    def test_too_long(self):
        err = validate_barcode(BarcodeFormat.ITF, "0" * 82)
        assert "too long" in err
