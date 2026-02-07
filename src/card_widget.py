import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GObject
import cairo

from card_model import LoyaltyCard


def parse_color(hex_color):
    rgba = Gdk.RGBA()
    rgba.parse(hex_color)
    return rgba


def contrasting_text_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return '#ffffff' if luminance < 0.5 else '#1a1a1a'


class CardWidget(Gtk.Button):
    __gtype_name__ = 'CardWidget'

    __gsignals__ = {
        'card-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, card: LoyaltyCard, **kwargs):
        super().__init__(**kwargs)
        self.card = card
        self.set_css_name('card-widget')
        self.add_css_class('card-button')

        self._build_ui()
        self._apply_color()

        self.connect('clicked', self._on_clicked)

    def _build_ui(self):
        overlay = Gtk.Overlay()

        drawing = Gtk.DrawingArea()
        drawing.set_content_width(280)
        drawing.set_content_height(160)
        drawing.set_draw_func(self._draw_card)
        overlay.set_child(drawing)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content.set_halign(Gtk.Align.START)
        content.set_valign(Gtk.Align.END)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_bottom(16)
        content.set_margin_top(16)

        self._name_label = Gtk.Label(label=self.card.name)
        self._name_label.set_halign(Gtk.Align.START)
        self._name_label.add_css_class('card-name')
        content.append(self._name_label)

        if self.card.barcode_data:
            barcode_label = Gtk.Label(label=self.card.barcode_data)
            barcode_label.set_halign(Gtk.Align.START)
            barcode_label.add_css_class('card-barcode-text')
            content.append(barcode_label)

        overlay.add_overlay(content)
        self.set_child(overlay)

    def _draw_card(self, area, cr, width, height):
        radius = 12
        rgba = parse_color(self.card.color)

        cr.new_sub_path()
        cr.arc(width - radius, radius, radius, -1.5708, 0)
        cr.arc(width - radius, height - radius, radius, 0, 1.5708)
        cr.arc(radius, height - radius, radius, 1.5708, 3.14159)
        cr.arc(radius, radius, radius, 3.14159, 4.71239)
        cr.close_path()

        cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
        cr.fill_preserve()

        cr.set_source_rgba(rgba.red * 0.8, rgba.green * 0.8, rgba.blue * 0.8, 0.5)
        cr.set_line_width(1)
        cr.stroke()

        # Subtle shine effect at top
        gradient = cairo.LinearGradient(0, 0, 0, height * 0.4)
        gradient.add_color_stop_rgba(0, 1, 1, 1, 0.15)
        gradient.add_color_stop_rgba(1, 1, 1, 1, 0)
        cr.new_sub_path()
        cr.arc(width - radius, radius, radius, -1.5708, 0)
        cr.line_to(width, height * 0.4)
        cr.line_to(0, height * 0.4)
        cr.arc(radius, radius, radius, 3.14159, 4.71239)
        cr.close_path()
        cr.set_source(gradient)
        cr.fill()

    def _apply_color(self):
        text_color = contrasting_text_color(self.card.color)
        css = f"""
            .card-name {{
                color: {text_color};
                font-size: 18px;
                font-weight: bold;
            }}
            .card-barcode-text {{
                color: {text_color};
                font-size: 11px;
                opacity: 0.8;
                font-family: monospace;
            }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_string(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
            )

    def _on_clicked(self, _button):
        self.emit('card-activated', self.card.card_id)

    def update_card(self, card: LoyaltyCard):
        self.card = card
        self._name_label.set_label(card.name)
        self._apply_color()
        drawing = self.get_child().get_child()
        drawing.queue_draw()
