"""Camera barcode scanner page for the add-card flow.

Uses GStreamer with the zbar element for real-time barcode detection
from the device camera. Displays a viewfinder and emits a signal
when a barcode is successfully decoded.
"""

import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import Adw, Gdk, GLib, GObject, Gst, Gtk

from loyalty_card_app.barcode_formats import BarcodeFormat

# Map zbar type names to our BarcodeFormat enum
ZBAR_FORMAT_MAP: dict[str, BarcodeFormat] = {
    "EAN-13": BarcodeFormat.EAN_13,
    "EAN-8": BarcodeFormat.EAN_8,
    "UPC-A": BarcodeFormat.UPC_A,
    "CODE-128": BarcodeFormat.CODE_128,
    "Code-128": BarcodeFormat.CODE_128,
    "CODE-39": BarcodeFormat.CODE_39,
    "Code-39": BarcodeFormat.CODE_39,
    "QR-Code": BarcodeFormat.QR_CODE,
    "CODABAR": BarcodeFormat.CODABAR,
    "Codabar": BarcodeFormat.CODABAR,
    "I2/5": BarcodeFormat.ITF,
}


def map_zbar_format(zbar_type: str) -> BarcodeFormat | None:
    """Map a zbar barcode type string to a BarcodeFormat enum value.

    Returns None if the format is not supported.
    """
    return ZBAR_FORMAT_MAP.get(zbar_type)


