"""Scan a barcode from an image file.

Lets the user pick an image (PNG, JPEG, etc.) via a file chooser
and extracts barcodes using the GStreamer zbar element.
"""

import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Adw, GdkPixbuf, GLib, GObject, Gst, Gtk

from loyalty_card_app.barcode_formats import BarcodeFormat

# Map zbar symbol type names to our BarcodeFormat enum.
ZBAR_FORMAT_MAP = {
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


def _scan_pixbuf(pixbuf):
    """Scan a GdkPixbuf for barcodes using the GStreamer zbar element.

    Returns a list of (BarcodeFormat, str) tuples, or an empty list.
    """
    Gst.init(None)

    width = pixbuf.get_width()
    height = pixbuf.get_height()

    # Convert pixbuf to RGBA bytes for appsrc
    if not pixbuf.get_has_alpha():
        pixbuf = pixbuf.add_alpha(False, 0, 0, 0)
    pixels = pixbuf.get_pixels()
    rowstride = pixbuf.get_rowstride()

    # Build pipeline: appsrc → videoconvert → zbar → fakesink
    pipeline = Gst.parse_launch(
        "appsrc name=src ! videoconvert ! zbar name=zbar ! fakesink"
    )
    if pipeline is None:
        return []

    src = pipeline.get_by_name("src")
    src.set_property("caps", Gst.Caps.from_string(
        f"video/x-raw,format=RGBA,width={width},height={height},"
        f"framerate=1/1,pixel-aspect-ratio=1/1"
    ))
    src.set_property("format", Gst.Format.TIME)

    pipeline.set_state(Gst.State.PLAYING)

    # Push the pixbuf as a single frame, packing rows tightly (RGBA = 4 bytes/pixel)
    if rowstride == width * 4:
        data = bytes(pixels)
    else:
        rows = [pixels[y * rowstride: y * rowstride + width * 4] for y in range(height)]
        data = b"".join(rows)

    buf = Gst.Buffer.new_wrapped(data)
    buf.pts = 0
    buf.duration = Gst.SECOND
    src.emit("push-buffer", buf)
    src.emit("end-of-stream")

    # Poll the bus synchronously — signal handlers won't fire while blocking
    results = []
    bus = pipeline.get_bus()
    deadline = 5 * Gst.SECOND
    while True:
        msg = bus.timed_pop(deadline)
        if msg is None:
            break
        if msg.type == Gst.MessageType.EOS or msg.type == Gst.MessageType.ERROR:
            break
        if msg.type == Gst.MessageType.ELEMENT:
            struct = msg.get_structure()
            if struct and struct.get_name() == "barcode":
                barcode_type = struct.get_string("type")
                barcode_data = struct.get_string("symbol")
                fmt = ZBAR_FORMAT_MAP.get(barcode_type)
                if fmt and barcode_data:
                    results.append((fmt, barcode_data))
        deadline = Gst.CLOCK_TIME_NONE  # subsequent pops don't need a timeout

    pipeline.set_state(Gst.State.NULL)

    return results


class FileScannerPage(Adw.NavigationPage):
    """Page that scans a barcode from a user-selected image file."""

    __gtype_name__ = "FileScannerPage"

    __gsignals__ = {
        "barcode-scanned": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str, str),  # (format_value, barcode_data)
        ),
    }

    def __init__(self, **kwargs):
        super().__init__(title="Scan from File", **kwargs)
        self._build_ui()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        self._stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        toolbar_view.set_content(self._stack)

        # Initial state: prompt to pick a file
        pick_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=24,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.CENTER,
            margin_start=24,
            margin_end=24,
        )
        pick_icon = Gtk.Image(
            icon_name="image-x-generic-symbolic",
            pixel_size=64,
            css_classes=["dim-label"],
        )
        pick_box.append(pick_icon)
        pick_label = Gtk.Label(
            label="Select an image containing a barcode",
            css_classes=["title-3"],
            wrap=True,
            justify=Gtk.Justification.CENTER,
        )
        pick_box.append(pick_label)
        pick_btn = Gtk.Button(
            label="Choose Image",
            css_classes=["suggested-action", "pill"],
            halign=Gtk.Align.CENTER,
        )
        pick_btn.connect("clicked", self._on_pick_clicked)
        pick_box.append(pick_btn)
        self._stack.add_named(pick_box, "pick")

        # Result: show scanned image + result
        result_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_start=12,
            margin_end=12,
            margin_top=12,
            margin_bottom=12,
        )
        self._result_picture = Gtk.Picture(
            content_fit=Gtk.ContentFit.CONTAIN,
            hexpand=True,
            vexpand=True,
        )
        result_box.append(self._result_picture)
        self._result_label = Gtk.Label(
            css_classes=["title-3"],
            wrap=True,
            justify=Gtk.Justification.CENTER,
        )
        result_box.append(self._result_label)
        retry_btn = Gtk.Button(
            label="Try Another Image",
            css_classes=["pill"],
            halign=Gtk.Align.CENTER,
            margin_bottom=12,
        )
        retry_btn.connect("clicked", self._on_pick_clicked)
        result_box.append(retry_btn)
        self._stack.add_named(result_box, "result")

        # Error state
        self._error_page = Adw.StatusPage(
            icon_name="dialog-warning-symbolic",
            title="No Barcode Found",
            description="Could not find a supported barcode in the selected image.",
        )
        error_btn = Gtk.Button(
            label="Try Another Image",
            css_classes=["suggested-action", "pill"],
            halign=Gtk.Align.CENTER,
        )
        error_btn.connect("clicked", self._on_pick_clicked)
        self._error_page.set_child(error_btn)
        self._stack.add_named(self._error_page, "error")

        self._stack.set_visible_child_name("pick")

    def _on_pick_clicked(self, _btn):
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Images")
        file_filter.add_mime_type("image/png")
        file_filter.add_mime_type("image/jpeg")
        file_filter.add_mime_type("image/webp")
        file_filter.add_mime_type("image/bmp")
        file_filter.add_mime_type("image/tiff")

        filters = Gtk.FilterListModel.new(None, None)

        dialog = Gtk.FileDialog()
        dialog.set_title("Select Barcode Image")

        filter_store = dialog.get_filters()
        if filter_store is None:
            filter_store = __import__("gi").repository.Gio.ListStore.new(Gtk.FileFilter)
            dialog.set_filters(filter_store)
        filter_store.append(file_filter)

        dialog.open(self.get_root(), None, self._on_file_selected)

    def _on_file_selected(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            # User cancelled
            return

        self._scan_gfile(gfile)

    def _scan_gfile(self, gfile):
        """Load the image and scan for barcodes."""
        try:
            stream = gfile.read(None)
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
            stream.close(None)
        except GLib.Error:
            self._error_page.set_title("Cannot Open Image")
            self._error_page.set_description(
                "The selected file could not be loaded as an image."
            )
            self._stack.set_visible_child_name("error")
            return

        # Show the image
        texture = __import__("gi").repository.Gdk.Texture.new_for_pixbuf(pixbuf)
        self._result_picture.set_paintable(texture)

        results = _scan_pixbuf(pixbuf)

        if not results:
            self._error_page.set_title("No Barcode Found")
            self._error_page.set_description(
                "Could not find a supported barcode in the selected image. "
                "Try a clearer photo or a different image."
            )
            self._stack.set_visible_child_name("error")
            return

        # Use the first result
        fmt, data = results[0]
        self._result_label.set_label(f"Found: {fmt.value}")
        self._stack.set_visible_child_name("result")

        self.emit("barcode-scanned", fmt.value, data)
