with source_data as (
	select 
		*
	from 
		{{ref('int_coin_daily_metrics')}}
),
total_market_cap_and_avg_market_volume as(
	select
		date_stamp ,
		sum(close_market_cap) as total_market_cap,
		avg(close_total_volume) as average_volume
	from 
		source_data
	group by 
		date_stamp 
),
top_gainer_and_top_loser_formula as (
	select 
		coin_id,
		date_stamp,
		daily_price_change_pcg,
		row_number()over(
		partition by date_stamp 
		order by daily_price_change_pcg desc 
		) as ranked_gainer,
		row_number()over(
		partition by date_stamp 
		order by daily_price_change_pcg asc
		) as ranked_loser
	from 
		source_data 
	where 
		daily_price_change_pcg is not null
),
top_gainer as (
	select 
		date_stamp,
		coin_id as top_gainer
	from 
		top_gainer_and_top_loser_formula   
	where 
		ranked_gainer =1
),
top_loser as (
	select 
		date_stamp,
		coin_id as top_loser
	from 
		top_gainer_and_top_loser_formula  
	where 
		ranked_loser =1
),
joined as(
	select 
		tmcaamv.date_stamp ,
		tmcaamv.total_market_cap ,
		tg.top_gainer ,
		tl.top_loser ,
		tmcaamv.average_volume 
	from 
		total_market_cap_and_avg_market_volume tmcaamv
	left join top_gainer tg
		on tmcaamv.date_stamp = tg.date_stamp 
	left join top_loser tl
		on tmcaamv.date_stamp = tl.date_stamp 
)
select 
	*
from 
	joined