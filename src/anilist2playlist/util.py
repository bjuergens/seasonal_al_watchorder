import calendar
import datetime
import sys
from typing import Any

# One media entry as returned by the AniList GraphQL API
Media = dict[str, Any]


def parse_al_date_round_up(fuzzy: dict[str, int | None]) -> datetime.date:
    """AniList FuzzyDate -> date, rounding missing parts up: unknown year becomes
    2999, unknown month the last month, unknown day the last day of the month."""
    y, mo, d = fuzzy["year"], fuzzy["month"], fuzzy["day"]
    if y is not None and mo is not None and d is not None:
        return datetime.date(y, mo, d)
    if y is None:
        y = 2999
    if mo is None:
        mo = 12
    if d is None:
        d = calendar.monthrange(y, mo)[1]
    result = datetime.date(y, mo, d)
    Log.warn(f"incomplete AniList date {fuzzy} rounded up to {result}")
    return result


class Log:
    """Emoji logging per project conventions: ✅ success, ❌ error, ⚠️ warning."""

    @staticmethod
    def info(msg: str) -> None:
        print(msg)

    @staticmethod
    def success(msg: str) -> None:
        print(f"✅ {msg}")

    @staticmethod
    def warn(msg: str) -> None:
        print(f"⚠️ {msg}", file=sys.stderr)

    @staticmethod
    def error(msg: str) -> None:
        print(f"❌ {msg}", file=sys.stderr)
