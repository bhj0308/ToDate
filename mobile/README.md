# ToDate Mobile

Expo (React Native) + TypeScript client per [ADR-0002](../docs/adr/0002-tech-stack.md). Talks to the [backend](../backend) via a typed client generated from its OpenAPI schema.

## Quickstart

```bash
npm install                              # install deps
cp .env.example .env                     # EXPO_PUBLIC_API_URL, defaults to http://localhost:8000
npx expo start --ios                     # run against a local backend (uv run uvicorn app.main:app --reload)
```

Android emulator: set `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000` instead of `localhost`.

**Don't pass `CI=1`** to `expo start` — it silently disables Metro's file watcher, so
edits stop reaching the running app until you notice and restart. It's only useful for
non-interactive one-shot invocations, not for a dev session.

After changing a backend route/schema, regenerate the typed API client against a running backend:

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts
```

## Layout

```
src/
  api/
    client.ts           thin openapi-fetch wrapper: bearer auth + 401-refresh-retry middleware
    schema.d.ts          generated from the backend's OpenAPI schema — do not hand-edit
  auth/
    tokenStore.ts        SecureStore-backed token persistence (non-React)
    AuthContext.tsx       React session state; wraps tokenStore + /users/me
  navigation/             AuthStack, per-tab stacks, AppTabs, RootNavigator
  components/             shared primitives: Screen, PrimaryButton, TextField, StatusMessage
  features/               one folder per backend module — mirrors backend/app/modules/
    identity/             auth screens, profile view/edit, verified-attributes badge   ✅ working
    matchmaking/           discovery feed, match list/detail shell                      ✅ working
    structured/            conversation, date-progression (prompt/availability/venue/plan) ✅ working
    intelligent/           coaching insights + compatibility score                      ✅ working
    entitlements/          catalog + subscription management                           ✅ working
    verification/          status screen surfacing the backend's deliberate 501         ⛔ blocked
```

`features/<domain>` is the anti-refactor structure: a new backend endpoint in a domain
lands in exactly one folder, not scattered across screens. `MatchDetailScreen` hosts
Conversation / Date / Insights as an in-screen segmented view (not separate nav routes)
since they all key off the same `match_id`.

## Status & what's intentionally NOT built

- **Realtime chat transport** — ADR-0002 calls for WebSocket, but the backend only
  exposes REST `POST .../messages` today. `ConversationScreen` polls via React Query
  (`refetchInterval`) instead. Swap this out once the backend adds a WS endpoint.
- **Photo upload** — object storage vendor isn't chosen yet; `photos` accepts URL
  strings, not a native image-picker-to-blob-storage flow.
- **Payment capture UI** — `SubscriptionScreen` only sends `plan`/`billing_cycle`; no
  raw card fields, consistent with the backend's tokenized-processor assumption.
- **Date plan re-fetch** — there's no `GET /matches/{id}/date-plan` endpoint yet, so
  a created plan lives only in `MatchDetailScreen`'s local state (lifted above the
  tab-switching to survive Chat/Insights navigation, but lost on app restart). Add the
  backend endpoint and swap in a query if this becomes a real gap.
- **Admin & Moderation** — no backend endpoints exist yet, so no screens either.
- **Verification** — `VerificationStatusScreen` calls the backend's deliberately
  blocked `POST /verification-cases` and renders the 501 message; no real flow.

## Verification

```bash
npx tsc --noEmit      # typecheck
```

No test suite yet (screens are thin wrappers around typed API hooks; the meaningful
logic lives in the backend, which has its own test suite). Manual verification: run
against a local backend, register via OTP, and walk through each tab.
