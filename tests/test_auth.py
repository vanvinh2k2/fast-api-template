import jwt
from sqlalchemy import select
from uuid import UUID

from app.core.config import settings
from app.models.refresh_token import RefreshToken, RefreshTokenFamily
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
    assert j3["refresh_token"] != refresh


def test_access_token_uses_standard_claims(client, db_session):
    make_user(db_session, email="claims@example.com", password="secret", is_active=True)
    db_session.commit()

    access, _ = login(client, username="claims@example.com", password="secret")
    payload = jwt.decode(
        access,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer="auth-service",
        audience="api",
    )

    UUID(payload["sub"])
    assert payload["type"] == "access"
    assert payload["iss"] == "auth-service"
    assert payload["aud"] == "api"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload
    assert "user_id" not in payload
    assert "token_type" not in payload


def test_inactive_user_cannot_login(client, db_session):
    make_user(db_session, email="inactive@example.com", password="secret", is_active=False)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "secret"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


def test_register_rejects_duplicate_email(client, db_session):
    make_user(db_session, email="taken@example.com")
    db_session.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "taken@example.com",
            "full_name": "Taken User",
            "password": "Secret123!",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak-password@example.com",
            "full_name": "Weak Password",
            "password": "secret123",
        },
    )

    assert response.status_code == 422
    assert "Password must contain an uppercase letter" in response.text


def test_inactive_user_cannot_use_existing_access_token(client, db_session):
    user = make_user(db_session, email="active-then-disabled@example.com", password="secret")
    db_session.commit()
    access, _ = login(client, username=user.email, password="secret")

    user.is_active = False
    db_session.add(user)
    db_session.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User inactive"


def test_inactive_user_cannot_refresh_existing_token(client, db_session):
    user = make_user(db_session, email="refresh-disabled@example.com", password="secret")
    db_session.commit()
    _, refresh = login(client, username=user.email, password="secret")

    user.is_active = False
    db_session.add(user)
    db_session.commit()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})

    assert response.status_code == 401
    assert response.json()["detail"] == "User inactive"


def test_refresh_token_rotation_revokes_old_token(client, db_session):
    make_user(db_session, email="rotate@example.com", password="secret", is_active=True)
    db_session.commit()
    _, refresh_a = login(client, username="rotate@example.com", password="secret")

    first_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_a})

    assert first_refresh.status_code == 200, first_refresh.text
    refresh_b = first_refresh.json()["refresh_token"]
    assert refresh_b != refresh_a

    reused_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_a})

    assert reused_refresh.status_code == 401
    assert reused_refresh.json()["detail"] == "Invalid or expired refresh token"

    second_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_b})

    assert second_refresh.status_code == 401
    assert second_refresh.json()["detail"] == "Invalid or expired refresh token"


def test_refresh_token_can_rotate_as_a_family_chain(client, db_session):
    make_user(db_session, email="chain@example.com", password="secret", is_active=True)
    db_session.commit()
    _, refresh_a = login(client, username="chain@example.com", password="secret")

    first_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_a})

    assert first_refresh.status_code == 200, first_refresh.text
    refresh_b = first_refresh.json()["refresh_token"]

    second_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_b})

    assert second_refresh.status_code == 200, second_refresh.text
    assert second_refresh.json()["refresh_token"] != refresh_b


def test_login_stores_refresh_token_family(client, db_session):
    make_user(db_session, email="family@example.com", password="secret", is_active=True)
    db_session.commit()

    _, refresh = login(client, username="family@example.com", password="secret")
    payload = jwt.decode(
        refresh,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer="auth-service",
        audience="api",
    )

    token = db_session.scalars(select(RefreshToken).where(RefreshToken.jti == payload["jti"])).one()
    family = db_session.get(RefreshTokenFamily, token.family_id)

    assert family is not None
    assert family.user_id == UUID(payload["sub"])
    assert family.revoked_at is None
    assert token.revoked_at is None
