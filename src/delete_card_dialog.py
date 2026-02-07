# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GObject, Gtk


class DeleteCardDialog(Adw.AlertDialog):
    """Confirmation dialog for deleting a loyalty card."""

    __gtype_name__ = "DeleteCardDialog"

    __gsignals__ = {
        "card-deleted": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, card_id, card_name="", **kwargs):
        super().__init__(**kwargs)

        self._card_id = card_id

        self.set_heading("Delete Card?")
        self.set_body(
            f'The card "{card_name}" will be permanently deleted. '
            "This action cannot be undone."
        )

        self.add_response("cancel", "Cancel")
        self.add_response("delete", "Delete")

        self.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        self.set_default_response("cancel")
        self.set_close_response("cancel")

        self.connect("response", self._on_response)

    def _on_response(self, dialog, response):
        if response == "delete":
            self.emit("card-deleted", self._card_id)
