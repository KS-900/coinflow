{% snapshot dim_coins_snapshot %}
    {{
        config(
            target_schema='snapshots',
            unique_key='id',
            strategy='check',
            check_cols=['name', 'symbol', 'market_cap', 'price_usd', 'volume_24h', 'circulating_supply'],
            updated_at='last_updated'
        )
    }}

    select *
    from {{ ref('dim_coins') }}

{% endsnapshot %}