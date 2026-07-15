import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_smoke.db")

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as c:
            yield c


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_entitlements_catalog_is_public(client):
    r = await client.get("/v1/entitlements/catalog")
    assert r.status_code == 200
    body = r.json()
    assert "dedicated_ai_coach" in body
    assert body["dedicated_ai_coach"] == ["elite"]
    # universal feature is on all three plans
    assert set(body["standard_chat"]) == {"elite", "premium", "premium_plus"}


async def test_otp_login_flow_and_entitlements(client):
    # Passwordless email OTP auto-registers on first login (ADR-0001 flow).
    start = await client.post(
        "/v1/auth/otp/start",
        json={"destination": "smoke@todate.test", "channel": "email"},
    )
    assert start.status_code == 200
    payload = start.json()
    code = payload["dev_code"]
    assert code is not None  # dev exposes the code; prod would not

    verify = await client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": payload["challenge_id"], "code": code},
    )
    assert verify.status_code == 200
    access = verify.json()["access_token"]
    auth = {"Authorization": f"Bearer {access}"}

    me = await client.get("/v1/users/me", headers=auth)
    assert me.status_code == 200
    assert me.json()["email"] == "smoke@todate.test"
    assert me.json()["account_state"] == "REGISTERED"

    # No subscription => effective plan is free Premium tier.
    ent = await client.get("/v1/entitlements/me", headers=auth)
    assert ent.status_code == 200
    assert ent.json()["effective_plan"] == "premium"
    assert "dedicated_ai_coach" not in ent.json()["features"]


async def test_protected_route_requires_token(client):
    r = await client.get("/v1/users/me")
    assert r.status_code in (401, 403)


async def test_verification_is_blocked(client):
    start = await client.post(
        "/v1/auth/otp/start",
        json={"destination": "vblock@todate.test", "channel": "email"},
    )
    payload = start.json()
    verify = await client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": payload["challenge_id"], "code": payload["dev_code"]},
    )
    auth = {"Authorization": f"Bearer {verify.json()['access_token']}"}
    r = await client.post("/v1/verification-cases", headers=auth)
    assert r.status_code == 501  # blocked pending legal sign-off
