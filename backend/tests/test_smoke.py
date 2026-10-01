import json
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_smoke.db")

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    """Rate-limit counters are process-global; keep them from leaking between
    tests (otherwise unrelated tests start 429-ing once the suite grows)."""
    from app.modules.identity import router as identity_router

    identity_router._otp_start_limiter._hits.clear()
    identity_router._otp_verify_limiter._hits.clear()
    yield


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


async def test_refresh_token_issues_new_access_token(client):
    start = await client.post(
        "/v1/auth/otp/start",
        json={"destination": "refresh@todate.test", "channel": "email"},
    )
    payload = start.json()
    verify = await client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": payload["challenge_id"], "code": payload["dev_code"]},
    )
    tokens = verify.json()

    refreshed = await client.post(
        "/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]
    assert new_access != tokens["access_token"]

    me = await client.get(
        "/v1/users/me", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "refresh@todate.test"

    bad = await client.post("/v1/auth/refresh", json={"refresh_token": "not-a-token"})
    assert bad.status_code == 401


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


ADULT_DOB = "1990-01-01"


async def _login(client, email: str, date_of_birth: str | None = ADULT_DOB) -> dict:
    """Helper: OTP login, then state an adult birth date as onboarding would.

    Pass date_of_birth=None for a member who hasn't completed that step.
    """
    start = await client.post(
        "/v1/auth/otp/start", json={"destination": email, "channel": "email"}
    )
    p = start.json()
    verify = await client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": p["challenge_id"], "code": p["dev_code"]},
    )
    auth = {"Authorization": f"Bearer {verify.json()['access_token']}"}
    if date_of_birth is not None:
        me = await client.get("/v1/users/me", headers=auth)
        if me.json()["date_of_birth"] is None:
            await client.put(
                "/v1/users/me/date-of-birth",
                json={"date_of_birth": date_of_birth},
                headers=auth,
            )
    return auth


async def test_subscription_crud(client):
    auth = await _login(client, "sub@todate.test")

    # No subscription yet → 404
    r = await client.get("/v1/subscriptions/me", headers=auth)
    assert r.status_code == 404

    # Missing payment_token → 422 (schema validation)
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "premium_plus", "billing_cycle": "monthly"},
        headers=auth,
    )
    assert r.status_code == 422

    # Malformed token (not the dev-stub format) → 402, not 409/500
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "premium_plus", "billing_cycle": "monthly", "payment_token": "sk_live_whatever"},
        headers=auth,
    )
    assert r.status_code == 402

    # Create Premium+ monthly
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "premium_plus", "billing_cycle": "monthly", "payment_token": "tok_dev_test"},
        headers=auth,
    )
    assert r.status_code == 201
    sub = r.json()
    assert sub["plan"] == "premium_plus"
    assert sub["status"] == "active"
    assert sub["activation_fee_paid_at"] is not None

    # Duplicate → 409
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "elite", "billing_cycle": "annual", "payment_token": "tok_dev_test"},
        headers=auth,
    )
    assert r.status_code == 409

    # Upgrade to Elite
    r = await client.put(
        "/v1/subscriptions/me", json={"plan": "elite"}, headers=auth
    )
    assert r.status_code == 200
    assert r.json()["plan"] == "elite"

    # Cancel
    r = await client.delete("/v1/subscriptions/me", headers=auth)
    assert r.status_code == 204

    # Now 404 again
    r = await client.get("/v1/subscriptions/me", headers=auth)
    assert r.status_code == 404


