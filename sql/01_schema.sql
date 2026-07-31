CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS raw.netflix_titles (
    show_id TEXT PRIMARY KEY,
    content_type TEXT NOT NULL,
    title TEXT NOT NULL,
    director TEXT,
    cast_members TEXT,
    country TEXT,
    date_added DATE,
    release_year INTEGER,
    rating TEXT,
    duration TEXT,
    listed_in TEXT,
    description TEXT,
    views_millions NUMERIC(10, 2),
    completion_rate NUMERIC(5, 4)
);

CREATE TABLE IF NOT EXISTS raw.users (
    user_id TEXT PRIMARY KEY,
    signup_date DATE NOT NULL,
    country TEXT NOT NULL,
    age_group TEXT NOT NULL,
    device_preference TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.subscriptions (
    subscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    monthly_price NUMERIC(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.streaming_activity (
    activity_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    show_id TEXT NOT NULL,
    watched_at TIMESTAMP NOT NULL,
    watch_minutes INTEGER NOT NULL,
    device_type TEXT NOT NULL,
    completed BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_user (
    user_key SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    signup_date DATE NOT NULL,
    country TEXT NOT NULL,
    age_group TEXT NOT NULL,
    device_preference TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_content (
    content_key SERIAL PRIMARY KEY,
    show_id TEXT UNIQUE NOT NULL,
    content_type TEXT NOT NULL,
    title TEXT NOT NULL,
    country TEXT,
    release_year INTEGER,
    rating TEXT,
    duration_minutes INTEGER,
    seasons INTEGER,
    primary_genre TEXT
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.bridge_content_genre (
    content_key INTEGER REFERENCES warehouse.dim_content(content_key),
    genre TEXT NOT NULL,
    PRIMARY KEY (content_key, genre)
);

CREATE TABLE IF NOT EXISTS warehouse.fact_subscription (
    subscription_key SERIAL PRIMARY KEY,
    subscription_id TEXT UNIQUE NOT NULL,
    user_key INTEGER REFERENCES warehouse.dim_user(user_key),
    plan_name TEXT NOT NULL,
    monthly_price NUMERIC(10, 2) NOT NULL,
    start_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    end_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_streaming_activity (
    activity_key SERIAL PRIMARY KEY,
    activity_id TEXT UNIQUE NOT NULL,
    user_key INTEGER REFERENCES warehouse.dim_user(user_key),
    content_key INTEGER REFERENCES warehouse.dim_content(content_key),
    watched_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    watched_at TIMESTAMP NOT NULL,
    watch_minutes INTEGER NOT NULL,
    device_type TEXT NOT NULL,
    completed BOOLEAN NOT NULL
);
