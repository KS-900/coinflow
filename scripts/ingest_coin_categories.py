# import necessary libraries
import os
import sys
import psycopg2
from dotenv import load_dotenv
import requests

# ------------------------------------------------------------------------------
# Load dotenv to read environment variables from .env file
# ------------------------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------------------------
# Create coin default settings
# ------------------------------------------------------------------------------   
DEFAULT_COINS = ("Bitcoin", "Ethereum", "Litecoin", "Cardano", "Polkadot", "Chainlink",
 "Stellar", "Uniswap", "Aave", "SushiSwap", "Avalanche", "Cosmos Hub", "Filecoin", "Flare", "Gate", "GHO", "Global Dollar",
 "Hedera", "HTX DAO", "Hyperliquid", "Internet Computer", "Janus Henderson Anemoy Treasury Fund", "Jupiter", "JUST", "Kaspa",
 "KuCoin", "LEO Token", "Mantle", "MemeCore", "Midnight", "Monero", "Morpho", "NEAR Protocol", "NEXO", "Official Trump", "OKB", "Ondo", "Ondo US Dollar Yield",
 "OUSG", "PAX Gold", "PayPal USD", "Pepe", "Pi Network", "POL (ex-MATIC)", "Polkadot", "Provenance Blockchain", "Pudgy Penguins",
 "Pump.fun", "Quant", "Rain", "Render", "Ripple USD", "Shiba Inu", "Siren", "Sky", "Solana", "Spiko EU T-Bills Money Market Fund",
  "Stable", "Stellar", "Sui", "Superstate Short Duration U.S. Government Securities Fund (USTB)", "Terra Luna Classic", "Tether", 
  "Tether Gold", "Toncoin", "TRON", "Uniswap", "United Stables", "USD1", "USDC", "USDD", "USDS", "USDtb", "Usual USD", "VeChain", "Venice Token", "WhiteBIT Coin",
 "Worldcoin", "World Liberty Financial", "XDC Network", "Zcash", "XRP")
DEFAULT_DELAY_SEC = 2.5
DEFAULT_URL = "https://api.coingecko.com/api/v3"

 # ------------------------------------------------------------------------------
 # Parse coin IDs from environment variable or use defaults
 # ------------------------------------------------------------------------------
def _parse_coin_ids() -> list[str]:
        """Comma-separated COINGECKO_COIN_IDS overrides DEFAULT_COINS."""
        raw = os.getenv("COINGECKO_COIN_IDS", "").strip()
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
    return os.getenv("COINGECKO_API_KEY") or os.getenv("CG_DEMO_API_KEY") or None

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
# Fetch categories from CoinGecko API
# ------------------------------------------------------------------------------
def _fetch_coin_and_category_data(
    session: requests.Session,
    base_url: str,
    api_key: str | None,
) -> list[dict]:
    """
    GET /coins/categories/list — returns id, name, market_cap, market_cap_change_24h, content, top_3_coins.

    Returns a list of category data dictionaries.
    """

    url = f"{base_url}/coins/categories/list"
    response = session.get(url,)
    response.raise_for_status()
    return response.json()
    