async def test_verified_attributes(client):
    auth = await _login(client, "va@todate.test")
    r = await client.get("/v1/users/me/verified-attributes", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["identity_verified"] is False
    assert body["criminal_check_status"] == "pending"
    assert body["eligibility"] == "ineligible"


async def test_profile_photo_upload(client):
    auth = await _login(client, "photo_user@todate.test")
    r = await client.post(
        "/v1/profiles/me/photos",
        files={"file": ("test.jpg", b"fake-image-bytes", "image/jpeg")},
        headers=auth,
    )
    assert r.status_code == 200
    photos = r.json()["photos"]
    assert len(photos) == 1
    assert photos[0].startswith("http://test/uploads/")
    assert photos[0].endswith(".jpg")

    # A second upload appends rather than replacing.
    r = await client.post(
        "/v1/profiles/me/photos",
        files={"file": ("second.png", b"more-fake-bytes", "image/png")},
        headers=auth,
    )
    assert r.status_code == 200
    assert len(r.json()["photos"]) == 2

    # The uploaded file is actually served back.
    r = await client.get(photos[0].replace("http://test", ""))
    assert r.status_code == 200
    assert r.content == b"fake-image-bytes"


async def test_matchmaking(client):
    auth_a = await _login(client, "match_a@todate.test")
    auth_b = await _login(client, "match_b@todate.test")

    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    # Discovery is empty until a profile is manually activated by an admin
    # (see test_admin_activates_profile_for_discovery for that flow).
    r = await client.get("/v1/discovery", headers=auth_a)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Create match
    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    assert r.status_code == 201
    match = r.json()
    assert match["state"] == "CHAT_OPEN"
    match_id = match["id"]

    # Duplicate → 409
    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    assert r.status_code == 409

    # Both users can see the match
    r = await client.get("/v1/matches", headers=auth_a)
    assert any(m["id"] == match_id for m in r.json())

    r = await client.get("/v1/matches", headers=auth_b)
    assert any(m["id"] == match_id for m in r.json())

    # Get by id
    r = await client.get(f"/v1/matches/{match_id}", headers=auth_a)
    assert r.status_code == 200

    # Third user cannot access
    auth_c = await _login(client, "match_c@todate.test")
    r = await client.get(f"/v1/matches/{match_id}", headers=auth_c)
    assert r.status_code == 404


async def test_structured_full_flow(client):
    """Exercises the complete date progression state machine end-to-end."""
    auth_a = await _login(client, "flow_a@todate.test")
    auth_b = await _login(client, "flow_b@todate.test")
    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    # Create match
    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    assert r.status_code == 201
    match_id = r.json()["id"]

    # --- CHAT_OPEN: messaging works ---
    r = await client.post(
        f"/v1/matches/{match_id}/messages",
        json={"body": "Hey, how's it going?"},
        headers=auth_a,
    )
    assert r.status_code == 201

    r = await client.post(
        f"/v1/matches/{match_id}/messages",
        json={"body": "Pretty well, thanks!"},
        headers=auth_b,
    )
    assert r.status_code == 201

    r = await client.get(f"/v1/matches/{match_id}/conversation", headers=auth_a)
    assert r.status_code == 200
    conv = r.json()
    assert len(conv["messages"]) == 2
    assert conv["state"] == "CHAT_OPEN"

    # --- Trigger date prompt (system action) ---
    r = await client.post(f"/v1/matches/{match_id}/date-prompt", headers=auth_a)
    assert r.status_code == 200
    assert r.json()["state"] == "DATE_PROMPT_PENDING"

    # Messaging blocked in DATE_PROMPT_PENDING
    r = await client.post(
        f"/v1/matches/{match_id}/messages",
        json={"body": "Can still chat?"},
        headers=auth_a,
    )
    assert r.status_code == 409

    # --- date prompt state: prompt active, no response yet ---
    r = await client.get(f"/v1/matches/{match_id}/date-prompt", headers=auth_a)
    assert r.status_code == 200
    prompt = r.json()
    assert prompt["active"] is True
    assert prompt["my_choice"] is None
    assert prompt["resolved"] is False
    assert prompt["counterpart_choice"] is None

    # --- User A responds YES ---
    r = await client.post(
        f"/v1/matches/{match_id}/date-prompt/response",
        json={"choice": "yes"},
        headers=auth_a,
    )
    assert r.status_code == 200
    state_a = r.json()
    assert state_a["my_choice"] == "yes"
    assert state_a["resolved"] is False  # B hasn't answered yet
    assert state_a["counterpart_choice"] is None  # not revealed yet

    # Duplicate response is rejected
    r = await client.post(
        f"/v1/matches/{match_id}/date-prompt/response",
        json={"choice": "yes"},
        headers=auth_a,
    )
    assert r.status_code == 409

    # --- User B responds YES → match becomes SCHEDULE_READY ---
    r = await client.post(
        f"/v1/matches/{match_id}/date-prompt/response",
        json={"choice": "yes"},
        headers=auth_b,
    )
    assert r.status_code == 200
    state_b = r.json()
    assert state_b["resolved"] is True
    assert state_b["counterpart_choice"] == "yes"
    assert state_b["resolved_state"] == "SCHEDULE_READY"

    # Match state confirmed
    r = await client.get(f"/v1/matches/{match_id}", headers=auth_a)
    assert r.json()["state"] == "SCHEDULE_READY"

    # --- Venue recommendations ---
    r = await client.get(
        f"/v1/matches/{match_id}/venue-recommendations", headers=auth_a
    )
    assert r.status_code == 200
    venues = r.json()
    assert len(venues) > 0
    assert all("name" in v and "price_tier" in v for v in venues)

    # --- Submit availability ---
    r = await client.post(
        f"/v1/matches/{match_id}/availability",
        json={"slots": ["2026-08-01T19:00:00Z", "2026-08-03T20:00:00Z"]},
        headers=auth_a,
    )
    assert r.status_code == 200
    assert r.json()["slots"] == ["2026-08-01T19:00:00Z", "2026-08-03T20:00:00Z"]

    # --- No plan yet: GET returns null, not 404 ---
    r = await client.get(f"/v1/matches/{match_id}/date-plan", headers=auth_a)
    assert r.status_code == 200
    assert r.json() is None

    # --- Confirm date plan ---
    r = await client.post(
        f"/v1/matches/{match_id}/date-plan",
        json={
            "venue_name": "The Penthouse",
            "venue_address": "1 Luxury Ave",
            "scheduled_at": "2026-08-01T19:00:00Z",
        },
        headers=auth_a,
    )
    assert r.status_code == 201
    plan = r.json()
    assert plan["venue_name"] == "The Penthouse"
    assert plan["outcome"] is None

    # --- Plan now survives a "restart": GET returns it (other participant too) ---
    r = await client.get(f"/v1/matches/{match_id}/date-plan", headers=auth_b)
    assert r.status_code == 200
    assert r.json()["venue_name"] == "The Penthouse"

    # Duplicate date plan rejected
    r = await client.post(
        f"/v1/matches/{match_id}/date-plan",
        json={"venue_name": "Other", "scheduled_at": "2026-08-02T19:00:00Z"},
        headers=auth_a,
    )
    assert r.status_code == 409

    # --- Record outcome ---
    r = await client.post(
        f"/v1/matches/{match_id}/date-plan/outcome",
        json={"outcome": "went_well"},
        headers=auth_b,
    )
    assert r.status_code == 200
    assert r.json()["outcome"] == "went_well"

    # Duplicate outcome rejected
    r = await client.post(
        f"/v1/matches/{match_id}/date-plan/outcome",
        json={"outcome": "cancelled"},
        headers=auth_a,
    )
    assert r.status_code == 409


async def test_intelligent_basic_tier(client):
    """Premium users (default) get basic insights and score without factors."""
    auth_a = await _login(client, "intel_a@todate.test")
    auth_b = await _login(client, "intel_b@todate.test")
    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    match_id = r.json()["id"]

    # Exchange a few messages to generate signals.
    for body in ["Hey there!", "How's your week going?", "Great, thanks for asking!"]:
        await client.post(
            f"/v1/matches/{match_id}/messages", json={"body": body}, headers=auth_a
        )
    await client.post(
        f"/v1/matches/{match_id}/messages",
        json={"body": "Really well! Excited to chat more."},
        headers=auth_b,
    )

    # --- Coaching insights ---
    r = await client.get(f"/v1/matches/{match_id}/coaching-insights", headers=auth_a)
    assert r.status_code == 200
    body = r.json()
    assert body["insight_tier"] == "basic"
    assert len(body["insights"]) >= 1
    assert all(i["tier"] == "basic" for i in body["insights"])

    # --- Compatibility score (basic: no factors) ---
    r = await client.get(
        f"/v1/matches/{match_id}/compatibility-score", headers=auth_a
    )
    assert r.status_code == 200
    sc = r.json()
    assert 0 <= sc["score"] <= 100
    assert sc["factors"] is None       # not exposed at basic tier
    assert sc["signals_summary"] is None


async def test_intelligent_extended_tier(client):
    """Premium+ users get factor breakdown in score and extended insights."""
    auth_a = await _login(client, "ext_a@todate.test")
    auth_b = await _login(client, "ext_b@todate.test")
    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    # Upgrade to Premium+
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "premium_plus", "billing_cycle": "monthly", "payment_token": "tok_dev_test"},
        headers=auth_a,
    )
    assert r.status_code == 201

    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    match_id = r.json()["id"]

    for msg in ["Hello!", "Lovely to meet you.", "What do you enjoy doing?"]:
        await client.post(
            f"/v1/matches/{match_id}/messages", json={"body": msg}, headers=auth_a
        )
    await client.post(
        f"/v1/matches/{match_id}/messages",
        json={"body": "I love hiking and cooking — you?"},
        headers=auth_b,
    )

    r = await client.get(
        f"/v1/matches/{match_id}/compatibility-score", headers=auth_a
    )
    assert r.status_code == 200
    sc = r.json()
    assert sc["factors"] is not None
    assert "engagement_balance" in sc["factors"]
    assert sc["signals_summary"] is None  # only dedicated gets this

    r = await client.get(f"/v1/matches/{match_id}/coaching-insights", headers=auth_a)
    assert r.status_code == 200
    body = r.json()
    assert body["insight_tier"] == "extended"
    tiers_seen = {i["tier"] for i in body["insights"]}
    assert "basic" in tiers_seen  # always includes basic


