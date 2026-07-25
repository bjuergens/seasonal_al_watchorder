import calendar
import datetime

from .config import Rule
from .util import Log, Media


class Show:
    """One anime, fully parsed from the raw AniList media entry by Show.of().
    Everything is fixed at construction; the watch order is global and passed
    into tsv_row() instead."""

    COLUMNS = [
        "title",
        "romaji",
        "source",
        "siteUrl",
        "status",
        "startDate",
        "genres",
        "duration",
        "studio",
        "AL Rank",
        "watchorder",
        "skip",
        "notes",
        "SPOILER tags SPOILER",
        "score",
    ]

    title: str
    romaji: str
    source: str
    site_url: str
    status: str
    latest_start_date: datetime.date  # missing parts rounded up
    genres: list[str]
    duration: int | None
    studios: list[str]
    tag_names: list[str]
    is_sequel: bool
    is_side_story: bool
    al_rank: int  # popularity rank (the fetch order)
    notes: list[str]
    skip_reasons: list[str]
    score_value: int  # adjusted rank

    @classmethod
    def of(cls, raw: Media, al_rank: int, rules: list[Rule], special_date: datetime.date) -> "Show":
        from .score import Score

        show = cls()
        show.al_rank = al_rank
        show.title = raw["title"]["english"] or raw["title"]["romaji"]
        show.romaji = raw["title"]["romaji"]
        show.source = raw["source"]
        show.site_url = raw["siteUrl"]
        show.status = raw["status"]
        # start date with missing parts rounded up: unknown year becomes 2999,
        # unknown month the last month, unknown day the last day of the month
        y, mo, d = (raw["startDate"][k] for k in ("year", "month", "day"))
        if y is not None and mo is not None and d is not None:
            show.latest_start_date = datetime.date(y, mo, d)
        else:
            ry, rmo = y if y is not None else 2999, mo if mo is not None else 12
            rd = d if d is not None else calendar.monthrange(ry, rmo)[1]
            show.latest_start_date = datetime.date(ry, rmo, rd)
            Log.warn(
                f"incomplete AniList date {raw['startDate']} rounded up to {show.latest_start_date}"
            )
        show.genres = list(raw["genres"])
        show.duration = raw["duration"]
        show.studios = [s["name"] for s in raw["studios"]["nodes"]]
        show.tag_names = [t["name"] for t in raw["tags"]]

        def anime_relations(relation_type: str) -> list[Media]:
            return [
                e["node"]
                for e in raw["relations"]["edges"]
                if e["relationType"] == relation_type and e["node"]["type"] == "ANIME"
            ]

        show.is_sequel = bool(anime_relations("PREQUEL"))
        show.is_side_story = bool(anime_relations("PARENT"))
        # remake: an alternative version of an anime that started in an earlier year
        is_remake = y is not None and any(
            node["startDate"]["year"] is not None and node["startDate"]["year"] < y
            for node in anime_relations("ALTERNATIVE")
        )

        notes: list[str] = []
        if raw["format"] != "TV":
            notes.append(raw["format"])
        if show.is_sequel:
            notes.append("sequel")
        if show.is_side_story:
            notes.append("side story")
        if is_remake:
            notes.append("remake")
        if y is None:
            Log.info(f"{show.romaji}: start date unknown")
            notes.append("start date unknown")
        elif mo is None or d is None:
            # the start date exactly as far as AniList knows it: "2026" or "2026-07"
            note = f"start date incomplete ({y if mo is None else f'{y}-{mo:02d}'})"
            Log.info(f"{show.romaji}: {note}")
            notes.append(note)
        elif datetime.date(y, mo, d) == special_date:
            notes.append("releases on special day")
        if any(t["rank"] is None for t in raw["tags"]):
            notes.append("unranked tags")
        show.notes = notes

        score = Score.of(show, rules, special_date)
        show.skip_reasons = score.skip_reasons
        show.score_value = score.value
        return show

    def tsv_row(self, watchorder: int | None) -> list[str | int | None]:
        return [
            self.title,
            self.romaji,
            self.source,
            self.site_url,
            self.status,
            self.latest_start_date.isoformat(),
            ", ".join(self.genres),
            self.duration,
            ", ".join(self.studios),
            self.al_rank,
            "skip" if watchorder is None else watchorder,
            ", ".join(self.skip_reasons),
            ", ".join(self.notes),
            ", ".join(self.tag_names),
            self.score_value,
        ]
