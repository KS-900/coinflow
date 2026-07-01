/* pseudo code for int_coin_daily_metrics.sql:
 1. join the tables before calculating the metrics to avoid redundant calculations in the final reporting models
2. Then calculate daily price change %. 
3. 7-day moving average for each coin 
4. Use window functions to calculate the metrics efficiently.
5. Ensure that the model is incremental to optimize performance.
*/

with price_history_7d as (
	select
		*
	from 
		{{ref('stg_coin_price_history') }} --staging.stg_coin_price_history
	where coin_date >= (select max(coin_date) -6 from {{ref('stg_coin_price_history') }} scph2 )
),
history_info as(
	select 
		coin_id,
		coin_date as date_stamp,
		open_price,
		close_price,
		high_price,
		low_price,
		close_market_cap,
		close_total_volume
	from price_history_7d phd
),
market_info as(
	select 
		name_id, 
		scm.name_of_coin
	from 
		{{ref('stg_coin_markets') }} scm 
),
metrics_data as(
	select 
		*,
		lag(hi.close_price,1,null) over(
			partition by hi.coin_id
			order by hi.date_stamp asc ) as prev_day_price
	from history_info hi
		left join market_info mi
			on hi.coin_id = mi.name_id 
),
final_metrics as(
	select 
		*,
		case
			when prev_day_price is null then null
			when prev_day_price = 0 then null
			else round(((hi.close_price - prev_day_price)/prev_day_price)*100, 2)
		end as daily_price_change_pcg,
		round(avg(hi.close_price) OVER (
    		partition by hi.coin_id
    		order by hi.date_stamp asc
    		rows between 6 preceding and current row
		),2) AS moving_avg_7d
	from metrics_data hi
),
final_table as(
	select 
		coin_id,
		name_of_coin,
		date_stamp,
		open_price,
		high_price,
		low_price,
		close_price,
		close_market_cap,
		close_total_volume,
		prev_day_price,
		daily_price_change_pcg,
		moving_avg_7d,
		row_number() over(
			partition by coin_id
			order by date_stamp desc) as row_num
	from final_metrics
), 
final as(
	select 
		coin_id,
		name_of_coin,
		date_stamp,
		open_price,
		high_price,
		low_price,
		close_price,
		close_market_cap,
		close_total_volume,
		prev_day_price,
		daily_price_change_pcg,
		moving_avg_7d
	from final_table
	where row_num = 1
)
select 
	coin_id ,
	name_of_coin,
	date_stamp ,
	open_price ,
	high_price ,
	low_price ,
	close_price ,
	close_market_cap ,
	close_total_volume ,
	prev_day_price ,
	daily_price_change_pcg ,
	moving_avg_7d 
from 
	final