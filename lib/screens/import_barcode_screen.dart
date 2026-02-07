import 'dart:io';

import 'package:flutter/material.dart';
import 'package:google_mlkit_barcode_scanning/google_mlkit_barcode_scanning.dart';
import 'package:image_picker/image_picker.dart';

import '../models/scan_result.dart';
import '../services/barcode_scanner_service.dart';

class ImportBarcodeScreen extends StatefulWidget {
  const ImportBarcodeScreen({super.key});

  @override
  State<ImportBarcodeScreen> createState() => _ImportBarcodeScreenState();
}

class _ImportBarcodeScreenState extends State<ImportBarcodeScreen> {
  final _imagePicker = ImagePicker();
  final _scannerService = BarcodeScannerService();

  bool _isProcessing = false;
  String? _imagePath;
  List<ScanResult>? _results;
  String? _error;

  @override
  void dispose() {
    _scannerService.dispose();
    super.dispose();
  }

  Future<void> _pickAndScanImage(ImageSource source) async {
    setState(() {
      _isProcessing = true;
      _results = null;
      _error = null;
      _imagePath = null;
    });

    try {
      final pickedFile = await _imagePicker.pickImage(source: source);
      if (pickedFile == null) {
        setState(() => _isProcessing = false);
        return;
      }

      setState(() => _imagePath = pickedFile.path);

      final inputImage = InputImage.fromFilePath(pickedFile.path);
      final results = await _scannerService.scanImage(inputImage);

      setState(() {
        _results = results;
        _isProcessing = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to process image: $e';
        _isProcessing = false;
      });
    }
  }

  void _selectBarcode(ScanResult result) {
    Navigator.of(context).pop(result);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Import Barcode'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildImageSourceButtons(),
            const SizedBox(height: 16),
            Expanded(child: _buildContent()),
          ],
        ),
      ),
    );
  }

  Widget _buildImageSourceButtons() {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: _isProcessing
                ? null
                : () => _pickAndScanImage(ImageSource.gallery),
            icon: const Icon(Icons.photo_library),
            label: const Text('Gallery'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: _isProcessing
                ? null
                : () => _pickAndScanImage(ImageSource.camera),
            icon: const Icon(Icons.camera_alt),
            label: const Text('Camera'),
          ),
        ),
      ],
    );
  }

  Widget _buildContent() {
    if (_isProcessing) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Scanning for barcodes...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
            const SizedBox(height: 16),
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => setState(() => _error = null),
              child: const Text('Try Again'),
            ),
          ],
        ),
      );
    }

    if (_results == null) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.image_search, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'Pick an image to scan for barcodes',
              style: TextStyle(fontSize: 16, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    if (_results!.isEmpty) {
      return _buildNoBarcodesFound();
    }

    if (_results!.length == 1) {
      return _buildSingleResult(_results!.first);
    }

    return _buildMultipleResults(_results!);
  }

  Widget _buildImagePreview() {
    if (_imagePath == null) return const SizedBox.shrink();
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: Image.file(
        File(_imagePath!),
        height: 150,
        width: double.infinity,
        fit: BoxFit.contain,
      ),
    );
  }

  Widget _buildNoBarcodesFound() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildImagePreview(),
          const SizedBox(height: 24),
          Icon(Icons.search_off, size: 64, color: Colors.orange[300]),
          const SizedBox(height: 16),
          const Text(
            'No barcode found',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'The image does not appear to contain a recognizable barcode. '
            'Try a different image with a clear, well-lit barcode.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: () => _pickAndScanImage(ImageSource.gallery),
            icon: const Icon(Icons.refresh),
            label: const Text('Try Another Image'),
          ),
        ],
      ),
    );
  }

  Widget _buildSingleResult(ScanResult result) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildImagePreview(),
          const SizedBox(height: 24),
          Icon(Icons.check_circle, size: 64, color: Colors.green[400]),
          const SizedBox(height: 16),
          const Text(
            'Barcode Found',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          _buildResultCard(result),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () => _selectBarcode(result),
            icon: const Icon(Icons.check),
            label: const Text('Use This Barcode'),
          ),
        ],
      ),
    );
  }

  Widget _buildMultipleResults(List<ScanResult> results) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _buildImagePreview(),
        const SizedBox(height: 16),
        Row(
          children: [
            Icon(Icons.info_outline, color: Colors.blue[400]),
            const SizedBox(width: 8),
            Text(
              '${results.length} barcodes found - select one',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView.separated(
            itemCount: results.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final result = results[index];
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.qr_code),
                  title: Text(
                    result.displayValue,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  subtitle: Text(result.formatName),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _selectBarcode(result),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildResultCard(ScanResult result) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                const Icon(Icons.qr_code, size: 32),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        result.displayValue,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        result.formatName,
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
