import datetime
from dataclasses import dataclass

from .config import Rule
from .show import Show
from .util import Log


@dataclass(frozen=True)
class Score:
    value: int
    skip_reasons: list[str]

    def __lt__(self, other: "Score") -> bool:
        return self.value < other.value  # ties don't matter, the stable sort decides

    @classmethod
    def of(cls, show: Show, rules: list[Rule], special_date: datetime.date) -> "Score":
        fs = features(show)
        matches = [(rule.key, rule.value) for rule in rules if rule.needs.issubset(fs)]
        reasons = [key for key, value in matches if value is None]
        if show.latest_start_date > special_date:
            reasons.append("releases after special")
        return cls(show.al_rank + sum(v for _, v in matches if v is not None), reasons)


def features(show: Show) -> set[str]:
    """The feature ids of a show that weight rules match against."""
    fs = {f"genre:{g}" for g in show.raw["genres"]}
    fs.update(f"tag:{t}" for t in show.tag_names)
    fs.add(f"source:{show.raw['source']}")
    if show.is_sequel:
        fs.add("sequel")
    if show.is_side_story:
        fs.add("side story")
    return fs


def warn_unused_weight_keys(shows: list[Show], rules: list[Rule]) -> None:
    """Warn about configured features that appear nowhere in the data (typos)."""
    known_features = {"sequel", "side story"}  # fixed config flags, can't be typos
    for show in shows:
        known_features.update(features(show))
    for rule in rules:
        for feature in sorted(rule.needs - known_features):
            Log.warn(f"weight {rule.key!r}: {feature!r} appears nowhere in the data")
