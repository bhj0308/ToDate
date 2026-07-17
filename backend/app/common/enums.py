import enum


class AccountState(str, enum.Enum):
    """User onboarding state machine (docs/architecture/overview.md).

    Auth (OTP) gets a user to REGISTERED; the Vetted domain moves them toward
    VERIFIED_AND_ELIGIBLE. See ADR-0001 on why auth != identity verification.
    """

    REGISTERED = "REGISTERED"
    PROFILE_INCOMPLETE = "PROFILE_INCOMPLETE"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    VERIFICATION_IN_REVIEW = "VERIFICATION_IN_REVIEW"
    VERIFIED_AND_ELIGIBLE = "VERIFIED_AND_ELIGIBLE"
    PROFILE_ACTIVE = "PROFILE_ACTIVE"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    BANNED = "banned"


class Plan(str, enum.Enum):
    PREMIUM = "premium"
    PREMIUM_PLUS = "premium_plus"
    ELITE = "elite"


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class IncomePercentileTier(str, enum.Enum):
    T0_25 = "0-25"
    T25_50 = "25-50"
    T50_75 = "50-75"
    T75_90 = "75-90"
    T90_PLUS = "90+"


class CriminalCheckStatus(str, enum.Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    DISPUTED = "disputed"


class Eligibility(str, enum.Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    EXCEPTION_GRANTED = "exception_granted"


class VerificationCaseType(str, enum.Enum):
    IDENTITY = "identity"
    CRIMINAL = "criminal"
    INCOME = "income"
    EDUCATION = "education"


class MatchState(str, enum.Enum):
    CHAT_OPEN = "CHAT_OPEN"
    DATE_PROMPT_PENDING = "DATE_PROMPT_PENDING"
    DATE_PROMPT_CAPTURED = "DATE_PROMPT_CAPTURED"
    EXTENDED_CHAT = "EXTENDED_CHAT"
    SCHEDULE_READY = "SCHEDULE_READY"
    CLOSED = "CLOSED"


class DatePromptChoice(str, enum.Enum):
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"


class DateOutcome(str, enum.Enum):
    WENT_WELL = "went_well"
    DID_NOT_GO_WELL = "did_not_go_well"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"


class VerificationState(str, enum.Enum):
    """Compliance-driven verification state machine.

    Full list per docs/compliance/background-checks.md. NOTE: the transitions
    between these states (adverse-action timing, dispute handling) are BLOCKED
    on legal sign-off and intentionally not implemented — see the Verification
    module stub.
    """

    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    DISCLOSURE_PRESENTED = "DISCLOSURE_PRESENTED"
    AUTHORIZATION_CAPTURED = "AUTHORIZATION_CAPTURED"
    CHECK_IN_PROGRESS = "CHECK_IN_PROGRESS"
    CHECK_COMPLETE = "CHECK_COMPLETE"
    PRE_ADVERSE_ACTION_NOTICE_SENT = "PRE_ADVERSE_ACTION_NOTICE_SENT"
    DISPUTED = "DISPUTED"
    UNDER_RECONSIDERATION = "UNDER_RECONSIDERATION"
    POST_ADVERSE_ACTION_NOTICE_SENT = "POST_ADVERSE_ACTION_NOTICE_SENT"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    VERIFIED_AND_ELIGIBLE = "VERIFIED_AND_ELIGIBLE"
