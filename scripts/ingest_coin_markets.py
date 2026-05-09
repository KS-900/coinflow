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
        coins = r.json()
        return coins
    except Exception as e:
        print(f"Error fetching coin markets: {e}")
        return []

def transform_coin_markets(coins):
    try:
        coins_df = pd.json_normalize(coins)
        coins_df['ingested_at'] = pd.Timestamp.now()
        return coins_df
    except Exception as e:
        print(f"Error transforming coin markets: {e}")
        return pd.DataFrame()

def load_coin_markets(coins_df):
     # connect to database
    try:
        db_connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    # creating cursor
    cur = db_connection.cursor()
    # try insert data into database
    for _, coin in coins_df.iterrows():
        try:
            roi = coin.get("roi") or {}
            cur.execute(
                """
                 UPSERT raw.coin_markets (
                    id, symbol, name, image, current_price, market_cap, market_cap_rank, fully_diluted_valuation,
                    total_volume, high_24h, low_24h, price_change_24h, price_change_percentage_24h,
                    market_cap_change_24h, market_cap_change_percentage_24h, circulating_supply,
                    total_supply, max_supply, ath, ath_change_percentage, ath_date,
                    atl, atl_change_percentage, atl_date, roi_times, roi_currency,
                    roi_percentage, last_updated, ingested_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    coin['id'],
                    coin['symbol'],
                    coin['name'],
                    coin['image'],
                    coin['current_price'],
                    coin['market_cap'],
                    coin['market_cap_rank'],
                    coin['fully_diluted_valuation'],
                    coin['total_volume'],
                    coin['high_24h'],
                    coin['low_24h'],
                    coin['price_change_24h'],
                    coin['price_change_percentage_24h'],
                    coin['market_cap_change_24h'],
                    coin['market_cap_change_percentage_24h'],
                    coin['circulating_supply'],
                    coin['total_supply'],
                    coin['max_supply'],
                    coin['ath'],
                    coin['ath_change_percentage'],
                    coin['ath_date'],
                    coin['atl'],
                    coin['atl_change_percentage'],
                    coin['atl_date'],
                    roi.get("times"),
                    roi.get("currency"),
                    roi.get("percentage"),
                    coin['last_updated'],
                    coin['ingested_at']
                )
            )
            #dropping duplicates
            coin.drop_duplicates(inplace=True)
        except Exception as e:
                print(f"Error inserting data for coin {coin['id']}: {e}")
# commit changes and close connection
    db_connection.commit()
    db_connection.close()

 