async def test_intelligent_dedicated_tier(client):
    """Elite users get full signals summary and dedicated coaching."""
    auth_a = await _login(client, "ded_a@todate.test")
    auth_b = await _login(client, "ded_b@todate.test")
    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "elite", "billing_cycle": "annual", "payment_token": "tok_dev_test"},
        headers=auth_a,
    )
    assert r.status_code == 201

    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    match_id = r.json()["id"]

    # Send several messages to build meaningful signals.
    long_msg = "I've been thinking a lot about what I want in a relationship. " * 3
    for _ in range(5):
        await client.post(
            f"/v1/matches/{match_id}/messages",
            json={"body": long_msg},
            headers=auth_a,
        )
        await client.post(
            f"/v1/matches/{match_id}/messages",
            json={"body": "That's really interesting, tell me more!"},
            headers=auth_b,
        )

    r = await client.get(
        f"/v1/matches/{match_id}/compatibility-score", headers=auth_a
    )
    assert r.status_code == 200
    sc = r.json()
    assert sc["factors"] is not None
    assert sc["signals_summary"] is not None
    assert "my_message_count" in sc["signals_summary"]
    assert "my_avg_message_length" in sc["signals_summary"]

    r = await client.get(f"/v1/matches/{match_id}/coaching-insights", headers=auth_a)
    assert r.status_code == 200
    body = r.json()
    assert body["insight_tier"] == "dedicated"

    # Non-participant cannot access
    auth_c = await _login(client, "ded_c@todate.test")
    r = await client.get(
        f"/v1/matches/{match_id}/coaching-insights", headers=auth_c
    )
    assert r.status_code == 404


async def test_date_prompt_no_closes_match(client):
    """Any No in the prompt cleanly closes the conversation."""
    auth_a = await _login(client, "no_a@todate.test")
    auth_b = await _login(client, "no_b@todate.test")
    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    match_id = r.json()["id"]

    await client.post(f"/v1/matches/{match_id}/date-prompt", headers=auth_a)

    await client.post(
        f"/v1/matches/{match_id}/date-prompt/response",
        json={"choice": "yes"},
        headers=auth_a,
    )
    r = await client.post(
        f"/v1/matches/{match_id}/date-prompt/response",
        json={"choice": "no"},
        headers=auth_b,
    )
    assert r.json()["resolved_state"] == "CLOSED"

    r = await client.get(f"/v1/matches/{match_id}", headers=auth_a)
    assert r.json()["state"] == "CLOSED"


async def test_date_prompt_maybe_extends_chat(client):
    """YES+MAYBE extends the chat window."""
    auth_a = await _login(client, "maybe_a@todate.test")
    auth_b = await _login(client, "maybe_b@todate.test")
    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    r = await client.post(
        "/v1/matches", json={"target_user_id": user_b_id}, headers=auth_a
    )
    match_id = r.json()["id"]
    await client.post(f"/v1/matches/{match_id}/date-prompt", headers=auth_a)

    await client.post(
        f"/v1/matches/{match_id}/date-prompt/response",
        json={"choice": "yes"},
        headers=auth_a,
    )
    r = await client.post(
        f"/v1/matches/{match_id}/date-prompt/response",
        json={"choice": "maybe"},
        headers=auth_b,
    )
    assert r.json()["resolved_state"] == "EXTENDED_CHAT"

    # Messaging is open again in EXTENDED_CHAT
    r = await client.post(
        f"/v1/matches/{match_id}/messages",
        json={"body": "Let me think about it..."},
        headers=auth_b,
    )
    assert r.status_code == 201


def _login_sync(tc: TestClient, email: str) -> tuple[str, dict]:
    start = tc.post("/v1/auth/otp/start", json={"destination": email, "channel": "email"})
    p = start.json()
    verify = tc.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": p["challenge_id"], "code": p["dev_code"]},
    )
    token = verify.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    if tc.get("/v1/users/me", headers=auth).json()["date_of_birth"] is None:
        tc.put("/v1/users/me/date-of-birth", json={"date_of_birth": ADULT_DOB}, headers=auth)
    return token, auth


def test_conversation_websocket_delivers_realtime_messages():
    with TestClient(app) as tc:
        token_a, auth_a = _login_sync(tc, "ws_a@todate.test")
        token_b, _ = _login_sync(tc, "ws_b@todate.test")

        me_b = tc.get(
            "/v1/users/me", headers={"Authorization": f"Bearer {token_b}"}
        ).json()

        match = tc.post(
            "/v1/matches", json={"target_user_id": me_b["id"]}, headers=auth_a
        )
        assert match.status_code == 201
        match_id = match.json()["id"]

        # No token → rejected before joining the broadcast group.
        with pytest.raises(WebSocketDisconnect):
            with tc.websocket_connect(f"/v1/matches/{match_id}/ws"):
                pass

        with (
            tc.websocket_connect(f"/v1/matches/{match_id}/ws?token={token_a}") as ws_a,
            tc.websocket_connect(f"/v1/matches/{match_id}/ws?token={token_b}") as ws_b,
        ):
            ws_a.send_text(json.dumps({"body": "hello from A"}))

            payload_a = ws_a.receive_json()
            payload_b = ws_b.receive_json()
            assert payload_a == payload_b
            assert payload_a["type"] == "message"
            assert payload_a["data"]["body"] == "hello from A"

        # REST reflects the WS-sent message too.
        conv = tc.get(f"/v1/matches/{match_id}/conversation", headers=auth_a).json()
        assert len(conv["messages"]) == 1
        assert conv["messages"][0]["body"] == "hello from A"


async def test_admin_moderation_and_invites(client):
    from app.config import get_settings

    settings = get_settings()

    settings.bootstrap_admin_emails = "admin_user@todate.test"
    try:
        auth_admin = await _login(client, "admin_user@todate.test")
    finally:
        settings.bootstrap_admin_emails = ""

    me_admin = await client.get("/v1/users/me", headers=auth_admin)
    assert me_admin.json()["is_admin"] is True

    auth_reporter = await _login(client, "reporter@todate.test")
    auth_target = await _login(client, "reported_user@todate.test")
    target_id = (await client.get("/v1/users/me", headers=auth_target)).json()["id"]

    # Non-admin can't see the queue or act on cases.
    r = await client.get("/v1/admin/moderation-cases", headers=auth_reporter)
    assert r.status_code == 403

    # Any member can report.
    r = await client.post(
        "/v1/admin/moderation-cases",
        json={"subject_type": "user", "subject_id": target_id, "reason": "spam"},
        headers=auth_reporter,
    )
    assert r.status_code == 201
    case = r.json()
    assert case["status"] == "open"
    assert case["reporter_id"] != target_id

    # Admin sees it in the open queue.
    r = await client.get("/v1/admin/moderation-cases?status=open", headers=auth_admin)
    assert r.status_code == 200
    assert any(c["id"] == case["id"] for c in r.json())

    # Non-admin can't action it.
    r = await client.post(
        f"/v1/admin/moderation-cases/{case['id']}/action",
        json={"decision": "actioned"},
        headers=auth_reporter,
    )
    assert r.status_code == 403

    # Admin actions it.
    r = await client.post(
        f"/v1/admin/moderation-cases/{case['id']}/action",
        json={"decision": "actioned"},
        headers=auth_admin,
    )
    assert r.status_code == 200
    resolved = r.json()
    assert resolved["status"] == "actioned"
    assert resolved["resolved_at"] is not None

    # Re-resolving an already-resolved case is rejected.
    r = await client.post(
        f"/v1/admin/moderation-cases/{case['id']}/action",
        json={"decision": "dismissed"},
        headers=auth_admin,
    )
    assert r.status_code == 409

    # The action left an audit trail.
    r = await client.get(f"/v1/admin/audit-events?subject_id={target_id}", headers=auth_admin)
    assert r.status_code == 200
    assert any(e["event_type"] == "moderation_case_actioned" for e in r.json())

    # --- Beta invites ---
    r = await client.post(
        "/v1/admin/beta-invites", json={"email": "invited@todate.test"}, headers=auth_admin
    )
    assert r.status_code == 201
    assert r.json()["email"] == "invited@todate.test"
    assert r.json()["redeemed_at"] is None

    # Non-admin can't create invites.
    r = await client.post(
        "/v1/admin/beta-invites", json={"email": "x@todate.test"}, headers=auth_reporter
    )
    assert r.status_code == 403

    # Duplicate invite for the same email is rejected.
    r = await client.post(
        "/v1/admin/beta-invites", json={"email": "invited@todate.test"}, headers=auth_admin
    )
    assert r.status_code == 409


