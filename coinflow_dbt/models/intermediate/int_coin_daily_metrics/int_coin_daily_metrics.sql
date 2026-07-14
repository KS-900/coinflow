{{ config(
    materialized='incremental',
    unique_key=['coin_id', 'date_stamp'],
    incremental_strategy='merge'
) }}

with price_history_windowed as (
    select *
    from {{ ref('stg_coin_price_history') }}
    {% if is_incremental() %}
    where coin_date >= (
        select max(date_stamp) - interval '6 days'
        from {{ this }}
    )
    {% endif %}
),

history_info as (
    select
        coin_id,
        coin_date as date_stamp,
        open_price,
        close_price,
        high_price,
        low_price,
        close_market_cap,
        close_total_volume
    from price_history_windowed
),

market_info as (
    select
        name_id,
        scm.name_of_coin
    from {{ ref('stg_coin_markets') }} scm
),

metrics_data as (
    select
        hi.*,
        mi.name_of_coin,
        lag(hi.close_price, 1, null) over (
            partition by hi.coin_id
            order by hi.date_stamp asc
        ) as prev_day_price
    from history_info hi
    left join market_info mi
        on hi.coin_id = mi.name_id
),

final_metrics as (
    select
        *,
        case
            when prev_day_price is null then 0
            when prev_day_price = 0 then null
            else round(((close_price - prev_day_price) / prev_day_price) * 100, 2)
        end as daily_price_change_pcg_raw,
        round(avg(close_price) over (
            partition by coin_id
            order by date_stamp asc
            rows between 6 preceding and current row
        ), 2) as moving_avg_7d
    from metrics_data
)

select
    coin_id,
    name_of_coin,
    date_stamp,
    open_price,
    high_price,
    low_price,
    close_price,
    close_market_cap,
    close_total_volume,
    prev_day_price,
    coalesce(daily_price_change_pcg_raw, 0) as daily_price_change_pcg,
    moving_avg_7d
from final_metrics