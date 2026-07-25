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


def split_combo(combo: str) -> set[str]:
    # separator is " + " with spaces — a bare "+" can be part of a tag name ("LGBTQ+ Themes")
    return set(combo.split(" + "))


def parse_weight_value(qualname: str, value: Any, path: Path) -> int | None:
    if value == "skip":
        return None
    # bool is an int subclass, so e.g. `sequel = true` would otherwise score as 1
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError(f'bad weight value for {qualname} in {path} — must be an integer or "skip"')


@dataclass(frozen=True)
class Rule:
    """One [weights] entry, normalized: matches a show when all needed features are present."""

    key: str  # display / skip-reason name from the config
    needs: frozenset[str]  # feature ids, e.g. {"genre:Isekai", "genre:Fantasy"}
    value: int | None  # None means skip

    @classmethod
    def flag(cls, toml_key: str, value: Any, path: Path) -> "Rule":
        """A fixed-flag weight: sequel or side_story."""
        key = toml_key.replace("_", " ")
        return cls(key, frozenset({key}), parse_weight_value(toml_key, value, path))

    @classmethod
    def source(cls, source: str, value: Any, path: Path) -> "Rule":
        needs = frozenset({f"source:{source}"})
        return cls(source, needs, parse_weight_value(f"sources.{source}", value, path))

    @classmethod
    def combo(cls, kind: str, combo: str, value: Any, path: Path) -> "Rule":
        """A combo weight; kind is the feature prefix, "genre" or "tag"."""
        needs = frozenset(f"{kind}:{part}" for part in split_combo(combo))
        return cls(combo, needs, parse_weight_value(f"{kind}s.{combo}", value, path))


@dataclass(frozen=True)
class Config:
    raw_file: Path
    output: Path
    pin_top: int
    tag_cutoff: int
    cache_max_age_hours: int
    rules: list[Rule]


def season_of(date: datetime.date) -> tuple[str, int]:
    return SEASONS[(date.month - 1) // 3], date.year


def parse_weights(weights: dict[str, Any], path: Path) -> list[Rule]:
    missing = WEIGHT_KEYS - set(weights)
    unknown = set(weights) - WEIGHT_KEYS
    if missing or unknown:
        raise ValueError(
            f"bad [weights] in {path}: missing {sorted(missing)}, unknown {sorted(unknown)} "
            "— use --regenerate-config to restore the defaults"
        )
    rules = [
        Rule.flag("sequel", weights["sequel"], path),
        Rule.flag("side_story", weights["side_story"], path),
    ]
    for source, value in weights["sources"].items():
        rules.append(Rule.source(source, value, path))
    for combo, value in weights["genres"].items():
        rules.append(Rule.combo("genre", combo, value, path))
    for combo, value in weights["tags"].items():
        rules.append(Rule.combo("tag", combo, value, path))
    return rules


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
        rules=parse_weights(data["weights"], path),
    )
