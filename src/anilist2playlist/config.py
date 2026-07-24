import datetime
import importlib.resources
import tomllib
from dataclasses import dataclass
from pathlib import Path

from typing import Any

from .util import Log

DEFAULT_CONFIG_PATH = Path("config.toml")


def write_default_config(path: Path) -> None:
    template = importlib.resources.files("anilist2playlist").joinpath("config.default.toml")
    path.write_text(template.read_text())
    Log.success(f"wrote default config to {path}")

SEASONS = ("WINTER", "SPRING", "SUMMER", "FALL")

# Watch order adjustments, applied to the AL-popularity rank (ascending = watch first).
# Overridable via [weights] in the config file.
DEFAULT_WEIGHTS: dict[str, Any] = {
    "sequel": 1000,
    "side_story": 500,
    # per-genre adjustment; "+"-joined keys match only if the show has all listed genres
    "genres": {"Action+Adventure": 5, "Action+Fantasy": 5},
    "sources": {"ORIGINAL": -10, "LIGHT_NOVEL": 5},  # per-source adjustment
    "tags": {"Isekai": 5},  # per-tag adjustment, applied if the tag is in the top 10
}


@dataclass(frozen=True)
class Config:
    season: str
    year: int
    raw_file: Path
    output: Path
    special_date: datetime.date | None
    weights: dict[str, Any]  # DEFAULT_WEIGHTS shape: ints plus the "tags" sub-table


def current_season() -> tuple[str, int]:
    today = datetime.date.today()
    season = SEASONS[(today.month - 1) // 3]
    Log.warn(f"no season/year given, derived from today: {season} {today.year}")
    return season, today.year


def load_config(path: Path | None, cli_overrides: dict[str, Any]) -> Config:
    """Merge config sources. Precedence: CLI flag > config file > derived default."""
    if path is None:
        path = DEFAULT_CONFIG_PATH
        if not path.exists():
            write_default_config(path)
    data = tomllib.loads(path.read_text())

    merged = {**data, **{k: v for k, v in cli_overrides.items() if v is not None}}

    season = merged.get("season")
    year = merged.get("year")
    if season is None or year is None:
        derived_season, derived_year = current_season()
        season = season or derived_season
        year = year or derived_year
    season = season.upper()
    if season not in SEASONS:
        raise ValueError(f"invalid season {season!r}, must be one of {SEASONS}")

    special_date = merged.get("special_date")
    if isinstance(special_date, str):
        special_date = datetime.date.fromisoformat(special_date)

    weight_overrides = merged.get("weights", {})
    unknown = set(weight_overrides) - set(DEFAULT_WEIGHTS)
    if unknown:
        raise ValueError(f"unknown weight keys {sorted(unknown)}, known: {sorted(DEFAULT_WEIGHTS)}")

    return Config(
        season=season,
        year=int(year),
        raw_file=Path(merged.get("raw_file", f"raw_{season}_{year}.json")),
        output=Path(merged.get("output", f"playlist_{season}_{year}.tsv")),
        special_date=special_date,
        weights={**DEFAULT_WEIGHTS, **weight_overrides},
    )
