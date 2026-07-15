"""Verification vendor adapter — INTENTIONALLY UNIMPLEMENTED.

The disclosure / authorization / adverse-action / dispute flows are compliance-
critical (FCRA and state law) and MUST NOT be built against the draft
requirements alone. See docs/compliance/background-checks.md — every numbered
requirement there is a placeholder for "what legal counsel confirms."

Building the wrong adverse-action flow is worse than shipping none: it creates
legal exposure. So this module deliberately raises until:
  1. Legal counsel signs off on the compliance doc, and
  2. A background-check vendor is selected (docs/vendors/vendor-selection.md).

The adapter interface below is the seam those decisions plug into.
"""

from typing import Protocol


class VerificationVendorAdapter(Protocol):
    """The contract a real background-check vendor integration will implement.

    Kept as a Protocol so the vendor choice (Checkr/Persona/etc.) plugs in
    behind a stable interface, per the Architecture doc's adapter boundary.
    """

    async def submit_check(self, case_id: str) -> str:  # -> vendor_reference_id
        ...

    async def fetch_result(self, vendor_reference_id: str) -> dict:
        ...


class NotYetApprovedError(RuntimeError):
    """Raised for any real verification action pending legal sign-off."""


class BlockedVendorAdapter:
    """Default adapter: refuses to run until compliance sign-off exists."""

    async def submit_check(self, case_id: str) -> str:
        raise NotYetApprovedError(
            "Verification is blocked pending legal sign-off of "
            "docs/compliance/background-checks.md and vendor selection."
        )

    async def fetch_result(self, vendor_reference_id: str) -> dict:
        raise NotYetApprovedError(
            "Verification is blocked pending legal sign-off."
        )


def get_adapter() -> VerificationVendorAdapter:
    return BlockedVendorAdapter()