async def test_admin_activates_profile_for_discovery(client):
    """Verification is blocked, so an admin manually activating a profile is
    the only path to PROFILE_ACTIVE — and thus the only way to show up in
    another member's discovery feed."""
    from app.config import get_settings

    settings = get_settings()

    settings.bootstrap_admin_emails = "curator@todate.test"
    try:
        auth_admin = await _login(client, "curator@todate.test")
    finally:
        settings.bootstrap_admin_emails = ""

    auth_new_member = await _login(client, "new_member@todate.test")
    me = await client.get("/v1/users/me", headers=auth_new_member)
    member = me.json()
    assert member["account_state"] == "REGISTERED"

    # Non-admin can't see the curation queue or activate.
    r = await client.get("/v1/admin/users", headers=auth_new_member)
    assert r.status_code == 403
    r = await client.post(f"/v1/admin/users/{member['id']}/activate", headers=auth_new_member)
    assert r.status_code == 403

    # Admin finds them in the REGISTERED queue.
    r = await client.get("/v1/admin/users?account_state=REGISTERED", headers=auth_admin)
    assert r.status_code == 200
    assert any(u["id"] == member["id"] for u in r.json())

    # Admin activates.
    r = await client.post(f"/v1/admin/users/{member['id']}/activate", headers=auth_admin)
    assert r.status_code == 200
    assert r.json()["account_state"] == "PROFILE_ACTIVE"

    # Re-activating is rejected.
    r = await client.post(f"/v1/admin/users/{member['id']}/activate", headers=auth_admin)
    assert r.status_code == 409

    # No longer in the REGISTERED queue.
    r = await client.get("/v1/admin/users?account_state=REGISTERED", headers=auth_admin)
    assert not any(u["id"] == member["id"] for u in r.json())

    # Now visible in another member's discovery feed.
    auth_seeker = await _login(client, "seeker@todate.test")
    r = await client.get("/v1/discovery", headers=auth_seeker)
    assert r.status_code == 200
    assert any(p["user_id"] == member["id"] for p in r.json())


async def test_discovery_income_and_education_filters(client):
    from app.config import get_settings

    settings = get_settings()

    settings.bootstrap_admin_emails = "filter_curator@todate.test"
    try:
        auth_admin = await _login(client, "filter_curator@todate.test")
    finally:
        settings.bootstrap_admin_emails = ""

    # Two candidates: one high income tier + PhD, one low income tier + BA.
    auth_high = await _login(client, "high_earner@todate.test")
    high_id = (await client.get("/v1/users/me", headers=auth_high)).json()["id"]
    auth_low = await _login(client, "low_earner@todate.test")
    low_id = (await client.get("/v1/users/me", headers=auth_low)).json()["id"]

    for uid in (high_id, low_id):
        r = await client.post(f"/v1/admin/users/{uid}/activate", headers=auth_admin)
        assert r.status_code == 200

    r = await client.post(
        f"/v1/admin/users/{high_id}/verified-attributes",
        json={"income_percentile_tier": "90+", "education_level": "PhD"},
        headers=auth_admin,
    )
    assert r.status_code == 200
    assert r.json()["income_percentile_tier"] == "90+"

    r = await client.post(
        f"/v1/admin/users/{low_id}/verified-attributes",
        json={"income_percentile_tier": "0-25", "education_level": "BA"},
        headers=auth_admin,
    )
    assert r.status_code == 200

    # Non-admin can't set verified attributes.
    r = await client.post(
        f"/v1/admin/users/{low_id}/verified-attributes",
        json={"income_percentile_tier": "90+"},
        headers=auth_high,
    )
    assert r.status_code == 403

    # A free-Premium seeker (no subscription) can't use either filter.
    auth_seeker = await _login(client, "filter_seeker@todate.test")
    r = await client.get(
        "/v1/discovery", params={"min_income_tier": "90+"}, headers=auth_seeker
    )
    assert r.status_code == 403
    r = await client.get(
        "/v1/discovery", params={"education_level": "PhD"}, headers=auth_seeker
    )
    assert r.status_code == 403

    # Upgrade to Premium+ — filters unlock.
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "premium_plus", "billing_cycle": "monthly", "payment_token": "tok_dev_test"},
        headers=auth_seeker,
    )
    assert r.status_code == 201

    # Income filter: "90+" minimum excludes the 0-25 candidate.
    r = await client.get(
        "/v1/discovery", params={"min_income_tier": "90+"}, headers=auth_seeker
    )
    assert r.status_code == 200
    ids = {p["user_id"] for p in r.json()}
    assert high_id in ids
    assert low_id not in ids

    # A lower threshold includes both.
    r = await client.get(
        "/v1/discovery", params={"min_income_tier": "0-25"}, headers=auth_seeker
    )
    assert r.status_code == 200
    ids = {p["user_id"] for p in r.json()}
    assert high_id in ids
    assert low_id in ids

    # Education filter is an exact match.
    r = await client.get(
        "/v1/discovery", params={"education_level": "PhD"}, headers=auth_seeker
    )
    assert r.status_code == 200
    ids = {p["user_id"] for p in r.json()}
    assert high_id in ids
    assert low_id not in ids


