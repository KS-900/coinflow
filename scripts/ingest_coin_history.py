import os
import requests
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def fetch_coin_history(coin_id, days):
    """Fetch history for all coins"""
    all_coin_history = {}
    try:
        for coin in coin_id:
            try:
                r = requests.get(
                    f'https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days={days}'
                )
                r.raise_for_status()
                all_coin_history[coin] = r.json()
                print(f"Fetched data for {coin}")
            except requests.RequestException as e:
                print(f"Error fetching coin history for {coin}: {e}")
                continue
        return all_coin_history
    except Exception as e:
        print(f"Unexpected error in fetch_coin_history: {e}")
        return {}

def transform_coin_history(coin_history):
    """Transform coin history data into DataFrame"""
    try:
        rows = []
        for coin_id, data in coin_history.items():
            row = {
                'coin_id': coin_id,
                'lands_price': data.get('prices', []),
                'market_cap': data.get('market_caps', []),
                'volume_arrays': data.get('total_volumes', []),
                'ingested_at': pd.Timestamp.now()
            }
            rows.append(row)
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error transforming coin history: {e}")
        return pd.DataFrame()

def load_coin_history(coin_history_df):
    """Load coin history into database"""
    if coin_history_df.empty:
        print("No data to load")
        return
    
    try:
        db_connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        
        cur = db_connection.cursor()
        
        # Create table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.coin_price_history (
                coin_id TEXT PRIMARY KEY,
                lands_price NUMERIC[][],
                market_cap NUMERIC[][],
                volume_arrays NUMERIC[][],
                ingested_at TIMESTAMP
            );
        """)
        
        data_to_load = list(coin_history_df.itertuples(index=False, name=None))
        
        insert_query = """
        INSERT INTO raw.coin_price_history (coin_id, lands_price, market_cap, volume_arrays, ingested_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (coin_id) DO UPDATE SET
        lands_price = EXCLUDED.lands_price,
        market_cap = EXCLUDED.market_cap,
        volume_arrays = EXCLUDED.volume_arrays,
        ingested_at = EXCLUDED.ingested_at
        """
        
        cur.executemany(insert_query, data_to_load)
        db_connection.commit()
        print(f"Inserted {cur.rowcount} records into the database.")
        
        cur.execute("SELECT COUNT(*) FROM raw.coin_price_history;")
        count = cur.fetchone()[0]
        print(f"Total records in coin_price_history: {count}")
        
        db_connection.close()
    except Exception as e:
        print(f"Error loading coin history: {e}")

if __name__ == "__main__":
    print("Starting coin history ingestion...")
    
    coin_id = ["bitcoin", "ethereum", "binancecoin", "ripple", "cardano", "dogecoin", "polkadot", "solana", "chainlink", "litecoin", "avalanche-2", "shiba-inu", "tron", "uniswap", "wrapped-bitcoin", "dai", "cosmos", "filecoin", "vechain", "algorand", "aave", "tezos", "theta-network", "decentraland", "elrond-erd-2", "the-sandbox", "axie-infinity", "flow", "hedera-hashgraph", "fantom", "near", "iota", "klaytn", "celo", "chiliz", "enjincoin", "zilliqa", "harmony", "decred", 
               "nexo", "huobi-token", "celsius", "dash", "sushi", "yearn-finance", "basic-attention-token", "compound-governance-token", "0x", "maker", "curve-dao-token", "pancakeswap-token", "safemoon", "gala", "chiliz", "the-graph", "safepal", "1inch", "huobi-btc", "huobi-eth", "huobi-usdt", "huobi-usdc", "huobi-busd", "huobi-eos", "huobi-xrp", "huobi-ltc", "huobi-bch", "huobi-link", "huobi-dot", "huobi-ada", "huobi-sol", "huobi-avax",
               "huobi-shiba-inu", "huobi-tron", "huobi-uniswap", "huobi-wrapped-bitcoin", "huobi-dai", "huobi-cosmos", "huobi-filecoin", "huobi-vechain", "huobi-algorand", "huobi-aave", "huobi-tezos", "huobi-theta-network", "huobi-decentraland", "huobi-elrond-erd-2", "huobi-the-sandbox", "huobi-axie-infinity", "huobi-flow", "huobi-hedera-hashgraph", "huobi-fantom", "huobi-near", "huobi-iota", "huobi-klaytn", "huobi-celo", "huobi-chiliz", "huobi-enjincoin", "huobi-zilliqa", "huobi-harmony", "huobi-decred",
               "huobi-nexo", "huobi-huobi-token", "huobi-celsius", "huobi-dash", "huobi-sushi", "huobi-yearn-finance", "huobi-basic-attention-token", "huobi-compound-governance-token", "huobi-0x", "huobi-maker", "huobi-curve-dao-token", "huobi-pancakeswap-token", "huobi-safemoon", "huobi-gala", "huobi-chiliz", "huobi-the-graph", "huobi-safepal", "huobi-1inch"]
    
    days = 90
    
    coin_history = fetch_coin_history(coin_id, days)
    print(f"Fetched history for {len(coin_history)} coins")
    
    coin_history_df = transform_coin_history(coin_history)
    print(f"Transformed {len(coin_history_df)} records into DataFrame")
    
    load_coin_history(coin_history_df)
    print("Coin history ingestion completed.")