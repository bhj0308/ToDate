# ToDate — Demo Guide

A runnable, multi-user demo of ToDate: the FastAPI backend plus a self-contained
web client, served as **one app on one URL**. Teammates open a link on their
phone or laptop, sign in, and actually match, chat (in real time), and run the
signature date prompt against each other.

## What's in the demo

The web client (served at `/`) walks the product spine end-to-end, all backed by
the real API:

1. **Sign in** — email → a one-time code (shown on screen; SMS is stubbed)
2. **Profile** — name, bio, city, interests
3. **Discover** — vetted members near you
4. **Match** → **real-time chat** (WebSocket)
5. **The date prompt** — private, simultaneous Yes / No / Maybe; mutual Yes moves
   the match to `SCHEDULE_READY` (the anti-ghosting mechanic). The panel
   **updates live** when your counterpart answers, so a side-by-side demo shows
   the reveal without anyone refreshing.
6. **Scheduling the real date** — share availability, pick from curated venues,
   confirm a time, then report the outcome (which feeds the match engine)
7. **AI coaching** — compatibility score + tiered nudges

### DEMO_MODE

Set `DEMO_MODE=true` so every new sign-in is **auto-activated** and given seeded
verified attributes — otherwise discovery is empty by design until an admin
curates each member (the real invite-only flow). It's a demo-only flag; normal
behavior is untouched when it's off.

## Run it locally

```bash
cd backend
uv sync
DEMO_MODE=true ENVIRONMENT=development \
  uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 . Interactive API docs live at `/docs`.

## Share it with teammates — three options

### A. Same Wi-Fi (fastest, zero tools)
Bind to `0.0.0.0` (as above) and share `http://<your-mac-LAN-ip>:8000`. Only
works for teammates on the same network.

### B. Public link via tunnel (any device, anywhere — no cloud account)
Keep the server running, then in a second terminal:

```bash
cd backend
bash scripts/share-demo.sh 8000
```

It prints a public `https://…` URL that points at your Mac. Share it. Live only
while your Mac + the tunnel are running — perfect for a demo session. (Needs
`cloudflared`: `brew install cloudflared`. The script lists fallbacks.)

### C. Hosted deploy (a durable link)
A [`render.yaml`](render.yaml) blueprint is included. Push the repo to GitHub,
then Render → New → Blueprint → pick the repo. It builds the
[Dockerfile](backend/Dockerfile) and sets `DEMO_MODE`. Defaults to ephemeral
SQLite (state resets on redeploy — fine for a demo); uncomment the Postgres
block for durable state. The same Docker image runs on Railway, Fly.io, or Cloud
Run if you prefer — the cloud push needs your own account login.

## Suggested 2-minute script for teammates

1. Two people open the link, sign in with different emails (the code auto-fills).
2. Set a display name in **Profile**.
3. Go to **Discover** — you'll see each other. Tap **Match** on someone.
4. In **Matches**, open the match and send a message — it appears live on both
   screens.
5. Tap **Trigger date prompt**, both pick **Yes** — the other person's screen
   reveals the result on its own. Try a **Maybe** or **No** on another match to
   see the extend / clean-exit paths.
6. Pick a **venue**, set a time, **confirm the date** — then report the outcome.
7. Note the **compatibility score** and AI nudges update as you go.

## Honest limits (so nobody's surprised)

- **Not the real product UI** — this web client is a demo harness over the real
  API, not the planned React Native app (ADR-0002).
- **Verification is stubbed** — DEMO_MODE fakes "verified". The real
  background-check flow is blocked pending legal sign-off (see
  [docs/compliance/background-checks.md](docs/compliance/background-checks.md)).
- **OTP, photos, venues, payments are dev-stubbed** — see
  [backend/README.md](backend/README.md) for the full list.
- **SQLite** for the demo; production is Postgres (ADR-0002).