async def test_production_registration_requires_invite(client):
    from app.config import get_settings

    settings = get_settings()

    # Get a dev OTP code while not in production (production never returns one).
    start = await client.post(
        "/v1/auth/otp/start",
        json={"destination": "uninvited@todate.test", "channel": "email"},
    )
    challenge_id, code = start.json()["challenge_id"], start.json()["dev_code"]

    settings.environment = "production"
    try:
        r = await client.post(
            "/v1/auth/otp/verify", json={"challenge_id": challenge_id, "code": code}
        )
        assert r.status_code == 401
        assert "invite" in r.json()["detail"].lower()
    finally:
        settings.environment = "development"

    # Bootstrap an admin (in dev mode) to issue the invite.
    settings.bootstrap_admin_emails = "prod_admin@todate.test"
    try:
        auth_admin = await _login(client, "prod_admin@todate.test")
    finally:
        settings.bootstrap_admin_emails = ""

    r = await client.post(
        "/v1/admin/beta-invites",
        json={"email": "uninvited@todate.test"},
        headers=auth_admin,
    )
    assert r.status_code == 201

    # Same email, fresh challenge, now under production with an invite.
    start2 = await client.post(
        "/v1/auth/otp/start",
        json={"destination": "uninvited@todate.test", "channel": "email"},
    )
    challenge_id2, code2 = start2.json()["challenge_id"], start2.json()["dev_code"]

    settings.environment = "production"
    try:
        r = await client.post(
            "/v1/auth/otp/verify", json={"challenge_id": challenge_id2, "code": code2}
        )
        assert r.status_code == 200
    finally:
        settings.environment = "development"


async def test_production_never_returns_the_otp_code(client):
    """The one-time code must never appear in the API response in production.

    If it did, the app would be an open door: submit any email, read the code
    straight back, and you're signed in as that person. `ENVIRONMENT=production`
    is the switch the private beta depends on, so it's asserted here rather than
    trusted.
    """
    from app.config import get_settings

    settings = get_settings()

    settings.environment = "production"
    try:
        r = await client.post(
            "/v1/auth/otp/start",
            json={"destination": "prodcode@todate.test", "channel": "email"},
        )
        assert r.status_code == 200
        assert r.json()["dev_code"] is None
    finally:
        settings.environment = "development"

    # ...and still returned outside production, or the demo flow breaks.
    r = await client.post(
        "/v1/auth/otp/start",
        json={"destination": "prodcode@todate.test", "channel": "email"},
    )
    assert r.json()["dev_code"] is not None


async def test_demo_mode_off_does_not_auto_activate(client):
    """With DEMO_MODE off, a new account stays unvetted and out of discovery.

    DEMO_MODE fakes the whole Vetted pillar (auto-activation + seeded verified
    facts). If its gate regressed, unverified people would silently appear in
    everyone's discovery feed.
    """
    from app.config import get_settings

    settings = get_settings()
    settings.demo_mode = False
    try:
        auth = await _login(client, "notdemo@todate.test")

        me = await client.get("/v1/users/me", headers=auth)
        assert me.json()["account_state"] == "REGISTERED"

        va = await client.get("/v1/users/me/verified-attributes", headers=auth)
        body = va.json()
        assert body["identity_verified"] is False
        assert body["criminal_check_status"] == "pending"
        assert body["eligibility"] == "ineligible"
        assert body["income_percentile_tier"] is None
    finally:
        settings.demo_mode = False


async def test_health_reports_database_state(client):
    """The host routes traffic on /health, so it must reflect the database."""
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


async def test_otp_endpoints_are_rate_limited(client):
    """A 6-digit code with unlimited guesses is brute-forceable in minutes.

    Both OTP endpoints are throttled per client address; exceeding the window
    must return 429 rather than continuing to accept attempts.
    """
    from app.modules.identity import router as identity_router

    start_limiter = identity_router._otp_start_limiter
    verify_limiter = identity_router._otp_verify_limiter

    # Isolate from other tests' hits against the shared in-process counters.
    start_limiter._hits.clear()
    verify_limiter._hits.clear()
    try:
        allowed = start_limiter.max_requests
        for _ in range(allowed):
            r = await client.post(
                "/v1/auth/otp/start",
                json={"destination": "flood@todate.test", "channel": "email"},
            )
            assert r.status_code == 200

        r = await client.post(
            "/v1/auth/otp/start",
            json={"destination": "flood@todate.test", "channel": "email"},
        )
        assert r.status_code == 429

        # Brute-forcing the code is throttled too.
        for _ in range(verify_limiter.max_requests):
            await client.post(
                "/v1/auth/otp/verify",
                json={"challenge_id": str(uuid.uuid4()), "code": "000000"},
            )
        r = await client.post(
            "/v1/auth/otp/verify",
            json={"challenge_id": str(uuid.uuid4()), "code": "000000"},
        )
        assert r.status_code == 429
    finally:
        start_limiter._hits.clear()
        verify_limiter._hits.clear()


# ---------------------------------------------------------------------------
# Release readiness: blocking, age gate, account deletion, push, version gate
# ---------------------------------------------------------------------------


async def _user_id(client, auth) -> str:
    return (await client.get("/v1/users/me", headers=auth)).json()["id"]


async def _activate(client, *user_ids):
    """Make users discoverable the way a curator would."""
    from app.config import get_settings

    settings = get_settings()
    settings.bootstrap_admin_emails = "release_admin@todate.test"
    try:
        admin = await _login(client, "release_admin@todate.test")
    finally:
        settings.bootstrap_admin_emails = ""
    for uid in user_ids:
        await client.post(f"/v1/admin/users/{uid}/activate", headers=admin)


async def test_blocking_hides_both_ways_and_ends_the_conversation(client):
    a = await _login(client, "blk_a@todate.test")
    b = await _login(client, "blk_b@todate.test")
    a_id, b_id = await _user_id(client, a), await _user_id(client, b)
    await _activate(client, a_id, b_id)

    match = (await client.post("/v1/matches", json={"target_user_id": b_id}, headers=a)).json()
    assert (await client.post(f"/v1/matches/{match['id']}/messages", json={"body": "hi"}, headers=b)).status_code == 201

    # Validation paths
    assert (await client.post(f"/v1/users/{a_id}/block", headers=a)).status_code == 400
    assert (await client.post(f"/v1/users/{uuid.uuid4()}/block", headers=a)).status_code == 404

    assert (await client.post(f"/v1/users/{b_id}/block", headers=a)).status_code == 204
    assert (await client.post(f"/v1/users/{b_id}/block", headers=a)).status_code == 204  # idempotent
    assert (await client.get("/v1/users/me/blocks", headers=a)).json() == [b_id]

    # The conversation is over — for both of them.
    assert (await client.get(f"/v1/matches/{match['id']}", headers=a)).json()["state"] == "CLOSED"
    assert (await client.post(f"/v1/matches/{match['id']}/messages", json={"body": "?"}, headers=b)).status_code == 409

    # Invisible in both directions, and indistinguishable from "doesn't exist".
    for viewer, other in ((a, b_id), (b, a_id)):
        assert other not in {p["user_id"] for p in (await client.get("/v1/discovery", headers=viewer)).json()}
        r = await client.get(f"/v1/profiles/{other}", headers=viewer)
        assert r.status_code == 404 and r.json()["detail"] == "profile not found"

    # Blocking someone you never matched with (e.g. from their profile) must
    # hide them too. A and B above were matched, which hides them regardless,
    # so this pair is what actually exercises the block filter.
    c = await _login(client, "blk_c@todate.test")
    c_id = await _user_id(client, c)
    await _activate(client, c_id)
    assert c_id in {p["user_id"] for p in (await client.get("/v1/discovery", headers=b)).json()}
    await client.post(f"/v1/users/{c_id}/block", headers=b)
    assert c_id not in {p["user_id"] for p in (await client.get("/v1/discovery", headers=b)).json()}
    assert b_id not in {p["user_id"] for p in (await client.get("/v1/discovery", headers=c)).json()}

    # The blocked person can't start a new match either, and isn't told why.
    r = await client.post("/v1/matches", json={"target_user_id": b_id}, headers=c)
    assert r.status_code == 409 and r.json()["detail"] == "cannot match with this user"

    # Unblocking restores visibility; the closed match stays closed.
    assert (await client.delete(f"/v1/users/{b_id}/block", headers=a)).status_code == 204
    assert (await client.get("/v1/users/me/blocks", headers=a)).json() == []
    assert (await client.get(f"/v1/profiles/{b_id}", headers=a)).status_code == 200
    assert (await client.get(f"/v1/matches/{match['id']}", headers=a)).json()["state"] == "CLOSED"


