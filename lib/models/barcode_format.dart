enum BarcodeFormat {
  ean13,
  ean8,
  upcA,
  code128,
  code39,
  qr,
  dataMatrix,
}

extension BarcodeFormatExtension on BarcodeFormat {
  String get displayName {
    switch (this) {
      case BarcodeFormat.ean13:
        return 'EAN-13';
      case BarcodeFormat.ean8:
        return 'EAN-8';
      case BarcodeFormat.upcA:
        return 'UPC-A';
      case BarcodeFormat.code128:
        return 'Code 128';
      case BarcodeFormat.code39:
        return 'Code 39';
      case BarcodeFormat.qr:
        return 'QR Code';
      case BarcodeFormat.dataMatrix:
        return 'Data Matrix';
    }
  }
}
