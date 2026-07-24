import datetime
import json
from pathlib import Path

from .util import Log, Media

CACHE_VERSION = 2  # bump when the fetched schema changes; stale caches must be re-fetched


def write_raw(media: list[Media], season: str, year: int, path: Path) -> None:
    path.write_text(json.dumps({
        "version": CACHE_VERSION,
        "fetched_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "season": season,
        "year": year,
        "media": media,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    Log.success(f"wrote {len(media)} entries to {path}")


def read_raw(path: Path) -> list[Media]:
    data = json.loads(path.read_text(encoding="utf-8"))  # FileNotFoundError propagates loudly
    if data.get("version") != CACHE_VERSION:
        raise ValueError(
            f"cache {path} has version {data.get('version')}, "
            f"expected {CACHE_VERSION} — re-run fetch"
        )
    age = datetime.datetime.now(datetime.UTC) - datetime.datetime.fromisoformat(data["fetched_at"])
    if age > datetime.timedelta(hours=24):
        Log.warn(f"cache {path} is {age.days}d {age.seconds // 3600}h old — consider re-running fetch")
    media: list[Media] = data["media"]
    return media
