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
    "score",
]


def sort_shows(shows: list[Show], cfg: Config, special_date: datetime.date) -> list[Show]:
    """Watch order: the top pin_top non-skipped shows keep their AL Rank order, the
    rest are sorted by adjusted rank (ascending = watch first). Skipped shows sort
    like any other but get watchorder "skip" and don't consume a number."""
    warn_unused_weight_keys(shows, cfg.rules)
    # the query fetches POPULARITY_DESC, so the fetch order is the AL popularity rank
    for rank, show in enumerate(shows, 1):
        show.al_rank = rank
    scored = [(show, Score.of(show, cfg.rules, special_date)) for show in shows]
    for show, score in scored:
        show.skip = ", ".join(score.skip_reasons)
        show.score_value = score.value
    kept = [s for s in shows if not s.skip]
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
                    show.raw["title"]["romaji"],
                    show.raw["source"],
                    show.raw["siteUrl"],
                    show.raw["status"],
                    show.latest_start_date.isoformat(),
                    ", ".join(show.raw["genres"]),
                    show.raw["duration"],
                    ", ".join(show.studios),
                    show.al_rank,
                    "skip" if show.watchorder is None else show.watchorder,
                    show.skip,
                    show.notes(special_date),
                    ", ".join(show.tag_names),
                    show.score_value,
                ]
            )
    Log.success(f"wrote {len(shows)} rows to {cfg.output}")
