import argparse
import datetime
from pathlib import Path

from .anilist import fetch_season
from .config import DEFAULT_CONFIG_PATH, Config, load_config, season_of, write_default_config
from .playlist import sort_media, write_tsv
from .storage import read_raw, write_raw
from .util import Log


def cmd_fetch(cfg: Config, special_date: datetime.date) -> None:
    season, year = season_of(special_date)
    Log.info(f"fetching {season} {year} from AniList")
    media = fetch_season(season, year, cfg.tag_cutoff)
    write_raw(media, season, year, cfg.raw_file)


def cmd_build(cfg: Config, special_date: datetime.date) -> None:
    media = read_raw(cfg.raw_file, cfg.cache_max_age_hours)
    Log.info(f"building playlist from {len(media)} entries in {cfg.raw_file}")
    write_tsv(sort_media(media, cfg), cfg, special_date)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="anilist2playlist",
        description="Fetch the seasonal anime list from AniList and build a playlist TSV",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in [
        ("fetch", "fetch season list from AniList into a raw JSON cache"),
        ("build", "build the playlist TSV from the raw JSON cache"),
        ("run", "fetch and build in one go"),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--config", type=Path, help="path to TOML config file")
        p.add_argument(
            "--regenerate-config",
            action="store_true",
            help=f"overwrite the config file (--config or {DEFAULT_CONFIG_PATH}) "
            "with the defaults before running",
        )
        p.add_argument(
            "--special-date",
            required=True,
            type=datetime.date.fromisoformat,
            help="date of the special (ISO, e.g. 2026-07-18); also selects the season",
        )

    args = parser.parse_args()
    if args.regenerate_config:
        write_default_config(args.config or DEFAULT_CONFIG_PATH)
    cfg = load_config(args.config)

    if args.command in ("fetch", "run"):
        cmd_fetch(cfg, args.special_date)
    if args.command in ("build", "run"):
        cmd_build(cfg, args.special_date)
