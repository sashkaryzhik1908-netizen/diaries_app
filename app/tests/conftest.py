import pytest

from app import create_app
from app.extensions import db
from app.models import TherapySource, TherapySourceValue


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
        }
    )

    with app.app_context():
        db.create_all()

        sources = {
            "Режим": [],
            "Диета": [],
            "Режим восполнения": [],
            "Единицы измерения": ["мг", "гр", "мл"],
            "Способы введения": ["внутривенно"],
            "Кратность": ["1 р/сут", "2 р/сут"],
        }

        for source_name, values in sources.items():
            source = TherapySource(name=source_name)
            source.values = [TherapySourceValue(name=value) for value in values]
            db.session.add(source)

        db.session.commit()

    yield app

    with app.app_context():
        try:
            db.session.remove()
            db.drop_all()
        finally:
            db.session.remove()
            db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()
