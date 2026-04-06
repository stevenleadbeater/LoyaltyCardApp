"""Scan a barcode from an image file.

Lets the user pick an image (PNG, JPEG, etc.) via a file chooser
and extracts barcodes using the zbar library.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Adw, GdkPixbuf, GLib, GObject, Gtk

from loyalty_card_app.barcode_formats import BarcodeFormat

# Map zbar symbol type names to our BarcodeFormat enum.
# Matches the mapping in barcode_scanner.py.
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
    """Scan a GdkPixbuf for barcodes using zbar.

    Returns a list of (BarcodeFormat, str) tuples, or an empty list.
    """
    import ctypes
    import ctypes.util

    lib_path = ctypes.util.find_library("zbar")
    if lib_path is None:
        # Try common paths
        for path in ["/app/lib/libzbar.so.0", "/usr/lib/libzbar.so.0",
                     "/usr/lib/x86_64-linux-gnu/libzbar.so.0",
                     "/usr/lib/aarch64-linux-gnu/libzbar.so.0"]:
            try:
                ctypes.CDLL(path)
                lib_path = path
                break
            except OSError:
                continue

    if lib_path is None:
        return []

    zbar = ctypes.CDLL(lib_path)

    # Set up function signatures
    zbar.zbar_image_scanner_create.restype = ctypes.c_void_p
    zbar.zbar_image_scanner_destroy.argtypes = [ctypes.c_void_p]
    zbar.zbar_image_create.restype = ctypes.c_void_p
    zbar.zbar_image_destroy.argtypes = [ctypes.c_void_p]
    zbar.zbar_image_set_format.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    zbar.zbar_image_set_size.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    zbar.zbar_image_set_data.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p]
    zbar.zbar_scan_image.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    zbar.zbar_scan_image.restype = ctypes.c_int
    zbar.zbar_image_first_symbol.argtypes = [ctypes.c_void_p]
    zbar.zbar_image_first_symbol.restype = ctypes.c_void_p
    zbar.zbar_symbol_next.argtypes = [ctypes.c_void_p]
    zbar.zbar_symbol_next.restype = ctypes.c_void_p
    zbar.zbar_symbol_get_type.argtypes = [ctypes.c_void_p]
    zbar.zbar_symbol_get_type.restype = ctypes.c_int
    zbar.zbar_symbol_get_data.argtypes = [ctypes.c_void_p]
    zbar.zbar_symbol_get_data.restype = ctypes.c_char_p
    zbar.zbar_get_symbol_name.argtypes = [ctypes.c_int]
    zbar.zbar_get_symbol_name.restype = ctypes.c_char_p

    # Scale down large images — barcodes are scannable at much lower resolution
    # and the pure-Python pixel loop is O(w*h), so limiting to ~1MP keeps it fast.
    MAX_DIM = 1024
    orig_w = pixbuf.get_width()
    orig_h = pixbuf.get_height()
    if orig_w > MAX_DIM or orig_h > MAX_DIM:
        scale = MAX_DIM / max(orig_w, orig_h)
        pixbuf = pixbuf.scale_simple(
            int(orig_w * scale), int(orig_h * scale),
            GdkPixbuf.InterpType.BILINEAR,
        )

    # Convert pixbuf to raw grayscale (Y800)
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    n_channels = pixbuf.get_n_channels()
    rowstride = pixbuf.get_rowstride()
    pixels = pixbuf.get_pixels()

    # Convert to grayscale
    gray = bytearray(width * height)
    for y in range(height):
        row_off = y * rowstride
        for x in range(width):
            o = row_off + x * n_channels
            gray[y * width + x] = (pixels[o] * 299 + pixels[o + 1] * 587 + pixels[o + 2] * 114) // 1000

    gray_buf = (ctypes.c_ubyte * len(gray)).from_buffer(gray)

    scanner = zbar.zbar_image_scanner_create()
    image = zbar.zbar_image_create()

    # Y800 format = ord('Y') | (ord('8') << 8) | (ord('0') << 16) | (ord('0') << 24)
    fourcc = ord('Y') | (ord('8') << 8) | (ord('0') << 16) | (ord('0') << 24)
    zbar.zbar_image_set_format(image, fourcc)
    zbar.zbar_image_set_size(image, width, height)
    zbar.zbar_image_set_data(image, gray_buf, len(gray), None)

    results = []
    n = zbar.zbar_scan_image(scanner, image)
    if n > 0:
        sym = zbar.zbar_image_first_symbol(image)
        while sym:
            type_id = zbar.zbar_symbol_get_type(sym)
            type_name = zbar.zbar_get_symbol_name(type_id).decode("utf-8", errors="replace")
            data = zbar.zbar_symbol_get_data(sym).decode("utf-8", errors="replace")
            fmt = ZBAR_FORMAT_MAP.get(type_name)
            if fmt is not None and data:
                results.append((fmt, data))
            sym = zbar.zbar_symbol_next(sym)

    zbar.zbar_image_destroy(image)
    zbar.zbar_image_scanner_destroy(scanner)

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

        path = gfile.get_path()
        if path is None:
            return

        self._scan_file(path)

    def _scan_file(self, path):
        """Load the image and scan for barcodes."""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
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
