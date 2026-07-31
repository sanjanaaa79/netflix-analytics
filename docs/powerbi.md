# Power BI Dashboard Guide

Connect Power BI Desktop to PostgreSQL:

- Server: `localhost:5433`
- Database: `netflix_analytics`
- Username: `netflix`
- Password: `netflix`

Import these views from the `mart` schema:

- `content_performance`
- `revenue_trends`
- `user_engagement`
- `retention_metrics`

## Suggested Report Pages

### Executive Overview

- Cards: total streams, total watch minutes, active MRR, average completion rate
- Bar chart: top titles by watch minutes
- Donut chart: content type or genre split

### Revenue Trends

- Line chart: monthly recurring revenue by month
- Stacked column chart: MRR by plan name
- Table: paid users by plan

### User Engagement

- Matrix: country by age group with streams and watch minutes
- Bar chart: device type by watch minutes
- KPI: completion rate

### Retention

- Map or bar chart: retention rate by country
- Cards: retained users and churned users
- Table: subscribers, retained users, churned users, retention rate

## Example DAX Measures

```DAX
Total Watch Minutes = SUM(content_performance[total_watch_minutes])

Average Completion Rate = AVERAGE(content_performance[completion_rate])

Total MRR = SUM(revenue_trends[monthly_recurring_revenue])

Retention Rate = AVERAGE(retention_metrics[retention_rate])
```

## Notes

The `mart` views are intentionally denormalized for reporting. Keep Power BI
connected to the mart layer instead of the raw schema so dashboard logic stays
stable while ingestion details evolve.
