--This sql script renames
with raw_data as (
    SELECT DISTINCT ON (id)
        cast(trim(coalesce(id, 'Unknown')) as text) as name_id,
        cast(trim(coalesce(symbol, 'Unknown')) as text) as symbol_name,
        cast(trim(coalesce(name, 'Unknown')) as text) as name_of_coin,
        cast(trim(coalesce(image, 'Unknown'))as text) as coin_image,
        round(cast(coalesce(current_price, 0) as numeric ), 2) as current_price,
        round(cast(coalesce(market_cap, 0) as numeric ), 2) as market_cap,
        cast(coalesce(market_cap_rank, 0) as numeric) as market_cap_rank,
        round(cast(coalesce(fully_diluted_valuation, 0) as numeric ), 2) as fully_diluted_valuation,
        cast(coalesce(total_volume, 0) as numeric) as total_volume,
        round(cast(coalesce(high_24h, 0) as numeric ), 2) as high_24h,
        round(cast(coalesce(low_24h, 0)  as numeric ), 2) as low_24h,
        round(cast(coalesce(price_change_24h, 0) as numeric ), 2) as price_change_24h,
        round(cast(coalesce(market_cap_change_24h, 0) as numeric ), 2) as market_cap_change_24h,
        round(cast(coalesce(circulating_supply, 0)   as numeric ), 2) as circulating_supply,
        round(cast(coalesce(total_supply, 0) as numeric ), 2) as total_supply,
        round(cast(coalesce(max_supply, 0) as numeric ), 2) as max_supply,
        round(cast(coalesce(ath, 0) as numeric ), 2) as all_time_high,
        round(cast(coalesce(ath_change_percentage, 0)   as numeric ), 2) as all_time_high_change_percentage,
        cast(coalesce(ath_date,CURRENT_DATE) as date ) as all_time_high_date,
        round(cast(coalesce(atl, 0) as numeric ), 2) as all_time_low,
        round(cast(coalesce(atl_change_percentage, 0) as numeric ), 2) as all_time_low_change_percentage,
        cast(coalesce(ath_date,CURRENT_DATE) as date ) as all_time_low_date,
        round(cast(coalesce(roi_times, 0) as numeric ), 2) as return_on_investment_times,
        cast(trim(coalesce(roi_currency, 'Unknown')) as text ) as return_on_investment_currency,
        round(cast(coalesce(roi_percentage, 0) as numeric ), 2) as return_on_investment_percentage,
        cast(coalesce(last_updated,CURRENT_TIMESTAMP) as timestamp ) as last_updated,
        cast(coalesce(_ingested_at,CURRENT_TIMESTAMP) as timestamp ) as ingested_at

    FROM
        {{source('coins_raw', 'coin_markets') }} --coinflow.raw.coin_markets
    
)
select
    *
from 
    raw_data