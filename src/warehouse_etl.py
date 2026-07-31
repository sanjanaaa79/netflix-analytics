"""ETL pipeline for the PostgreSQL analytics warehouse.

The script can be run locally against the Postgres service from docker-compose:

    python src/warehouse_etl.py
"""

from __future__ import annotations

import csv
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SQL_DIR = ROOT / "sql"


def connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "netflix_analytics"),
        user=os.getenv("POSTGRES_USER", "netflix"),
        password=os.getenv("POSTGRES_PASSWORD", "netflix"),
    )


def read_csv(name: str) -> list[dict[str, str]]:
    with (RAW_DIR / name).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def run_sql_file(cursor, path: Path) -> None:
    cursor.execute(path.read_text(encoding="utf-8"))


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def duration_minutes(duration: str, content_type: str) -> int | None:
    if content_type == "Movie" and duration.endswith(" min"):
        return int(duration.replace(" min", ""))
    return None


def seasons(duration: str, content_type: str) -> int | None:
    if content_type == "TV Show" and "Season" in duration:
        return int(duration.split()[0])
    return None


def date_key(value: date) -> int:
    return int(value.strftime("%Y%m%d"))


def load_raw_tables(cursor) -> None:
    cursor.execute("TRUNCATE raw.streaming_activity, raw.subscriptions, raw.users, raw.netflix_titles CASCADE;")

    titles = read_csv("netflix_titles_sample.csv")
    execute_values(
        cursor,
        """
        INSERT INTO raw.netflix_titles (
            show_id, content_type, title, director, cast_members, country, date_added,
            release_year, rating, duration, listed_in, description, views_millions, completion_rate
        ) VALUES %s
        """,
        [
            (
                row["show_id"],
                row["type"],
                row["title"],
                row["director"],
                row["cast"],
                row["country"],
                row["date_added"],
                int(row["release_year"]),
                row["rating"],
                row["duration"],
                row["listed_in"],
                row["description"],
                float(row["views_millions"]),
                float(row["completion_rate"]),
            )
            for row in titles
        ],
    )

    users = read_csv("users.csv")
    execute_values(
        cursor,
        "INSERT INTO raw.users (user_id, signup_date, country, age_group, device_preference) VALUES %s",
        [(row["user_id"], row["signup_date"], row["country"], row["age_group"], row["device_preference"]) for row in users],
    )

    subscriptions = read_csv("subscriptions.csv")
    execute_values(
        cursor,
        """
        INSERT INTO raw.subscriptions (
            subscription_id, user_id, plan_name, monthly_price, start_date, end_date, status
        ) VALUES %s
        """,
        [
            (
                row["subscription_id"],
                row["user_id"],
                row["plan_name"],
                float(row["monthly_price"]),
                row["start_date"],
                row["end_date"] or None,
                row["status"],
            )
            for row in subscriptions
        ],
    )

    activity = read_csv("streaming_activity.csv")
    execute_values(
        cursor,
        """
        INSERT INTO raw.streaming_activity (
            activity_id, user_id, show_id, watched_at, watch_minutes, device_type, completed
        ) VALUES %s
        """,
        [
            (
                row["activity_id"],
                row["user_id"],
                row["show_id"],
                row["watched_at"],
                int(row["watch_minutes"]),
                row["device_type"],
                parse_bool(row["completed"]),
            )
            for row in activity
        ],
    )


