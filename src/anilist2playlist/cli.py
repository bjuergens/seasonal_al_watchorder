import argparse
from pathlib import Path

from .anilist import fetch_season
from .config import DEFAULT_CONFIG_PATH, Config, load_config, write_default_config
from .playlist import sort_media, write_tsv
from .storage import read_raw, write_raw
from .util import Log


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, help="path to TOML config file")
    parser.add_argument("--season", help="anime season (WINTER/SPRING/SUMMER/FALL)")
    parser.add_argument("--year", type=int, help="season year")
    parser.add_argument("--raw-file", type=Path, help="path to raw JSON cache")
    parser.add_argument("--output", type=Path, help="path to output TSV")
    parser.add_argument("--special-date", help="date of the special (ISO, e.g. 2026-07-18)")
    parser.add_argument(
        "--regenerate-config", action="store_true",
        help=f"overwrite {DEFAULT_CONFIG_PATH} with the defaults before running",
    )


def cmd_fetch(cfg: Config) -> None:
    Log.info(f"fetching {cfg.season} {cfg.year} from AniList")
    media = fetch_season(cfg.season, cfg.year)
    write_raw(media, cfg.season, cfg.year, cfg.raw_file)


def cmd_build(cfg: Config) -> None:
    if cfg.special_date is None:
        raise SystemExit("❌ special_date is required for build (config or --special-date)")
    media = read_raw(cfg.raw_file)
    Log.info(f"building playlist from {len(media)} entries in {cfg.raw_file}")
    write_tsv(sort_media(media, cfg), cfg.output)


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
        add_common_args(sub.add_parser(name, help=help_text))

    args = vars(parser.parse_args())
    command = args.pop("command")
    config_path = args.pop("config")
    if args.pop("regenerate_config"):
        write_default_config(config_path or DEFAULT_CONFIG_PATH)
    cfg = load_config(config_path, args)

    if command in ("fetch", "run"):
        cmd_fetch(cfg)
    if command in ("build", "run"):
        cmd_build(cfg)
