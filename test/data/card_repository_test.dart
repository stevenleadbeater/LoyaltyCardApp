import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:loyalty_card_app/data/card_repository.dart';
import 'package:loyalty_card_app/data/database_helper.dart';
import 'package:loyalty_card_app/models/barcode_format.dart';
import 'package:loyalty_card_app/models/loyalty_card.dart';

Future<Database> _createTestDb() async {
  return databaseFactoryFfi.openDatabase(
    inMemoryDatabasePath,
    options: OpenDatabaseOptions(
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE ${DatabaseHelper.table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode_data TEXT NOT NULL,
            barcode_format TEXT NOT NULL,
            color INTEGER NOT NULL,
            created_at TEXT NOT NULL
          )
        ''');
      },
    ),
  );
}

void main() {
  sqfliteFfiInit();

  late Database db;
  late CardRepository repo;

  final now = DateTime(2026, 1, 15, 10, 30);

  LoyaltyCard makeCard({
    String name = 'Test Card',
    String barcodeData = '1234567890',
    BarcodeFormat format = BarcodeFormat.ean13,
    Color color = Colors.blue,
  }) {
    return LoyaltyCard(
      name: name,
      barcodeData: barcodeData,
      barcodeFormat: format,
      color: color,
      createdAt: now,
    );
  }

  setUp(() async {
    db = await _createTestDb();
    repo = CardRepository(getDatabase: () async => db);
  });

  tearDown(() async {
    await db.close();
  });

  group('CardRepository', () {
    test('insert returns new id', () async {
      final id = await repo.insert(makeCard());
      expect(id, greaterThan(0));
    });

    test('getById returns inserted card', () async {
      final id = await repo.insert(makeCard(name: 'Tesco'));
      final card = await repo.getById(id);
      expect(card, isNotNull);
      expect(card!.id, id);
      expect(card.name, 'Tesco');
      expect(card.barcodeData, '1234567890');
      expect(card.barcodeFormat, BarcodeFormat.ean13);
      expect(card.color.toARGB32(), Colors.blue.toARGB32());
    });

    test('getById returns null for missing id', () async {
      final card = await repo.getById(999);
      expect(card, isNull);
    });

    test('getAll returns all cards ordered by created_at DESC', () async {
      final earlier = makeCard(name: 'First');
      final later = LoyaltyCard(
        name: 'Second',
        barcodeData: '999',
        barcodeFormat: BarcodeFormat.qr,
        color: Colors.red,
        createdAt: now.add(const Duration(hours: 1)),
      );
      await repo.insert(earlier);
      await repo.insert(later);

      final cards = await repo.getAll();
      expect(cards, hasLength(2));
      expect(cards[0].name, 'Second');
      expect(cards[1].name, 'First');
    });

    test('getAll returns empty list when no cards', () async {
      final cards = await repo.getAll();
      expect(cards, isEmpty);
    });

    test('update modifies existing card', () async {
      final id = await repo.insert(makeCard(name: 'Old Name'));
      var card = await repo.getById(id);
      final updated = card!.copyWith(name: 'New Name');
      final rowsAffected = await repo.update(updated);
      expect(rowsAffected, 1);

      card = await repo.getById(id);
      expect(card!.name, 'New Name');
    });

    test('delete removes card', () async {
      final id = await repo.insert(makeCard());
      expect(await repo.count(), 1);

      final rowsDeleted = await repo.delete(id);
      expect(rowsDeleted, 1);
      expect(await repo.count(), 0);
      expect(await repo.getById(id), isNull);
    });

    test('delete returns 0 for missing id', () async {
      final rowsDeleted = await repo.delete(999);
      expect(rowsDeleted, 0);
    });

    test('count tracks insertions and deletions', () async {
      expect(await repo.count(), 0);

      final id1 = await repo.insert(makeCard(name: 'A'));
      await repo.insert(makeCard(name: 'B'));
      expect(await repo.count(), 2);

      await repo.delete(id1);
      expect(await repo.count(), 1);
    });

    test('stores all barcode formats correctly', () async {
      for (final format in BarcodeFormat.values) {
        final id = await repo.insert(makeCard(
          name: format.displayName,
          format: format,
        ));
        final card = await repo.getById(id);
        expect(card!.barcodeFormat, format);
      }
    });

    test('stores color correctly', () async {
      final id = await repo.insert(makeCard(color: const Color(0xFFABCDEF)));
      final card = await repo.getById(id);
      expect(card!.color, const Color(0xFFABCDEF));
    });
  });
}
