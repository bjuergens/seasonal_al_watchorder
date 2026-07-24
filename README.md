# anilist2playlist

Fetch the seasonal anime list from [AniList](https://anilist.co) and turn it into a TSV playlist.

```sh
anilist2playlist fetch --special-date 2026-07-18   # season list → raw JSON cache
anilist2playlist build --special-date 2026-07-18   # cache → sorted TSV
anilist2playlist run --special-date 2026-07-18     # both
```

The season is selected by `--special-date`; weights and paths come from `config.toml`. The watch order is the AniList popularity rank adjusted by configurable weights (source, genre/tag combos, sequels, side stories).

Run from GitHub without cloning:

```sh
uvx --from git+https://github.com/bjuergens/seasonal_al_watchorder anilist2playlist run --special-date 2026-07-18
```

## Configuration

On first run a `config.toml` with the defaults is created in the working directory (next to the cache and TSV). Edit it, pass `--config PATH` for a different file, or use `--regenerate-config` to reset it.

## Development

```sh
uv run anilist2playlist run --special-date 2026-07-18
uv run mypy   # strict, must pass clean
```
