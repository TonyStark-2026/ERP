# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:/Users/ruancanling/Desktop/ERP VIBE CODING/frontend', 'frontend')]
binaries = []
hiddenimports = ['uvicorn', 'uvicorn.lifespan', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'fastapi', 'pydantic', 'pydantic.dataclasses', 'sqlalchemy', 'sqlalchemy.dialects', 'sqlalchemy.dialects.sqlite', 'qrcode', 'PIL', 'PIL.Image', 'webview', 'webview.platforms.edgechromium', 'webview.platforms.mshtml', 'webview.platforms.winforms', 'webview.platforms.gtk', 'webview.platforms.gtkloader', 'webview.http', 'webview.http.staticfiles', 'webview.util', 'clr', 'pythonnet', 'backend', 'backend.app', 'backend.models', 'backend.schemas', 'backend.crud', 'backend.database', 'backend.api', 'backend.api.auth', 'backend.api.bom', 'backend.api.materials', 'backend.api.finance', 'backend.api.plan', 'backend.api.sales', 'backend.api.purchase', 'backend.api.production', 'backend.api.inventory', 'backend.api.procurement', 'backend.api.employees', 'backend.api.compliance', 'backend.api.crossborder', 'backend.api.scanning', 'backend.api.invoice_recognition', 'backend.api.config_center', 'backend.api.contracts']
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:/Users/ruancanling/Desktop/ERP VIBE CODING/_exe_embedded_launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='ERP智能系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ERP智能系统',
)
