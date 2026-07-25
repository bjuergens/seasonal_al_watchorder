from .util import Media


class Show:
    """One anime: read-only access to the raw AniList media entry plus the
    pipeline state computed for it (AL rank, skip reasons, watch order)."""

    def __init__(self, raw: Media) -> None:
        self.raw = raw
        self.al_rank = 0  # popularity rank, assigned in sort_shows
        self.skip = ""  # comma-joined skip reasons, assigned in sort_shows
        self.watchorder: int | None = None  # stays None for skipped shows

    @property
    def title(self) -> str:
        title: str = self.raw["title"]["english"] or self.raw["title"]["romaji"]
        return title

    @property
    def popularity(self) -> int:
        popularity: int = self.raw["popularity"] or 0
        return popularity

    @property
    def tag_names(self) -> list[str]:
        return [t["name"] for t in self.raw["tags"]]

    @property
    def has_unranked_tags(self) -> bool:
        return any(t["rank"] is None for t in self.raw["tags"])

    @property
    def studios(self) -> list[str]:
        return [s["name"] for s in self.raw["studios"]["nodes"]]

    def anime_relations(self, relation_type: str) -> list[Media]:
        return [
            e["node"]
            for e in self.raw["relations"]["edges"]
            if e["relationType"] == relation_type and e["node"]["type"] == "ANIME"
        ]

    @property
    def is_sequel(self) -> bool:
        return bool(self.anime_relations("PREQUEL"))

    @property
    def is_remake(self) -> bool:
        """Remake: an alternative version of an anime that started in an earlier year."""
        year = self.raw["startDate"]["year"]
        if year is None:
            return False
        return any(
            node["startDate"]["year"] is not None and node["startDate"]["year"] < year
            for node in self.anime_relations("ALTERNATIVE")
        )

    @property
    def is_side_story(self) -> bool:
        return bool(self.anime_relations("PARENT"))
