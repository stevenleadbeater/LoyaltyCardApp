# SPDX-License-Identifier: GPL-3.0-or-later

"""Card detail page with barcode display."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, GObject, Gtk


class CardDetailPage(Adw.NavigationPage):
    """Detail view for a single loyalty card with barcode display."""

    __gtype_name__ = "CardDetailPage"

    __gsignals__ = {
        "card-edit-requested": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str, str, str),  # (card_id, card_name, card_color)
        ),
        "card-delete-requested": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str, str),  # (card_id, card_name)
        ),
    }

    def __init__(self, card, **kwargs):
        super().__init__(title=card["name"], **kwargs)
        self._card = card
        self._css_provider = Gtk.CssProvider()
        self._build_ui()

    def _build_ui(self):
        card = self._card

        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()

        edit_btn = Gtk.Button(
            icon_name="document-edit-symbolic",
            tooltip_text="Edit Card",
        )
        edit_btn.connect("clicked", self._on_edit_clicked)
        header.pack_end(edit_btn)

        delete_btn = Gtk.Button(
            icon_name="user-trash-symbolic",
            tooltip_text="Delete Card",
        )
        delete_btn.add_css_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete_clicked)
        header.pack_end(delete_btn)

        toolbar_view.add_top_bar(header)

        clamp = Adw.Clamp(
            maximum_size=500,
            margin_top=24,
            margin_bottom=24,
            margin_start=12,
            margin_end=12,
        )
        toolbar_view.set_content(clamp)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=24,
            valign=Gtk.Align.START,
        )
        clamp.set_child(box)

        # Colored card header
        card_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            halign=Gtk.Align.FILL,
        )
        card_box.set_size_request(-1, 120)
        card_box.set_valign(Gtk.Align.CENTER)
        card_box.add_css_class("card-detail-box")

        name_label = Gtk.Label(label=card["name"])
        name_label.add_css_class("title-1")
        name_label.add_css_class("card-detail-label")
        card_box.append(name_label)

        format_label = Gtk.Label(label=card["barcode_format"])
        format_label.add_css_class("caption")
        format_label.add_css_class("card-detail-label")
        card_box.append(format_label)

        box.append(card_box)

        # Barcode value display
        barcode_frame = Gtk.Frame()
        barcode_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_top=24,
            margin_bottom=24,
            margin_start=16,
            margin_end=16,
            halign=Gtk.Align.CENTER,
        )

        barcode_label = Gtk.Label(
            label=card["barcode_value"],
            selectable=True,
            wrap=True,
        )
        barcode_label.add_css_class("monospace")
        barcode_label.add_css_class("title-2")
        barcode_box.append(barcode_label)

        hint = Gtk.Label(
            label="Long press to copy barcode number",
            css_classes=["dim-label", "caption"],
        )
        barcode_box.append(hint)

        barcode_frame.set_child(barcode_box)
        box.append(barcode_frame)

        # Apply card color CSS
        css = f"""
            .card-detail-box {{
                background-color: {card["color"]};
                border-radius: 12px;
                padding: 24px;
            }}
            .card-detail-label {{
                color: white;
            }}
        """
        self._css_provider.load_from_string(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                self._css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _on_edit_clicked(self, _btn):
        card = self._card
        self.emit("card-edit-requested", card["id"], card["name"], card["color"])

    def _on_delete_clicked(self, _btn):
        card = self._card
        self.emit("card-delete-requested", card["id"], card["name"])

    def update_card(self, card):
        self._card = card
