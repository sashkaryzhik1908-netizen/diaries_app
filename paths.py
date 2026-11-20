import os
import shutil
import sys
from pathlib import Path


def get_data_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")

    if not local_app_data:
        raise RuntimeError("Не найдена папка LOCALAPPDATA Windows.")

    data_dir = Path(local_app_data) / "Diaries"
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def initialize_database():
    data_dir = get_data_dir()
    database_path = data_dir / "database.db"

    if database_path.exists():
        return database_path

    if getattr(sys, "frozen", False):
        source_path = Path(sys._MEIPASS) / "instance" / "database.db"
    else:
        source_path = Path(__file__).resolve().parent / "instance" / "database.db"

    if not source_path.exists():
        raise FileNotFoundError(f"Не найдена начальная база данных: {source_path}")

    shutil.copy2(source_path, database_path)

    return database_path
