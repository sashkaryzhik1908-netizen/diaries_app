import os
import secrets
import sys
import webbrowser
from pathlib import Path
from threading import Timer

from dotenv import load_dotenv
from waitress import serve


# Настройка окружения
if getattr(sys, "frozen", False):
    config_dir = Path(os.environ["APPDATA"]) / "Diaries"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Загрузка переменных окружения
    load_dotenv(config_dir / ".env")

    # Создание секретного ключа Flask
    secret_file = config_dir / "secret_key.txt"

    if not secret_file.exists():
        secret_file.write_text(
            secrets.token_hex(32),
            encoding="utf-8",
        )

    os.environ["SECRET_KEY"] = secret_file.read_text(encoding="utf-8").strip()

else:
    load_dotenv(Path(__file__).resolve().parent / ".env")


from app import create_app


def get_database_path():
    if getattr(sys, "frozen", False):
        database_dir = Path(os.environ["APPDATA"]) / "Diaries"
        database_dir.mkdir(parents=True, exist_ok=True)

        return database_dir / "database.db"

    return Path(__file__).resolve().parent / "instance" / "database.db"


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    database_path = get_database_path()

    if not database_path.is_file():
        raise FileNotFoundError(f"База данных не найдена: {database_path}")

    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": (f"sqlite:///{database_path.as_posix()}"),
        }
    )

    Timer(1.5, open_browser).start()

    serve(
        app,
        host="127.0.0.1",
        port=5000,
        threads=4,
    )
