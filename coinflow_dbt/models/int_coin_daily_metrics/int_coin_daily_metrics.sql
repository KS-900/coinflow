/* pseudo code for int_coin_daily_metrics.sql:
 1. join the tables before calculating the metrics to avoid redundant calculations in the final reporting models
2. Then calculate daily price change %. 
3. 7-day moving average for each coin 
4. Use window functions to calculate the metrics efficiently.
5. Ensure that the model is incremental to optimize performance.
*/