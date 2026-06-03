"""
Ingest CoinGecko market_chart data into raw.coin_price_history.

Design notes (see TASK.md Phase 2):
- Raw layer stores API-shaped arrays; dbt stg_coin_price_history unnests them.
- Upsert on (coin_id, chart_days) keeps reruns idempotent (no duplicate logical rows).
- JSONB columns match nested [[unix_ms, value], ...] payloads and are easy to explode in SQL.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import Json

# ------------------------------------------------------------------------------
# Defaults match TASK.md examples; override via env for Airflow / local runs
# without editing code (12-factor style config).
# ------------------------------------------------------------------------------
DEFAULT_COIN_IDS = ("bitcoin", "ethereum", "solana")
DEFAULT_CHART_DAYS = 90
# CoinGecko free tier is ~10–30 calls/min; spacing requests avoids 429 bursts.
DEFAULT_REQUEST_DELAY_SEC = 2.5
BASE_URL = "https://api.coingecko.com/api/v3"


def _parse_coin_ids() -> list[str]:
    """Comma-separated COINGECKO_COIN_IDS overrides DEFAULT_COIN_IDS."""
    raw = os.getenv("COINGECKO_COIN_IDS", "").strip()
    if not raw:
        return list(DEFAULT_COIN_IDS)
    return [c.strip().lower() for c in raw.split(",") if c.strip()]


def _dedupe_preserve_order(ids: list[str]) -> list[str]:
    # Duplicate IDs (e.g. copy-paste lists) waste API quota; keep first occurrence only.
    return list(dict.fromkeys(ids))


def _chart_days() -> int:
    raw = os.getenv("COINGECKO_CHART_DAYS", "").strip()
    if not raw:
        return DEFAULT_CHART_DAYS
    return max(1, int(raw))


def _request_delay_sec() -> float:
    raw = os.getenv("COINGECKO_REQUEST_DELAY_SEC", "").strip()
    if not raw:
        return DEFAULT_REQUEST_DELAY_SEC
    return max(0.0, float(raw))


def _optional_demo_api_key() -> str | None:
    """
    TASK.md: demo key is optional but raises rate limits.
    We only append it when set so free-tier/no-key setups still work.
    """
    return os.getenv("COINGECKO_API_KEY") or os.getenv("CG_DEMO_API_KEY") or None


def _require_db_settings() -> dict[str, str]:
    keys = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    return {k: os.environ[k] for k in keys}


def fetch_market_chart(
    session: requests.Session,
    coin_id: str,
    chart_days: int,
    api_key: str | None,
) -> dict | None:
    """
    GET /coins/{id}/market_chart — returns prices, market_caps, total_volumes arrays.

    Returns None on hard failure so callers can continue other coins; raises only
    for caller-controlled fatal cases if we extend this later.
    """
    params: dict[str, str] = {"vs_currency": "usd", "days": str(chart_days)}
    if api_key:
        params["x_cg_demo_api_key"] = api_key

    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Bounded timeout: hung connections should not block orchestration forever.
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 429:
                # Respect Retry-After when present; backoff avoids hammering the API.
                wait_raw = r.headers.get("Retry-After", "60")
                try:
                    wait_s = int(wait_raw)
                except ValueError:
                    wait_s = 60
                wait_s = min(max(wait_s, 1), 120)
                print(
                    f"Rate limited on {coin_id} (attempt {attempt + 1}/{max_retries}); "
                    f"sleeping {wait_s}s"
                )
                time.sleep(wait_s)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"Error fetching market_chart for {coin_id}: {e}")
            return None
    print(f"Giving up on {coin_id} after {max_retries} attempts (rate limit).")
    return None


def fetch_all_coin_charts(
    coin_ids: list[str],
    chart_days: int,
    delay_sec: float,
    api_key: str | None,
) -> dict[str, dict]:
    """Fetch each coin sequentially with delay — respects CoinGecko per-minute caps."""
    out: dict[str, dict] = {}
    session = requests.Session()
    for i, cid in enumerate(coin_ids):
        payload = fetch_market_chart(session, cid, chart_days, api_key)
        if payload is not None:
            out[cid] = payload
            print(f"Fetched chart for {cid}")
        # Do not sleep after the last coin, saves one unnecessary pause.
        if i < len(coin_ids) - 1 and delay_sec > 0:
            time.sleep(delay_sec)
    return out


def load_coin_price_history(rows: list[tuple]) -> None:
    """
    Insert / upsert into raw.coin_price_history.

    Composite PK (coin_id, chart_days): same coin can hold both e.g. 30d and 90d
    windows without overwriting; rerunning the same window updates arrays in place
    (idempotent load per TASK.md).
    """
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
        )
        cur = conn.cursor()
        # JSONB: psycopg2 adapts Json(); avoids fragile NUMERIC[][] rectangle rules.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.coin_price_history (
                coin_id TEXT NOT NULL,
                chart_days INTEGER NOT NULL,
                prices JSONB NOT NULL,
                market_caps JSONB NOT NULL,
                total_volumes JSONB NOT NULL,
                _ingested_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (coin_id, chart_days)
            );
            """
        )

        insert_sql = """
            INSERT INTO raw.coin_price_history (
                coin_id, chart_days, prices, market_caps, total_volumes, _ingested_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (coin_id, chart_days) DO UPDATE SET
                prices = EXCLUDED.prices,
                market_caps = EXCLUDED.market_caps,
                total_volumes = EXCLUDED.total_volumes,
                _ingested_at = EXCLUDED._ingested_at;
        """
        cur.executemany(insert_sql, rows)
        conn.commit()
        # executemany rowcount is driver-dependent; len(rows) is the truthful batch size.
        print(f"Upserted {len(rows)} row(s) into raw.coin_price_history.")

        cur.execute("SELECT COUNT(*) FROM raw.coin_price_history;")
        total = cur.fetchone()[0]
        print(f"Total rows in raw.coin_price_history: {total}")
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
    coin_ids = _dedupe_preserve_order(_parse_coin_ids())
    chart_days = _chart_days()
    delay_sec = _request_delay_sec()
    api_key = _optional_demo_api_key()

    print("Starting coin history ingestion...")
    print(f"Coins: {coin_ids}, chart_days={chart_days}")

    charts = fetch_all_coin_charts(coin_ids, chart_days, delay_sec, api_key)

    if len(charts) < len(coin_ids):
        missing = set(coin_ids) - set(charts)
        print(f"Warning: no payload for {len(missing)} coin(s): {sorted(missing)}")

    if not charts:
        print(
            "Error: zero charts fetched — nothing to load. "
            "Check network, API status, and coin IDs.",
            file=sys.stderr,
        )
        return 1

    ingested_at = datetime.now(timezone.utc)
    rows = []
    for cid, data in charts.items():
        rows.append(
            (
                cid,
                chart_days,
                Json(data.get("prices") or []),
                Json(data.get("market_caps") or []),
                Json(data.get("total_volumes") or []),
                ingested_at,
            )
        )

    try:
        load_coin_price_history(rows)
    except Exception as e:
        print(f"Database error: {e}", file=sys.stderr)
        return 1

    print("Coin history ingestion completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
