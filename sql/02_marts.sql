CREATE OR REPLACE VIEW mart.content_performance AS
SELECT
    c.title,
    c.content_type,
    c.primary_genre,
    c.country,
    c.release_year,
    COUNT(a.activity_key) AS total_streams,
    SUM(a.watch_minutes) AS total_watch_minutes,
    ROUND(AVG(CASE WHEN a.completed THEN 1 ELSE 0 END)::NUMERIC, 3) AS completion_rate
FROM warehouse.dim_content c
LEFT JOIN warehouse.fact_streaming_activity a ON a.content_key = c.content_key
GROUP BY c.title, c.content_type, c.primary_genre, c.country, c.release_year;

CREATE OR REPLACE VIEW mart.revenue_trends AS
SELECT
    d.year,
    d.month,
    d.month_name,
    s.plan_name,
    COUNT(DISTINCT s.user_key) AS paid_users,
    SUM(s.monthly_price) AS monthly_recurring_revenue
FROM warehouse.fact_subscription s
JOIN warehouse.dim_date d ON d.date_key = s.start_date_key
GROUP BY d.year, d.month, d.month_name, s.plan_name;

CREATE OR REPLACE VIEW mart.user_engagement AS
SELECT
    u.country,
    u.age_group,
    a.device_type,
    COUNT(DISTINCT u.user_key) AS active_users,
    COUNT(a.activity_key) AS streams,
    SUM(a.watch_minutes) AS watch_minutes,
    ROUND(AVG(CASE WHEN a.completed THEN 1 ELSE 0 END)::NUMERIC, 3) AS completion_rate
FROM warehouse.fact_streaming_activity a
JOIN warehouse.dim_user u ON u.user_key = a.user_key
GROUP BY u.country, u.age_group, a.device_type;

CREATE OR REPLACE VIEW mart.retention_metrics AS
SELECT
    u.country,
    COUNT(DISTINCT s.user_key) AS subscribers,
    COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.user_key END) AS retained_users,
    COUNT(DISTINCT CASE WHEN s.status = 'cancelled' THEN s.user_key END) AS churned_users,
    ROUND(
        COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.user_key END)::NUMERIC
        / NULLIF(COUNT(DISTINCT s.user_key), 0),
        3
    ) AS retention_rate
FROM warehouse.fact_subscription s
JOIN warehouse.dim_user u ON u.user_key = s.user_key
GROUP BY u.country;
