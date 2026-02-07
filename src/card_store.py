# SPDX-License-Identifier: GPL-3.0-or-later

"""SQLite data store for loyalty cards."""

import os
import sqlite3
import uuid

from gi.repository import GLib


def _get_db_path():
    data_dir = GLib.get_user_data_dir()
    app_dir = os.path.join(data_dir, "loyalty-card-app")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "cards.db")


class CardStore:
    """SQLite-backed storage for loyalty card data."""

    def __init__(self, db_path=None):
        self._db_path = db_path or _get_db_path()
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#3498db',
                barcode_format TEXT NOT NULL,
                barcode_value TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.commit()

    def add_card(self, name, color, barcode_format, barcode_value):
        card_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO cards (id, name, color, barcode_format, barcode_value) "
            "VALUES (?, ?, ?, ?, ?)",
            (card_id, name, color, barcode_format, barcode_value),
        )
        self._conn.commit()
        return card_id

    def get_all_cards(self):
        cursor = self._conn.execute(
            "SELECT * FROM cards ORDER BY created_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_card(self, card_id):
        cursor = self._conn.execute(
            "SELECT * FROM cards WHERE id = ?", (card_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_card(self, card_id, name=None, color=None):
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        if not updates:
            return
        params.append(card_id)
        self._conn.execute(
            f"UPDATE cards SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self._conn.commit()

    def delete_card(self, card_id):
        self._conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        self._conn.commit()

    def close(self):
        self._conn.close()
