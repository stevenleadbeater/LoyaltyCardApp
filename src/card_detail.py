# SPDX-License-Identifier: GPL-3.0-or-later

"""Card detail page with barcode display."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Adw, Gdk, GdkPixbuf, GLib, GObject, Gtk

from loyalty_card_app.barcode_render import render_barcode


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

        self._toast_overlay = Adw.ToastOverlay()
        toolbar_view.set_content(self._toast_overlay)

        clamp = Adw.Clamp(
            maximum_size=500,
            margin_top=24,
            margin_bottom=24,
            margin_start=12,
            margin_end=12,
        )
        self._toast_overlay.set_child(clamp)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=24,
            valign=Gtk.Align.START,
        )
        clamp.set_child(box)

        # Colored card — looks like a physical loyalty card with barcode inside
        self._card_css_class = f"card-detail-{card['id'][:8]}"
        card_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            halign=Gtk.Align.FILL,
        )
        card_box.add_css_class(self._card_css_class)

        name_label = Gtk.Label(label=card["name"])
        name_label.add_css_class("title-1")
        name_label.add_css_class("card-detail-label")
        card_box.append(name_label)

        format_label = Gtk.Label(label=card["barcode_format"])
        format_label.add_css_class("caption")
        format_label.add_css_class("card-detail-label")
        card_box.append(format_label)

        # Barcode image inside the card
        barcode_rendered = False
        try:
            surface = render_barcode(card["barcode_format"], card["barcode_value"])
            if surface is not None:
                import tempfile, os
                fd, tmp_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                try:
                    surface.write_to_png(tmp_path)
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(tmp_path)
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    barcode_picture = Gtk.Picture(
                        content_fit=Gtk.ContentFit.CONTAIN,
                        hexpand=True,
                    )
                    barcode_picture.set_size_request(-1, 120)
                    barcode_picture.set_paintable(texture)

                    # Long press on barcode to copy number
                    long_press = Gtk.GestureLongPress()
                    long_press.connect(
                        "pressed", self._on_barcode_long_press
                    )
                    barcode_picture.add_controller(long_press)

                    card_box.append(barcode_picture)
                    barcode_rendered = True
                finally:
                    os.unlink(tmp_path)
        except Exception:
            pass

        if not barcode_rendered:
            no_barcode = Gtk.Label(
                label="Visual barcode not available for this format",
                css_classes=["dim-label", "caption", "card-detail-label"],
            )
            card_box.append(no_barcode)

        box.append(card_box)

        hint = Gtk.Label(
            label="Long press barcode to copy number",
            css_classes=["dim-label", "caption"],
        )
        box.append(hint)

        # Apply card color CSS
        css = f"""
            .{self._card_css_class} {{
                background-color: {card["color"]};
                border-radius: 16px;
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

    def _on_barcode_long_press(self, _gesture, _x, _y):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(self._card["barcode_value"])
        self._toast_overlay.add_toast(Adw.Toast(title="Barcode number copied"))

    def _on_edit_clicked(self, _btn):
        card = self._card
        self.emit("card-edit-requested", card["id"], card["name"], card["color"])

    def _on_delete_clicked(self, _btn):
        card = self._card
        self.emit("card-delete-requested", card["id"], card["name"])

    def do_unroot(self):
        """Remove CSS provider when page is removed from widget tree."""
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.remove_provider_for_display(
                display, self._css_provider
            )
        Adw.NavigationPage.do_unroot(self)

    def update_card(self, card):
        self._card = card
