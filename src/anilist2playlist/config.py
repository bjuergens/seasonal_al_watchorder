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
class Config:
    season: str
    year: int
    raw_file: Path
    output: Path
    weights: dict[str, Any]


def write_default_config(path: Path) -> None:
    template = importlib.resources.files("anilist2playlist").joinpath("config.default.toml")
    path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    Log.success(f"wrote default config to {path}")


def current_season() -> tuple[str, int]:
    today = datetime.date.today()
    season = SEASONS[(today.month - 1) // 3]
    Log.warn(f"no season/year given, derived from today: {season} {today.year}")
    return season, today.year


def load_config(path: Path | None) -> Config:
    if path is None:
        path = DEFAULT_CONFIG_PATH
        if not path.exists():
            write_default_config(path)
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    season = data.get("season")
    year = data.get("year")
    if season is None or year is None:
        derived_season, derived_year = current_season()
        season = season or derived_season
        year = year or derived_year
    season = season.upper()
    if season not in SEASONS:
        raise ValueError(f"invalid season {season!r}, must be one of {SEASONS}")

    if "weights" not in data:
        raise ValueError(f"missing [weights] section in {path}")
    weights = data["weights"]
    missing = WEIGHT_KEYS - set(weights)
    unknown = set(weights) - WEIGHT_KEYS
    if missing or unknown:
        raise ValueError(
            f"bad [weights] in {path}: missing {sorted(missing)}, unknown {sorted(unknown)}"
        )

    return Config(
        season=season,
        year=int(year),
        raw_file=Path(data.get("raw_file", f"raw_{season}_{year}.json")),
        output=Path(data.get("output", f"playlist_{season}_{year}.tsv")),
        weights=weights,
    )
