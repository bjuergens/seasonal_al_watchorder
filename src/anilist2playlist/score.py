import datetime
from dataclasses import dataclass

from .config import Rule
from .util import Log, Media, anilist_date_to_date, is_sequel, is_side_story


@dataclass(frozen=True)
class Score:
    value: int
    skip_reasons: list[str]

    def __lt__(self, other: "Score") -> bool:
        return self.value < other.value  # ties don't matter, the stable sort decides


def features(m: Media) -> set[str]:
    """The feature ids of a show that weight rules match against."""
    fs = {f"genre:{g}" for g in m["genres"]}
    fs |= {f"tag:{t['name']}" for t in m["tags"]}
    fs.add(f"source:{m['source']}")
    if is_sequel(m):
        fs.add("sequel")
    if is_side_story(m):
        fs.add("side story")
    return fs


def warn_unused_weight_keys(media: list[Media], rules: list[Rule]) -> None:
    """Warn about configured features that appear nowhere in the data (typos)."""
    universe = {"sequel", "side story"}  # fixed config flags, can't be typos
    for m in media:
        universe |= features(m)
    for rule in rules:
        for feature in sorted(rule.needs - universe):
            Log.warn(f"weight {rule.key!r}: {feature!r} appears nowhere in the data")


class Scorer:
    """Applies the config's weight rules and skip logic, one show at a time."""

    def __init__(self, rules: list[Rule], special_date: datetime.date) -> None:
        self.rules = rules
        self.special_date = special_date

    def score(self, m: Media) -> Score:
        fs = features(m)
        matches = [(rule.key, rule.value) for rule in self.rules if rule.needs <= fs]
        reasons = [key for key, value in matches if value is None]
        start = anilist_date_to_date(m["startDate"])
        if start is not None and start > self.special_date:
            reasons.append("releases after special")
        value: int = m["AL Rank"] + sum(v for _, v in matches if v is not None)
        return Score(value, reasons)
