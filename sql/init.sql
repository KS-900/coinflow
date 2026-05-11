CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE raw.coin_markets (
id TEXT PRIMARY KEY UNIQUE,
symbol TEXT,
name TEXT ,
image TEXT NULL,
current_price NUMERIC NULL,
market_cap NUMERIC NULL,
market_cap_rank NUMERIC NULL,
fully_diluted_valuation NUMERIC NULL,
total_volume NUMERIC NULL,
high_24h NUMERIC NULL,
low_24h NUMERIC NULL,
price_change_24h NUMERIC NULL,
price_change_percentage_24h NUMERIC NULL,
market_cap_change_24h NUMERIC NULL,
market_cap_change_percentage_24h NUMERIC NULL,
circulating_supply NUMERIC NULL,
total_supply NUMERIC NULL,
max_supply NUMERIC NULL,
ath NUMERIC NULL,
ath_change_percentage NUMERIC NULL,
ath_date DATE NULL,
atl NUMERIC NULL,
atl_change_percentage NUMERIC NULL,
atl_date DATE NULL,
roi_times NUMERIC NULL,
roi_currency TEXT NULL,
roi_percentage NUMERIC NULL,
last_updated TIMESTAMP
);