async def test_age_gate_requires_an_adult_birth_date(client):
    from app.common.age import adult_birthdate_cutoff

    no_dob = await _login(client, "nodob@todate.test", date_of_birth=None)
    adult = await _login(client, "adult@todate.test")
    no_dob_id = await _user_id(client, no_dob)

    # Nothing that puts you in front of other members without a stated age.
    for r in (
        await client.get("/v1/discovery", headers=no_dob),
        await client.post("/v1/matches", json={"target_user_id": await _user_id(client, adult)}, headers=no_dob),
    ):
        assert r.status_code == 403 and r.json()["detail"] == "date of birth required"

    # ...and nobody can match with you either.
    r = await client.post("/v1/matches", json={"target_user_id": no_dob_id}, headers=adult)
    assert r.status_code == 409

    # Implausible dates are rejected without using up the one attempt.
    assert (await client.put("/v1/users/me/date-of-birth", json={"date_of_birth": "2999-01-01"}, headers=no_dob)).status_code == 422

    # Turning 18 today counts.
    exactly_18 = adult_birthdate_cutoff().isoformat()
    r = await client.put("/v1/users/me/date-of-birth", json={"date_of_birth": exactly_18}, headers=no_dob)
    assert r.status_code == 200 and r.json()["date_of_birth"] == exactly_18
    assert (await client.get("/v1/discovery", headers=no_dob)).status_code == 200

    # Set once: can't be changed to retry.
    r = await client.put("/v1/users/me/date-of-birth", json={"date_of_birth": "1980-01-01"}, headers=no_dob)
    assert r.status_code == 409


async def test_underage_answer_suspends_the_account(client):
    from datetime import timedelta

    import sqlalchemy as sa

    from app.common.age import adult_birthdate_cutoff
    from app.db import SessionLocal
    from app.modules.admin.models import AuditEvent
    from app.modules.identity.models import User

    minor = await _login(client, "minor@todate.test", date_of_birth=None)
    minor_id = await _user_id(client, minor)
    one_day_short = (adult_birthdate_cutoff() + timedelta(days=1)).isoformat()

    r = await client.put("/v1/users/me/date-of-birth", json={"date_of_birth": one_day_short}, headers=minor)
    assert r.status_code == 403

    # Locked out: the existing token stops working, and so does logging in again.
    r = await client.get("/v1/users/me", headers=minor)
    assert r.status_code == 403 and r.json()["detail"] == "this account is not active"
    start = (await client.post("/v1/auth/otp/start", json={"destination": "minor@todate.test", "channel": "email"})).json()
    r = await client.post("/v1/auth/otp/verify", json={"challenge_id": start["challenge_id"], "code": start["dev_code"]})
    assert r.status_code == 401

    async with SessionLocal() as s:
        user = await s.get(User, uuid.UUID(minor_id))
        assert user.status.value == "suspended"
        assert user.date_of_birth is None  # a minor's birth date is not kept
        events = (await s.scalars(sa.select(AuditEvent).where(AuditEvent.subject_id == user.id))).all()
        assert "account_suspended_underage" in {e.event_type for e in events}


async def test_account_deletion_anonymizes_and_keeps_compliance_records(client):
    import os

    import sqlalchemy as sa

    from app.config import get_settings
    from app.db import SessionLocal
    from app.modules.admin.models import AuditEvent, BetaInvite
    from app.modules.identity.models import OtpChallenge, Profile, User, VerifiedAttributes
    from app.modules.notifications.models import PushToken
    from app.modules.structured.models import Message

    settings = get_settings()
    email = "leaving@todate.test"

    # A beta invite whose audit event carries the raw email.
    settings.bootstrap_admin_emails = "del_admin@todate.test"
    try:
        admin = await _login(client, "del_admin@todate.test")
    finally:
        settings.bootstrap_admin_emails = ""
    assert (await client.post("/v1/admin/beta-invites", json={"email": email}, headers=admin)).status_code == 201

    me = await _login(client, email)
    other = await _login(client, "staying@todate.test")
    me_id, other_id = await _user_id(client, me), await _user_id(client, other)
    await _activate(client, me_id, other_id)

    await client.put("/v1/profiles/me", json={"display_name": "Leaving", "bio": "bye", "city_market": "NYC", "interests": ["x"]}, headers=me)
    photo = (await client.post("/v1/profiles/me/photos", files={"file": ("p.jpg", b"img", "image/jpeg")}, headers=me)).json()["photos"][0]
    photo_path = settings.upload_dir + "/" + photo.rsplit("/", 1)[-1]
    await client.post("/v1/users/me/push-tokens", json={"token": "ExponentPushToken[leaving]", "platform": "ios"}, headers=me)
    await client.post("/v1/subscriptions", json={"plan": "elite", "billing_cycle": "monthly", "payment_token": "tok_dev_x"}, headers=me)

    match = (await client.post("/v1/matches", json={"target_user_id": other_id}, headers=me)).json()
    await client.post(f"/v1/matches/{match['id']}/messages", json={"body": "mine"}, headers=me)
    await client.post(f"/v1/matches/{match['id']}/messages", json={"body": "theirs"}, headers=other)
    start = (await client.post("/v1/auth/otp/start", json={"destination": email, "channel": "email"})).json()
    refresh = (await client.post("/v1/auth/otp/verify", json={"challenge_id": start["challenge_id"], "code": start["dev_code"]})).json()["refresh_token"]

    assert os.path.exists(photo_path)

    assert (await client.delete("/v1/users/me", headers=me)).status_code == 204

    # Every credential the person held stops working.
    assert (await client.get("/v1/users/me", headers=me)).status_code == 401
    assert (await client.post("/v1/auth/refresh", json={"refresh_token": refresh})).status_code == 401

    # The counterpart keeps their side of the conversation, sees it closed,
    # and can no longer find the deleted person.
    conv = (await client.get(f"/v1/matches/{match['id']}/conversation", headers=other)).json()
    assert conv["state"] == "CLOSED"
    assert [m["body"] for m in conv["messages"]] == ["theirs"]
    assert (await client.get(f"/v1/profiles/{me_id}", headers=other)).status_code == 404
    assert me_id not in {p["user_id"] for p in (await client.get("/v1/discovery", headers=other)).json()}

    assert not os.path.exists(photo_path)

    async with SessionLocal() as s:
        uid = uuid.UUID(me_id)
        user = await s.get(User, uid)
        assert user.status.value == "deleted"
        assert email not in user.email and user.phone is None and user.date_of_birth is None
        profile = await s.scalar(sa.select(Profile).where(Profile.user_id == uid))
        assert all(getattr(profile, f) is None for f in ("display_name", "bio", "photos", "interests", "city_market"))
        va = await s.scalar(sa.select(VerifiedAttributes).where(VerifiedAttributes.user_id == uid))
        assert va.income_percentile_tier is None and va.education_level is None
        assert (await s.scalars(sa.select(Message).where(Message.sender_id == uid))).all() == []
        assert (await s.scalars(sa.select(PushToken).where(PushToken.user_id == uid))).all() == []
        assert (await s.scalars(sa.select(OtpChallenge).where(OtpChallenge.destination == email))).all() == []
        assert (await s.scalars(sa.select(BetaInvite).where(BetaInvite.email == email))).all() == []

        # Audit trail survives, with the email redacted out of it.
        events = (await s.scalars(sa.select(AuditEvent))).all()
        assert "account_deleted" in {e.event_type for e in events if e.subject_id == uid}
        invite_events = [e for e in events if e.event_type == "beta_invite_created" and e.event_metadata and e.event_metadata.get("email") in (email, "[redacted]")]
        assert invite_events and all(e.event_metadata["email"] == "[redacted]" for e in invite_events)
        assert not any(email in str(e.event_metadata) for e in events)

    # Signing up again with the same email starts a brand-new account.
    again = await _login(client, email)
    assert await _user_id(client, again) != me_id


