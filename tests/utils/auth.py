from typing import Tuple


def login(client, username: str, password: str) -> Tuple[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data["access_token"], data.get("refresh_token", "")
