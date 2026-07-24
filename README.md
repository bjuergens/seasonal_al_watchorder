# anilist2playlist

Fetch the seasonal anime list from [AniList](https://anilist.co) and turn it into a TSV playlist.

```sh
anilist2playlist fetch                            # season list → raw JSON cache
anilist2playlist build --special-date 2026-07-18  # cache → sorted TSV
anilist2playlist run --special-date 2026-07-18    # both
```

Season/year default to today's date. The watch order is the AniList popularity rank adjusted by configurable weights (source, genre/tag combos, sequels, side stories) — see the generated `config.toml`.

Run straight from the repo:

```sh
uvx --from git+https://github.com/bjuergens/seasonal_al_watchorder anilist2playlist run
```

## Configuration

On first run a `config.toml` with the defaults is created in the working directory (next to the cache and TSV). Edit it, pass `--config PATH` for a different file, or use `--regenerate-config` to reset it. CLI flags override config values.

## Development

```sh
uv run anilist2playlist run --special-date 2026-07-18
uv run mypy   # strict, must pass clean
```
