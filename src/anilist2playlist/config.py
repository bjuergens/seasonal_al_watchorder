import datetime
import importlib.resources
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .util import Log, Score

DEFAULT_CONFIG_PATH = Path("config.toml")

SEASONS = ("WINTER", "SPRING", "SUMMER", "FALL")

WEIGHT_KEYS = {"sequel", "side_story", "sources", "genres", "tags"}


@dataclass(frozen=True)
class Config:
    raw_file: Path
    output: Path
    pin_top: int
    tag_cutoff: int
    cache_max_age_hours: int
    weights: dict[str, Any]


def season_of(date: datetime.date) -> tuple[str, int]:
    return SEASONS[(date.month - 1) // 3], date.year


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
    weights = data["weights"]
    missing = WEIGHT_KEYS - set(weights)
    unknown = set(weights) - WEIGHT_KEYS
    if missing or unknown:
        raise ValueError(
            f"bad [weights] in {path}: missing {sorted(missing)}, unknown {sorted(unknown)} "
            "— use --regenerate-config to restore the defaults"
        )
    values = [(key, weights[key]) for key in ("sequel", "side_story")] + [
        (f"{table}.{key}", value)
        for table in ("sources", "genres", "tags")
        for key, value in weights[table].items()
    ]
    bad = [
        key
        for key, value in values
        if value != "skip" and not (isinstance(value, int) and not isinstance(value, bool))
    ]
    if bad:
        raise ValueError(f'bad weight values for {bad} in {path} — must be an integer or "skip"')

    def to_score(key: str, value: Any) -> Score:
        """A "skip" weight becomes a Score carrying its config key as the skip reason."""
        return Score(reasons=(key,)) if value == "skip" else Score(value)

    scored: dict[str, Any] = {
        "sequel": to_score("sequel", weights["sequel"]),
        "side_story": to_score("side story", weights["side_story"]),
    } | {
        table: {key: to_score(key, value) for key, value in weights[table].items()}
        for table in ("sources", "genres", "tags")
    }

    return Config(
        raw_file=Path(data["raw_file"]),
        output=Path(data["output"]),
        pin_top=int(data["pin_top"]),
        tag_cutoff=int(data["tag_cutoff"]),
        cache_max_age_hours=int(data["cache_max_age_hours"]),
        weights=scored,
    )
