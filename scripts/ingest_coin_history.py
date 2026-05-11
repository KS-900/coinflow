# this script is used to ingest coin history data into the database
import os
import requests
import psycopg2
import pandas as pd
from dotenv import load_dotenv
print("Starting coin history ingestion...")
load_dotenv()
def fetch_coin_history(coin_id, date):
    try:
        r = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={date}&x_cg_demo_api_key={os.getenv("API_KEY")}')
        r.raise_for_status()  # Check if the request was successful
        coin_history = r.json()
        return coin_history
    except requests.RequestException as e:
        print(f"Error fetching coin history for {coin_id} on {date}: {e}")
        return {}
print("Fetching coin history data...")
    
def transform_coin_history(coin_history):
    try:
        coin_history_df = pd.json_normalize(coin_history)
        coin_history_df['ingested_at'] = pd.Timestamp.now()
        return coin_history_df
    except Exception as e:
        print(f"Error transforming coin history: {e}")
        return pd.DataFrame()
print("Transformed coin history data into DataFrame.")
def load_coin_history(coin_history_df):
    if coin_history_df.empty:
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
        data_to_load = list(coin_history_df.itertuples(index=False, name=None))
        # insert query to insert data into database
        cur.execute("CREATE TABLE IF NOT EXISTS raw.coin_price_history"
        "(lands_price NUMERIC, market_cap NUMERIC, volume_arrays NUMERIC,ingested_at TIMESTAMP);")
        
        insert_query = """
        INSERT INTO raw.coin_price_history (coin_id, lands_price, market_cap, volume_arrays, ingested_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        cur.executemany(insert_query, data_to_load)
        print(f"Inserted {cur.rowcount} records into the database.")
    except Exception as e:
        print(f"Error loading coin history: {e}")  
    # commit changes and close connection  
    db_connection.commit()
    cur.execute("SELECT COUNT(*) FROM raw.coin_price_history;")
    count = cur.fetchone()[0]
    print(f"Total records in coin_price_history: {count}")
    db_connection.close()
print("Coin history ingestion completed.")
