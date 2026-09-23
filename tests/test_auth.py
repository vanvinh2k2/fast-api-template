from tests.factories.user import make_user
from tests.utils.auth import login

def test_auth_flow(client, db_session):
    make_user(db_session, email="u1@example.com", password="secret", is_active=True)

    # LOGIN
    access, refresh = login(client, username="u1@example.com", password="secret")
    assert access

    # REFRESH
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r3.status_code == 200, r3.text
    j3 = r3.json()
    assert "access_token" in j3 and j3["access_token"] != access