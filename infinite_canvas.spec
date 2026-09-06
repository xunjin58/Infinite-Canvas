# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project = Path(SPEC).resolve().parent
datas = [
    (str(project / "static"), "static"),
    (str(project / "workflows"), "workflows"),
    (str(project / "VERSION"), "."),
]

a = Analysis(
    [str(project / "windows_launcher.py")],
    pathex=[str(project)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "tkinter",
        "tkinter.filedialog",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Infinite-Canvas",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
