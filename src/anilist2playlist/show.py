import datetime
from functools import cached_property

from .util import Log, Media, parse_al_date_round_up


class Show:
    """One anime: read-only access to the raw AniList media entry plus the
    pipeline state computed for it (AL rank, score, skip reasons, watch order)."""

    def __init__(self, raw: Media) -> None:
        self.raw = raw
        self.al_rank = 0  # popularity rank, assigned in sort_shows
        self.score_value = 0  # adjusted rank, assigned in sort_shows
        self.skip = ""  # comma-joined skip reasons, assigned in sort_shows
        self.watchorder: int | None = None  # stays None for skipped shows

    @property
    def title(self) -> str:
        title: str = self.raw["title"]["english"] or self.raw["title"]["romaji"]
        return title

    @cached_property
    def latest_start_date(self) -> datetime.date:
        """Start date with missing parts rounded up; cached so the parser's
        incomplete-date warning fires once per show."""
        return parse_al_date_round_up(self.raw["startDate"])

    @property
    def tag_names(self) -> list[str]:
        return [t["name"] for t in self.raw["tags"]]

    @property
    def has_unranked_tags(self) -> bool:
        return any(t["rank"] is None for t in self.raw["tags"])

    @property
    def studios(self) -> list[str]:
        return [s["name"] for s in self.raw["studios"]["nodes"]]

    def anime_relations(self, relation_type: str) -> list[Media]:
        return [
            e["node"]
            for e in self.raw["relations"]["edges"]
            if e["relationType"] == relation_type and e["node"]["type"] == "ANIME"
        ]

    @property
    def is_sequel(self) -> bool:
        return bool(self.anime_relations("PREQUEL"))

    @property
    def is_remake(self) -> bool:
        """Remake: an alternative version of an anime that started in an earlier year."""
        year = self.raw["startDate"]["year"]
        if year is None:
            return False
        return any(
            node["startDate"]["year"] is not None and node["startDate"]["year"] < year
            for node in self.anime_relations("ALTERNATIVE")
        )

    @property
    def is_side_story(self) -> bool:
        return bool(self.anime_relations("PARENT"))

    @property
    def start_date_str(self) -> str:
        """The start date exactly as far as AniList knows it: "", "2026" or "2026-07"."""
        date = self.raw["startDate"]
        y, mo, d = date["year"], date["month"], date["day"]
        if y is None:
            return ""
        if mo is None:
            return str(y)
        if d is None:
            return f"{y}-{mo:02d}"
        return f"{y}-{mo:02d}-{d:02d}"

    def notes(self, special_date: datetime.date) -> str:
        parts: list[str] = []
        if self.raw["format"] != "TV":
            parts.append(self.raw["format"])
        if self.is_sequel:
            parts.append("sequel")
        if self.is_side_story:
            parts.append("side story")
        if self.is_remake:
            parts.append("remake")
        date = self.raw["startDate"]
        y, mo, d = date["year"], date["month"], date["day"]
        if y is None:
            Log.info(f"{self.raw['title']['romaji']}: start date unknown")
            parts.append("start date unknown")
        elif mo is None or d is None:
            note = f"start date incomplete ({self.start_date_str})"
            Log.info(f"{self.raw['title']['romaji']}: {note}")
            parts.append(note)
        elif datetime.date(y, mo, d) == special_date:
            parts.append("releases on special day")
        if self.has_unranked_tags:
            parts.append("unranked tags")
        return ", ".join(parts)
