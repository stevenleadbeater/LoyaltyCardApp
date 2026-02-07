#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from card_model import LoyaltyCard, CardStore, CARD_COLORS


class TestLoyaltyCard(unittest.TestCase):
    def test_create_card_defaults(self):
        card = LoyaltyCard(name='Test Store')
        self.assertEqual(card.name, 'Test Store')
        self.assertEqual(card.color, '#3498db')
        self.assertTrue(len(card.card_id) > 0)
        self.assertEqual(card.barcode_data, '')
        self.assertEqual(card.barcode_type, 'CODE128')
        self.assertEqual(card.notes, '')

    def test_create_card_custom(self):
        card = LoyaltyCard(
            name='Coffee Shop',
            color='#e74c3c',
            barcode_data='123456789',
            notes='Buy 10 get 1 free',
        )
        self.assertEqual(card.name, 'Coffee Shop')
        self.assertEqual(card.color, '#e74c3c')
        self.assertEqual(card.barcode_data, '123456789')
        self.assertEqual(card.notes, 'Buy 10 get 1 free')

    def test_to_dict(self):
        card = LoyaltyCard(name='Test', card_id='abc-123')
        d = card.to_dict()
        self.assertEqual(d['name'], 'Test')
        self.assertEqual(d['card_id'], 'abc-123')
        self.assertIn('color', d)

    def test_from_dict(self):
        data = {
            'name': 'Grocery',
            'color': '#27ae60',
            'card_id': 'xyz-789',
            'barcode_data': '555',
            'barcode_type': 'QR',
            'notes': 'member discount',
        }
        card = LoyaltyCard.from_dict(data)
        self.assertEqual(card.name, 'Grocery')
        self.assertEqual(card.color, '#27ae60')
        self.assertEqual(card.card_id, 'xyz-789')

    def test_from_dict_ignores_unknown_fields(self):
        data = {'name': 'Test', 'unknown_field': 'value'}
        card = LoyaltyCard.from_dict(data)
        self.assertEqual(card.name, 'Test')
        self.assertFalse(hasattr(card, 'unknown_field'))

    def test_roundtrip(self):
        card = LoyaltyCard(name='Roundtrip', color='#9b59b6', barcode_data='999')
        d = card.to_dict()
        card2 = LoyaltyCard.from_dict(d)
        self.assertEqual(card.name, card2.name)
        self.assertEqual(card.color, card2.color)
        self.assertEqual(card.card_id, card2.card_id)
        self.assertEqual(card.barcode_data, card2.barcode_data)


class TestCardStore(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.store = CardStore(data_dir=self._tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_empty_store(self):
        self.assertEqual(len(self.store.cards), 0)

    def test_add_card(self):
        card = LoyaltyCard(name='Test Store')
        self.store.add_card(card)
        self.assertEqual(len(self.store.cards), 1)
        self.assertEqual(self.store.cards[0].name, 'Test Store')

    def test_persistence(self):
        card = LoyaltyCard(name='Persist', color='#e74c3c')
        self.store.add_card(card)

        store2 = CardStore(data_dir=self._tmpdir)
        self.assertEqual(len(store2.cards), 1)
        self.assertEqual(store2.cards[0].name, 'Persist')
        self.assertEqual(store2.cards[0].color, '#e74c3c')

    def test_remove_card(self):
        card = LoyaltyCard(name='Remove Me')
        self.store.add_card(card)
        self.store.remove_card(card.card_id)
        self.assertEqual(len(self.store.cards), 0)

    def test_update_card(self):
        card = LoyaltyCard(name='Old Name', color='#3498db')
        self.store.add_card(card)
        updated = self.store.update_card(card.card_id, name='New Name', color='#e74c3c')
        self.assertEqual(updated.name, 'New Name')
        self.assertEqual(updated.color, '#e74c3c')

    def test_update_nonexistent_card(self):
        result = self.store.update_card('nonexistent', name='X')
        self.assertIsNone(result)

    def test_get_card(self):
        card = LoyaltyCard(name='Find Me')
        self.store.add_card(card)
        found = self.store.get_card(card.card_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, 'Find Me')

    def test_get_card_nonexistent(self):
        self.assertIsNone(self.store.get_card('nope'))

    def test_multiple_cards(self):
        for i in range(5):
            self.store.add_card(LoyaltyCard(name=f'Card {i}'))
        self.assertEqual(len(self.store.cards), 5)

    def test_cards_returns_copy(self):
        card = LoyaltyCard(name='Copy Test')
        self.store.add_card(card)
        cards = self.store.cards
        cards.clear()
        self.assertEqual(len(self.store.cards), 1)

    def test_json_file_format(self):
        self.store.add_card(LoyaltyCard(name='JSON Test', card_id='test-id'))
        with open(os.path.join(self._tmpdir, 'cards.json')) as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'JSON Test')
        self.assertEqual(data[0]['card_id'], 'test-id')


class TestCardColors(unittest.TestCase):
    def test_color_palette_exists(self):
        self.assertGreater(len(CARD_COLORS), 0)

    def test_colors_are_hex(self):
        for name, color in CARD_COLORS.items():
            self.assertTrue(
                color.startswith('#') and len(color) == 7,
                f'{name}: {color} is not a valid hex color'
            )


if __name__ == '__main__':
    unittest.main()
