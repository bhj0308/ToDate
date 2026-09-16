# ADR-0003: Account Deletion and Data Retention

**Status:** Accepted
**Date:** 2026-09-16
**Related:** [Background-check compliance](../compliance/background-checks.md), [Security & data classification](../architecture/security.md), [App release architecture](../architecture/app-release.md)

## Context

Apple (App Store Review Guideline 5.1.1(v)) and Google Play both require that an app which lets people create an account also lets them delete it from inside the app. ToDate must ship this before either store will accept it.

"Delete everything" collides with two other obligations:

- The [compliance doc](../compliance/background-checks.md) expects verification cases, decisions and artifacts to have retention periods set by legal counsel, and possibly legal holds.
- Trust and safety needs moderation cases and the audit trail to outlive the account that was reported or banned.

## Decision

**Deleting an account anonymizes the person immediately and keeps system and compliance records under their own retention rules.** It is irreversible, with no grace period.

`DELETE /v1/users/me` (see `delete_account` in `backend/app/modules/identity/service.py`):

| Data | What happens | Why |
|---|---|---|
| Email, phone, date of birth | Email replaced with `deleted+<id>@deleted.invalid`; phone and DOB cleared | Identifies the person |
| Profile (name, bio, prompts, photos, interests, location, dining preferences) | Cleared; photo files deleted | Identifies the person |
| Income tier, education on `verified_attributes` | Cleared | Sensitive derived facts |
| Messages they sent | Deleted | Content they wrote |
| Availability windows | Deleted | Their personal schedule |
| Matches | Set to `CLOSED`; the other person keeps their own messages | The counterpart's side isn't the deleter's to erase |
| Active subscription | Canceled | Stop billing |
| Push tokens | Deleted | Device must stop receiving pushes |
| OTP challenges | Deleted | They store the email/phone |
| Beta invites | Deleted | They store the email |
| Account status | `DELETED`, removed from discovery | Existing tokens stop working immediately |
| **Verification cases, decisions, artifacts** | **Kept** | Retention set by legal (compliance doc) |
| **Moderation cases** | **Kept** | Trust and safety record |
| **Audit events** | **Kept**, with one exception below | Compliance trail |
| Date-prompt responses, date plans | Kept | Yes/No/Maybe and a venue; nothing identifying once the account is anonymized |

### The one exception to "audit events are append-only"

`beta_invite_created` events store the invited email in their metadata. Keeping them untouched would leave a deleted person's email in the log. On deletion, that one field is replaced with `[redacted]`; the event itself (who invited, when) is kept. No other audit event stores contact details today. **New audit events must not put email, phone or other contact details in `event_metadata`**; reference the subject by ID instead.

## Consequences

- **Positive:** Meets both stores' requirements; keeps compliance and safety records defensible; the same email can sign up again as a brand-new account.
- **Negative:** No undo. People who delete by mistake start over. A 30-day grace period was considered and rejected for v1 because it needs a scheduled job.
- **Open for legal review:** Whether any retained verification record is itself personal data that must be deleted on request in some jurisdictions (GDPR-style erasure). If counsel says yes, this ADR gets superseded rather than edited.

## Verification

`test_account_deletion_anonymizes_and_keeps_compliance_records` checks every row above against the database, plus that the email appears nowhere in audit metadata. A deliberately reintroduced bug that skips the redaction makes the test fail.
