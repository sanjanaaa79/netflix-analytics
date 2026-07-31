from __future__ import annotations

import os
from typing import Any

import psycopg2
from fastapi import FastAPI
from psycopg2.extras import RealDictCursor


app = FastAPI(
    title="Netflix Analytics API",
    description="Analytics endpoints backed by PostgreSQL warehouse mart views.",
    version="1.0.0",
)


def connection_params() -> dict[str, str]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": os.getenv("POSTGRES_DB", "netflix_analytics"),
        "user": os.getenv("POSTGRES_USER", "netflix"),
        "password": os.getenv("POSTGRES_PASSWORD", "netflix"),
    }


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg2.connect(**connection_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/kpis")
def kpis() -> dict[str, Any]:
    rows = fetch_all(
        """
        SELECT
            (SELECT COUNT(*) FROM warehouse.dim_content) AS total_titles,
            (SELECT COUNT(*) FROM warehouse.dim_user) AS total_users,
            (SELECT COUNT(*) FROM warehouse.fact_streaming_activity) AS total_streams,
            (SELECT COALESCE(SUM(watch_minutes), 0) FROM warehouse.fact_streaming_activity) AS watch_minutes,
            (SELECT COALESCE(SUM(monthly_price), 0) FROM warehouse.fact_subscription WHERE status = 'active') AS active_mrr,
            (SELECT ROUND(AVG(CASE WHEN completed THEN 1 ELSE 0 END)::NUMERIC, 3) FROM warehouse.fact_streaming_activity) AS completion_rate
        """
    )
    return rows[0]


@app.get("/content-performance")
def content_performance(limit: int = 10) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT *
        FROM mart.content_performance
        ORDER BY total_watch_minutes DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )


@app.get("/revenue-trends")
def revenue_trends() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT *
        FROM mart.revenue_trends
        ORDER BY year, month, plan_name
        """
    )


@app.get("/user-engagement")
def user_engagement() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT *
        FROM mart.user_engagement
        ORDER BY watch_minutes DESC
        """
    )


@app.get("/retention")
def retention() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT *
        FROM mart.retention_metrics
        ORDER BY retention_rate DESC NULLS LAST
        """
    )
