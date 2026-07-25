import calendar
import datetime
from dataclasses import dataclass
from typing import ClassVar

from .config import SEQUEL, SIDE_STORY, Rule, feature
from .score import Score
from .util import Log, Media


@dataclass(frozen=True)
class Show:
    """One immutable show parsed from the raw AniList."""

    COLUMNS: ClassVar[list[str]] = [
        "title",
        "romaji",
        "source",
        "siteUrl",
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
    latest_start_date: datetime.date  # missing parts rounded up
    genres: list[str]
    duration: int | None
    studios: list[str]
    tag_names: list[str]
    features: set[str]  # the feature ids that weight rules match against
    al_rank: int  # popularity rank (the fetch order)
    notes: list[str]
    skip_reasons: list[str]
    score_value: int  # adjusted rank

    @classmethod
    def of(cls, raw: Media, al_rank: int, rules: list[Rule], special_date: datetime.date) -> "Show":
        romaji: str = raw["title"]["romaji"]
        genres = list(raw["genres"])
        tag_names = [t["name"] for t in raw["tags"]]

        y, mo, d = (raw["startDate"][k] for k in ("year", "month", "day"))
        if y is not None and mo is not None and d is not None:
            latest_start_date = datetime.date(y, mo, d)
        else:
            ry, rmo = y if y is not None else 2999, mo if mo is not None else 12
            rd = d if d is not None else calendar.monthrange(ry, rmo)[1]
            latest_start_date = datetime.date(ry, rmo, rd)
            Log.warn(
                f"incomplete AniList date {raw['startDate']} rounded up to {latest_start_date}"
            )

        def anime_relations(relation_type: str) -> list[Media]:
            return [
                e["node"]
                for e in raw["relations"]["edges"]
                if e["relationType"] == relation_type and e["node"]["type"] == "ANIME"
            ]

        is_sequel = bool(anime_relations("PREQUEL"))
        is_side_story = bool(anime_relations("PARENT"))
        # remake: an alternative version of an anime that started in an earlier year
        is_remake = y is not None and any(
            node["startDate"]["year"] is not None and node["startDate"]["year"] < y
            for node in anime_relations("ALTERNATIVE")
        )

        features = {feature("genre", g) for g in genres}
        features.update(feature("tag", t) for t in tag_names)
        features.add(feature("source", raw["source"]))

        notes: list[str] = []
        if raw["format"] != "TV":
            notes.append(raw["format"])
        if raw["status"] != "RELEASING":
            notes.append(raw["status"])
        if raw["isAdult"]:
            notes.append("adult")
        if is_sequel:
            notes.append(SEQUEL)
            features.add(SEQUEL)
        if is_side_story:
            notes.append(SIDE_STORY)
            features.add(SIDE_STORY)
        if is_remake:
            notes.append("remake")
        if y is None:
            Log.info(f"{romaji}: start date unknown")
            notes.append("start date unknown")
        elif mo is None or d is None:
            # the start date exactly as far as AniList knows it: "2026" or "2026-07"
            note = f"start date incomplete ({y if mo is None else f'{y}-{mo:02d}'})"
            Log.info(f"{romaji}: {note}")
            notes.append(note)
        elif latest_start_date == special_date:
            notes.append("releases on special day")
        if any(t["rank"] is None for t in raw["tags"]):
            notes.append("unranked tags")

        score = Score.of(al_rank, latest_start_date, features, rules, special_date)
        return cls(
            title=raw["title"]["english"] or romaji,
            romaji=romaji,
            source=raw["source"],
            site_url=raw["siteUrl"],
            latest_start_date=latest_start_date,
            genres=genres,
            duration=raw["duration"],
            studios=[s["name"] for s in raw["studios"]["nodes"]],
            tag_names=tag_names,
            features=features,
            al_rank=al_rank,
            notes=notes,
            skip_reasons=score.skip_reasons,
            score_value=score.value,
        )

    def tsv_row(self, watchorder: int | None) -> list[str | int | None]:
        return [
            self.title,
            self.romaji,
            self.source,
            self.site_url,
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
