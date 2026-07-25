import datetime
import sys
from typing import Any

# One media entry as returned by the AniList GraphQL API
Media = dict[str, Any]


def anilist_date_to_date(fuzzy: dict[str, int | None]) -> datetime.date | None:
    """AniList FuzzyDate -> real date, or None if any part is missing."""
    y, mo, d = fuzzy["year"], fuzzy["month"], fuzzy["day"]
    if y is None or mo is None or d is None:
        return None
    return datetime.date(y, mo, d)


def anime_relations(m: Media, relation_type: str) -> list[Media]:
    return [
        e["node"]
        for e in m["relations"]["edges"]
        if e["relationType"] == relation_type and e["node"]["type"] == "ANIME"
    ]


def is_sequel(m: Media) -> bool:
    return bool(anime_relations(m, "PREQUEL"))


def is_remake(m: Media) -> bool:
    """Remake: an alternative version of an anime that started in an earlier year."""
    if m["startDate"]["year"] is None:
        return False
    return any(
        node["startDate"]["year"] is not None and node["startDate"]["year"] < m["startDate"]["year"]
        for node in anime_relations(m, "ALTERNATIVE")
    )


def is_side_story(m: Media) -> bool:
    return bool(anime_relations(m, "PARENT"))


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
