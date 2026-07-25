import datetime
from dataclasses import dataclass

from .config import Rule
from .util import Log


@dataclass(frozen=True)
class Score:
    value: int
    skip_reasons: list[str]

    @classmethod
    def of(
        cls,
        al_rank: int,
        latest_start_date: datetime.date,
        features: set[str],
        rules: list[Rule],
        special_date: datetime.date,
    ) -> "Score":
        rule_matches = [(rule.key, rule.value) for rule in rules if rule.needs.issubset(features)]
        skip_reasons = [key for key, value in rule_matches if value is None]
        if latest_start_date > special_date:
            skip_reasons.append("releases after special")
        return cls(al_rank + sum(v for _, v in rule_matches if v is not None), skip_reasons)


def warn_unused_weight_keys(feature_sets: list[set[str]], rules: list[Rule]) -> None:
    """Warn about configured features that appear nowhere in the data (typos)."""
    known_features = {"sequel", "side story"}  # fixed config flags, can't be typos
    for features in feature_sets:
        known_features.update(features)
    for rule in rules:
        for feature in sorted(rule.needs - known_features):
            Log.warn(f"weight {rule.key!r}: {feature!r} appears nowhere in the data")
