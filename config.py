import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    BABEL_DEFAULT_LOCALE = "ru"
    BABEL_DEFAULT_TIMEZONE = "Asia/Almaty"

    if not SECRET_KEY:
        raise RuntimeError(
            "Не задан SECRET_KEY. Создайте файл .env на основе .env.example."
        )

    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
