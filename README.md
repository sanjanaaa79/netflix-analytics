# Netflix Analytics Data Platform

End-to-end analytics platform for streaming, subscription, and user activity data.
The project models a production-style flow: raw CSV ingestion, PostgreSQL warehouse
loading, analytical mart views, scheduled Airflow orchestration, FastAPI endpoints,
and Power BI-ready reporting tables.

## Tech Stack

- Python for ETL and local analytics generation
- PostgreSQL for the normalized data warehouse
- FastAPI for analytics API endpoints
- Apache Airflow for pipeline scheduling
- Docker Compose for local infrastructure
- Power BI for dashboard/reporting consumption

## Architecture

```text
CSV source data
  -> Python ETL
  -> raw PostgreSQL schema
  -> warehouse dimensions, bridges, and facts
  -> mart analytical views
  -> FastAPI endpoints and Power BI dashboards
```

## Warehouse Model

The PostgreSQL model separates raw ingestion from analytics-ready structures.

- `raw.netflix_titles`, `raw.users`, `raw.subscriptions`, `raw.streaming_activity`
- `warehouse.dim_user`, `warehouse.dim_content`, `warehouse.dim_date`
- `warehouse.bridge_content_genre`
- `warehouse.fact_subscription`, `warehouse.fact_streaming_activity`
- `mart.content_performance`, `mart.revenue_trends`, `mart.user_engagement`, `mart.retention_metrics`

## Project Structure

```text
api/
  main.py
dags/
  netflix_analytics_dag.py
dashboard/
  index.html
  styles.css
  app.js
data/
  raw/
  processed/
docs/
  powerbi.md
sql/
  01_schema.sql
  02_marts.sql
src/
  netflix_pipeline.py
  warehouse_etl.py
docker-compose.yml
Dockerfile.api
requirements.txt
```

## Run With Docker

Start PostgreSQL, FastAPI, and Airflow:

```powershell
docker compose up --build
```

In another terminal, load the warehouse:

```powershell
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5433"
$env:POSTGRES_DB="netflix_analytics"
$env:POSTGRES_USER="netflix"
$env:POSTGRES_PASSWORD="netflix"
python src/warehouse_etl.py
```

Services:

- FastAPI: `http://localhost:8011/docs`
- Airflow: `http://localhost:18080` with `admin` / `admin`
- PostgreSQL: `localhost:5433`, database `netflix_analytics`

## API Endpoints

- `GET /health`
- `GET /kpis`
- `GET /content-performance`
- `GET /revenue-trends`
- `GET /user-engagement`
- `GET /retention`

## Static Dashboard

The included static dashboard uses generated JSON metrics and can run without
Docker:

```powershell
python src/netflix_pipeline.py
python -m http.server 8000
```

Open:

```text
http://localhost:8000/dashboard/
```

After GitHub Pages deployment, the hosted dashboard is available at:

```text
https://bunnysunny24.github.io/Netflix-Analytics-Data-Platform/dashboard/
```

## Power BI

Use PostgreSQL as the data source and connect to the `mart` schema views. See
`docs/powerbi.md` for suggested pages, measures, and visuals.

## Resume Alignment

This project demonstrates:

- Normalized PostgreSQL warehouse design for streaming, subscription, and user activity data
- Automated Python and Airflow ETL from raw sources into analytical facts and dimensions
- FastAPI endpoints for KPI, engagement, revenue, retention, and content performance metrics
- Power BI-ready mart views using SQL transformations and aggregations
