import datetime
import importlib.resources
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .util import Log

DEFAULT_CONFIG_PATH = Path("config.toml")

SEASONS = ("WINTER", "SPRING", "SUMMER", "FALL")

WEIGHT_KEYS = {"sequel", "side_story", "sources", "genres", "tags"}


@dataclass(frozen=True)
class Rule:
    """One [weights] entry, normalized: matches a show when all needed features are present."""

    key: str  # display / skip-reason name from the config
    needs: frozenset[str]  # feature ids, e.g. {"genre:Isekai", "genre:Fantasy"}
    value: int | None  # None means skip


@dataclass(frozen=True)
class Config:
    raw_file: Path
    output: Path
    pin_top: int
    tag_cutoff: int
    cache_max_age_hours: int
    weights: list[Rule]


def season_of(date: datetime.date) -> tuple[str, int]:
    return SEASONS[(date.month - 1) // 3], date.year


def split_combo(combo: str) -> set[str]:
    # separator is " + " with spaces — a bare "+" can be part of a tag name ("LGBTQ+ Themes")
    return set(combo.split(" + "))


def parse_weights(weights: dict[str, Any], path: Path) -> list[Rule]:
    missing = WEIGHT_KEYS - set(weights)
    unknown = set(weights) - WEIGHT_KEYS
    if missing or unknown:
        raise ValueError(
            f"bad [weights] in {path}: missing {sorted(missing)}, unknown {sorted(unknown)} "
            "— use --regenerate-config to restore the defaults"
        )
    # (qualified name for errors, display key, needed features, raw value)
    entries: list[tuple[str, str, frozenset[str], Any]] = [
        ("sequel", "sequel", frozenset({"sequel"}), weights["sequel"]),
        ("side_story", "side story", frozenset({"side story"}), weights["side_story"]),
    ]
    for source, value in weights["sources"].items():
        entries.append((f"sources.{source}", source, frozenset({f"source:{source}"}), value))
    for combo, value in weights["genres"].items():
        needs = frozenset(f"genre:{part}" for part in split_combo(combo))
        entries.append((f"genres.{combo}", combo, needs, value))
    for combo, value in weights["tags"].items():
        needs = frozenset(f"tag:{part}" for part in split_combo(combo))
        entries.append((f"tags.{combo}", combo, needs, value))
    bad = [
        qualname
        for qualname, _, _, value in entries
        if value != "skip" and not (isinstance(value, int) and not isinstance(value, bool))
    ]
    if bad:
        raise ValueError(f'bad weight values for {bad} in {path} — must be an integer or "skip"')
    return [
        Rule(key, needs, None if value == "skip" else value) for _, key, needs, value in entries
    ]


def write_default_config(path: Path) -> None:
    template = importlib.resources.files("anilist2playlist").joinpath("config.default.toml")
    path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    Log.success(f"wrote default config to {path}")


def load_config(path: Path | None) -> Config:
    if path is None:
        path = DEFAULT_CONFIG_PATH
        if not path.exists():
            write_default_config(path)
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    missing_props = [
        key
        for key in ("raw_file", "output", "pin_top", "tag_cutoff", "cache_max_age_hours", "weights")
        if key not in data
    ]
    if missing_props:
        raise ValueError(
            f"missing {missing_props} in {path} — use --regenerate-config to restore the defaults"
        )

    return Config(
        raw_file=Path(data["raw_file"]),
        output=Path(data["output"]),
        pin_top=int(data["pin_top"]),
        tag_cutoff=int(data["tag_cutoff"]),
        cache_max_age_hours=int(data["cache_max_age_hours"]),
        weights=parse_weights(data["weights"], path),
    )
