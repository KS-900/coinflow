# import necessary libraries
import os
import sys
import psycopg2
from dotenv import load_dotenv
import requests
import time
import datetime

# ------------------------------------------------------------------------------
# Load dotenv to read environment variables from .env file
# ------------------------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------------------------
# Create coin default settings
# ------------------------------------------------------------------------------   
DEFAULT_COINS = ("bitcoin", "ethereum", "tether", "binancecoin", "usd-coin", "ripple", "solana", "tron", 
                 "figure-heloc", "hyperliquid", "dogecoin", "usds", "leo-token", "rain", "zcash", "stellar", 
                 "canton-network", "cardano", "monero", "chainlink", "whitebit-coin", "the-open-network", 
                 "usd1-wlfi", "ethena-usd", "dai", "bitcoin-cash", "memecore", "hedera-hashgraph", 
                 "labra-finance", "litecoin", "sui", "hashnote-usd", "avalanche-2", "near-protocol", 
                 "paypal-usd", "shiba-inu", "crypto-com-chain", "tether-gold", "global-dollar-stablecoin-gds", 
                 "blackrock-usd-institutional-digital-liquidity-fund", "ondo-us-dollar-yield", "bittensor", 
                 "pax-gold", "ondo-finance", "mantle", "world-liberty-financial", "worldcoin", "ripple-usd", 
                 "polkadot", "aster-2", "htx-dao", "uniswap", "okb", "falcon-financial", "pi-network", "usdd", 
                 "sky", "bfusd", "internet-computer", "bitget-token", "audiera", "pepe", "morpho", 
                 "ethereum-classic", "dexe", "usdtb", "eutbl", "united-states-dollar", "quant-network", 
                 "blockchain-capital", "aave", "superstate", "cosmos", "siren-2", "kaspa", 
                 "janus-henderson-anemoy-treasury-fund", "kucoin-shares", "render-token", "algorand", 
                 "polygon-ecosystem", "nexo", "ethena", "stable-2", "venice-token", "just", "bianrensheng", 
                 "gatechain-token", "xdce-crowd", "beldex", "flare-network", "filecoin", "gho", "injective-protocol", 
                 "usual-usd", "aptos", "pump-fun", "ylds", "hash-2", "midnight-3", "jupiter-exchange")   
DEFAULT_DELAY_SEC = 2.5 # delay in seconds between API calls to avoid rate limits
DEFAULT_URL = "https://api.coingecko.com/api/v3"

 # ------------------------------------------------------------------------------
 # Parse coin IDs from environment variable or use defaults
 # ------------------------------------------------------------------------------
def _parse_coin_ids() -> list[str]:
        """Comma-separated COINGECKO_COIN_IDS overrides DEFAULT_COINS."""
        raw = os.getenv("COIN_IDS", "").strip()
        if not raw:
            return list(DEFAULT_COINS)
        return [c.strip() for c in raw.split(",") if c.strip()]

# ------------------------------------------------------------------------------
# Parse delay seconds from environment variable or use default
# ------------------------------------------------------------------------------
def _request_delay_sec() -> float:
    raw = os.getenv("API_DELAY_SECONDS", "").strip()
    if not raw:
        return DEFAULT_DELAY_SEC
    return max(0.0, float(raw))

# ------------------------------------------------------------------------------
# Parse base URL from environment variable or use default
# ------------------------------------------------------------------------------
def _base_url() -> str:
    raw = os.getenv("URL_COINGECKO", "").strip()
    if not raw:
        return DEFAULT_URL
    return raw

# ------------------------------------------------------------------------------
# deduplicate coin IDs while preserving order
# ------------------------------------------------------------------------------
def _dedupe_preserve_order(ids: list[str]) -> list[str]:
    # Duplicate IDs (e.g. copy-paste lists) waste API quota; keep first occurrence only.
    return list(dict.fromkeys(ids))

# ------------------------------------------------------------------------------
# Parse API key from environment variable or return None
# ------------------------------------------------------------------------------
def _optional_demo_api_key() -> str:
    """
    We only append it when set so free-tier/no-key setups still work.
    """
    return os.getenv("API_KEY") or os.getenv("CG_DEMO_API_KEY") or None

# ------------------------------------------------------------------------------
# Require database settings from environment variables
# ------------------------------------------------------------------------------
def _require_db_settings() -> dict[str, str]:
    """
    Require database settings from environment variables.
    Raises an exception if any required setting is missing.
    """
    keys = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_PORT")
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    return {k: os.environ[k] for k in keys}

