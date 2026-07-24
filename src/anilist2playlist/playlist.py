import csv
import datetime
from typing import Any

from .config import Config
from .util import Log, Media, Score

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


def anime_relations(m: Media, relation_type: str) -> list[Media]:
    return [
        e["node"]
        for e in m["relations"]["edges"]
        if e["relationType"] == relation_type and e["node"]["type"] == "ANIME"
    ]


def is_sequel(m: Media) -> bool:
    return bool(anime_relations(m, "PREQUEL"))


def is_remake(m: Media) -> bool:
    """Remake: an alternative version of an anime that started in an earlier year."""
    if m["startDate"]["year"] is None:
        return False
    return any(
        node["startDate"]["year"] is not None and node["startDate"]["year"] < m["startDate"]["year"]
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


def split_combo(combo: str) -> set[str]:
    # separator is " + " with spaces — a bare "+" can be part of a tag name ("LGBTQ+ Themes")
    return set(combo.split(" + "))


def matching_weights(m: Media, weights: dict[str, Any]) -> list[Score]:
    """All weight entries that apply to this show."""
    matches: list[Score] = []
    if m["source"] in weights["sources"]:
        matches.append(weights["sources"][m["source"]])
    for table, present in (("genres", set(m["genres"])), ("tags", {t["name"] for t in m["tags"]})):
        matches.extend(w for combo, w in weights[table].items() if split_combo(combo) <= present)
    if is_sequel(m):
        matches.append(weights["sequel"])
    if is_side_story(m):
        matches.append(weights["side_story"])
    return matches


def releases_after_special(m: Media, special_date: datetime.date) -> bool:
    y, mo, d = m["startDate"]["year"], m["startDate"]["month"], m["startDate"]["day"]
    return None not in (y, mo, d) and datetime.date(y, mo, d) > special_date


def score(m: Media, weights: dict[str, Any], special_date: datetime.date) -> Score:
    s = sum(matching_weights(m, weights), Score(m["AL Rank"]))
    if releases_after_special(m, special_date):
        s += Score(reasons=("releases after special",))
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


def sort_media(media: list[Media], cfg: Config, special_date: datetime.date) -> list[Media]:
    """Watch order: the top pin_top non-skipped shows keep their AL Rank order, the
    rest are sorted by adjusted rank (ascending = watch first). Skipped shows sort
    like any other but get watchorder "skip" and don't consume a number."""
    warn_unused_weight_keys(media, cfg.weights)
    by_popularity = sorted(media, key=lambda m: m["popularity"] or 0, reverse=True)
    for rank, m in enumerate(by_popularity, 1):
        m["AL Rank"] = rank
        m["score"] = score(m, cfg.weights, special_date)
        m["skip"] = ", ".join(m["score"].reasons)
    kept = sorted((m for m in media if not m["score"].skip), key=lambda m: m["AL Rank"])
    pinned = kept[: cfg.pin_top]
    rest = [m for m in media if m not in pinned]
    ordered = pinned + sorted(rest, key=lambda m: (m["score"], m["AL Rank"]))
    order = 1
    for m in ordered:
        if m["score"].skip:
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