def load_dimensions(cursor) -> None:
    cursor.execute(
        """
        TRUNCATE warehouse.fact_streaming_activity, warehouse.fact_subscription,
                 warehouse.bridge_content_genre, warehouse.dim_content,
                 warehouse.dim_user, warehouse.dim_date
        RESTART IDENTITY CASCADE;
        """
    )

    users = read_csv("users.csv")
    execute_values(
        cursor,
        """
        INSERT INTO warehouse.dim_user (user_id, signup_date, country, age_group, device_preference)
        VALUES %s
        """,
        [(row["user_id"], row["signup_date"], row["country"], row["age_group"], row["device_preference"]) for row in users],
    )

    titles = read_csv("netflix_titles_sample.csv")
    execute_values(
        cursor,
        """
        INSERT INTO warehouse.dim_content (
            show_id, content_type, title, country, release_year, rating,
            duration_minutes, seasons, primary_genre
        ) VALUES %s
        """,
        [
            (
                row["show_id"],
                row["type"],
                row["title"],
                row["country"].split(",")[0].strip(),
                int(row["release_year"]),
                row["rating"],
                duration_minutes(row["duration"], row["type"]),
                seasons(row["duration"], row["type"]),
                row["listed_in"].split(",")[0].strip(),
            )
            for row in titles
        ],
    )

    min_date = date(2023, 1, 1)
    max_date = date(2024, 12, 31)
    dates = []
    current = min_date
    while current <= max_date:
        dates.append((date_key(current), current, current.year, current.month, current.strftime("%B"), (current.month - 1) // 3 + 1))
        current += timedelta(days=1)
    execute_values(
        cursor,
        "INSERT INTO warehouse.dim_date (date_key, full_date, year, month, month_name, quarter) VALUES %s",
        dates,
    )

    cursor.execute("SELECT content_key, show_id FROM warehouse.dim_content;")
    content_lookup = {show_id: content_key for content_key, show_id in cursor.fetchall()}
    genre_rows = []
    for row in titles:
        for genre in [item.strip() for item in row["listed_in"].split(",") if item.strip()]:
            genre_rows.append((content_lookup[row["show_id"]], genre))
    execute_values(cursor, "INSERT INTO warehouse.bridge_content_genre (content_key, genre) VALUES %s", genre_rows)


def load_facts(cursor) -> None:
    cursor.execute("SELECT user_key, user_id FROM warehouse.dim_user;")
    user_lookup = {user_id: user_key for user_key, user_id in cursor.fetchall()}
    cursor.execute("SELECT content_key, show_id FROM warehouse.dim_content;")
    content_lookup = {show_id: content_key for content_key, show_id in cursor.fetchall()}

    subscriptions = read_csv("subscriptions.csv")
    execute_values(
        cursor,
        """
        INSERT INTO warehouse.fact_subscription (
            subscription_id, user_key, plan_name, monthly_price, start_date_key, end_date_key, status
        ) VALUES %s
        """,
        [
            (
                row["subscription_id"],
                user_lookup[row["user_id"]],
                row["plan_name"],
                float(row["monthly_price"]),
                int(row["start_date"].replace("-", "")),
                int(row["end_date"].replace("-", "")) if row["end_date"] else None,
                row["status"],
            )
            for row in subscriptions
        ],
    )

    activity = read_csv("streaming_activity.csv")
    fact_rows = []
    for row in activity:
        watched_at = datetime.strptime(row["watched_at"], "%Y-%m-%d %H:%M:%S")
        fact_rows.append(
            (
                row["activity_id"],
                user_lookup[row["user_id"]],
                content_lookup[row["show_id"]],
                date_key(watched_at.date()),
                watched_at,
                int(row["watch_minutes"]),
                row["device_type"],
                parse_bool(row["completed"]),
            )
        )
    execute_values(
        cursor,
        """
        INSERT INTO warehouse.fact_streaming_activity (
            activity_id, user_key, content_key, watched_date_key, watched_at,
            watch_minutes, device_type, completed
        ) VALUES %s
        """,
        fact_rows,
    )


def run_pipeline() -> None:
    with connect() as connection:
        with connection.cursor() as cursor:
            run_sql_file(cursor, SQL_DIR / "01_schema.sql")
            load_raw_tables(cursor)
            load_dimensions(cursor)
            load_facts(cursor)
            run_sql_file(cursor, SQL_DIR / "02_marts.sql")
    print("Warehouse ETL completed.")


if __name__ == "__main__":
    run_pipeline()
