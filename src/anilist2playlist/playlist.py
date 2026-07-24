import csv
from pathlib import Path
from typing import Any

from .config import Config
from .util import Log, Media

COLUMNS = [
    "title", "romaji", "source", "siteUrl", "status", "startDate",
    "genres", "duration", "studio", "AL-popularity", "watchorder",
    "sequel", "remake", "notes",
]

def anime_relations(m: Media, relation_type: str) -> list[Media]:
    return [
        e["node"] for e in m["relations"]["edges"]
        if e["relationType"] == relation_type and e["node"]["type"] == "ANIME"
    ]


def is_sequel(m: Media) -> bool:
    return bool(anime_relations(m, "PREQUEL"))


def is_remake(m: Media) -> bool:
    """Remake: an alternative version of an anime that started in an earlier year."""
    return any(
        node["startDate"]["year"] is not None
        and node["startDate"]["year"] < m["startDate"]["year"]
        for node in anime_relations(m, "ALTERNATIVE")
    )


def is_side_story(m: Media) -> bool:
    return bool(anime_relations(m, "PARENT"))


def notes(m: Media) -> str:
    parts = []
    if m["format"] != "TV":
        parts.append(m["format"])
    if is_side_story(m):
        parts.append("side story")
    return ", ".join(parts)


def combo_weights(table: dict[str, int], present: set[str]) -> int:
    """Sum weights of all "+"-joined keys whose genres/tags are all present."""
    return sum(w for combo, w in table.items() if set(combo.split("+")) <= present)


def score(m: Media, weights: dict[str, Any]) -> int:
    s: int = m["AL-popularity"]
    s += weights["sources"].get(m["source"], 0)
    s += combo_weights(weights["genres"], set(m["genres"]))
    s += combo_weights(weights["tags"], {t["name"] for t in m["tags"]})
    if is_sequel(m):
        s += weights["sequel"]
    if is_side_story(m):
        s += weights["side_story"]
    return s


def sort_media(media: list[Media], cfg: Config) -> list[Media]:
    """Order by adjusted AL-popularity rank, ascending (lowest score = watch first)."""
    for rank, m in enumerate(media, 1):  # raw data is popularity-sorted
        m["AL-popularity"] = rank
    ordered = sorted(media, key=lambda m: (score(m, cfg.weights), m["AL-popularity"]))
    for order, m in enumerate(ordered, 1):
        m["watchorder"] = order
    return ordered


def write_tsv(media: list[Media], path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f, dialect="excel-tab")
        writer.writerow(COLUMNS)
        for m in media:
            start = m["startDate"]
            writer.writerow([
                m["title"]["english"] or m["title"]["romaji"],
                m["title"]["romaji"],
                m["source"],
                m["siteUrl"],
                m["status"],
                f"{start['year']}-{start['month']}-{start['day']}",
                ", ".join(m["genres"]),
                m["duration"],
                ", ".join(s["name"] for s in m["studios"]["nodes"]),
                m["AL-popularity"],
                m["watchorder"],
                "yes" if is_sequel(m) else "",
                "yes" if is_remake(m) else "",
                notes(m),
            ])
    Log.success(f"wrote {len(media)} rows to {path}")
