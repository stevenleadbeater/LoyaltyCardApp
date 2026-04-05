# Loyalty Card App

A GNOME mobile app for managing loyalty cards and membership cards. Built with GTK4 and libadwaita for adaptive mobile/desktop UI, targeting Phosh/GNOME mobile.

## Building

```bash
meson setup builddir
meson compile -C builddir
meson install -C builddir
```

## Building with Flatpak

```bash
flatpak-builder --user --install --force-clean _build io.github.stevenleadbeater.LoyaltyCardApp.json
flatpak run io.github.stevenleadbeater.LoyaltyCardApp
```

## Stack

- **Language:** Python 3
- **UI Toolkit:** GTK4 + libadwaita
- **Build System:** Meson
- **Packaging:** Flatpak
- **Target:** GNOME mobile (Phosh) and desktop

## License

This project is licensed under the [GPL-3.0-or-later](COPYING) license.
