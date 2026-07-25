import csv
import datetime

from .config import Config
from .score import Score, warn_unused_weight_keys
from .show import Show
from .util import Log

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
]


def start_date_str(show: Show) -> str:
    y, mo, d = show.start_date["year"], show.start_date["month"], show.start_date["day"]
    if y is None:
        return ""
    if mo is None:
        return str(y)
    if d is None:
        return f"{y}-{mo:02d}"
    return f"{y}-{mo:02d}-{d:02d}"


def notes(show: Show, special_date: datetime.date) -> str:
    parts = []
    if show.format != "TV":
        parts.append(show.format)
    if show.is_sequel:
        parts.append("sequel")
    if show.is_side_story:
        parts.append("side story")
    if show.is_remake:
        parts.append("remake")
    y, mo, d = show.start_date["year"], show.start_date["month"], show.start_date["day"]
    if y is None:
        Log.info(f"{show.romaji}: start date unknown")
        parts.append("start date unknown")
    elif mo is None or d is None:
        Log.info(f"{show.romaji}: start date incomplete ({start_date_str(show)})")
        parts.append("start date incomplete")
    elif datetime.date(y, mo, d) == special_date:
        parts.append("releases on special day")
    if show.has_unranked_tags:
        parts.append("unranked tags")
    return ", ".join(parts)


def sort_shows(shows: list[Show], cfg: Config, special_date: datetime.date) -> list[Show]:
    """Watch order: the top pin_top non-skipped shows keep their AL Rank order, the
    rest are sorted by adjusted rank (ascending = watch first). Skipped shows sort
    like any other but get watchorder "skip" and don't consume a number."""
    warn_unused_weight_keys(shows, cfg.rules)
    by_popularity = sorted(shows, key=lambda s: s.popularity, reverse=True)
    for rank, show in enumerate(by_popularity, 1):
        show.al_rank = rank
    scored = [(show, Score.of(show, cfg.rules, special_date)) for show in shows]
    for show, score in scored:
        show.skip = ", ".join(score.skip_reasons)
    kept = sorted((s for s in shows if not s.skip), key=lambda s: s.al_rank)
    pinned = kept[: cfg.pin_top]
    rest = [(show, score) for show, score in scored if show not in pinned]
    ordered = pinned + [show for show, _ in sorted(rest, key=lambda pair: pair[1])]
    order = 1
    for show in ordered:
        if not show.skip:
            show.watchorder = order
            order += 1
    return ordered


def write_tsv(shows: list[Show], cfg: Config, special_date: datetime.date) -> None:
    with cfg.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, dialect="excel-tab")
        writer.writerow(COLUMNS)
        for show in shows:
            writer.writerow(
                [
                    show.title,
                    show.romaji,
                    show.source,
                    show.site_url,
                    show.status,
                    start_date_str(show),
                    ", ".join(show.genres),
                    show.duration,
                    ", ".join(show.studios),
                    show.al_rank,
                    "skip" if show.watchorder is None else show.watchorder,
                    show.skip,
                    notes(show, special_date),
                    ", ".join(show.tag_names),
                ]
            )
    Log.success(f"wrote {len(shows)} rows to {cfg.output}")
