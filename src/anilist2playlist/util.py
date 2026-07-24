import functools
import sys
from dataclasses import dataclass
from typing import Any

# One media entry as returned by the AniList GraphQL API
Media = dict[str, Any]


@functools.total_ordering
@dataclass(frozen=True)
class Score:
    """Additive watch-order adjustment. Adding Scores sums the values and ORs the
    skip flags, so skip can only ever go from False to True."""

    value: int = 0
    skip: bool = False

    def __add__(self, other: "Score") -> "Score":
        return Score(self.value + other.value, self.skip or other.skip)

    def __iadd__(self, other: "Score") -> "Score":
        return self + other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Score):
            return NotImplemented
        return (self.value, self.skip) == (other.value, other.skip)

    def __lt__(self, other: "Score") -> bool:
        return (self.value, self.skip) < (other.value, other.skip)


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