class BarcodeScannerPage(Adw.NavigationPage):
    """Page that opens the camera and scans for barcodes in real-time."""

    __gtype_name__ = "BarcodeScannerPage"

    __gsignals__ = {
        "barcode-scanned": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str, str),  # (format_value, barcode_data)
        ),
    }

    def __init__(self, **kwargs):
        super().__init__(title="Scan Barcode", **kwargs)

        self._pipeline = None
        self._bus_watch_id = None
        self._frame_timeout_id = None
        self._detected = False

        self._build_ui()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Main content
        overlay = Gtk.Overlay()
        toolbar_view.set_content(overlay)

        # Camera viewfinder
        self._picture = Gtk.Picture(
            content_fit=Gtk.ContentFit.COVER,
            hexpand=True,
            vexpand=True,
        )
        overlay.set_child(self._picture)

        # Scanning overlay with instructions
        overlay_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            valign=Gtk.Align.END,
            margin_bottom=24,
            margin_start=12,
            margin_end=12,
            spacing=12,
        )
        overlay.add_overlay(overlay_box)

        self._status_label = Gtk.Label(
            label="Point camera at a barcode",
            css_classes=["title-3"],
            halign=Gtk.Align.CENTER,
        )
        # Semi-transparent background for readability
        self._status_label.add_css_class("osd")
        overlay_box.append(self._status_label)

        self.connect("map", self._on_mapped)
        self.connect("unmap", self._on_unmapped)

    def _on_mapped(self, _widget):
        """Start camera when page becomes visible."""
        self._detected = False
        self._start_pipeline()

    def _on_unmapped(self, _widget):
        """Stop camera when page is hidden."""
        self._stop_pipeline()

    def _start_pipeline(self):
        """Create and start the GStreamer pipeline for camera + barcode detection."""
        if self._pipeline is not None:
            return

        Gst.init(None)

        self._pipeline = Gst.Pipeline.new("barcode-scanner")

        # Camera source
        src = Gst.ElementFactory.make("autovideosrc", "camera")
        convert1 = Gst.ElementFactory.make("videoconvert", "convert1")
        tee = Gst.ElementFactory.make("tee", "tee")

        # Barcode detection branch
        queue_zbar = Gst.ElementFactory.make("queue", "queue-zbar")
        zbar = Gst.ElementFactory.make("zbar", "zbar")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")

        # Display branch - appsink for getting frames
        queue_display = Gst.ElementFactory.make("queue", "queue-display")
        convert2 = Gst.ElementFactory.make("videoconvert", "convert2")
        capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
        capsfilter.set_property(
            "caps", Gst.Caps.from_string("video/x-raw,format=RGBA")
        )
        self._appsink = Gst.ElementFactory.make("appsink", "appsink")
        self._appsink.set_property("emit-signals", True)
        self._appsink.set_property("max-buffers", 1)
        self._appsink.set_property("drop", True)

        for el in [
            src, convert1, tee,
            queue_zbar, zbar, fakesink,
            queue_display, convert2, capsfilter, self._appsink,
        ]:
            if el is None:
                self._status_label.set_label("Camera not available")
                return
            self._pipeline.add(el)

        # Link camera -> convert -> tee
        src.link(convert1)
        convert1.link(tee)

        # Link tee -> zbar branch
        tee.link(queue_zbar)
        queue_zbar.link(zbar)
        zbar.link(fakesink)

        # Link tee -> display branch
        tee.link(queue_display)
        queue_display.link(convert2)
        convert2.link(capsfilter)
        capsfilter.link(self._appsink)

        # Listen for barcode messages on the bus
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        self._bus_watch_id = bus.connect("message::element", self._on_bus_message)

        # Also handle error/eos
        bus.connect("message::error", self._on_bus_error)

        # Start playing
        ret = self._pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self._status_label.set_label("Failed to start camera")
            self._stop_pipeline()
            return

        # Start pulling frames for display
        self._frame_timeout_id = GLib.timeout_add(33, self._pull_frame)

    def _pull_frame(self) -> bool:
        """Pull a frame from appsink and display it."""
        if self._appsink is None or self._pipeline is None:
            return False

        sample = self._appsink.try_pull_sample(0)
        if sample is None:
            return True

        buf = sample.get_buffer()
        caps = sample.get_caps()
        struct = caps.get_structure(0)

        success_w, width = struct.get_int("width")
        success_h, height = struct.get_int("height")
        if not success_w or not success_h:
            return True

        result, mapinfo = buf.map(Gst.MapFlags.READ)
        if not result:
            return True

        try:
            # Create GdkTexture from the raw RGBA data
            data = GLib.Bytes.new(mapinfo.data)
            texture = Gdk.MemoryTexture.new(
                width, height,
                Gdk.MemoryFormat.R8G8B8A8,
                data,
                width * 4,
            )
            self._picture.set_paintable(texture)
        finally:
            buf.unmap(mapinfo)

        return True

    def _on_bus_message(self, _bus, message):
        """Handle barcode detection messages from zbar."""
        if self._detected:
            return

        struct = message.get_structure()
        if struct is None or struct.get_name() != "barcode":
            return

        barcode_type = struct.get_string("type")
        barcode_data = struct.get_string("symbol")

        if not barcode_type or not barcode_data:
            return

        fmt = map_zbar_format(barcode_type)
        if fmt is None:
            # Unknown format - still report it with the raw type name
            self._status_label.set_label(f"Unsupported format: {barcode_type}")
            return

        self._detected = True
        self._status_label.set_label(f"Found: {fmt.value}")

        # Emit signal with the format and data
        GLib.idle_add(self._emit_result, fmt.value, barcode_data)

    def _emit_result(self, format_value, barcode_data):
        """Emit the barcode-scanned signal on the main thread."""
        self.emit("barcode-scanned", format_value, barcode_data)
        return False

    def _on_bus_error(self, _bus, message):
        """Handle GStreamer errors."""
        err, debug = message.parse_error()
        self._status_label.set_label("Camera error")
        self._stop_pipeline()

    def _stop_pipeline(self):
        """Stop and clean up the GStreamer pipeline."""
        if self._frame_timeout_id is not None:
            GLib.source_remove(self._frame_timeout_id)
            self._frame_timeout_id = None

        if self._pipeline is not None:
            bus = self._pipeline.get_bus()
            if self._bus_watch_id is not None:
                bus.disconnect(self._bus_watch_id)
                self._bus_watch_id = None
            bus.remove_signal_watch()
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None

        self._appsink = None
