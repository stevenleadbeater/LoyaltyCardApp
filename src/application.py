import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio

from window import LoyaltyCardWindow


class LoyaltyCardApplication(Adw.Application):
    __gtype_name__ = 'LoyaltyCardApplication'

    def __init__(self):
        super().__init__(
            application_id='com.example.LoyaltyCards',
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = LoyaltyCardWindow(application=self)
        win.present()
