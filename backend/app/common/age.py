"""Age rules for a dating service.

MINIMUM_AGE is a legal/policy floor, not tunable configuration.
"""

from datetime import date, datetime, timezone

MINIMUM_AGE = 18
# Anything older than this is treated as a typo rather than a real birth date.
_MAXIMUM_PLAUSIBLE_AGE = 120


def age_on(date_of_birth: date, today: date | None = None) -> int:
    today = today or datetime.now(timezone.utc).date()
    had_birthday = (today.month, today.day) >= (date_of_birth.month, date_of_birth.day)
    return today.year - date_of_birth.year - (0 if had_birthday else 1)


def is_adult(date_of_birth: date | None, today: date | None = None) -> bool:
    return date_of_birth is not None and age_on(date_of_birth, today) >= MINIMUM_AGE


def is_plausible(date_of_birth: date, today: date | None = None) -> bool:
    today = today or datetime.now(timezone.utc).date()
    return date_of_birth <= today and age_on(date_of_birth, today) <= _MAXIMUM_PLAUSIBLE_AGE


def adult_birthdate_cutoff(today: date | None = None) -> date:
    """Latest birth date that is 18 or older today (for SQL filtering)."""
    today = today or datetime.now(timezone.utc).date()
    try:
        return today.replace(year=today.year - MINIMUM_AGE)
    except ValueError:  # today is Feb 29 and that year has none
        return today.replace(year=today.year - MINIMUM_AGE, day=28)
