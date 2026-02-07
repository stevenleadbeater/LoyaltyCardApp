import 'package:flutter_test/flutter_test.dart';
import 'package:google_mlkit_barcode_scanning/google_mlkit_barcode_scanning.dart';

import 'package:loyalty_card_app/models/scan_result.dart';

void main() {
  group('ScanResult', () {
    test('formatName returns correct name for EAN-13', () {
      const result = ScanResult(
        rawValue: '1234567890128',
        format: BarcodeFormat.ean13,
        displayValue: '1234567890128',
      );
      expect(result.formatName, 'EAN-13');
    });

    test('formatName returns correct name for QR Code', () {
      const result = ScanResult(
        rawValue: 'https://example.com',
        format: BarcodeFormat.qrCode,
        displayValue: 'https://example.com',
      );
      expect(result.formatName, 'QR Code');
    });

    test('formatName returns correct name for Code 128', () {
      const result = ScanResult(
        rawValue: 'ABC123',
        format: BarcodeFormat.code128,
        displayValue: 'ABC123',
      );
      expect(result.formatName, 'Code 128');
    });

    test('formatName returns correct name for UPC-A', () {
      const result = ScanResult(
        rawValue: '012345678905',
        format: BarcodeFormat.upca,
        displayValue: '012345678905',
      );
      expect(result.formatName, 'UPC-A');
    });

    test('formatName returns correct name for Data Matrix', () {
      const result = ScanResult(
        rawValue: 'data',
        format: BarcodeFormat.dataMatrix,
        displayValue: 'data',
      );
      expect(result.formatName, 'Data Matrix');
    });

    test('formatName returns Unknown for unrecognized format', () {
      const result = ScanResult(
        rawValue: 'data',
        format: BarcodeFormat.unknown,
        displayValue: 'data',
      );
      expect(result.formatName, 'Unknown');
    });

    test('formatName covers all supported formats', () {
      final formatMap = {
        BarcodeFormat.ean13: 'EAN-13',
        BarcodeFormat.ean8: 'EAN-8',
        BarcodeFormat.upca: 'UPC-A',
        BarcodeFormat.upce: 'UPC-E',
        BarcodeFormat.code128: 'Code 128',
        BarcodeFormat.code39: 'Code 39',
        BarcodeFormat.code93: 'Code 93',
        BarcodeFormat.qrCode: 'QR Code',
        BarcodeFormat.dataMatrix: 'Data Matrix',
        BarcodeFormat.pdf417: 'PDF417',
        BarcodeFormat.aztec: 'Aztec',
        BarcodeFormat.itf: 'ITF',
        BarcodeFormat.codabar: 'Codabar',
      };

      for (final entry in formatMap.entries) {
        final result = ScanResult(
          rawValue: 'test',
          format: entry.key,
          displayValue: 'test',
        );
        expect(result.formatName, entry.value,
            reason: 'Format ${entry.key} should map to ${entry.value}');
      }
    });
  });
}
