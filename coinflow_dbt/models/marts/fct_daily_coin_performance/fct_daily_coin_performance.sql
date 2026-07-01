SELECT
    coin_id,
    name_of_coin,
    date_stamp as trade_date,
    open_price as open_price_usd,
    high_price as high_price_usd,
    low_price as low_price_usd,
    close_price as close_price_usd,
    close_total_volume as volume,
    close_market_cap as market_cap,
    daily_price_change_pcg as daily_price_change_pct,
    moving_avg_7d as moving_avg_7d_price
FROM {{ref('int_coin_daily_metrics') }}