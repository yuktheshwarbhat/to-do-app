import pytest
from app import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app(db_path=tmp_path / "test.db")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()