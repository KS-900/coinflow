#import required libraries
import os
import psycopg2   
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
# Send get request to API
r=requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&x_cg_demo_api_key=CG-YDeKBMcSiDvrAtRj3ENdvpQc')
coins= r.json()



# connect to database
db_connection = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"))

# creating cursor
cur = db_connection.cursor()


# map data from api 
for coin in coins:
    id = coin['id']
    symbol = coin['symbol']
    name = coin['name']
    image = coin['image']
    current_price = coin['current_price']
    market_cap = coin['market_cap']
    market_cap_rank = coin['market_cap_rank']
    fully_diluted_valuation = coin['fully_diluted_valuation']
    total_volume = coin['total_volume']
    high_24h = coin['high_24h']
    low_24h = coin['low_24h']
    price_change_24h = coin['price_change_24h']
    price_change_percentage_24h = coin['price_change_percentage_24h']
    market_cap_change_24h = coin['market_cap_change_24h']
    market_cap_change_percentage_24h = coin['market_cap_change_percentage_24h']
    circulating_supply = coin['circulating_supply']
    total_supply = coin['total_supply']
    max_supply = coin['max_supply']
    ath = coin['ath']
    ath_change_percentage = coin['ath_change_percentage']
    ath_date = coin['ath_date']
    atl = coin['atl']
    atl_change_percentage = coin['atl_change_percentage']
    atl_date = coin['atl_date']
    roi = coin.get("roi") or {}

    roi_times = roi.get("times")
    roi_currency = roi.get("currency")
    roi_percentage = roi.get("percentage")
    last_updated = coin['last_updated']
    # try insert data into database
    try:
        cur.execute(
            "INSERT INTO raw.coin_markets "
            "(id, symbol, name, image, current_price, market_cap, market_cap_rank, fully_diluted_valuation, total_volume, high_24h, " \
            "low_24h, price_change_24h, price_change_percentage_24h, market_cap_change_24h, market_cap_change_percentage_24h, circulating_supply, total_supply, max_supply, " \
            "ath, ath_change_percentage, ath_date, atl, atl_change_percentage, atl_date, roi_times, roi_currency, roi_percentage, last_updated) VALUES "
            "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                id,
                symbol,
                name,
                image,
                current_price,
                market_cap,
                market_cap_rank,
                fully_diluted_valuation,
                total_volume,
                high_24h,
                low_24h,
                price_change_24h,
                price_change_percentage_24h,
                market_cap_change_24h,
                market_cap_change_percentage_24h,
                circulating_supply,
                total_supply,
                max_supply,
                ath,
                ath_change_percentage,
                ath_date,
                atl,
                atl_change_percentage,
                atl_date,
                roi_times,
                roi_currency,
                roi_percentage,
                last_updated,
            ),
        
        )
        # once database is loaded save the data into the database
        db_connection.commit()
        # error handling
    except Exception as e:
        print (f"This request cannot be completed due to {e}")
        # close cursor and connection

    #this is the problem, basically because you have the finally inside of the for loop it will close the cursor and connection after each iteration of the loop. so you need to move the finally outside of the for loop.

cur.close()
db_connection.close()
        