pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'loyalty_card_app'

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('APP_ID', 'com.github.loyaltycardapp.LoyaltyCardApp')

configure_file(
  input: 'loyalty-card-app.in',
  output: 'loyalty-card-app',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

loyalty_card_app_sources = [
  '__init__.py',
  'camera_scanner.py',
  'card_detail.py',
  'card_manager.py',
  'card_store.py',
  'delete_card_dialog.py',
  'edit_card_dialog.py',
  'main.py',
  'window.py',
]

install_data(loyalty_card_app_sources, install_dir: moduledir)

install_data(
  [
    'loyalty_card_app/barcode_entry.py',
    'loyalty_card_app/barcode_formats.py',
    'loyalty_card_app/barcode_scanner.py',
    'loyalty_card_app/file_scanner.py',
    'loyalty_card_app/camera_devices.py',
    'loyalty_card_app/barcode_render.py',
  ],
  install_dir: moduledir,
)
