with raw_categories as (
    select 
        cast(trim(coin_id) as text) as coin_id,
        cast(trim(category) as text) as category,
        cast(_ingested_at as timestamp) as _ingested_at
    from 
        {{source('categories_raw', 'coins_categories') }} --coinflow.raw.coins_categories
)
select
    *
from 
    raw_categories