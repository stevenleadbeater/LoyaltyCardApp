# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the card detail page."""

import unittest

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw

from src.card_detail import CardDetailPage

SAMPLE_CARD = {
    "id": "test-card-1",
    "name": "Tesco Clubcard",
    "color": "#e74c3c",
    "barcode_format": "EAN-13",
    "barcode_value": "4006381333931",
    "created_at": "2026-01-01 00:00:00",
}


class TestCardDetailPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Adw.Application(application_id="test.card.detail")

    def test_create_page(self):
        page = CardDetailPage(card=SAMPLE_CARD)
        self.assertIsNotNone(page)

    def test_page_title(self):
        page = CardDetailPage(card=SAMPLE_CARD)
        self.assertEqual(page.get_title(), "Tesco Clubcard")

    def test_edit_requested_signal(self):
        page = CardDetailPage(card=SAMPLE_CARD)
        results = []
        page.connect(
            "card-edit-requested",
            lambda p, cid, cn, cc: results.append((cid, cn, cc)),
        )
        page.emit("card-edit-requested", "test-card-1", "Tesco Clubcard", "#e74c3c")
        self.assertEqual(
            results, [("test-card-1", "Tesco Clubcard", "#e74c3c")]
        )

    def test_delete_requested_signal(self):
        page = CardDetailPage(card=SAMPLE_CARD)
        results = []
        page.connect(
            "card-delete-requested",
            lambda p, cid, cn: results.append((cid, cn)),
        )
        page.emit("card-delete-requested", "test-card-1", "Tesco Clubcard")
        self.assertEqual(results, [("test-card-1", "Tesco Clubcard")])

    def test_update_card(self):
        page = CardDetailPage(card=SAMPLE_CARD)
        updated = dict(SAMPLE_CARD)
        updated["name"] = "Updated Name"
        page.update_card(updated)
        self.assertEqual(page._card["name"], "Updated Name")


if __name__ == "__main__":
    unittest.main()
