# Design source of truth

Exports from the ToDate Figma file, used to build the React Native screens.

```
screens/     the 13 onboarding screens, numbered in the designer's flow order (@2x)
reference/   component sheet, spec notes and content lists — not screens
icons/       SVG icons (none yet)
images/      photography / illustration assets (none yet)
_unused/     Figma canvas furniture that came along in the export (safe to delete)
tokens.md    colors, type, spacing — still eyeballed, see caveat in that file
```

All screens exported at **@2x** (804×1748, iPhone 16 Pro).

## Screens

| File | Screen |
|---|---|
| `01-welcome.png` | Landing: "Where meaningful relationships begin" · **Continue with phone** · Sign in |
| `02-values-ranking.png` | "What do you value most in a relationship?" — drag to reorder |
| `03-dating-goals.png` | "What brings you to ToDate?" — multi-select chips |
| `04-intent.png` | "Which best describes you?" — multi-select chips |
| `04-intent-warning.png` | Same, showing the community warning |
| `05-phone-number.png` | Phone number + country code |
| `05-phone-number-error.png` | Invalid number state |
| `06-phone-verification.png` | 6-digit code, Resend |
| `07-gender.png` | "Select your gender" — single select (Woman / Man / Non-binary) |
| `08-interested-in.png` | "Who are you interested in?" — multi-select |
| `09-first-name.png` | First name |
| `10-birthday.png` | Birthday wheel picker |
| `11-birthday-confirm.png` | "Are you 29?" sheet — *"cannot be changed later"* |

## Reference

| File | What it is |
|---|---|
| `components.png` | Component sheet: Continue (enabled/disabled), chip (unselected/selected), progress-bar states, **Apple Pay button** |
| `email-address-error.png` | An **email address** step with its invalid-email error state |
| `values-list.png` | The 10 values used by `02`: Loyalty, Communication, Emotional Connection, Physical Chemistry, Financial Stability, Ambition & Growth, Intelligence, Shared Values, Romance, Fun & Adventure |
| `note-intent-warning-rule.png` | Designer's rule: *"If one of the last two are selected, show error message"* — the trigger for `04-intent-warning` |

## Where the designs and the build disagree

1. ~~**Sign-up starts with phone; the backend can't create an account from one.**~~
   **Resolved — phone-first.** The backend now creates accounts from a phone
   number (stored as E.164, e.g. `+16132462840`), email is optional, and beta
   invites can target a phone. `01`, `05` and `06` are built.
   **Flow-order assumption to confirm with the designer:** the file numbers put
   the questions (`02`–`04`) before phone (`05`–`06`), but `01`'s button says
   *"Continue with phone"*, so the build runs **01 → 05 → 06 → 02 → 03 → 04 →
   07 → 08 → 09 → 10 → 11**. The email step (`reference/email-address-error.png`)
   isn't placed in the flow yet — its position isn't shown in the designs.
2. **Apple Pay for subscriptions is likely to be rejected.** The component sheet
   has a "Pay with  Pay" button. Apple generally requires **In-App Purchase**
   for digital subscriptions (guideline 3.1.1); Apple Pay is for physical goods
   and real-world services. Worth confirming against the current guidelines
   before building any payment UI — it changes the payment architecture, the
   commission, and what the backend's stubbed `payment_token` becomes.
3. **Onboarding collects five things the backend can't store:** gender,
   interested-in, dating goals, intent, and the values ranking. Only first name
   maps to an existing field (`profiles.display_name`). These need either new
   columns or the existing `prompts`/`interests` JSON.
4. **Dark theme.** The designs are dark brown/gold/wine; the app is currently
   light-only (`userInterfaceStyle: "light"`, light palette in
   `src/theme/colors.ts`).

## Where they agree

`11-birthday-confirm.png` says the birthday **cannot be changed later** — the
exact one-time date-of-birth rule already built and tested (`set_date_of_birth`).
Designer and backend landed on the same rule independently.

## Still missing

- **No core app screens.** All 13 are onboarding. Discovery, matches,
  conversation, the date prompt, profile and billing — the parts already built —
  have no designs.
- **No store-required screens:** "Update required", and the block /
  delete-account confirmations.
- **No icons or images**, and no authoritative token list. Specifically blocking
  fidelity now: the **welcome background photo** (currently a stopgap cropped
  from the flattened `01` export — `mobile/assets/images/welcome-bg.jpg`; the
  original photo export will be sharper and keep the full composition), the
  **phone icon** on `01`'s button (omitted), and the **country picker's open
  state** on `05` (the selector is fixed to +1 until it's designed).
- **No error state for `06`** — the code screen reuses `05`'s red-text pattern. `components.png` is
  the best current source for button and chip states.
