import sqlite3

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


# Включение контроля внешних ключей SQLite
@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        autocommit = dbapi_connection.autocommit
        dbapi_connection.autocommit = True

        try:
            cursor = dbapi_connection.cursor()

            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()
        finally:
            dbapi_connection.autocommit = autocommit
