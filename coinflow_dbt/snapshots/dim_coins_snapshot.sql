{% snapshot dim_coins_snapshot %}
    {{
        config(
            target_schema='snapshots',
            unique_key='coin_id',
            strategy='check',
            check_cols=['coin_id', 'name_of_coin', 'symbol', 'category', 'first_seen_date'],
            invalidate_hard_deletes=True
        )
    }}

    select *
    from {{ ref('dim_coins') }}

{% endsnapshot %}