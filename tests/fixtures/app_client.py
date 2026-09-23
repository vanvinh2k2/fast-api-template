import pytest
from starlette.testclient import TestClient

from tests.fixtures.db import TestingSessionLocal
from app.api.deps import get_db_dep
from app.main import app

@pytest.fixture()
def client():
    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_dep] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
