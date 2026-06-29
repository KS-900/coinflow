with raw_categories as (
    select 
        cast(trim(coin_id) as text) as coin_id,
        cast(trim(category) as text) as category,
        cast(ingested_at as timestamp) as ingested_at
    from 
        {{source('categories_raw', 'coins_categories') }} --coinflow.raw.coins_categories
)
select
    *
from 
    raw_categories