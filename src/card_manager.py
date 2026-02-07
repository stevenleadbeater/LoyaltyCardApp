# SPDX-License-Identifier: GPL-3.0-or-later

"""Card management operations: rename, change color, and delete.

Provides high-level functions for card management that integrate the edit
and delete dialogs with the data store. Designed to be called from the
card list view (via long-press/swipe actions) or the card detail view.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GObject, Gtk

from .delete_card_dialog import DeleteCardDialog
from .edit_card_dialog import EditCardDialog


class CardManager(GObject.Object):
    """Manages card editing and deletion operations.

    Connect to signals to receive notifications when cards are modified or deleted.
    The caller is responsible for persisting changes to the data store.
    """

    __gtype_name__ = "CardManager"

    __gsignals__ = {
        # (card_id, new_name, new_color)
        "card-changed": (GObject.SignalFlags.RUN_LAST, None, (str, str, str)),
        # (card_id,)
        "card-deleted": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def show_edit_dialog(self, parent, card_id, card_name, card_color):
        """Show the edit card dialog for renaming or changing color.

        Args:
            parent: The parent Gtk.Widget to present the dialog from.
            card_id: The unique identifier of the card being edited.
            card_name: The current name of the card.
            card_color: The current color hex string of the card.
        """
        dialog = EditCardDialog(card_name=card_name, card_color=card_color)
        dialog.connect(
            "card-updated",
            self._on_card_updated,
            card_id,
        )
        dialog.present(parent)

    def show_delete_dialog(self, parent, card_id, card_name):
        """Show the delete confirmation dialog.

        Args:
            parent: The parent Gtk.Widget to present the dialog from.
            card_id: The unique identifier of the card to delete.
            card_name: The name of the card (shown in confirmation message).
        """
        dialog = DeleteCardDialog(card_id=card_id, card_name=card_name)
        dialog.connect("card-deleted", self._on_card_deleted)
        dialog.choose(parent, None, None)

    def show_card_actions(self, parent, card_id, card_name, card_color):
        """Show an action sheet with edit and delete options.

        Useful for long-press or swipe context menus on the card list.

        Args:
            parent: The parent Gtk.Widget to present from.
            card_id: The unique identifier of the card.
            card_name: The current name of the card.
            card_color: The current color hex string of the card.
        """
        dialog = Adw.AlertDialog()
        dialog.set_heading(card_name)
        dialog.set_body("Choose an action for this card.")

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("edit", "Edit Card")
        dialog.add_response("delete", "Delete Card")

        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        dialog.connect(
            "response",
            self._on_action_response,
            parent,
            card_id,
            card_name,
            card_color,
        )
        dialog.choose(parent, None, None)

    def _on_action_response(
        self, dialog, response, parent, card_id, card_name, card_color
    ):
        if response == "edit":
            self.show_edit_dialog(parent, card_id, card_name, card_color)
        elif response == "delete":
            self.show_delete_dialog(parent, card_id, card_name)

    def _on_card_updated(self, dialog, new_name, new_color, card_id):
        self.emit("card-changed", card_id, new_name, new_color)

    def _on_card_deleted(self, dialog, card_id):
        self.emit("card-deleted", card_id)
