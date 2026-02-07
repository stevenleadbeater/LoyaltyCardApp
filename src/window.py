# window.py
#
# Copyright 2026
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path='/com/github/loyaltycardapp/LoyaltyCardApp/window.ui')
class LoyaltyCardAppWindow(Adw.ApplicationWindow):
    """Main application window with adaptive mobile layout."""

    __gtype_name__ = 'LoyaltyCardAppWindow'

    cards_list = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
