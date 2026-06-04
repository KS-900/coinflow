{{config(
    materialized='incremental',
    unique_key='idx',
    incremental_strategy='delete+insert'
)}}
with raw_data as(
select 
        coin_id,
        (p_elem->>0)::BIGINT as price_timestamp_raw,
        (p_elem->>1)::numeric as price_value,
        (m_elem->>1)::numeric as market_cap_value,
        (t_elem->>1)::numeric as total_volume_value,
        row_index as idx
    from {{source('history_coins_raw', 'coin_price_history')}},
    {% if is_incremental() %}
        where inserted_at > (select max(inserted_at) from {{this}})
    {% endif %},
        lateral rows from(
        	jsonb_array_elements(prices::jsonb),
        	jsonb_array_elements(market_caps::jsonb),
        	jsonb_array_elements(total_volumes::jsonb)
        )  with ordinality as t(p_elem, m_elem, t_elem, row_index)
)
select
    *
from 
    raw_data