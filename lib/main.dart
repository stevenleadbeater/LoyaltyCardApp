import 'package:flutter/material.dart';

import 'models/scan_result.dart';
import 'screens/import_barcode_screen.dart';

void main() {
  runApp(const LoyaltyCardApp());
}

class LoyaltyCardApp extends StatelessWidget {
  const LoyaltyCardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Loyalty Card App',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  ScanResult? _lastImportedBarcode;

  Future<void> _importBarcode() async {
    final result = await Navigator.of(context).push<ScanResult>(
      MaterialPageRoute(builder: (_) => const ImportBarcodeScreen()),
    );
    if (result != null) {
      setState(() => _lastImportedBarcode = result);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Imported ${result.formatName}: ${result.displayValue}'),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Loyalty Card App'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Center(
        child: _lastImportedBarcode != null
            ? Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.credit_card, size: 64),
                  const SizedBox(height: 16),
                  Text(
                    'Last Imported Barcode',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(_lastImportedBarcode!.displayValue),
                  Text(
                    _lastImportedBarcode!.formatName,
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                ],
              )
            : const Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.credit_card, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text(
                    'No cards yet',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Import a barcode from an image to get started',
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _importBarcode,
        icon: const Icon(Icons.add_photo_alternate),
        label: const Text('Import Barcode'),
      ),
    );
  }
}