# ------------------------------------------------------------------------------
# Fetch 1 coin and its category data from CoinGecko API
# ------------------------------------------------------------------------------
def _fetch_coin_and_category_data(
    session: requests.Session,
    id: str,
) -> list[dict]:
    """
    GET /coins/{id} — returns coin data including its category.
    """


    url = f"{DEFAULT_URL}/coins/{id}"
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=30)
            print(f"Fetched data for coin: {id} (attempt {attempt + 1}/{max_retries})")
            if response.status_code == 429:
                # Rate limit exceeded; wait and retry
                wait_raw = response.headers.get("Retry-After", "60")
                try:
                    wait_s = int(wait_raw)
                except ValueError:
                    wait_s = 60
                wait_s = min(max(wait_s, 1), 122)
                print(f"Rate limit exceeded on coin: {id} (attempt {attempt + 1}/{max_retries}). Waiting for {wait_s} seconds before retrying...")
                time.sleep(wait_s)
                continue
            response.raise_for_status()  # Raise an exception for other HTTP errors
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching coin data for {id}: {e}")
            return None  # Return None if all retries failed
    print(f"Giving up on fetching coin data for {id} after {max_retries} attempts.")
    return None  # Return None if all retries failed

# ------------------------------------------------------------------------------
# Fetch all coins and their category data from CoinGecko API
# ------------------------------------------------------------------------------
def _fetch_all_coins_and_categories(
    coin_ids: list[str],
    delay_sec: float = 2.5,
) -> dict[str, dict]:
    data = {} # Store coin data keyed by coin ID
    session = requests.Session()  # Use a session for connection pooling
    for i, coin_id in enumerate(coin_ids):
        print(f"Fetching data for coin {i + 1}/{len(coin_ids)}: {coin_id}")
        coin_data = _fetch_coin_and_category_data(session, id=coin_id)
        if coin_data is not None:
            data[coin_id] = coin_data
        else:
            print(f"Failed to fetch data for coin: {coin_id}")
        if i < len(coin_ids) - 1 and delay_sec > 0:
            time.sleep(delay_sec)
    return data

# ------------------------------------------------------------------------------
# Load coins from api to database
# ------------------------------------------------------------------------------
def load_coins_with_categories_to_database(data: dict[str, dict]):
    """
    Load coin data with categories into the database.
    Respects ideompotency by using upsert logic.
    """
    if not data:
        print("No coin data to load.")
        return
    
    settings = _require_db_settings()
    new_data = []
    _ingested_at = datetime.datetime.now(datetime.timezone.utc)  # Current UTC timestamp for _ingested_at
    conn = None
    try:
        conn= psycopg2.connect(
            host=settings["DB_HOST"],
            database=settings["DB_NAME"],
            user=settings["DB_USER"],
            password=settings["DB_PASSWORD"],
            port=settings["DB_PORT"]
        )
        for coin_id, coin_data in data.items():
            if coin_id is None or coin_data is None:
                print(f"Skipping coin {coin_id} due to missing id or categories.")
                continue
            new_coin_id = coin_data.get("id")
            categories = coin_data.get("categories") or []
            if new_coin_id is None or categories is None:
                print(f"Skipping coin {coin_id} due to missing id or categories.")
                continue
            for category in categories:
                new_data.append((new_coin_id, category, _ingested_at))
            if not new_data:
                print(f"No categories found for coin {coin_id}. Skipping insertion.")
                continue
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.coins_categories (
                coin_id TEXT NOT NULL,
                category TEXT NOT NULL,
                _ingested_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (coin_id, category)
            );
            """
        )
        insert_query = """
            INSERT INTO raw.coins_categories (coin_id, category, _ingested_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (coin_id, category) DO UPDATE SET 
                _ingested_at = EXCLUDED._ingested_at;
        """
        cur.executemany(insert_query, new_data)
        conn.commit()
        print(f"Inserted/Updated {len(data)} coins into the database.")
    except Exception:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(f"Error loading data into database: {e}")
    finally:
        if conn:
            conn.close()

def main():
    coin_ids = _parse_coin_ids()
    coin_ids = _dedupe_preserve_order(coin_ids)
    delay_sec = _request_delay_sec()
    print(f"Fetching data for {len(coin_ids)} coins with a delay of {delay_sec} seconds between requests.")
    try:
        data = _fetch_all_coins_and_categories(coin_ids, delay_sec)
    except Exception as e:
        print(f"Error fetching coin data: {e}")
        return
    print(f"Fetched data for {len(data)} coins. Now loading into the database.")
    try:
        load_coins_with_categories_to_database(data)
    except Exception as e:
        print(f"Error loading data into database: {e}")
        return
    print("Data ingestion completed successfully.")

if __name__ == "__main__":
    main()