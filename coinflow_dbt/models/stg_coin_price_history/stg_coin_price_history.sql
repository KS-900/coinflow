with raw_data as(
    select 
        coin_id,
        (p.elem->>0)::BIGINT as price_timestamp_raw,
        (p.elem->>1)::numeric as price_value,
        (m.elem->>0)::BIGINT as market_cap_timestamp_raw,
        (m.elem->>1)::numeric as market_cap_value,
        (t.elem->>0)::BIGINT as total_volume_timestamp_raw,
        (t.elem->>1)::numeric as total_volume_value,
        p.idx
    from 
        {{source('history_coins_raw', 'coin_price_history')}},
lateral jsonb_array_elements(prices::jsonb) with ordinality as p(elem, idx),
lateral jsonb_array_elements(market_caps::jsonb) with ordinality as m(elem, idx),
lateral jsonb_array_elements(total_volumes::jsonb) with ordinality as t(elem, idx)
)
select
    *
from 
    raw_data