"""Manual barcode entry page for the add-card flow.

Provides a GTK4/libadwaita page where users can:
- Select a barcode format from a dropdown
- Type in the barcode value
- See real-time validation feedback
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GObject, Gtk

from loyalty_card_app.barcode_formats import (
    FORMAT_1D,
    FORMAT_2D,
    BarcodeFormat,
    validate_barcode,
)


class BarcodeEntryPage(Adw.NavigationPage):
    """Page for manually entering a barcode number and selecting its format."""

    __gtype_name__ = "BarcodeEntryPage"

    __gsignals__ = {
        "barcode-submitted": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str, str),  # (format_value, barcode_value)
        ),
    }

    def __init__(self, **kwargs):
        super().__init__(title="Enter Barcode", **kwargs)

        self._selected_format: BarcodeFormat = BarcodeFormat.EAN_13
        self._build_ui()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        # Header bar
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Main content in a clamp for adaptive width
        clamp = Adw.Clamp(maximum_size=500, margin_top=24, margin_bottom=24,
                          margin_start=12, margin_end=12)
        toolbar_view.set_content(clamp)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(box)

        # Format selector group
        format_group = Adw.PreferencesGroup(title="Barcode Format")
        box.append(format_group)

        self._format_row = Adw.ComboRow(title="Format")
        format_list = Gtk.StringList()

        self._format_map: list[BarcodeFormat] = []
        for fmt in FORMAT_1D + FORMAT_2D:
            format_list.append(fmt.value)
            self._format_map.append(fmt)

        self._format_row.set_model(format_list)
        self._format_row.connect("notify::selected", self._on_format_changed)
        format_group.add(self._format_row)

        # Barcode value entry group
        entry_group = Adw.PreferencesGroup(title="Barcode Value")
        box.append(entry_group)

        self._entry_row = Adw.EntryRow(title="Barcode number")
        self._entry_row.connect("changed", self._on_entry_changed)
        entry_group.add(self._entry_row)

        # Validation feedback
        self._error_label = Gtk.Label(
            xalign=0,
            wrap=True,
            css_classes=["error"],
            visible=False,
            margin_start=12,
        )
        box.append(self._error_label)

        # Format hint
        self._hint_label = Gtk.Label(
            xalign=0,
            wrap=True,
            css_classes=["dim-label", "caption"],
            margin_start=12,
        )
        self._update_hint()
        box.append(self._hint_label)

        # Submit button
        self._submit_btn = Gtk.Button(
            label="Add Card",
            css_classes=["suggested-action", "pill"],
            halign=Gtk.Align.CENTER,
            sensitive=False,
        )
        self._submit_btn.connect("clicked", self._on_submit)
        box.append(self._submit_btn)

    def _on_format_changed(self, row, _pspec):
        idx = row.get_selected()
        if 0 <= idx < len(self._format_map):
            self._selected_format = self._format_map[idx]
        self._update_hint()
        self._validate()

    def _on_entry_changed(self, _row):
        self._validate()

    def _validate(self) -> bool:
        value = self._entry_row.get_text().strip()
        if not value:
            self._error_label.set_visible(False)
            self._submit_btn.set_sensitive(False)
            self._entry_row.remove_css_class("error")
            return False

        error = validate_barcode(self._selected_format, value)
        if error:
            self._error_label.set_label(error)
            self._error_label.set_visible(True)
            self._submit_btn.set_sensitive(False)
            self._entry_row.add_css_class("error")
            return False

        self._error_label.set_visible(False)
        self._submit_btn.set_sensitive(True)
        self._entry_row.remove_css_class("error")
        return True

    def _update_hint(self):
        hints = {
            BarcodeFormat.EAN_13: "13 digits with check digit (e.g. 4006381333931)",
            BarcodeFormat.EAN_8: "8 digits with check digit (e.g. 96385074)",
            BarcodeFormat.UPC_A: "12 digits with check digit (e.g. 042100005264)",
            BarcodeFormat.CODE_128: "ASCII text, up to 80 characters",
            BarcodeFormat.CODE_39: "Letters, digits, and - . $ / + % SPACE",
            BarcodeFormat.QR_CODE: "Any text, up to ~4296 bytes",
            BarcodeFormat.DATA_MATRIX: "Any text, up to ~2335 bytes",
            BarcodeFormat.PDF_417: "Any text, up to ~1850 bytes",
            BarcodeFormat.CODABAR: "Digits and - $ : / . + with A-D start/stop",
            BarcodeFormat.ITF: "Even number of digits (e.g. 1234567890)",
        }
        self._hint_label.set_label(hints.get(self._selected_format, ""))

    def _on_submit(self, _btn):
        value = self._entry_row.get_text().strip()
        if self._validate():
            self.emit(
                "barcode-submitted",
                self._selected_format.value,
                value,
            )

    def get_format(self) -> BarcodeFormat:
        """Return the currently selected barcode format."""
        return self._selected_format

    def get_value(self) -> str:
        """Return the current barcode value text."""
        return self._entry_row.get_text().strip()
