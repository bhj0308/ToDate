"""Client app version comparison for the minimum-version gate."""

import re


def parse_version(value: str) -> tuple[int, ...] | None:
    """Parse "1.4.2" (or "1.4.2-beta") into (1, 4, 2); None if unparseable."""
    match = re.match(r"^\s*(\d+(?:\.\d+)*)", value or "")
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def is_below(client_version: str, minimum: str) -> bool:
    """True only when both parse and the client is strictly older.

    Unparseable input never blocks a request — a malformed header must not lock
    people out of the app.
    """
    client, floor = parse_version(client_version), parse_version(minimum)
    if client is None or floor is None:
        return False
    width = max(len(client), len(floor))
    return client + (0,) * (width - len(client)) < floor + (0,) * (width - len(floor))
