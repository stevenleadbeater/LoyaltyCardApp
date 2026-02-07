# camera_scanner.py
#
# Copyright 2026
# SPDX-License-Identifier: GPL-3.0-or-later

"""Camera barcode scanner page.

Uses GStreamer with the zbar element for real-time barcode detection
from the device camera. Displays a live viewfinder and emits a signal
when a barcode is successfully decoded.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gst", "1.0")

from gi.repository import Adw, GLib, GObject, Gst, Gtk

Gst.init(None)

# Map ZBar type strings to display format names.
ZBAR_FORMAT_MAP = {
    "EAN-13": "EAN-13",
    "EAN-8": "EAN-8",
    "UPC-A": "UPC-A",
    "CODE-128": "Code 128",
    "CODE-39": "Code 39",
    "QR-Code": "QR Code",
    "SQR-Code": "QR Code",
    "DataMatrix": "DataMatrix",
}

# Formats we accept (from the issue requirements).
SUPPORTED_FORMATS = frozenset(ZBAR_FORMAT_MAP.values())

PIPELINE_DESC = (
    "v4l2src name=src ! "
    "videoconvert ! "
    "video/x-raw,format=RGB,width=640,height=480,framerate=30/1 ! "
    "zbar name=zbar ! "
    "videoconvert ! "
    "gtk4paintablesink name=sink"
)


class CameraScannerPage(Adw.NavigationPage):
    """Page that opens the camera viewfinder and scans barcodes in real-time."""

    __gtype_name__ = "CameraScannerPage"

    __gsignals__ = {
        "barcode-scanned": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str, str),  # (format_name, barcode_value)
        ),
    }

    def __init__(self, **kwargs):
        super().__init__(title="Scan Barcode", **kwargs)

        self._pipeline = None
        self._bus_watch_id = None
        self._scanned = False

        self._build_ui()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Stack to switch between viewfinder and status messages.
        self._stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        toolbar_view.set_content(self._stack)

        # Viewfinder: Gtk.Picture driven by the GStreamer paintable sink.
        viewfinder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._picture = Gtk.Picture(
            content_fit=Gtk.ContentFit.CONTAIN,
            hexpand=True,
            vexpand=True,
        )
        viewfinder_box.append(self._picture)

        self._hint = Gtk.Label(
            label="Point camera at a barcode",
            css_classes=["dim-label"],
            margin_bottom=12,
        )
        viewfinder_box.append(self._hint)
        self._stack.add_named(viewfinder_box, "viewfinder")

        # Status page shown when camera is unavailable.
        self._status_page = Adw.StatusPage(
            icon_name="camera-disabled-symbolic",
            title="Camera Unavailable",
            description="Could not access the device camera. "
            "Check permissions and try again.",
        )
        retry_btn = Gtk.Button(
            label="Retry",
            css_classes=["suggested-action", "pill"],
            halign=Gtk.Align.CENTER,
        )
        retry_btn.connect("clicked", lambda _: self.start())
        self._status_page.set_child(retry_btn)
        self._stack.add_named(self._status_page, "error")

        # Success overlay (brief flash when barcode detected).
        success_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.CENTER,
        )
        self._success_icon = Gtk.Image(
            icon_name="emblem-ok-symbolic",
            pixel_size=64,
            css_classes=["success"],
        )
        success_box.append(self._success_icon)
        self._success_label = Gtk.Label(css_classes=["title-2"])
        success_box.append(self._success_label)
        self._stack.add_named(success_box, "success")

        self._stack.set_visible_child_name("viewfinder")

    def start(self):
        """Start the camera pipeline and begin scanning."""
        self.stop()
        self._scanned = False

        try:
            self._pipeline = Gst.parse_launch(PIPELINE_DESC)
        except GLib.Error:
            self._stack.set_visible_child_name("error")
            return

        sink = self._pipeline.get_by_name("sink")
        if sink is None:
            self._stack.set_visible_child_name("error")
            return

        paintable = sink.get_property("paintable")
        self._picture.set_paintable(paintable)

        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        self._bus_watch_id = bus.connect("message", self._on_bus_message)

        ret = self._pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
            self._stack.set_visible_child_name("error")
            return

        self._stack.set_visible_child_name("viewfinder")

    def stop(self):
        """Stop the camera pipeline and release resources."""
        if self._pipeline is not None:
            bus = self._pipeline.get_bus()
            if self._bus_watch_id is not None:
                bus.disconnect(self._bus_watch_id)
                self._bus_watch_id = None
            bus.remove_signal_watch()
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None

    def _on_bus_message(self, _bus, message):
        if message.type == Gst.MessageType.ELEMENT:
            struct = message.get_structure()
            if struct and struct.get_name() == "barcode":
                self._handle_barcode(struct)
        elif message.type == Gst.MessageType.ERROR:
            self.stop()
            self._stack.set_visible_child_name("error")

    def _handle_barcode(self, struct):
        if self._scanned:
            return

        barcode_type = struct.get_string("type")
        symbol = struct.get_string("symbol")

        if not barcode_type or not symbol:
            return

        format_name = ZBAR_FORMAT_MAP.get(barcode_type)
        if format_name is None:
            return

        self._scanned = True
        self.stop()

        self._success_label.set_label(f"{format_name}: {symbol}")
        self._stack.set_visible_child_name("success")

        self.emit("barcode-scanned", format_name, symbol)

    def do_unroot(self):
        """Clean up when page is removed from the widget tree."""
        self.stop()
        Adw.NavigationPage.do_unroot(self)
