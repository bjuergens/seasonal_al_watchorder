import sys
from typing import Any

# One media entry as returned by the AniList GraphQL API
Media = dict[str, Any]


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
