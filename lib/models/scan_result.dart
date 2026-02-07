import 'package:google_mlkit_barcode_scanning/google_mlkit_barcode_scanning.dart';

class ScanResult {
  final String rawValue;
  final BarcodeFormat format;
  final String displayValue;

  const ScanResult({
    required this.rawValue,
    required this.format,
    required this.displayValue,
  });

  factory ScanResult.fromBarcode(Barcode barcode) {
    return ScanResult(
      rawValue: barcode.rawValue ?? '',
      format: barcode.format,
      displayValue: barcode.displayValue ?? barcode.rawValue ?? '',
    );
  }

  String get formatName {
    switch (format) {
      case BarcodeFormat.ean13:
        return 'EAN-13';
      case BarcodeFormat.ean8:
        return 'EAN-8';
      case BarcodeFormat.upca:
        return 'UPC-A';
      case BarcodeFormat.upce:
        return 'UPC-E';
      case BarcodeFormat.code128:
        return 'Code 128';
      case BarcodeFormat.code39:
        return 'Code 39';
      case BarcodeFormat.code93:
        return 'Code 93';
      case BarcodeFormat.qrCode:
        return 'QR Code';
      case BarcodeFormat.dataMatrix:
        return 'Data Matrix';
      case BarcodeFormat.pdf417:
        return 'PDF417';
      case BarcodeFormat.aztec:
        return 'Aztec';
      case BarcodeFormat.itf:
        return 'ITF';
      case BarcodeFormat.codabar:
        return 'Codabar';
      default:
        return 'Unknown';
    }
  }
}
