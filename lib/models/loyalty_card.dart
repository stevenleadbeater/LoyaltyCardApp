import 'package:flutter/material.dart';

import 'barcode_format.dart';

class LoyaltyCard {
  final int? id;
  final String name;
  final String barcodeData;
  final BarcodeFormat barcodeFormat;
  final Color color;
  final DateTime createdAt;

  const LoyaltyCard({
    this.id,
    required this.name,
    required this.barcodeData,
    required this.barcodeFormat,
    required this.color,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'name': name,
      'barcode_data': barcodeData,
      'barcode_format': barcodeFormat.name,
      'color': color.toARGB32(),
      'created_at': createdAt.toIso8601String(),
    };
  }

  factory LoyaltyCard.fromMap(Map<String, dynamic> map) {
    return LoyaltyCard(
      id: map['id'] as int,
      name: map['name'] as String,
      barcodeData: map['barcode_data'] as String,
      barcodeFormat: BarcodeFormat.values.byName(map['barcode_format'] as String),
      color: Color(map['color'] as int),
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }

  LoyaltyCard copyWith({
    int? id,
    String? name,
    String? barcodeData,
    BarcodeFormat? barcodeFormat,
    Color? color,
    DateTime? createdAt,
  }) {
    return LoyaltyCard(
      id: id ?? this.id,
      name: name ?? this.name,
      barcodeData: barcodeData ?? this.barcodeData,
      barcodeFormat: barcodeFormat ?? this.barcodeFormat,
      color: color ?? this.color,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is LoyaltyCard &&
        other.id == id &&
        other.name == name &&
        other.barcodeData == barcodeData &&
        other.barcodeFormat == barcodeFormat &&
        other.color.toARGB32() == color.toARGB32() &&
        other.createdAt == createdAt;
  }

  @override
  int get hashCode {
    return Object.hash(
        id, name, barcodeData, barcodeFormat, color.toARGB32(), createdAt);
  }

  @override
  String toString() {
    return 'LoyaltyCard(id: $id, name: $name, format: ${barcodeFormat.displayName})';
  }
}
