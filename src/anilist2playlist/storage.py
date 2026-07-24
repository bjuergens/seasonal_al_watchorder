import datetime
import json
from pathlib import Path

from .util import Log, Media


def write_raw(media: list[Media], season: str, year: int, path: Path) -> None:
    path.write_text(json.dumps({
        "fetched_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "season": season,
        "year": year,
        "media": media,
    }, indent=2, ensure_ascii=False))
    Log.success(f"wrote {len(media)} entries to {path}")


def read_raw(path: Path) -> list[Media]:
    data = json.loads(path.read_text())  # FileNotFoundError propagates loudly
    media: list[Media] = data["media"]
    return media
