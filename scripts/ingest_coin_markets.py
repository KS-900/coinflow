"""
Ingest CoinGecko /coins/markets snapshot into raw.coin_markets.

- Same endpoint params (usd, market_cap_desc, per_page=100, page=1).
- Lands ingest lineage as _ingested_at (underscore prefix matches task spec & history ingest).
- Upsert on id keeps reruns idempotent without duplicate primary keys.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

import psycopg2
import requests
from dotenv import load_dotenv

BASE_URL = "https://api.coingecko.com/api/v3"

DEFAULT_MARKETS_PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": "100",
    "page": "1",
}


def _optional_demo_api_key() -> str | None:
    """
    Demo key improves CoinGecko rate limits. Omit the query param entirely
    when unset — passing x_cg_demo_api_key=None breaks anonymous/free-tier calls.

    COINGECKO_API_KEY matches ingest_coin_history.py; API_KEY is supported for older .env files.
    """
    return (
        os.getenv("COINGECKO_API_KEY")
        or os.getenv("CG_DEMO_API_KEY")
        or os.getenv("API_KEY")
        or None
    )


def _require_db_settings() -> dict[str, str]:
    keys = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_PORT")
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    return {k: os.environ[k] for k in keys}


def _roi_fields(coin: dict) -> tuple:
    """Flatten nested roi object from CoinGecko into three nullable columns."""
    roi = coin.get("roi")
    if isinstance(roi, dict):
        return roi.get("times"), roi.get("currency"), roi.get("percentage")
    return None, None, None


def fetch_coin_markets(
    session: requests.Session,
    api_key: str | None,
) -> list[dict]:
    """
    GET /coins/markets — returns a JSON array of coin objects on success.

    Retries on 429 with Retry-After (same pattern as ingest_coin_history.py).
    Returns [] on failure or if the payload is not a list (error JSON objects).
    """
    params = dict(DEFAULT_MARKETS_PARAMS)
    if api_key:
        params["x_cg_demo_api_key"] = api_key

    url = f"{BASE_URL}/coins/markets"
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Timeout avoids hung tasks under Airflow/cron when the API stalls.
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 429:
                wait_raw = r.headers.get("Retry-After", "60")
                try:
                    wait_s = int(wait_raw)
                except ValueError:
                    wait_s = 60
                wait_s = min(max(wait_s, 1), 120)
                print(
                    f"Rate limited on /coins/markets (attempt {attempt + 1}/{max_retries}); "
                    f"sleeping {wait_s}s"
                )
                time.sleep(wait_s)
                continue
            r.raise_for_status()
            payload = r.json()
            # CoinGecko errors are objects; happy path is always a list here.
            if not isinstance(payload, list):
                print(f"Unexpected markets payload type: {type(payload).__name__}")
                return []
            return payload
        except requests.RequestException as e:
            print(f"Request failed for /coins/markets: {e}")
            return []

    print(f"Giving up on /coins/markets after {max_retries} attempts (rate limit).")
    return []


def coins_to_rows(coins: list[dict], ingested_at: datetime) -> list[tuple]:
    """
    Build insert tuples and dedupe by coin id (first row wins — mirrors prior pandas drop_duplicates).

    Warehouse convention: store ingest time in UTC so staging/marts see consistent timelines.
    """
    seen: set[str] = set()
    rows: list[tuple] = []
    for coin in coins:
        cid = coin.get("id")
        if not cid or cid in seen:
            continue
        seen.add(cid)

        roi_times, roi_currency, roi_percentage = _roi_fields(coin)
        rows.append(
            (
                cid,
                coin.get("symbol"),
                coin.get("name"),
                coin.get("image"),
                coin.get("current_price"),
                coin.get("market_cap"),
                coin.get("market_cap_rank"),
                coin.get("fully_diluted_valuation"),
                coin.get("total_volume"),
                coin.get("high_24h"),
                coin.get("low_24h"),
                coin.get("price_change_24h"),
                coin.get("price_change_percentage_24h"),
                coin.get("market_cap_change_24h"),
                coin.get("market_cap_change_percentage_24h"),
                coin.get("circulating_supply"),
                coin.get("total_supply"),
                coin.get("max_supply"),
                coin.get("ath"),
                coin.get("ath_change_percentage"),
                coin.get("ath_date"),
                coin.get("atl"),
                coin.get("atl_change_percentage"),
                coin.get("atl_date"),
                roi_times,
                roi_currency,
                roi_percentage,
                coin.get("last_updated"),
                ingested_at,
            )
        )
    return rows


def ensure_ingested_at_column(cur) -> None:
    """
    Older databases (or sql/init.sql before _ingested_at) need this column once.

    ADD COLUMN IF NOT EXISTS keeps reruns safe without manual DDL — same idea as
    CREATE TABLE IF NOT EXISTS on the history ingest script.
    """
    cur.execute(
        """
        ALTER TABLE raw.coin_markets
        ADD COLUMN IF NOT EXISTS _ingested_at TIMESTAMPTZ;
        """
    )


def load_coin_markets(rows: list[tuple]) -> None:
    if not rows:
        print("No rows to load — skipping database write.")
        return

    settings = _require_db_settings()
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings["DB_HOST"],
            database=settings["DB_NAME"],
            user=settings["DB_USER"],
            password=settings["DB_PASSWORD"],
            port=settings["DB_PORT"],
        )
        cur = conn.cursor()
        ensure_ingested_at_column(cur)

        upsert_sql = """
            INSERT INTO raw.coin_markets (
                id, symbol, name, image, current_price, market_cap, market_cap_rank,
                fully_diluted_valuation, total_volume, high_24h, low_24h,
                price_change_24h, price_change_percentage_24h, market_cap_change_24h,
                market_cap_change_percentage_24h, circulating_supply, total_supply,
                max_supply, ath, ath_change_percentage, ath_date, atl,
                atl_change_percentage, atl_date, roi_times, roi_currency,
                roi_percentage, last_updated, _ingested_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                symbol = EXCLUDED.symbol,
                name = EXCLUDED.name,
                image = EXCLUDED.image,
                current_price = EXCLUDED.current_price,
                market_cap = EXCLUDED.market_cap,
                market_cap_rank = EXCLUDED.market_cap_rank,
                fully_diluted_valuation = EXCLUDED.fully_diluted_valuation,
                total_volume = EXCLUDED.total_volume,
                high_24h = EXCLUDED.high_24h,
                low_24h = EXCLUDED.low_24h,
                price_change_24h = EXCLUDED.price_change_24h,
                price_change_percentage_24h = EXCLUDED.price_change_percentage_24h,
                market_cap_change_24h = EXCLUDED.market_cap_change_24h,
                market_cap_change_percentage_24h = EXCLUDED.market_cap_change_percentage_24h,
                circulating_supply = EXCLUDED.circulating_supply,
                total_supply = EXCLUDED.total_supply,
                max_supply = EXCLUDED.max_supply,
                ath = EXCLUDED.ath,
                ath_change_percentage = EXCLUDED.ath_change_percentage,
                ath_date = EXCLUDED.ath_date,
                atl = EXCLUDED.atl,
                atl_change_percentage = EXCLUDED.atl_change_percentage,
                atl_date = EXCLUDED.atl_date,
                roi_times = EXCLUDED.roi_times,
                roi_currency = EXCLUDED.roi_currency,
                roi_percentage = EXCLUDED.roi_percentage,
                last_updated = EXCLUDED.last_updated,
                _ingested_at = EXCLUDED._ingested_at
        """
        cur.executemany(upsert_sql, rows)
        conn.commit()
        # psycopg2 rowcount after executemany is driver-dependent; len(rows) is exact.
        print(f"Upserted {len(rows)} row(s) into raw.coin_markets.")

        cur.execute("SELECT COUNT(*) FROM raw.coin_markets;")
        total = cur.fetchone()[0]
        print(f"Total rows in raw.coin_markets: {total}")
        cur.close()
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()


def main() -> int:
    load_dotenv()
    api_key = _optional_demo_api_key()

    print("Starting coin markets ingestion...")
    session = requests.Session()
    coins = fetch_coin_markets(session, api_key)

    if not coins:
        print(
            "Error: no market rows fetched — check network, API status, and credentials.",
            file=sys.stderr,
        )
        return 1

    ingested_at = datetime.now(timezone.utc)
    rows = coins_to_rows(coins, ingested_at)
    if not rows:
        print("Error: payload contained no usable coin rows.", file=sys.stderr)
        return 1

    try:
        load_coin_markets(rows)
    except Exception as e:
        print(f"Database error: {e}", file=sys.stderr)
        return 1

    print("Coin markets ingestion completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())