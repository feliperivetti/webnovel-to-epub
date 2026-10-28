"""Exercise local token issuance and the real book authentication dependency."""

import time

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.main import verify_internal_token
from src.routes import book_routes, dev_routes


@pytest.fixture
def local_auth(monkeypatch):
    monkeypatch.setattr(dev_routes.settings, "DEBUG", True)
    monkeypatch.setattr(dev_routes.settings, "API_JWT_SECRET", "test-only-secret-" * 4)
    app = FastAPI()
    app.include_router(dev_routes.router)
    app.include_router(book_routes.router, dependencies=[Depends(verify_internal_token)])
    with TestClient(
        app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50000)
    ) as client:
        yield client


def test_local_token_authenticates_book_request(local_auth):
    response = local_auth.post("/dev/token")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    payload = jwt.decode(
        data["access_token"], dev_routes.settings.API_JWT_SECRET, algorithms=["HS256"]
    )
    assert payload["sub"] == "local-test"
    assert payload["action"] == "generate-epub"
    assert payload["exp"] - payload["iat"] == 3600
    assert dev_routes.settings.API_JWT_SECRET not in response.text

    # A missing task distinguishes successful authentication from a rejected JWT.
    path = "/books/download/nonexistent-auth-test"
    assert local_auth.get(path).status_code == 401
    authenticated = local_auth.get(
        path, headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert authenticated.status_code == 404
    assert authenticated.json()["detail"] == "File not ready or task not found."


@pytest.mark.parametrize("case", ["expired", "wrong-secret", "wrong-action"])
def test_book_auth_rejects_invalid_local_tokens(local_auth, case):
    payload = {
        "sub": "local-test", "action": "generate-epub", "exp": int(time.time()) + 3600
    }
    secret = dev_routes.settings.API_JWT_SECRET
    if case == "expired":
        payload["exp"] = int(time.time()) - 60
    elif case == "wrong-secret":
        secret = "different-test-secret-" * 4
    else:
        payload["action"] = "other"
    token = jwt.encode(payload, secret, algorithm="HS256")
    response = local_auth.get(
        "/books/download/nonexistent-auth-test",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == (403 if case == "wrong-action" else 401)


def test_token_issuer_disabled_without_debug(local_auth, monkeypatch):
    monkeypatch.setattr(dev_routes.settings, "DEBUG", False)
    assert local_auth.post("/dev/token").status_code == 404


def test_token_issuer_requires_secret(local_auth, monkeypatch):
    monkeypatch.setattr(dev_routes.settings, "API_JWT_SECRET", "")
    assert local_auth.post("/dev/token").status_code == 409


@pytest.mark.parametrize("host", ["192.0.2.1", "::ffff:192.0.2.1"])
def test_token_issuer_rejects_remote_client(local_auth, host):
    with TestClient(
        local_auth.app, base_url="http://127.0.0.1:8000", client=(host, 50000)
    ) as client:
        response = client.post("/dev/token", headers={"X-Forwarded-For": "127.0.0.1"})
    assert response.status_code == 404


@pytest.mark.parametrize("host", ["localhost", "[::1]"])
def test_token_issuer_accepts_local_hosts(local_auth, host):
    assert local_auth.post("/dev/token", headers={"Host": f"{host}:8000"}).status_code == 200


def test_token_issuer_rejects_nonlocal_host(local_auth):
    response = local_auth.post("/dev/token", headers={"Host": "remote.example"})
    assert response.status_code == 404


@pytest.mark.parametrize("headers", [
    {"Origin": "https://remote.example"},
    {"Origin": "null"},
    {"Referer": "https://remote.example/page"},
])
def test_token_issuer_rejects_remote_pages(local_auth, headers):
    assert local_auth.post("/dev/token", headers=headers).status_code == 403


def test_token_issuer_accepts_swagger_origin(local_auth):
    response = local_auth.post("/dev/token", headers={
        "Origin": "http://127.0.0.1:8000",
        "Referer": "http://127.0.0.1:8000/docs",
    })
    assert response.status_code == 200
