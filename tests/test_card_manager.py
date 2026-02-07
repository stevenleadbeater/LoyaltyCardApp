# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for card management: edit dialog, delete dialog, and card manager."""

import unittest

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from src.card_manager import CardManager
from src.delete_card_dialog import DeleteCardDialog
from src.edit_card_dialog import CARD_COLORS, EditCardDialog


class TestEditCardDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Adw.Application(application_id="test.edit.card")

    def test_create_with_defaults(self):
        dialog = EditCardDialog()
        self.assertEqual(dialog.get_title(), "Edit Card")

    def test_create_with_card_data(self):
        dialog = EditCardDialog(card_name="Tesco", card_color="#e74c3c")
        self.assertEqual(dialog._name_row.get_text(), "Tesco")
        self.assertEqual(dialog._selected_color, "#e74c3c")

    def test_save_button_disabled_when_name_empty(self):
        dialog = EditCardDialog(card_name="")
        self.assertFalse(dialog._save_button.get_sensitive())

    def test_save_button_enabled_when_name_set(self):
        dialog = EditCardDialog(card_name="Tesco")
        self.assertTrue(dialog._save_button.get_sensitive())

    def test_color_selection_updates(self):
        dialog = EditCardDialog(card_name="Test", card_color="#3498db")
        dialog._on_color_selected(None, "#e74c3c")
        self.assertEqual(dialog._selected_color, "#e74c3c")

    def test_preview_label_updates_with_name(self):
        dialog = EditCardDialog(card_name="Original")
        self.assertEqual(dialog._preview_label.get_label(), "Original")
        dialog._name_row.set_text("Updated")
        self.assertEqual(dialog._preview_label.get_label(), "Updated")

    def test_preview_shows_placeholder_when_empty(self):
        dialog = EditCardDialog(card_name="")
        self.assertEqual(dialog._preview_label.get_label(), "Card Name")

    def test_card_updated_signal(self):
        dialog = EditCardDialog(card_name="Test", card_color="#3498db")
        results = []
        dialog.connect("card-updated", lambda d, n, c: results.append((n, c)))
        dialog.emit("card-updated", "New Name", "#e74c3c")
        self.assertEqual(results, [("New Name", "#e74c3c")])


class TestDeleteCardDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Adw.Application(application_id="test.delete.card")

    def test_create_dialog(self):
        dialog = DeleteCardDialog(card_id="card-1", card_name="Tesco")
        self.assertEqual(dialog.get_heading(), "Delete Card?")
        self.assertIn("Tesco", dialog.get_body())

    def test_dialog_has_cancel_and_delete_responses(self):
        dialog = DeleteCardDialog(card_id="card-1", card_name="Test")
        # Verify the dialog was constructed without errors
        self.assertIsNotNone(dialog)

    def test_card_deleted_signal(self):
        dialog = DeleteCardDialog(card_id="card-1", card_name="Test")
        results = []
        dialog.connect("card-deleted", lambda d, cid: results.append(cid))
        dialog.emit("card-deleted", "card-1")
        self.assertEqual(results, ["card-1"])

    def test_cancel_does_not_emit_deleted(self):
        dialog = DeleteCardDialog(card_id="card-1", card_name="Test")
        results = []
        dialog.connect("card-deleted", lambda d, cid: results.append(cid))
        dialog._on_response(dialog, "cancel")
        self.assertEqual(results, [])

    def test_delete_response_emits_signal(self):
        dialog = DeleteCardDialog(card_id="card-1", card_name="Test")
        results = []
        dialog.connect("card-deleted", lambda d, cid: results.append(cid))
        dialog._on_response(dialog, "delete")
        self.assertEqual(results, ["card-1"])


class TestCardManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Adw.Application(application_id="test.card.manager")

    def test_create_manager(self):
        manager = CardManager()
        self.assertIsNotNone(manager)

    def test_card_changed_signal(self):
        manager = CardManager()
        results = []
        manager.connect(
            "card-changed", lambda m, cid, n, c: results.append((cid, n, c))
        )
        manager.emit("card-changed", "card-1", "New Name", "#e74c3c")
        self.assertEqual(results, [("card-1", "New Name", "#e74c3c")])

    def test_card_deleted_signal(self):
        manager = CardManager()
        results = []
        manager.connect("card-deleted", lambda m, cid: results.append(cid))
        manager.emit("card-deleted", "card-1")
        self.assertEqual(results, ["card-1"])


class TestCardColors(unittest.TestCase):
    def test_colors_have_hex_and_name(self):
        for hex_color, name in CARD_COLORS:
            self.assertTrue(hex_color.startswith("#"), f"{name} missing # prefix")
            self.assertEqual(len(hex_color), 7, f"{name} hex should be 7 chars")
            self.assertTrue(len(name) > 0, "Color name should not be empty")

    def test_at_least_5_colors(self):
        self.assertGreaterEqual(len(CARD_COLORS), 5)

    def test_no_duplicate_colors(self):
        hex_values = [c[0] for c in CARD_COLORS]
        self.assertEqual(len(hex_values), len(set(hex_values)))


if __name__ == "__main__":
    unittest.main()
