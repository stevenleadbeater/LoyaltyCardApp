# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GObject, Gtk

# Predefined color palette for card themes
CARD_COLORS = [
    ("#e74c3c", "Red"),
    ("#e67e22", "Orange"),
    ("#f1c40f", "Yellow"),
    ("#2ecc71", "Green"),
    ("#1abc9c", "Teal"),
    ("#3498db", "Blue"),
    ("#9b59b6", "Purple"),
    ("#e91e63", "Pink"),
    ("#795548", "Brown"),
    ("#607d8b", "Grey"),
    ("#000000", "Black"),
]


class EditCardDialog(Adw.Dialog):
    """Dialog for editing a loyalty card's name and color theme."""

    __gtype_name__ = "EditCardDialog"

    __gsignals__ = {
        "card-updated": (GObject.SignalFlags.RUN_LAST, None, (str, str)),
    }

    def __init__(self, card_name="", card_color="#3498db", **kwargs):
        super().__init__(**kwargs)

        self.set_title("Edit Card")
        self.set_content_width(360)
        self.set_content_height(480)

        self._selected_color = card_color

        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self._on_cancel)
        header.pack_start(cancel_button)

        self._save_button = Gtk.Button(label="Save")
        self._save_button.add_css_class("suggested-action")
        self._save_button.connect("clicked", self._on_save)
        header.pack_end(self._save_button)

        toolbar_view.add_top_bar(header)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)

        # Card name entry
        name_group = Adw.PreferencesGroup(title="Card Name")
        self._name_row = Adw.EntryRow(title="Name")
        self._name_row.set_text(card_name)
        self._name_row.connect("changed", self._on_name_changed)
        name_group.add(self._name_row)
        content.append(name_group)

        # Color picker
        color_group = Adw.PreferencesGroup(title="Card Color")
        color_grid = Gtk.FlowBox()
        color_grid.set_max_children_per_line(5)
        color_grid.set_min_children_per_line(5)
        color_grid.set_row_spacing(8)
        color_grid.set_column_spacing(8)
        color_grid.set_homogeneous(True)
        color_grid.set_selection_mode(Gtk.SelectionMode.NONE)

        self._color_buttons = []
        self._color_css_provider = Gtk.CssProvider()
        for i, (hex_color, color_name) in enumerate(CARD_COLORS):
            css_class = f"color-swatch-{i}"
            button = Gtk.Button()
            button.set_size_request(48, 48)
            button.add_css_class("circular")
            button.add_css_class(css_class)
            button.set_tooltip_text(color_name)

            button.connect("clicked", self._on_color_selected, hex_color)
            color_grid.append(button)
            self._color_buttons.append((button, hex_color, css_class))

        color_group.add(color_grid)
        content.append(color_group)

        # Preview
        preview_group = Adw.PreferencesGroup(title="Preview")
        self._preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._preview_box.set_size_request(-1, 80)
        self._preview_box.set_halign(Gtk.Align.FILL)
        self._preview_box.set_valign(Gtk.Align.CENTER)
        self._preview_label = Gtk.Label(label=card_name or "Card Name")
        self._preview_label.add_css_class("title-2")
        self._preview_box.append(self._preview_label)
        preview_group.add(self._preview_box)
        content.append(preview_group)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(content)
        scrolled.set_vexpand(True)
        toolbar_view.set_content(scrolled)

        # Preview CSS classes
        self._preview_box.add_css_class("card-preview-box")
        self._preview_label.add_css_class("card-preview-label")
        self._preview_css_provider = Gtk.CssProvider()

        # Add CSS providers to the display
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                self._color_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
            Gtk.StyleContext.add_provider_for_display(
                display,
                self._preview_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

        self._update_color_selection()
        self._update_preview_color()
        self._validate()

    def _on_name_changed(self, entry):
        text = entry.get_text()
        self._preview_label.set_label(text or "Card Name")
        self._validate()

    def _on_color_selected(self, button, hex_color):
        self._selected_color = hex_color
        self._update_color_selection()
        self._update_preview_color()

    def _update_color_selection(self):
        css_parts = []
        for button, hex_color, css_class in self._color_buttons:
            border = (
                "3px solid @accent_color"
                if hex_color == self._selected_color
                else "3px solid transparent"
            )
            css_parts.append(f"""
                .{css_class} {{
                    background-color: {hex_color};
                    border: {border};
                    min-width: 48px;
                    min-height: 48px;
                }}
                .{css_class}:hover {{
                    background-color: {hex_color};
                    opacity: 0.8;
                }}
            """)
        self._color_css_provider.load_from_string("".join(css_parts))

    def _update_preview_color(self):
        css = f"""
            .card-preview-box {{
                background-color: {self._selected_color};
                border-radius: 12px;
                padding: 16px;
            }}
            .card-preview-label {{
                color: white;
            }}
        """
        self._preview_css_provider.load_from_string(css)

    def _validate(self):
        name = self._name_row.get_text().strip()
        self._save_button.set_sensitive(len(name) > 0)

    def _on_cancel(self, button):
        self.close()

    def _on_save(self, button):
        name = self._name_row.get_text().strip()
        self.emit("card-updated", name, self._selected_color)
        self.close()
