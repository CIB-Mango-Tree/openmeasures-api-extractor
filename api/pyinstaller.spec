# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
import sys
mypyc_modules = []

for module_name in sys.modules.keys():
  if '__mypyc' not in module_name:
    continue
  
  mypyc_modules.append(module_name)
  print(f"Found __mypyc module: {module_name}")


# The alembic directory ships as data because migrations are loaded from disk by path at
# runtime, not imported as modules. src/db/migrate.py resolves it under sys._MEIPASS.
# ../site/dist is the built frontend, which this server now serves itself; src/settings.py
# resolves it the same way.
datas = [('src', 'src'), ('alembic', 'alembic'), ('../site/dist', 'dist')]
binaries = []
hiddenimports = [
  'src',
  'starlette',
  'starlette.applications',
  'starlette.routing',
  'starlette.middleware',
  'starlette.middleware.cors',
  'starlette.responses',
  'starlette.requests',
  'starlette.websockets',
  'uvicorn',
  'uvicorn.logging',
  'uvicorn.loops',
  'uvicorn.loops.auto',
  'uvicorn.protocols',
  'uvicorn.protocols.http',
  'uvicorn.protocols.http.auto',
  'uvicorn.protocols.websockets',
  'uvicorn.protocols.websockets.auto',
  'uvicorn.lifespan',
  'uvicorn.lifespan.on',
  'pyventus',
  'pyventus.events',
  'dateutil',
  'dateutil.relativedelta',
  'polars',
  'sqlalchemy',
  'sqlalchemy.ext',
  'sqlalchemy.ext.asyncio',
  'sqlalchemy.orm',
  'sqlalchemy.pool',
  'sqlalchemy.dialects',
  'sqlalchemy.dialects.sqlite',
  'alembic',
  'alembic.command',
  'alembic.config',
  'alembic.runtime.migration',
  'alembic.script',
  'alembic.ddl',
  'alembic.ddl.sqlite',
  'anyio',
  'anyio._backends',
  'anyio._backends._asyncio',
  'click',
  'h11',
  'idna',
  'pydantic',
  'pydantic.deprecated',
  'pydantic.deprecated.decorator',
  'requests',
  'sniffio',
  'typing_extensions',
  'tzlocal',
  'websockets',
  'xlsxwriter',
  'platformdirs'
]


tmp_ret = collect_all('starlette')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
hiddenimports.extend(mypyc_modules)
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=list(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

APP_NAME = 'CIB Mango Tree API Extractor'
BUNDLE_ID = 'org.cibmangotree.api.extractor'

# CI writes VERSION at the repo root before building; local builds may not have it.
try:
    with open('../VERSION') as version_file:
        VERSION = version_file.read().strip() or '0.0.0'
except OSError:
    VERSION = '0.0.0'

# onedir rather than onefile: a onefile binary re-extracts its whole archive to a temp directory
# on every launch, which is what the old launcher's readiness polling existed to hide. Inside a
# .app the files are just there.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mango-tree-api-extractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # No terminal: the app is a window. Failures go to the diagnostics logs in the app data dir.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    # Windows only (macOS takes its icon from the BUNDLE below). This is what gives the exe and
    # every shortcut NSIS creates a real icon.
    icon='icon.ico',
    codesign_identity=os.environ.get('APPLE_APP_CERT_ID'),
    entitlements_file="../mango.entitlements",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mango-tree-api-extractor',
)

app = BUNDLE(
    coll,
    name=f'{APP_NAME}.app',
    icon='icon.icns',
    bundle_identifier=BUNDLE_ID,
    version=VERSION,
    info_plist={
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'NSHighResolutionCapable': True,
        # Nothing here is a document editor or a background agent; it is a normal windowed app.
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'NSHumanReadableCopyright': 'CIB Mango Tree',
    },
)
