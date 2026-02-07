# window.py
#
# Copyright 2026
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gtk

from .card_detail import CardDetailPage
from .card_manager import CardManager
from .card_store import CardStore
from .edit_card_dialog import EditCardDialog


@Gtk.Template(
    resource_path="/com/github/loyaltycardapp/LoyaltyCardApp/window.ui"
)
class LoyaltyCardAppWindow(Adw.ApplicationWindow):
    """Main application window with adaptive mobile layout."""

    __gtype_name__ = "LoyaltyCardAppWindow"

    navigation_view = Gtk.Template.Child()
    content_stack = Gtk.Template.Child()
    cards_list = Gtk.Template.Child()
    add_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._store = CardStore()
        self._card_manager = CardManager()
        self._pending_barcode = None  # (format, value) awaiting name/color

        self._card_manager.connect("card-changed", self._on_card_changed)
        self._card_manager.connect("card-deleted", self._on_card_deleted)

        self.add_button.connect("clicked", self._on_add_clicked)
        self.cards_list.connect("row-activated", self._on_row_activated)

        self._css_provider = Gtk.CssProvider()
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                self._css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

        self._refresh_cards()

    def _refresh_cards(self):
        # Remove existing rows
        while True:
            row = self.cards_list.get_row_at_index(0)
            if row is None:
                break
            self.cards_list.remove(row)

        cards = self._store.get_all_cards()

        if not cards:
            self.content_stack.set_visible_child_name("empty")
            return

        self.content_stack.set_visible_child_name("cards")

        css_parts = []
        for card in cards:
            row = Adw.ActionRow(
                title=card["name"],
                subtitle=card["barcode_format"],
                activatable=True,
            )
            row.card_id = card["id"]

            # Color indicator as prefix
            css_class = f"card-color-{card['id'][:8]}"
            color_dot = Gtk.Box()
            color_dot.set_size_request(32, 32)
            color_dot.add_css_class("circular")
            color_dot.add_css_class(css_class)
            row.add_prefix(color_dot)

            # Arrow suffix
            arrow = Gtk.Image(icon_name="go-next-symbolic")
            arrow.add_css_class("dim-label")
            row.add_suffix(arrow)

            self.cards_list.append(row)

            css_parts.append(
                f".{css_class} {{ background-color: {card['color']}; }}"
            )

        self._css_provider.load_from_string("\n".join(css_parts))

    def _on_add_clicked(self, _btn):
        dialog = Adw.AlertDialog()
        dialog.set_heading("Add Loyalty Card")
        dialog.set_body("How would you like to add the barcode?")

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("manual", "Enter Manually")
        dialog.add_response("camera", "Scan with Camera")

        dialog.set_response_appearance(
            "manual", Adw.ResponseAppearance.SUGGESTED
        )
        dialog.set_default_response("manual")
        dialog.set_close_response("cancel")

        dialog.connect("response", self._on_add_method_response)
        dialog.choose(self, None, None)

    def _on_add_method_response(self, _dialog, response):
        if response == "manual":
            self._push_manual_entry()
        elif response == "camera":
            self._push_camera_scanner()

    def _push_manual_entry(self):
        from loyalty_card_app.barcode_entry import BarcodeEntryPage

        page = BarcodeEntryPage()
        page.connect("barcode-submitted", self._on_barcode_received)
        self.navigation_view.push(page)

    def _push_camera_scanner(self):
        from .camera_scanner import CameraScannerPage

        page = CameraScannerPage()
        page.connect("barcode-scanned", self._on_barcode_received)
        self.navigation_view.push(page)
        page.start()

    def _on_barcode_received(self, _page, barcode_format, barcode_value):
        self._pending_barcode = (barcode_format, barcode_value)
        self.navigation_view.pop()
        self._show_new_card_dialog()

    def _show_new_card_dialog(self):
        dialog = EditCardDialog(card_name="", card_color="#3498db")
        dialog.set_title("New Card")
        dialog.connect("card-updated", self._on_new_card_saved)
        dialog.present(self)

    def _on_new_card_saved(self, _dialog, name, color):
        if self._pending_barcode is None:
            return
        barcode_format, barcode_value = self._pending_barcode
        self._pending_barcode = None
        self._store.add_card(name, color, barcode_format, barcode_value)
        self._refresh_cards()

    def _on_row_activated(self, _listbox, row):
        card_id = row.card_id
        card = self._store.get_card(card_id)
        if card is None:
            return

        page = CardDetailPage(card=card)
        page.connect("card-edit-requested", self._on_detail_edit)
        page.connect("card-delete-requested", self._on_detail_delete)
        self.navigation_view.push(page)

    def _on_detail_edit(self, _page, card_id, card_name, card_color):
        self._card_manager.show_edit_dialog(
            self, card_id, card_name, card_color
        )

    def _on_detail_delete(self, _page, card_id, card_name):
        self._card_manager.show_delete_dialog(self, card_id, card_name)

    def _on_card_changed(self, _manager, card_id, new_name, new_color):
        self._store.update_card(card_id, name=new_name, color=new_color)
        self.navigation_view.pop()
        self._refresh_cards()

    def _on_card_deleted(self, _manager, card_id):
        self._store.delete_card(card_id)
        self.navigation_view.pop()
        self._refresh_cards()
