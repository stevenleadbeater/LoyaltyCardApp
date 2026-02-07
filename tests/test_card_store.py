# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the SQLite card data store."""

import os
import tempfile
import unittest

from src.card_store import CardStore


class TestCardStore(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "test_cards.db")
        self.store = CardStore(db_path=self._db_path)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self._db_path):
            os.remove(self._db_path)
        os.rmdir(self._tmpdir)

    def test_add_card_returns_id(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        self.assertIsInstance(card_id, str)
        self.assertTrue(len(card_id) > 0)

    def test_get_card(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        card = self.store.get_card(card_id)
        self.assertEqual(card["name"], "Tesco")
        self.assertEqual(card["color"], "#e74c3c")
        self.assertEqual(card["barcode_format"], "EAN-13")
        self.assertEqual(card["barcode_value"], "4006381333931")

    def test_get_card_not_found(self):
        card = self.store.get_card("nonexistent-id")
        self.assertIsNone(card)

    def test_get_all_cards_empty(self):
        cards = self.store.get_all_cards()
        self.assertEqual(cards, [])

    def test_get_all_cards(self):
        self.store.add_card("Tesco", "#e74c3c", "EAN-13", "4006381333931")
        self.store.add_card("Boots", "#3498db", "QR Code", "BOOTS123")
        cards = self.store.get_all_cards()
        self.assertEqual(len(cards), 2)

    def test_update_card_name(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        self.store.update_card(card_id, name="Tesco Clubcard")
        card = self.store.get_card(card_id)
        self.assertEqual(card["name"], "Tesco Clubcard")
        self.assertEqual(card["color"], "#e74c3c")

    def test_update_card_color(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        self.store.update_card(card_id, color="#3498db")
        card = self.store.get_card(card_id)
        self.assertEqual(card["color"], "#3498db")
        self.assertEqual(card["name"], "Tesco")

    def test_update_card_name_and_color(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        self.store.update_card(card_id, name="Updated", color="#2ecc71")
        card = self.store.get_card(card_id)
        self.assertEqual(card["name"], "Updated")
        self.assertEqual(card["color"], "#2ecc71")

    def test_update_card_no_changes(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        self.store.update_card(card_id)
        card = self.store.get_card(card_id)
        self.assertEqual(card["name"], "Tesco")

    def test_delete_card(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        self.store.delete_card(card_id)
        card = self.store.get_card(card_id)
        self.assertIsNone(card)

    def test_delete_card_not_found(self):
        self.store.delete_card("nonexistent-id")

    def test_card_ids_unique(self):
        id1 = self.store.add_card("A", "#e74c3c", "EAN-13", "4006381333931")
        id2 = self.store.add_card("B", "#3498db", "QR Code", "HELLO")
        self.assertNotEqual(id1, id2)

    def test_card_has_created_at(self):
        card_id = self.store.add_card(
            "Tesco", "#e74c3c", "EAN-13", "4006381333931"
        )
        card = self.store.get_card(card_id)
        self.assertIn("created_at", card)
        self.assertTrue(len(card["created_at"]) > 0)


if __name__ == "__main__":
    unittest.main()
