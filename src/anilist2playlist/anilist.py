import json
import urllib.request

from .util import Log, Media

API_URL = "https://graphql.anilist.co/"
PER_PAGE = 50  # AniList hard cap

QUERY = """
query ($season: MediaSeason, $year: Int, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage }
    media(
      season: $season, seasonYear: $year,
      format_in: [TV, ONA, OVA], isAdult: false, type: ANIME,
      sort: POPULARITY_DESC
    ) {
      id idMal
      title { english romaji }
      startDate { year month day }
      status season format genres episodes duration
      source(version: 2) siteUrl popularity averageScore
      studios(isMain: true) { nodes { name } }
      tags { name rank }
      relations {
        edges {
          relationType(version: 2)
          node { id type format title { english romaji } startDate { year } }
        }
      }
    }
  }
}
"""


def fetch_season(season: str, year: int, tag_cutoff: int) -> list[Media]:
    media: list[Media] = []
    page = 1
    while True:
        body = json.dumps(
            {
                "query": QUERY,
                "variables": {"season": season, "year": year, "page": page, "perPage": PER_PAGE},
            }
        ).encode()
        request = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                # AniList's edge rejects the default urllib user agent with 403
                "Content-Type": "application/json",
                "User-Agent": "anilist2playlist",
            },
        )
        with urllib.request.urlopen(request) as response:  # raises on non-2xx
            payload = json.load(response)
        if "errors" in payload:
            raise RuntimeError(f"AniList GraphQL errors: {payload['errors']}")
        result = payload["data"]["Page"]
        for m in result["media"]:
            if any(t["rank"] is None for t in m["tags"]):
                Log.info(f"{m['title']['romaji']}: tag(s) without rank, treated as rank 0")
            m["tags"] = sorted(m["tags"], key=lambda t: t["rank"] or 0, reverse=True)[:tag_cutoff]
        media.extend(result["media"])
        Log.success(f"fetched page {page} ({len(result['media'])} entries)")
        if not result["pageInfo"]["hasNextPage"]:
            break
        page += 1
    return media