async def test_push_notifications_are_sent_generic_and_never_block(client, monkeypatch):
    from app.config import get_settings
    from app.modules.notifications import service as push

    sent: list[dict] = []

    async def fake_deliver(messages):
        sent.extend(messages)
        return [
            {"status": "error", "details": {"error": "DeviceNotRegistered"}}
            if m["to"] == "ExponentPushToken[dead]" else {"status": "ok"}
            for m in messages
        ]

    monkeypatch.setattr(push, "_deliver", fake_deliver)
    settings = get_settings()

    a = await _login(client, "push_a@todate.test")
    b = await _login(client, "push_b@todate.test")
    b_id = await _user_id(client, b)
    await client.post("/v1/users/me/push-tokens", json={"token": "ExponentPushToken[a]", "platform": "ios"}, headers=a)
    await client.post("/v1/users/me/push-tokens", json={"token": "ExponentPushToken[b]", "platform": "android"}, headers=b)
    await client.post("/v1/users/me/push-tokens", json={"token": "ExponentPushToken[dead]"}, headers=b)

    # Disabled (the default): nothing leaves the building.
    match = (await client.post("/v1/matches", json={"target_user_id": b_id}, headers=a)).json()
    assert sent == []

    settings.push_enabled = True
    try:
        # A message notifies only the other person, and never includes its text.
        await client.post(f"/v1/matches/{match['id']}/messages", json={"body": "secret words"}, headers=a)
        assert {m["to"] for m in sent} == {"ExponentPushToken[b]", "ExponentPushToken[dead]"}
        assert all("secret words" not in str(m) for m in sent)
        assert sent[0]["data"] == {"type": "message", "match_id": match["id"]}

        # The uninstalled device was pruned after Expo reported it.
        sent.clear()
        await client.post(f"/v1/matches/{match['id']}/messages", json={"body": "again"}, headers=a)
        assert {m["to"] for m in sent} == {"ExponentPushToken[b]"}

        # Date prompt: both people, on trigger and on resolution.
        sent.clear()
        await client.post(f"/v1/matches/{match['id']}/date-prompt", headers=a)
        assert {m["to"] for m in sent} == {"ExponentPushToken[a]", "ExponentPushToken[b]"}
        sent.clear()
        await client.post(f"/v1/matches/{match['id']}/date-prompt/response", json={"choice": "yes"}, headers=a)
        assert sent == []  # not resolved yet
        await client.post(f"/v1/matches/{match['id']}/date-prompt/response", json={"choice": "yes"}, headers=b)
        assert {m["to"] for m in sent} == {"ExponentPushToken[a]", "ExponentPushToken[b]"}
        assert all("yes" not in m["body"].lower() for m in sent)  # outcome isn't on the lock screen

        # Expo failing must not fail the member's request.
        async def broken(messages):
            raise RuntimeError("expo is down")

        monkeypatch.setattr(push, "_deliver", broken)
        c = await _login(client, "push_c@todate.test")
        r = await client.post("/v1/matches", json={"target_user_id": b_id}, headers=c)
        assert r.status_code == 201
    finally:
        settings.push_enabled = False

    # Sign-out unregisters the device.
    import sqlalchemy as sa

    from app.db import SessionLocal
    from app.modules.notifications.models import PushToken

    await client.request("DELETE", "/v1/users/me/push-tokens", json={"token": "ExponentPushToken[a]"}, headers=a)
    async with SessionLocal() as s:
        assert (await s.scalars(sa.select(PushToken).where(PushToken.token == "ExponentPushToken[a]"))).all() == []


def test_websocket_messages_also_send_a_push(monkeypatch):
    import time

    from app.config import get_settings
    from app.modules.notifications import service as push

    sent: list[dict] = []

    async def fake_deliver(messages):
        sent.extend(messages)
        return [{"status": "ok"} for _ in messages]

    monkeypatch.setattr(push, "_deliver", fake_deliver)
    settings = get_settings()
    settings.push_enabled = True
    try:
        with TestClient(app) as tc:
            token_a, auth_a = _login_sync(tc, "wspush_a@todate.test")
            token_b, auth_b = _login_sync(tc, "wspush_b@todate.test")
            tc.post("/v1/users/me/push-tokens", json={"token": "ExponentPushToken[wsb]"}, headers=auth_b)
            b_id = tc.get("/v1/users/me", headers=auth_b).json()["id"]
            match_id = tc.post("/v1/matches", json={"target_user_id": b_id}, headers=auth_a).json()["id"]
            sent.clear()  # ignore the new-match push

            with tc.websocket_connect(f"/v1/matches/{match_id}/ws?token={token_a}") as ws:
                ws.send_text(json.dumps({"body": "over the socket"}))
                ws.receive_json()
                deadline = time.monotonic() + 3
                while not sent and time.monotonic() < deadline:
                    time.sleep(0.05)

            assert [m["to"] for m in sent] == ["ExponentPushToken[wsb]"]
            assert "over the socket" not in str(sent)
    finally:
        settings.push_enabled = False


