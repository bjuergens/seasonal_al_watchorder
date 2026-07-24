import csv
import datetime
from typing import Any

from .config import Config
from .util import Log, Media

COLUMNS = [
    "title", "romaji", "source", "siteUrl", "status", "startDate",
    "genres", "duration", "studio", "AL-popularity", "watchorder",
    "sequel", "remake", "notes", "SPOILER tags SPOILER",
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
    if m["startDate"]["year"] is None:
        return False
    return any(
        node["startDate"]["year"] is not None
        and node["startDate"]["year"] < m["startDate"]["year"]
        for node in anime_relations(m, "ALTERNATIVE")
    )


def is_side_story(m: Media) -> bool:
    return bool(anime_relations(m, "PARENT"))


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
    if is_side_story(m):
        parts.append("side story")
    y, mo, d = m["startDate"]["year"], m["startDate"]["month"], m["startDate"]["day"]
    if y is None:
        Log.info(f"{m['title']['romaji']}: start date unknown")
        parts.append("start date unknown")
    elif mo is None or d is None:
        Log.info(f"{m['title']['romaji']}: start date incomplete ({start_date_str(m)})")
        parts.append("start date incomplete")
    else:
        start = datetime.date(y, mo, d)
        if start == special_date:
            parts.append("releases on special day")
        elif start > special_date:
            parts.append("releases after special")
    if any(t["rank"] is None for t in m["tags"]):
        parts.append("unranked tags")
    return ", ".join(parts)


def split_combo(combo: str) -> set[str]:
    # separator is " + " with spaces — a bare "+" can be part of a tag name ("LGBTQ+ Themes")
    return set(combo.split(" + "))


def combo_weights(table: dict[str, int], present: set[str]) -> int:
    """Sum weights of all " + "-joined keys whose genres/tags are all present."""
    return sum(w for combo, w in table.items() if split_combo(combo) <= present)


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


def warn_unused_weight_keys(media: list[Media], weights: dict[str, Any]) -> None:
    """Warn about configured sources/genres/tags that appear nowhere in the data (typos)."""
    sources = {m["source"] for m in media}
    genres = {g for m in media for g in m["genres"]}
    tags = {t["name"] for m in media for t in m["tags"]}
    for source in weights["sources"]:
        if source not in sources:
            Log.warn(f"weight source {source!r} appears nowhere in the data")
    for table, present in (("genres", genres), ("tags", tags)):
        for combo in weights[table]:
            for part in split_combo(combo):
                if part not in present:
                    Log.warn(f"weight {table} key {combo!r}: {part!r} appears nowhere in the data")


def sort_media(media: list[Media], cfg: Config) -> list[Media]:
    """Order by adjusted AL-popularity rank, ascending (lowest score = watch first)."""
    warn_unused_weight_keys(media, cfg.weights)
    for rank, m in enumerate(media, 1):  # raw data is popularity-sorted
        m["AL-popularity"] = rank
    ordered = sorted(media, key=lambda m: (score(m, cfg.weights), m["AL-popularity"]))
    for order, m in enumerate(ordered, 1):
        m["watchorder"] = order
    return ordered


def write_tsv(media: list[Media], cfg: Config, special_date: datetime.date) -> None:
    with cfg.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, dialect="excel-tab")
        writer.writerow(COLUMNS)
        for m in media:
            writer.writerow([
                m["title"]["english"] or m["title"]["romaji"],
                m["title"]["romaji"],
                m["source"],
                m["siteUrl"],
                m["status"],
                start_date_str(m),
                ", ".join(m["genres"]),
                m["duration"],
                ", ".join(s["name"] for s in m["studios"]["nodes"]),
                m["AL-popularity"],
                m["watchorder"],
                "yes" if is_sequel(m) else "",
                "yes" if is_remake(m) else "",
                notes(m, special_date),
                ", ".join(t["name"] for t in m["tags"]),
            ])
    Log.success(f"wrote {len(media)} rows to {cfg.output}")
