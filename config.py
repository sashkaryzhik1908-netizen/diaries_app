import os

from paths import initialize_database


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"

    if os.environ.get("DIARIES_INSTALLED") == "1":
        database_path = initialize_database()

        SQLALCHEMY_DATABASE_URI = f"sqlite:///{database_path.as_posix()}"
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