async def test_old_app_versions_get_upgrade_required(client):
    from app.config import get_settings

    settings = get_settings()
    auth = await _login(client, "version@todate.test")
    settings.min_app_version = "1.2.0"
    try:
        r = await client.get("/v1/users/me", headers={**auth, "X-App-Version": "1.1.9"})
        assert r.status_code == 426
        assert r.json() == {"detail": "app update required", "min_app_version": "1.2.0"}

        for ok in ("1.2.0", "1.10.0", "not-a-version"):
            r = await client.get("/v1/users/me", headers={**auth, "X-App-Version": ok})
            assert r.status_code == 200, ok
        assert (await client.get("/v1/users/me", headers=auth)).status_code == 200  # no header: web client
        assert (await client.get("/health", headers={"X-App-Version": "0.0.1"})).status_code == 200
    finally:
        settings.min_app_version = ""


# ---------------------------------------------------------------------------
# Phone-first sign-up (design/screens/01, 05, 06)
# ---------------------------------------------------------------------------


async def _phone_login(client, phone: str):
    start = await client.post("/v1/auth/otp/start", json={"destination": phone, "channel": "phone"})
    assert start.status_code == 200, start.text
    p = start.json()
    return await client.post(
        "/v1/auth/otp/verify", json={"challenge_id": p["challenge_id"], "code": p["dev_code"]}
    )


async def test_phone_sign_up_creates_account_and_normalizes_number(client):
    r = await _phone_login(client, "+1 (613) 246-2840")
    assert r.status_code == 200
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    me = (await client.get("/v1/users/me", headers=auth)).json()
    assert me["phone"] == "+16132462840"
    assert me["email"] is None  # collected later in onboarding

    # The same number typed differently signs into the same account.
    again = await _phone_login(client, "+16132462840")
    me2 = (await client.get("/v1/users/me", headers={"Authorization": f"Bearer {again.json()['access_token']}"})).json()
    assert me2["id"] == me["id"]

    # Phone-only accounts go through onboarding like anyone else.
    r = await client.put("/v1/users/me/date-of-birth", json={"date_of_birth": ADULT_DOB}, headers=auth)
    assert r.status_code == 200


async def test_invalid_phone_numbers_are_rejected(client):
    for bad in ["(613) 246-2840", "+1 613", "not a number"]:
        r = await client.post("/v1/auth/otp/start", json={"destination": bad, "channel": "phone"})
        assert r.status_code == 422, bad


async def test_production_phone_sign_up_requires_a_phone_invite(client):
    import sqlalchemy as sa

    from app.config import get_settings
    from app.db import SessionLocal
    from app.modules.admin.models import AuditEvent, BetaInvite

    settings = get_settings()
    phone = "+14155550123"

    settings.environment = "production"
    try:
        # dev_code is withheld in production, so read the code from a dev start.
        settings.environment = "development"
        start = (await client.post("/v1/auth/otp/start", json={"destination": phone, "channel": "phone"})).json()
        settings.environment = "production"
        r = await client.post("/v1/auth/otp/verify", json={"challenge_id": start["challenge_id"], "code": start["dev_code"]})
        assert r.status_code == 401 and "invite" in r.json()["detail"]
    finally:
        settings.environment = "development"

    settings.bootstrap_admin_emails = "phone_admin@todate.test"
    try:
        admin = await _login(client, "phone_admin@todate.test")
    finally:
        settings.bootstrap_admin_emails = ""

    # Exactly one contact per invite.
    assert (await client.post("/v1/admin/beta-invites", json={}, headers=admin)).status_code == 422
    assert (await client.post("/v1/admin/beta-invites", json={"email": "a@todate.test", "phone": phone}, headers=admin)).status_code == 422
    r = await client.post("/v1/admin/beta-invites", json={"phone": "+1 (415) 555-0123"}, headers=admin)
    assert r.status_code == 201 and r.json()["phone"] == phone and r.json()["email"] is None

    start = (await client.post("/v1/auth/otp/start", json={"destination": phone, "channel": "phone"})).json()
    settings.environment = "production"
    try:
        r = await client.post("/v1/auth/otp/verify", json={"challenge_id": start["challenge_id"], "code": start["dev_code"]})
        assert r.status_code == 200
    finally:
        settings.environment = "development"

    async with SessionLocal() as s:
        invite = await s.scalar(sa.select(BetaInvite).where(BetaInvite.phone == phone))
        assert invite.redeemed_at is not None
        # ADR-0003: new audit events carry no contact details.
        event = await s.scalar(sa.select(AuditEvent).where(AuditEvent.subject_id == invite.id))
        assert phone not in str(event.event_metadata)


async def test_deleting_a_phone_only_account(client):
    import sqlalchemy as sa

    from app.db import SessionLocal
    from app.modules.identity.models import User

    r = await _phone_login(client, "+16135550199")
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}
    uid = (await client.get("/v1/users/me", headers=auth)).json()["id"]

    assert (await client.delete("/v1/users/me", headers=auth)).status_code == 204
    async with SessionLocal() as s:
        user = await s.get(User, uuid.UUID(uid))
        assert user.status.value == "deleted"
        assert user.phone is None and user.email is None

    # The number is free to start a brand-new account.
    again = await _phone_login(client, "+16135550199")
    new = (await client.get("/v1/users/me", headers={"Authorization": f"Bearer {again.json()['access_token']}"})).json()
    assert new["id"] != uid


async def test_demo_mode_still_sends_people_through_onboarding(client):
    """DEMO_MODE fakes verification and activation, but not the birth date.

    A stated birth date is what marks onboarding as done, so pre-filling it
    would skip the onboarding flow entirely on the demo deployment.
    """
    from app.config import get_settings

    settings = get_settings()
    settings.demo_mode = True
    try:
        viewer = await _login(client, "demo_viewer@todate.test")
        new = await _login(client, "demo_new@todate.test", date_of_birth=None)
        new_id = await _user_id(client, new)

        me = (await client.get("/v1/users/me", headers=new)).json()
        assert me["account_state"] == "PROFILE_ACTIVE"  # demo: auto-activated
        assert me["date_of_birth"] is None  # ...but onboarding still pending

        # Not discoverable until onboarding states an adult birth date.
        feed = {p["user_id"] for p in (await client.get("/v1/discovery", headers=viewer)).json()}
        assert new_id not in feed
        await client.put("/v1/users/me/date-of-birth", json={"date_of_birth": ADULT_DOB}, headers=new)
        feed = {p["user_id"] for p in (await client.get("/v1/discovery", headers=viewer)).json()}
        assert new_id in feed
    finally:
        settings.demo_mode = False


async def test_phone_sign_up_in_demo_mode(client):
    """The exact configuration of the Render demo: DEMO_MODE on + phone sign-up.

    Demo mode seeds fake verified attributes keyed off the contact detail; a
    phone-only account has no email, which used to crash sign-up with a 500.
    """
    from app.config import get_settings

    settings = get_settings()
    settings.demo_mode = True
    try:
        r = await _phone_login(client, "+16135550177")
        assert r.status_code == 200, r.text
        auth = {"Authorization": f"Bearer {r.json()['access_token']}"}
        va = (await client.get("/v1/users/me/verified-attributes", headers=auth)).json()
        assert va["identity_verified"] is True  # demo seeding still applied
    finally:
        settings.demo_mode = False
