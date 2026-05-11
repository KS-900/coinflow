#This script is going to automatically ingest the data from the CoinGecko API and load it into the database.
#import required libraries
import os 
import psycopg2
import pandas as pd
import requests
from dotenv import load_dotenv 

load_dotenv()
# Send get request to API
def fetch_coin_markets():
    try:
        r = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&x_cg_demo_api_key={os.getenv("API_KEY")}')
        r.raise_for_status()  # Check if the request was successful
        coins = r.json()
        return coins
    except requests.exceptions.HTTPError as e: 
        print(f"HTTP Error: {e}")
        return []
    except requests.exceptions.RateLimitError as e:
        print(f"Rate Limit Error: {e}")
        return []
    except requests.exceptions.EmptyDataError as e:
        print(f"Empty Data Error: {e}")
        return []
    

def transform_coin_markets(coins):
    try:
        coins_df = pd.json_normalize(coins)
        #dropping duplicates
        coins_df.drop_duplicates(subset=['id'], inplace=True, keep="first")
        coins_df['ingested_at'] = pd.Timestamp.now()
        return coins_df
    except Exception as e:
        print(f"Error transforming coin markets: {e}")
        return pd.DataFrame()

def load_coin_markets(coins_df):
    # check if dataframe is empty
    if coins_df.empty:
        print("No data to load")
        raise Exception("No data to load")
     # connect to database
    db_connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
    try:
        # creating cursor
        cur = db_connection.cursor()
        # converting dataframe to list of tuples for insertion
        data_to_load = list(coins_df.itertuples(index=False, name=None))
        # upsert query to insert or update data based on the primary key (id)
        upsert_query = """
        INSERT INTO raw.coin_markets (id, symbol, name, image, current_price, market_cap, market_cap_rank, fully_diluted_valuation,
        total_volume, high_24h, low_24h, price_change_24h, price_change_percentage_24h, market_cap_change_24h, market_cap_change_percentage_24h, circulating_supply,
        total_supply, max_supply, ath, ath_change_percentage, ath_date, atl, atl_change_percentage, atl_date, roi_times, roi_currency, roi_percentage, last_updated, ingested_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        ingested_at = EXCLUDED.ingested_at
        """
        # executing the upsert query
        cur.executemany(upsert_query, data_to_load)
        print(f"Inserted/Updated {cur.rowcount} records into the database.")
    except Exception as e:
        print(f"Error loading coin markets: {e}")

# commit changes and close connection
    db_connection.commit()
    db_connection.close()

 