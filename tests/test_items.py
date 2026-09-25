import pytest
from sqlalchemy import delete

from app.models.item import Item
from app.models.user import User
from tests.factories.user import make_user
from tests.utils.auth import login


@pytest.fixture(autouse=True)
def clean_items(db_session):
    db_session.execute(delete(Item))
    db_session.execute(delete(User))
    db_session.commit()
    yield
    db_session.execute(delete(Item))
    db_session.execute(delete(User))
    db_session.commit()


def auth_headers(client, db_session, email: str = "user@example.com") -> dict[str, str]:
    make_user(db_session, email=email, password="secret")
    db_session.commit()

    access_token, _ = login(client, username=email, password="secret")
    return {"Authorization": f"Bearer {access_token}"}


def test_list_items_returns_items(client, db_session):
    user = make_user(db_session, email="list-items@example.com")
    db_session.add(Item(title="First", description=None, owner_id=user.id))
    db_session.add(Item(title="Second", description="Two", owner_id=user.id))
    db_session.commit()

    response = client.get("/api/v1/items?ordering=-title")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["next"] is None
    assert data["previous"] is None
    assert [item["title"] for item in data["results"]] == ["Second", "First"]
    assert data["results"][0]["description"] == "Two"


def test_list_items_returns_paginated_response(client, db_session):
    user = make_user(db_session, email="paginated-items@example.com")
    for title in ["First", "Second", "Third"]:
        db_session.add(Item(title=title, description=None, owner_id=user.id))
    db_session.commit()

    first_page = client.get("/api/v1/items?limit=2&offset=0&ordering=-title")

    assert first_page.status_code == 200
    first_data = first_page.json()
    assert first_data["count"] == 3
    assert first_data["previous"] is None
    assert first_data["next"] == "http://testserver/api/v1/items?ordering=-title&limit=2&offset=2"
    assert [item["title"] for item in first_data["results"]] == ["Third", "Second"]

    second_page = client.get("/api/v1/items?limit=2&offset=2&ordering=-title")

    assert second_page.status_code == 200
    second_data = second_page.json()
    assert second_data["count"] == 3
    assert second_data["next"] is None
    assert (
        second_data["previous"] == "http://testserver/api/v1/items?ordering=-title&limit=2&offset=0"
    )
    assert [item["title"] for item in second_data["results"]] == ["First"]


def test_list_items_filters_by_search(client, db_session):
    user = make_user(db_session, email="search-items@example.com", full_name="Casey Owner")
    db_session.add(Item(title="Alpha notebook", description="Paper notes", owner_id=user.id))
    db_session.add(Item(title="Beta pencil", description="Graphite sketching", owner_id=user.id))
    db_session.add(Item(title="Gamma folder", description="Plain documents", owner_id=user.id))
    db_session.commit()

    response = client.get("/api/v1/items?search=alpha")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert [item["title"] for item in data["results"]] == ["Alpha notebook"]


def test_list_items_filters_by_owner_name(client, db_session):
    owner = make_user(db_session, email="owner-search@example.com", full_name="Morgan Fields")
    other = make_user(db_session, email="other-search@example.com", full_name="Jordan Rivers")
    db_session.add(Item(title="Notebook", description=None, owner_id=owner.id))
    db_session.add(Item(title="Notebook", description=None, owner_id=other.id))
    db_session.commit()

    response = client.get("/api/v1/items?search=morgan")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["owner_id"] == str(owner.id)


def test_list_items_orders_by_title(client, db_session):
    user = make_user(db_session, email="order-title@example.com")
    for title in ["Charlie", "Bravo", "Alpha"]:
        db_session.add(Item(title=title, description=None, owner_id=user.id))
    db_session.commit()

    response = client.get("/api/v1/items?ordering=title")

    assert response.status_code == 200
    data = response.json()
    assert [item["title"] for item in data["results"]] == ["Alpha", "Bravo", "Charlie"]


def test_list_items_orders_by_owner_name(client, db_session):
    alex = make_user(db_session, email="alex-owner@example.com", full_name="Alex Owner")
    morgan = make_user(db_session, email="morgan-owner@example.com", full_name="Morgan Owner")
    db_session.add(Item(title="Morgan item", description=None, owner_id=morgan.id))
    db_session.add(Item(title="Alex item", description=None, owner_id=alex.id))
    db_session.commit()

    response = client.get("/api/v1/items?ordering=full_name")

    assert response.status_code == 200
    data = response.json()
    assert [item["owner_id"] for item in data["results"]] == [str(alex.id), str(morgan.id)]


def test_list_items_rejects_unknown_ordering(client):
    response = client.get("/api/v1/items?ordering=random")

    assert response.status_code == 422
    assert "Invalid ordering field" in response.json()["detail"]


def test_list_items_search_pagination_links_keep_filter(client, db_session):
    user = make_user(db_session, email="search-pagination@example.com")
    for title in ["Alpha one", "Alpha two", "Alpha three"]:
        db_session.add(Item(title=title, description=None, owner_id=user.id))
    db_session.add(Item(title="Beta one", description=None, owner_id=user.id))
    db_session.commit()

    response = client.get("/api/v1/items?search=alpha&limit=2&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert data["next"] == "http://testserver/api/v1/items?search=alpha&limit=2&offset=2"


def test_create_item_requires_authentication(client):
    response = client.post(
        "/api/v1/items",
        json={"title": "Private item", "description": "Needs auth"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header"


def test_create_item_returns_created_item(client, db_session):
    headers = auth_headers(client, db_session, email="create-item@example.com")

    response = client.post(
        "/api/v1/items",
        json={"title": "Created item", "description": "Created over API"},
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Created item"
    assert data["description"] == "Created over API"
    assert data["owner_id"] is not None


def test_create_item_validates_required_title(client, db_session):
    headers = auth_headers(client, db_session, email="invalid-item@example.com")

    response = client.post(
        "/api/v1/items",
        json={"description": "Missing title"},
        headers=headers,
    )

    assert response.status_code == 422


def test_update_item_allows_owner(client, db_session):
    user = make_user(db_session, email="owner-update@example.com", password="secret")
    item = Item(title="Original", description="Before", owner_id=user.id)
    db_session.add(item)
    db_session.commit()
    access_token, _ = login(client, username=user.email, password="secret")

    response = client.put(
        f"/api/v1/items/{item.id}",
        json={"title": "Updated", "description": "After"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["description"] == "After"


def test_update_item_rejects_non_owner(client, db_session):
    owner = make_user(db_session, email="item-owner@example.com")
    other = make_user(db_session, email="other-user@example.com", password="secret")
    item = Item(title="Owned item", description=None, owner_id=owner.id)
    db_session.add(item)
    db_session.commit()
    access_token, _ = login(client, username=other.email, password="secret")

    response = client.put(
        f"/api/v1/items/{item.id}",
        json={"title": "Not allowed"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed"


def test_delete_item_removes_owned_item(client, db_session):
    user = make_user(db_session, email="delete-owner@example.com", password="secret")
    item = Item(title="Delete me", description=None, owner_id=user.id)
    db_session.add(item)
    db_session.commit()
    item_id = item.id
    access_token, _ = login(client, username=user.email, password="secret")

    response = client.delete(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 204
    db_session.expire_all()
    assert db_session.get(Item, item_id) is None
