{{ config(
    materialized='incremental',
    unique_key=['coin_id', 'coin_date'],
    incremental_strategy='delete+insert'
) }}

{% if is_incremental() %}
with max_ingested as (
    select max(_ingested_at) as max_ingested_at
    from {{ this }}
),
{% else %}
with
{% endif %}

raw_data as (
    select
        r.coin_id,
        r.prices,
        r.market_caps,
        r.total_volumes,
        r._ingested_at
    from {{ source('history_coins_raw', 'coin_price_history') }} r
    {% if is_incremental() %}
    cross join max_ingested m
    where r._ingested_at > m.max_ingested_at
    {% endif %}
),

unpacked as (
    select
        r.coin_id,
        r._ingested_at,
        to_timestamp((p.elem->>0)::bigint / 1000) as price_timestamp_raw,
        (p.elem->>1)::numeric                     as price_value,
        (p.m_elem->>1)::numeric                   as market_cap_value,
        (p.t_elem->>1)::numeric                   as total_volume_value
    from raw_data r
    cross join lateral (
        select
            p_inner.value      as elem,
            m_inner.value      as m_elem,
            t_inner.value      as t_elem
        from
            jsonb_array_elements(r.prices::jsonb)
                with ordinality as p_inner
            join jsonb_array_elements(r.market_caps::jsonb)
                with ordinality as m_inner
                on m_inner.ordinality = p_inner.ordinality
            join jsonb_array_elements(r.total_volumes::jsonb)
                with ordinality as t_inner
                on t_inner.ordinality = p_inner.ordinality
    ) as p(elem, m_elem, t_elem)
),

daily as (
    select
        coin_id,
        cast(price_timestamp_raw as date) as coin_date,
        price_timestamp_raw,
        price_value,
        market_cap_value,
        total_volume_value,
        _ingested_at
    from unpacked
),

aggregated as (
    select
        coin_id,
        coin_date,

        -- Open: first price of the day (earliest timestamp)
        round(
            (array_agg(price_value order by price_timestamp_raw asc))[1],
            2
        ) as open_price,

        -- Close: last price of the day (latest timestamp)
        round(
            (array_agg(price_value order by price_timestamp_raw desc))[1],
            2
        ) as close_price,

        -- High and Low: simple aggregates
        round(max(price_value), 2) as high_price,
        round(min(price_value), 2) as low_price,

        -- Close-of-day snapshot values (latest timestamp of the day)
        round(
            (array_agg(market_cap_value order by price_timestamp_raw desc))[1],
            2
        ) as close_market_cap,
        round(
            (array_agg(total_volume_value order by price_timestamp_raw desc))[1],
            2
        ) as close_total_volume,

        -- Most recent ingestion timestamp contributing to this day's row
        max(_ingested_at) as _ingested_at

    from daily
    group by coin_id, coin_date
)

select *
from aggregated