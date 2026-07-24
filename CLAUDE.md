# CLAUDE.md

## Project

anilist2playlist ([github](https://github.com/bjuergens/seasonal_al_watchorder)):
fetches the seasonal anime list from AniList and builds a TSV watch playlist for
the seasonal special. Package in `src/anilist2playlist/`, runnable via
`uvx --from git+<repo>`.

### rules

- **`config.default.toml` is the single source of defaults.** No default values  in code. A required key missing from the user's config is an error whose message points at `--regenerate-config`.
- **CLI carries no config values.** Only `--config`, `--regenerate-config`, and  the required `--special-date`

### Tools

    uv run mypy                    # strict
    uv run ruff check --fix src && uv run ruff format src
    uv run anilist2playlist run --special-date 2026-07-18 --regenerate-config

### Verification

raw.json, playlist.tsv into the workdir. A real fetch is cheap (2 requests).


# General 

This section is the same for multiple projects. 

## Principles

- 📏 Big functions are fine. Extract when there's reuse or the established abstractions call for it.
- ⏳ No premature performance optimization.
- 📋 Plans define what and done when, not how. Challenge a plan when it fights reality; don't silently deviate.
- 🔊 Fail loudly. Throw errors, don't swallow them. Log failures clearly. If something is wrong, the developer should know immediately, not discover it later through subtle misbehavior.

## Emoji

Use consistently in code, commits, and logging.

### Commits

Human-made commits usually contain no emoji, while agent-made commits do.

`<emoji> <type>: <description>`

- ✨ feat: new feature
- 🐛 fix: bug fix
- 🔧 config: configuration changes
- 📦 deps: dependency changes
- 🧪 test: tests
- 📝 docs: documentation
- 🧹 refactor: cleanup (no behavior change)


### Logging

- ✅ success operations
- ❌ errors and failures
- ⚠️ warnings
