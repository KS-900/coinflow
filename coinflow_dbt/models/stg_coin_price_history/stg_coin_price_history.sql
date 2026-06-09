{{ config(
    materialized='incremental',
    unique_key='idx',
    incremental_strategy='delete+insert'
) }}

with raw_data as (
    select
        coin_id,
        prices,
        market_caps,
        total_volumes,
        _ingested_at
    from {{ source('history_coins_raw', 'coin_price_history') }}
    {% if is_incremental() %}
        where _ingested_at > (
            select max(_ingested_at) from {{ this }}
        )
    {% endif %}
),

unpacked as (
    select
        r.coin_id,
        to_timestamp(
            (p.elem->>0)::bigint / 1000
        )                       as price_timestamp_raw,
        (p.elem->>1)::numeric   as price_value,
        (p.m_elem->>1)::numeric as market_cap_value,
        (p.t_elem->>1)::numeric as total_volume_value,
        p.ord                   as idx
    from raw_data r
    cross join lateral (
        select
            p_inner.value       as elem,
            p_inner.ordinality  as ord,
            m_inner.value       as m_elem,
            t_inner.value       as t_elem
        from
            jsonb_array_elements(r.prices::jsonb)
                with ordinality as p_inner
            join jsonb_array_elements(r.market_caps::jsonb)
                with ordinality as m_inner
                on m_inner.ordinality = p_inner.ordinality
            join jsonb_array_elements(r.total_volumes::jsonb)
                with ordinality as t_inner
                on t_inner.ordinality = p_inner.ordinality
    ) as p(elem, ord, m_elem, t_elem)
)

select * from unpacked