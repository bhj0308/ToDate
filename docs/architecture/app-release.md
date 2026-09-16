# App Release Architecture

What it takes to ship the ToDate mobile app to the App Store and Google Play: what's built, how the release pieces fit together, and what still needs a person with the right accounts.

Related: [ADR-0002 stack](../adr/0002-tech-stack.md), [ADR-0003 account deletion](../adr/0003-account-deletion-and-data-retention.md), [deployment roadmap](deployment-roadmap.md).

## Store requirements: status

| Requirement | Source | Status |
|---|---|---|
| In-app account deletion | Apple 5.1.1(v); Google Play account-deletion policy | ✅ Built: Profile → Delete account (ADR-0003) |
| Report abusive users | Apple 1.2 (user-generated content) | ✅ Existed already |
| Block abusive users | Apple 1.2 | ✅ Built: Profile → Block |
| 18+ gate for a dating service | Store policy and law | ✅ Self-reported DOB, one attempt, under-18 suspends the account (ID verification will confirm later) |
| Push permission handled correctly | Platform rules (Android 13 needs `POST_NOTIFICATIONS`) | ✅ Built |
| Bundle ID / package name | Required to submit | ✅ `com.todate.app` |
| Working reviewer sign-in | App Store Connect "App Review Information" | ⛔ **Not solved, see below** |
| Privacy policy and terms URLs | Both stores | ⛔ Needs to exist |
| Privacy "nutrition label" / Play Data safety form | Both stores | ⛔ Fill in from [security.md](security.md) |
| Web link to request account deletion | Google Play | ⛔ Needs a web page (can reuse the web client) |
| Age rating questionnaire | Both stores | ⛔ Answer as a dating app; check the current rating options when you submit |

Not required: **Sign in with Apple.** Apple only requires it when an app offers third-party social login, and ADR-0001 deferred social login.

## ⚠️ The App Review sign-in problem

Apple's reviewers must be able to sign in. ToDate's production configuration makes that impossible as it stands:

1. **OTP codes go by SMS or email, and `ENVIRONMENT=production` never returns the code in the API**, which is correct and test-guarded. A reviewer has no inbox to receive one.
2. **Registration is invite-only in production.**
3. **Discovery needs curated, activated members**, so a new reviewer sees an empty app.

Options, to decide before first submission:
- **Review environment (recommended):** a separate hosted backend running `DEMO_MODE=true` with seeded members, and a review build pointed at it. Nothing about the production security posture changes.
- **Allowlisted reviewer account:** one specific email that accepts a fixed code on production. Simpler, but it's a permanent backdoor in production. Avoid.

## Environments and builds (EAS)

`mobile/eas.json` defines three build profiles. The API URL is baked in at build time from `EXPO_PUBLIC_API_URL`:

| Profile | Distribution | API | Used for |
|---|---|---|---|
| `development` | internal (dev client) | `http://localhost:8000` | Day-to-day dev on a real device, **including testing push** |
| `preview` | internal | Render demo | Teammates installing a real build |
| `production` | store | Render demo, **change before launch** | App Store / Play submission |

Before a real launch, `production` must point at a production backend: paid plan (the free tier sleeps), managed Postgres, `ENVIRONMENT=production`, `DEMO_MODE=false`, real `JWT_SECRET`.

**Expo Go can't test push.** Remote notifications were removed from Expo Go in SDK 53. Everything else can still be tried in Expo Go; push needs a `development` build on a physical device.

## Push notifications

```
event (match, message, date prompt)
  → router schedules notify() in the background      (the member's request never waits)
  → load that user's push_tokens
  → POST https://exp.host/--/api/v2/push/send        (Expo relays to APNs / FCM)
  → tickets with DeviceNotRegistered → token deleted
```

- **Registration:** after sign-in the app asks permission, gets an Expo push token (needs the EAS `projectId`) and `POST /v1/users/me/push-tokens`. Sign-out calls `DELETE`, and account deletion removes every token.
- **Privacy:** notification text is fixed and generic ("You have a new message", "Your date prompt has a result"). Message text and date-prompt answers never go into a push, because lock screens are visible to others. This is test-guarded.
- **Off by default:** `PUSH_ENABLED=false`, so local dev and tests never call Expo. Turn it on in deployed environments once the EAS project exists.
- **Not built yet:** push *receipts* (Expo's second, delayed delivery check) and a scheduled job that triggers the date prompt after 3–5 days. Today the prompt is triggered manually.

## Minimum app version

Once a build is on people's phones you can't force them to update it. The client sends `X-App-Version` on every request; if `MIN_APP_VERSION` is set and the build is older, the API returns **`426 Upgrade Required`** and the app shows an update screen.

Use it deliberately: before shipping a **breaking** API change, release an app build that supports the new API, wait for adoption, *then* raise `MIN_APP_VERSION`. Requests without the header (web client, curl) are never gated, and a malformed header never blocks anyone.

## Checklist: what needs you

These need your accounts or decisions, so none of them can be done from the codebase:

1. **Apple Developer Program** membership and a **Google Play Console** account.
2. `cd mobile && npx eas-cli init`: creates the EAS project and writes `extra.eas.projectId` into `app.json`. Push stays off until this exists.
3. **Decide the App Review sign-in approach** (above) and set it up.
4. **Privacy policy, terms, and an account-deletion web page**, hosted at stable URLs.
5. **Decide on iPad:** `app.json` has `"supportsTablet": true`, so Apple will review and expect screenshots on iPad. For a phone-first app, set it to `false` unless iPad is intentional.
6. **App icon and splash:** still the Expo defaults.
7. Store listings, screenshots, the age-rating questionnaire, and the privacy and data-safety forms.
8. A production backend (see Environments), then `PUSH_ENABLED=true` and the Expo access token if enhanced push security is enabled.
