CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE raw.coin_markets(
id TEXT,
symbol TEXT,
name TEXT,
image TEXT,
current_price NUMERIC,
market_cap NUMERIC,
market_cap_rank NUMERIC,
fully_diluted_valuation NUMERIC,
total_volume NUMERIC,
high_24h NUMERIC,
low_24h NUMERIC,
price_change_24h NUMERIC,
price_change_percentage_24h NUMERIC,
market_cap_change_24h NUMERIC,
market_cap_change_percentage_24h NUMERIC,
circulating_supply NUMERIC,
total_supply NUMERIC,
max_supply NUMERIC,
ath NUMERIC,
ath_change_percentage NUMERIC,
ath_date DATE,
atl NUMERIC,
atl_change_percentage NUMERIC,
atl_date DATE,
roi_times NUMERIC,
roi_currency TEXT,
roi_percentage NUMERIC,
last_updated TIMESTAMP
);