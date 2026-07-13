with daily_metrics as(
	select 
		*
	from 
        {{ref('int_coin_daily_metrics') }} icdm
),
categories as(
	select 
		coin_id as id_coin,
		category,
		ingested_at as category_ingested_at
	from 
		{{ref('stg_coin_categories') }} scc 
),
categories_daily_metrics as(
	select 
		*
	from 
		categories c
	left join daily_metrics dm
		on c.id_coin = dm.coin_id  
)
select 
	id_coin  as coin_id,
	category ,
	name_of_coin ,
	prev_day_price ,
	daily_price_change_pcg ,
	moving_avg_7d ,
	category_ingested_at ,
	date_stamp 
from 
	categories_daily_metrics  
