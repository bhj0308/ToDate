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


async def _login(client, email: str) -> dict:
    """Helper: OTP login, return auth header."""
    start = await client.post(
        "/v1/auth/otp/start", json={"destination": email, "channel": "email"}
    )
    p = start.json()
    verify = await client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": p["challenge_id"], "code": p["dev_code"]},
    )
    return {"Authorization": f"Bearer {verify.json()['access_token']}"}


async def test_subscription_crud(client):
    auth = await _login(client, "sub@todate.test")

    # No subscription yet → 404
    r = await client.get("/v1/subscriptions/me", headers=auth)
    assert r.status_code == 404

    # Create Premium+ monthly
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "premium_plus", "billing_cycle": "monthly"},
        headers=auth,
    )
    assert r.status_code == 201
    sub = r.json()
    assert sub["plan"] == "premium_plus"
    assert sub["status"] == "active"

    # Duplicate → 409
    r = await client.post(
        "/v1/subscriptions",
        json={"plan": "elite", "billing_cycle": "annual"},
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


async def test_matchmaking(client):
    auth_a = await _login(client, "match_a@todate.test")
    auth_b = await _login(client, "match_b@todate.test")

    me_b = await client.get("/v1/users/me", headers=auth_b)
    user_b_id = me_b.json()["id"]

    # Discovery returns empty (no PROFILE_ACTIVE users in test)
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
    await client.post(
        "/v1/subscriptions",
        json={"plan": "premium_plus", "billing_cycle": "monthly"},
        headers=auth_a,
    )

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

    await client.post(
        "/v1/subscriptions",
        json={"plan": "elite", "billing_cycle": "annual"},
        headers=auth_a,
    )

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
