import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Gio

from card_model import CardStore, LoyaltyCard, CARD_COLORS
from card_widget import CardWidget


class LoyaltyCardWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'LoyaltyCardWindow'

    def __init__(self, application, **kwargs):
        super().__init__(application=application, **kwargs)
        self.set_default_size(360, 640)
        self.set_title('Loyalty Cards')

        self._store = CardStore()
        self._card_widgets = {}

        self._build_ui()
        self._load_css()
        self._populate_cards()

    def _build_ui(self):
        self._navigation = Adw.NavigationView()
        self.set_content(self._navigation)

        # Main list page
        list_page = Adw.NavigationPage(title='Loyalty Cards', tag='card-list')
        self._build_list_page(list_page)
        self._navigation.push(list_page)

    def _build_list_page(self, page):
        toolbar_view = Adw.ToolbarView()
        page.set_child(toolbar_view)

        header = Adw.HeaderBar()
        add_button = Gtk.Button(icon_name='list-add-symbolic')
        add_button.set_tooltip_text('Add Card')
        add_button.connect('clicked', self._on_add_card)
        header.pack_end(add_button)
        toolbar_view.add_top_bar(header)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        toolbar_view.set_content(scrolled)

        self._clamp = Adw.Clamp()
        self._clamp.set_maximum_size(600)
        self._clamp.set_tightening_threshold(400)
        scrolled.set_child(self._clamp)

        self._cards_box = Gtk.FlowBox()
        self._cards_box.set_valign(Gtk.Align.START)
        self._cards_box.set_homogeneous(True)
        self._cards_box.set_max_children_per_line(2)
        self._cards_box.set_min_children_per_line(1)
        self._cards_box.set_column_spacing(12)
        self._cards_box.set_row_spacing(12)
        self._cards_box.set_margin_start(12)
        self._cards_box.set_margin_end(12)
        self._cards_box.set_margin_top(12)
        self._cards_box.set_margin_bottom(12)
        self._cards_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._clamp.set_child(self._cards_box)

        # Empty state
        self._empty_status = Adw.StatusPage()
        self._empty_status.set_icon_name('wallet-symbolic')
        self._empty_status.set_title('No Cards Yet')
        self._empty_status.set_description('Tap + to add your first loyalty card')
        self._empty_status.set_visible(False)
        # We'll swap between cards_box and empty_status via a stack
        self._content_stack = Gtk.Stack()
        self._content_stack.add_named(self._cards_box, 'cards')
        self._content_stack.add_named(self._empty_status, 'empty')
        self._clamp.set_child(self._content_stack)

    def _load_css(self):
        css = """
            .card-button {
                padding: 0;
                margin: 0;
                border-radius: 12px;
                background: transparent;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                border: none;
                min-height: 160px;
            }
            .card-button:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            }
            .card-button:active {
                box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            }
            .color-button {
                min-width: 40px;
                min-height: 40px;
                border-radius: 20px;
                padding: 0;
                border: 2px solid transparent;
            }
            .color-button-selected {
                border: 3px solid @accent_color;
            }
            .detail-card-preview {
                min-height: 200px;
                border-radius: 16px;
            }
        """
        provider = Gtk.CssProvider()
        provider.load_from_string(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _populate_cards(self):
        self._card_widgets.clear()
        child = self._cards_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._cards_box.remove(child)
            child = next_child

        cards = self._store.cards
        if not cards:
            self._content_stack.set_visible_child_name('empty')
            return

        self._content_stack.set_visible_child_name('cards')
        for card in cards:
            widget = CardWidget(card)
            widget.connect('card-activated', self._on_card_activated)
            self._cards_box.append(widget)
            self._card_widgets[card.card_id] = widget

    def _on_card_activated(self, _widget, card_id):
        card = self._store.get_card(card_id)
        if card:
            self._show_card_detail(card)

    def _show_card_detail(self, card):
        detail_page = Adw.NavigationPage(title=card.name, tag=f'detail-{card.card_id}')
        toolbar_view = Adw.ToolbarView()
        detail_page.set_child(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        toolbar_view.set_content(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        clamp.set_child(content)

        # Card preview at top
        preview = CardWidget(card)
        preview.set_sensitive(False)
        content.append(preview)

        # Card info
        info_group = Adw.PreferencesGroup(title='Card Info')
        name_row = Adw.ActionRow(title='Name', subtitle=card.name)
        name_row.set_icon_name('contact-new-symbolic')
        info_group.add(name_row)

        if card.barcode_data:
            barcode_row = Adw.ActionRow(title='Barcode', subtitle=card.barcode_data)
            barcode_row.set_icon_name('view-barcode-symbolic')
            info_group.add(barcode_row)

        if card.notes:
            notes_row = Adw.ActionRow(title='Notes', subtitle=card.notes)
            notes_row.set_icon_name('document-text-symbolic')
            info_group.add(notes_row)

        content.append(info_group)

        self._navigation.push(detail_page)

    def _on_add_card(self, _button):
        self._show_card_editor(None)

    def _show_card_editor(self, card):
        is_new = card is None
        title = 'New Card' if is_new else 'Edit Card'

        dialog = Adw.Dialog()
        dialog.set_title(title)
        dialog.set_content_width(360)
        dialog.set_content_height(500)

        toolbar_view = Adw.ToolbarView()
        dialog.set_child(toolbar_view)

        header = Adw.HeaderBar()
        cancel_btn = Gtk.Button(label='Cancel')
        cancel_btn.connect('clicked', lambda _: dialog.close())
        header.pack_start(cancel_btn)

        save_btn = Gtk.Button(label='Save')
        save_btn.add_css_class('suggested-action')
        header.pack_end(save_btn)
        toolbar_view.add_top_bar(header)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(500)
        toolbar_view.set_content(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        clamp.set_child(content)

        # Name entry
        name_group = Adw.PreferencesGroup()
        name_row = Adw.EntryRow(title='Card Name')
        if card:
            name_row.set_text(card.name)
        name_group.add(name_row)
        content.append(name_group)

        # Barcode entry
        barcode_group = Adw.PreferencesGroup()
        barcode_row = Adw.EntryRow(title='Barcode Number')
        if card:
            barcode_row.set_text(card.barcode_data)
        barcode_group.add(barcode_row)
        content.append(barcode_group)

        # Notes entry
        notes_group = Adw.PreferencesGroup()
        notes_row = Adw.EntryRow(title='Notes')
        if card:
            notes_row.set_text(card.notes)
        notes_group.add(notes_row)
        content.append(notes_group)

        # Color picker
        color_group = Adw.PreferencesGroup(title='Card Color')
        color_flow = Gtk.FlowBox()
        color_flow.set_max_children_per_line(6)
        color_flow.set_min_children_per_line(4)
        color_flow.set_column_spacing(8)
        color_flow.set_row_spacing(8)
        color_flow.set_homogeneous(True)
        color_flow.set_selection_mode(Gtk.SelectionMode.NONE)

        selected_color = {'value': card.color if card else '#3498db'}
        color_buttons = {}

        for color_name, hex_val in CARD_COLORS.items():
            btn = Gtk.Button()
            btn.add_css_class('color-button')
            btn.set_tooltip_text(color_name.title())

            btn_css = Gtk.CssProvider()
            btn_css.load_from_string(
                f".color-swatch-{color_name} {{ background-color: {hex_val}; }}"
            )
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display, btn_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2
                )
            btn.add_css_class(f'color-swatch-{color_name}')

            if hex_val == selected_color['value']:
                btn.add_css_class('color-button-selected')

            def on_color_pick(b, hv=hex_val):
                selected_color['value'] = hv
                for cb in color_buttons.values():
                    cb.remove_css_class('color-button-selected')
                b.add_css_class('color-button-selected')

            btn.connect('clicked', on_color_pick)
            color_buttons[color_name] = btn
            color_flow.append(btn)

        color_group.add(color_flow)
        content.append(color_group)

        def on_save(_btn):
            name = name_row.get_text().strip()
            if not name:
                name_row.add_css_class('error')
                return

            if is_new:
                new_card = LoyaltyCard(
                    name=name,
                    color=selected_color['value'],
                    barcode_data=barcode_row.get_text().strip(),
                    notes=notes_row.get_text().strip(),
                )
                self._store.add_card(new_card)
            else:
                self._store.update_card(
                    card.card_id,
                    name=name,
                    color=selected_color['value'],
                    barcode_data=barcode_row.get_text().strip(),
                    notes=notes_row.get_text().strip(),
                )
            self._populate_cards()
            dialog.close()

        save_btn.connect('clicked', on_save)
        dialog.present(self)
