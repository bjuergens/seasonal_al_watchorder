import csv
from pathlib import Path

from .config import Config
from .util import Log, Media

CSV_COLUMNS = [
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


def score(m: Media, weights: dict[str, int]) -> int:
    genres = set(m["genres"])
    s: int = m["AL-popularity"]
    if m["source"] == "ORIGINAL":
        s += weights["original"]
    if m["source"] == "LIGHT_NOVEL":
        s += weights["light_novel"]
    if {"Action", "Adventure"} <= genres or {"Action", "Fantasy"} <= genres:
        s += weights["action_combo"]
    if any(t["name"] == "Isekai" for t in m["tags"]):
        s += weights["isekai"]
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


def write_csv(media: list[Media], path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
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
