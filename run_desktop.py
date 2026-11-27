import os
import secrets
import shutil
import sys
from pathlib import Path
import threading
import webbrowser

from waitress import serve


def get_app_data_dir():
    app_data = Path(os.environ["APPDATA"]) / "Diaries"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


def get_resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parent / relative_path


def initialize_user_data():
    app_data = get_app_data_dir()

    database_path = app_data / "database.db"
    env_path = app_data / ".env"

    source_database = get_resource_path("instance/database.db")

    if not database_path.exists():
        shutil.copy2(source_database, database_path)

    if not env_path.exists():
        env_path.write_text(
            f"SECRET_KEY={secrets.token_hex(32)}\nFLASK_DEBUG=false\n",
            encoding="utf-8",
        )

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["SECRET_KEY"] = load_secret_key(env_path)


def load_secret_key(env_path):
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SECRET_KEY="):
            return line.split("=", 1)[1].strip()

    raise RuntimeError("SECRET_KEY отсутствует в .env")


initialize_user_data()

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    threading.Timer(
        1.5,
        lambda: webbrowser.open("http://127.0.0.1:5000"),
    ).start()

    serve(app, host="127.0.0.1", port=5000)
