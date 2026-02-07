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
  'main.py',
  'window.py',
]

install_data(loyalty_card_app_sources, install_dir: moduledir)
