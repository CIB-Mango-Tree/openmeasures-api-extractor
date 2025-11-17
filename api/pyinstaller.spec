# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
import sys
import lagom.container
mypyc_modules = []

for module_name in sys.modules.keys():
  if '__mypyc' not in module_name:
    continue
  
  mypyc_modules.append(module_name)
  print(f"Found __mypyc module: {module_name}")


datas = [('src', 'src')]
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
  'sqlalchemy',
  'sqlalchemy.ext',
  'sqlalchemy.ext.asyncio',
  'sqlalchemy.orm',
  'sqlalchemy.pool',
  'sqlalchemy.dialects',
  'sqlalchemy.dialects.sqlite',
  'alembic',
  'anyio',
  'anyio._backends',
  'anyio._backends._asyncio',
  'click',
  'h11',
  'idna',
  'lagom',
  'lagom.container',
  'lagom.context_based',
  'lagom.updaters',
  'lagom.integrations',
  'lagom.integrations.starlette',
  'pandas',
  'pyarrow',
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


tmp_ret = collect_all('lagom')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mango-tree-api-extractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
