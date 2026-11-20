
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "app" / "templates"), "app/templates"),
    (str(ROOT / "app" / "static"), "app/static"),
    (str(ROOT / "laboratory" / "templates"), "laboratory/templates"),
    (str(ROOT / "migrations"), "migrations"),
    (str(ROOT / "instance" / "database.db"), "instance"),
]

binaries = []
hiddenimports = ["paths"]

packages = [
    "flask",
    "flask_login",
    "flask_migrate",
    "flask_sqlalchemy",
    "flask_wtf",
    "sqlalchemy",
    "alembic",
    "waitress",
    "jinja2",
    "werkzeug",
    "wtforms",
]

for package in packages:
    package_datas, package_binaries, package_hiddenimports = (
        collect_all(package)
    )

    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


a = Analysis(
    ["run_local.py"],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "coverage"],
    noarchive=False,
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
