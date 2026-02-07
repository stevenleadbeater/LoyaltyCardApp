# main.py
#
# Copyright 2026
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw

from .window import LoyaltyCardAppWindow

APP_ID = 'com.github.loyaltycardapp.LoyaltyCardApp'


class LoyaltyCardApp(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.version = version
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = LoyaltyCardAppWindow(application=self)
        win.present()

    def on_about_action(self, widget, _):
        about = Adw.AboutDialog(
            application_name='Loyalty Card App',
            application_icon=APP_ID,
            developer_name='Loyalty Card App Contributors',
            version=self.version,
            developers=['Loyalty Card App Contributors'],
            copyright='Copyright 2026',
            license_type=Gtk.License.GPL_3_0,
            website='https://github.com/loyaltycardapp/loyalty-card-app',
            issue_url='https://github.com/loyaltycardapp/loyalty-card-app/issues',
        )
        about.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)


def main(version):
    app = LoyaltyCardApp(version)
    return app.run(sys.argv)
