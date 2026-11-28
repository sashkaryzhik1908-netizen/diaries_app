# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    copy_metadata,
)


datas = [
    ("app/templates", "app/templates"),
    ("app/static", "app/static"),
    ("instrumental/templates", "instrumental/templates"),
    ("laboratory/templates", "laboratory/templates"),
]

datas += collect_data_files("flask_admin")
datas += collect_data_files("google.genai")
datas += copy_metadata("google-genai")

hiddenimports = (
    collect_submodules("app")
    + collect_submodules("instrumental")
    + collect_submodules("laboratory")
    + collect_submodules("google.genai")
)

a = Analysis(
    ["run_desktop.py"],
    pathex=[],
    binaries=[],
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
    name="Diaries",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Diaries",
)