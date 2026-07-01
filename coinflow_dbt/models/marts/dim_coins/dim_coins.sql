with coin_name_category as(
	select 
		coin_id,
		name_of_coin as name,
		category
	from 
		{{ref('int_coin_categories')}}
),
coin_symbol as(
	select
		name_id,
		name_of_coin, 
		symbol_name
	from 
		{{ref('stg_coin_markets')}}
),
first_seen_date as(
	select 
		scph.coin_id ,
		min(coin_date) as first_seen_date
	from 
		{{ref('stg_coin_price_history')}}
	group by
		coin_id 
),
final_coin as(
	select 
		cnc.coin_id,
		cnc.name,
		cnc.category,
		cs.symbol_name ,
		fsd.first_seen_date,
		row_number()over(
		partition by cnc.coin_id, cnc.category
		order by cs.symbol_name asc
		) as rn
	from coin_name_category cnc
	left join coin_symbol cs
		on cnc.coin_id  = cs.name_id 
	left join first_seen_date fsd
		on cnc.coin_id = fsd.coin_id 
)
select 
	coin_id,
	name as coin_name,
	symbol_name as symbol,
	category,
	first_seen_date 
from 
	final_coin 
where rn =1