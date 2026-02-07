import 'package:sqflite/sqflite.dart';

import '../models/loyalty_card.dart';
import 'database_helper.dart';

class CardRepository {
  final Future<Database> Function() _getDatabase;

  CardRepository({Future<Database> Function()? getDatabase})
      : _getDatabase = getDatabase ?? (() => DatabaseHelper.instance.database);

  Future<int> insert(LoyaltyCard card) async {
    final db = await _getDatabase();
    return db.insert(DatabaseHelper.table, card.toMap());
  }

  Future<LoyaltyCard?> getById(int id) async {
    final db = await _getDatabase();
    final maps = await db.query(
      DatabaseHelper.table,
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (maps.isEmpty) return null;
    return LoyaltyCard.fromMap(maps.first);
  }

  Future<List<LoyaltyCard>> getAll() async {
    final db = await _getDatabase();
    final maps = await db.query(
      DatabaseHelper.table,
      orderBy: 'created_at DESC',
    );
    return maps.map(LoyaltyCard.fromMap).toList();
  }

  Future<int> update(LoyaltyCard card) async {
    assert(card.id != null, 'Cannot update a card without an id');
    final db = await _getDatabase();
    return db.update(
      DatabaseHelper.table,
      card.toMap(),
      where: 'id = ?',
      whereArgs: [card.id],
    );
  }

  Future<int> delete(int id) async {
    final db = await _getDatabase();
    return db.delete(
      DatabaseHelper.table,
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> count() async {
    final db = await _getDatabase();
    final result = await db.rawQuery(
      'SELECT COUNT(*) AS cnt FROM ${DatabaseHelper.table}',
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }
}
