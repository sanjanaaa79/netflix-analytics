"""Build curated analytics outputs for the Netflix dashboard."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "netflix_titles_sample.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "dashboard_metrics.json"


def split_multi_value(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


def parse_duration_minutes(row: dict[str, str]) -> int | None:
    duration = row.get("duration", "")
    if row.get("type") != "Movie" or not duration.endswith(" min"):
        return None
    return int(duration.replace(" min", ""))


def parse_seasons(row: dict[str, str]) -> int | None:
    duration = row.get("duration", "")
    if row.get("type") != "TV Show" or "Season" not in duration:
        return None
    return int(duration.split()[0])


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            added_date = parse_date(row["date_added"])
            rows.append(
                {
                    **row,
                    "release_year": int(row["release_year"]),
                    "date_added": added_date.date().isoformat() if added_date else None,
                    "year_added": added_date.year if added_date else None,
                    "genres": split_multi_value(row["listed_in"]),
                    "countries": split_multi_value(row["country"]),
                    "views_millions": float(row["views_millions"]),
                    "completion_rate": float(row["completion_rate"]),
                    "duration_minutes": parse_duration_minutes(row),
                    "seasons": parse_seasons(row),
                }
            )
    return rows


def count_values(rows: list[dict], key: str) -> list[dict]:
    counter: Counter[str] = Counter()
    for row in rows:
        values = row[key] if isinstance(row[key], list) else [row[key]]
        counter.update(values)
    return [{"name": name, "count": count} for name, count in counter.most_common()]


def release_trend(rows: list[dict]) -> list[dict]:
    trend: dict[int, Counter[str]] = defaultdict(Counter)
    for row in rows:
        trend[row["release_year"]][row["type"]] += 1
    return [
        {
            "year": year,
            "movies": counts.get("Movie", 0),
            "tvShows": counts.get("TV Show", 0),
            "total": sum(counts.values()),
        }
        for year, counts in sorted(trend.items())
    ]


def rating_mix(rows: list[dict]) -> list[dict]:
    counter = Counter(row["rating"] for row in rows)
    return [{"rating": rating, "count": count} for rating, count in counter.most_common()]


def top_titles(rows: list[dict], limit: int = 8) -> list[dict]:
    ranked = sorted(rows, key=lambda row: row["views_millions"], reverse=True)[:limit]
    return [
        {
            "title": row["title"],
            "type": row["type"],
            "country": row["country"],
            "releaseYear": row["release_year"],
            "viewsMillions": row["views_millions"],
            "completionRate": row["completion_rate"],
            "genres": row["genres"],
        }
        for row in ranked
    ]


def build_metrics(rows: list[dict]) -> dict:
    movies = [row for row in rows if row["type"] == "Movie"]
    shows = [row for row in rows if row["type"] == "TV Show"]
    movie_durations = [row["duration_minutes"] for row in movies if row["duration_minutes"]]
    show_seasons = [row["seasons"] for row in shows if row["seasons"]]

    return {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "kpis": {
            "totalTitles": len(rows),
            "movies": len(movies),
            "tvShows": len(shows),
            "countries": len({country for row in rows for country in row["countries"]}),
            "genres": len({genre for row in rows for genre in row["genres"]}),
            "totalViewsMillions": round(sum(row["views_millions"] for row in rows), 1),
            "avgCompletionRate": round(mean(row["completion_rate"] for row in rows), 3),
            "avgMovieDurationMinutes": round(mean(movie_durations), 1),
            "avgTvSeasons": round(mean(show_seasons), 1),
        },
        "contentType": count_values(rows, "type"),
        "genres": count_values(rows, "genres")[:10],
        "countries": count_values(rows, "countries")[:10],
        "releaseTrend": release_trend(rows),
        "ratings": rating_mix(rows),
        "topTitles": top_titles(rows),
    }


def main() -> None:
    rows = load_rows(RAW_PATH)
    metrics = build_metrics(rows)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} with {len(rows)} source rows.")


if __name__ == "__main__":
    main()
