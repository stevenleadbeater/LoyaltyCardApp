import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:loyalty_card_app/models/barcode_format.dart';
import 'package:loyalty_card_app/models/loyalty_card.dart';

void main() {
  group('LoyaltyCard', () {
    final now = DateTime(2026, 1, 15, 10, 30);
    final card = LoyaltyCard(
      id: 1,
      name: 'Tesco Clubcard',
      barcodeData: '5012345678900',
      barcodeFormat: BarcodeFormat.ean13,
      color: Colors.blue,
      createdAt: now,
    );

    test('toMap produces correct map', () {
      final map = card.toMap();
      expect(map['id'], 1);
      expect(map['name'], 'Tesco Clubcard');
      expect(map['barcode_data'], '5012345678900');
      expect(map['barcode_format'], 'ean13');
      expect(map['color'], Colors.blue.toARGB32());
      expect(map['created_at'], now.toIso8601String());
    });

    test('toMap omits id when null', () {
      final freshCard = LoyaltyCard(
        name: 'Test',
        barcodeData: '123',
        barcodeFormat: BarcodeFormat.qr,
        color: Colors.red,
        createdAt: now,
      );
      expect(freshCard.toMap().containsKey('id'), isFalse);
    });

    test('fromMap round-trips correctly', () {
      final map = card.toMap();
      final restored = LoyaltyCard.fromMap(map);
      expect(restored, card);
    });

    test('copyWith creates modified copy', () {
      final renamed = card.copyWith(name: 'Sainsburys Nectar');
      expect(renamed.name, 'Sainsburys Nectar');
      expect(renamed.id, card.id);
      expect(renamed.barcodeData, card.barcodeData);
    });

    test('equality works', () {
      final same = LoyaltyCard(
        id: 1,
        name: 'Tesco Clubcard',
        barcodeData: '5012345678900',
        barcodeFormat: BarcodeFormat.ean13,
        color: Colors.blue,
        createdAt: now,
      );
      expect(card, same);
      expect(card.hashCode, same.hashCode);
    });

    test('inequality for different fields', () {
      expect(card, isNot(card.copyWith(name: 'Other')));
    });

    test('toString includes key info', () {
      expect(card.toString(), contains('Tesco Clubcard'));
      expect(card.toString(), contains('EAN-13'));
    });
  });

  group('BarcodeFormat', () {
    test('all formats have display names', () {
      for (final format in BarcodeFormat.values) {
        expect(format.displayName, isNotEmpty);
      }
    });

    test('display names are human-readable', () {
      expect(BarcodeFormat.ean13.displayName, 'EAN-13');
      expect(BarcodeFormat.qr.displayName, 'QR Code');
      expect(BarcodeFormat.code128.displayName, 'Code 128');
    });
  });
}
