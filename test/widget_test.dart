import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:loyalty_card_app/main.dart';

void main() {
  testWidgets('App shows home page with import button', (WidgetTester tester) async {
    await tester.pumpWidget(const LoyaltyCardApp());

    expect(find.text('Loyalty Card App'), findsOneWidget);
    expect(find.text('No cards yet'), findsOneWidget);
    expect(find.text('Import Barcode'), findsOneWidget);
    expect(find.byIcon(Icons.add_photo_alternate), findsOneWidget);
  });

  testWidgets('Import button navigates to import screen', (WidgetTester tester) async {
    await tester.pumpWidget(const LoyaltyCardApp());

    await tester.tap(find.text('Import Barcode'));
    await tester.pumpAndSettle();

    expect(find.text('Import Barcode'), findsWidgets);
    expect(find.text('Gallery'), findsOneWidget);
    expect(find.text('Camera'), findsOneWidget);
    expect(find.text('Pick an image to scan for barcodes'), findsOneWidget);
  });
}
