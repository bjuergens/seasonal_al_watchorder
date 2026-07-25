import csv

from .config import Config
from .score import warn_unused_weight_keys
from .show import Show
from .util import Log


def sort_shows(shows: list[Show], cfg: Config) -> list[Show]:
    """Watch order: the top pin_top non-skipped shows keep their AL Rank order, the
    rest are sorted by adjusted rank (ascending = watch first). Skipped shows sort
    like any other but don't consume a watch order number (see write_tsv)."""
    warn_unused_weight_keys(shows, cfg.rules)
    kept = [s for s in shows if not s.skip_reasons]
    pinned = kept[: cfg.pin_top]
    rest = [s for s in shows if s not in pinned]
    return pinned + sorted(rest, key=lambda s: s.score_value)


def write_tsv(shows: list[Show], cfg: Config) -> None:
    with cfg.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, dialect="excel-tab")
        writer.writerow(Show.COLUMNS)
        order = 1
        for show in shows:
            if show.skip_reasons:
                writer.writerow(show.tsv_row(None))
            else:
                writer.writerow(show.tsv_row(order))
                order += 1
    Log.success(f"wrote {len(shows)} rows to {cfg.output}")
