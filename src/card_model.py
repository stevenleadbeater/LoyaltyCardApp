import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


CARD_COLORS = {
    'red': '#e74c3c',
    'blue': '#3498db',
    'green': '#27ae60',
    'purple': '#9b59b6',
    'orange': '#e67e22',
    'teal': '#1abc9c',
    'pink': '#e91e63',
    'indigo': '#3f51b5',
    'amber': '#ff9800',
    'brown': '#795548',
    'slate': '#607d8b',
    'crimson': '#dc143c',
}


@dataclass
class LoyaltyCard:
    name: str
    color: str = '#3498db'
    card_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    barcode_data: str = ''
    barcode_type: str = 'CODE128'
    notes: str = ''

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        known = {'name', 'color', 'card_id', 'barcode_data', 'barcode_type', 'notes'}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class CardStore:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(
                os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')),
                'loyalty-card-app'
            )
        self._data_dir = data_dir
        self._file_path = os.path.join(data_dir, 'cards.json')
        self._cards: list[LoyaltyCard] = []
        self.load()

    @property
    def cards(self):
        return list(self._cards)

    def load(self):
        if not os.path.exists(self._file_path):
            self._cards = []
            return
        with open(self._file_path, 'r') as f:
            data = json.load(f)
        self._cards = [LoyaltyCard.from_dict(c) for c in data]

    def save(self):
        os.makedirs(self._data_dir, exist_ok=True)
        with open(self._file_path, 'w') as f:
            json.dump([c.to_dict() for c in self._cards], f, indent=2)

    def add_card(self, card: LoyaltyCard):
        self._cards.append(card)
        self.save()

    def remove_card(self, card_id: str):
        self._cards = [c for c in self._cards if c.card_id != card_id]
        self.save()

    def update_card(self, card_id: str, **kwargs):
        for card in self._cards:
            if card.card_id == card_id:
                for key, value in kwargs.items():
                    if hasattr(card, key):
                        setattr(card, key, value)
                self.save()
                return card
        return None

    def get_card(self, card_id: str) -> Optional[LoyaltyCard]:
        for card in self._cards:
            if card.card_id == card_id:
                return card
        return None
