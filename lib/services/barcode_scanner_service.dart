import 'package:google_mlkit_barcode_scanning/google_mlkit_barcode_scanning.dart';
import '../models/scan_result.dart';

class BarcodeScannerService {
  BarcodeScanner? _scanner;

  BarcodeScanner get scanner {
    _scanner ??= BarcodeScanner();
    return _scanner!;
  }

  Future<List<ScanResult>> scanImage(InputImage inputImage) async {
    final barcodes = await scanner.processImage(inputImage);
    return barcodes
        .where((b) => b.rawValue != null && b.rawValue!.isNotEmpty)
        .map((b) => ScanResult.fromBarcode(b))
        .toList();
  }

  void dispose() {
    _scanner?.close();
    _scanner = null;
  }
}
