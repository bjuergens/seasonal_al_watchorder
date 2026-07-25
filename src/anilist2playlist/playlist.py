import csv
import datetime

from .config import Config
from .score import Scorer, warn_unused_weight_keys
from .util import Log, Media, is_remake, is_sequel, is_side_story

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


def start_date_str(m: Media) -> str:
    y, mo, d = m["startDate"]["year"], m["startDate"]["month"], m["startDate"]["day"]
    if y is None:
        return ""
    if mo is None:
        return str(y)
    if d is None:
        return f"{y}-{mo:02d}"
    return f"{y}-{mo:02d}-{d:02d}"


def notes(m: Media, special_date: datetime.date) -> str:
    parts = []
    if m["format"] != "TV":
        parts.append(m["format"])
    if is_sequel(m):
        parts.append("sequel")
    if is_side_story(m):
        parts.append("side story")
    if is_remake(m):
        parts.append("remake")
    y, mo, d = m["startDate"]["year"], m["startDate"]["month"], m["startDate"]["day"]
    if y is None:
        Log.info(f"{m['title']['romaji']}: start date unknown")
        parts.append("start date unknown")
    elif mo is None or d is None:
        Log.info(f"{m['title']['romaji']}: start date incomplete ({start_date_str(m)})")
        parts.append("start date incomplete")
    elif datetime.date(y, mo, d) == special_date:
        parts.append("releases on special day")
    if any(t["rank"] is None for t in m["tags"]):
        parts.append("unranked tags")
    return ", ".join(parts)


def sort_media(media: list[Media], cfg: Config, special_date: datetime.date) -> list[Media]:
    """Watch order: the top pin_top non-skipped shows keep their AL Rank order, the
    rest are sorted by adjusted rank (ascending = watch first). Skipped shows sort
    like any other but get watchorder "skip" and don't consume a number."""
    warn_unused_weight_keys(media, cfg.weights)
    by_popularity = sorted(media, key=lambda m: m["popularity"] or 0, reverse=True)
    for rank, m in enumerate(by_popularity, 1):
        m["AL Rank"] = rank
    scorer = Scorer(cfg.weights, special_date)
    scored = [(m, scorer.score(m)) for m in media]
    for m, s in scored:
        m["skip"] = ", ".join(s.skip_reasons)
    kept = sorted((m for m in media if not m["skip"]), key=lambda m: m["AL Rank"])
    pinned = kept[: cfg.pin_top]
    rest = [(m, s) for m, s in scored if m not in pinned]
    ordered = pinned + [m for m, _ in sorted(rest, key=lambda pair: pair[1])]
    order = 1
    for m in ordered:
        if m["skip"]:
            m["watchorder"] = "skip"
        else:
            m["watchorder"] = order
            order += 1
    return ordered


def write_tsv(media: list[Media], cfg: Config, special_date: datetime.date) -> None:
    with cfg.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, dialect="excel-tab")
        writer.writerow(COLUMNS)
        for m in media:
            writer.writerow(
                [
                    m["title"]["english"] or m["title"]["romaji"],
                    m["title"]["romaji"],
                    m["source"],
                    m["siteUrl"],
                    m["status"],
                    start_date_str(m),
                    ", ".join(m["genres"]),
                    m["duration"],
                    ", ".join(s["name"] for s in m["studios"]["nodes"]),
                    m["AL Rank"],
                    m["watchorder"],
                    m["skip"],
                    notes(m, special_date),
                    ", ".join(t["name"] for t in m["tags"]),
                ]
            )
    Log.success(f"wrote {len(media)} rows to {cfg.output}")
