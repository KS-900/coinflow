# CoinFlow — Cryptocurrency Market Data Pipeline
## What You're Building
A complete data pipeline that:
1. Ingests cryptocurrency market data from a free public API
2. Lands it in a PostgreSQL data warehouse
3. Transforms it through a layered architecture using dbt
4. Orchestrates everything on a schedule with Airflow
5. Serves analytics through a dashboard

## Tech Stack:
1. Docker 
2. Python
3. PostgreSQL
4. dbt

## How to Inisialize the project
1. Activate virtual environment
2. Run docker-compose.yml file [docker-compose up -d]
3. Connect to database 

## Data Enginering Terminology 
1. Idempotency: This is running the same script/function multiple times and recive the same result in my code that is the ingest scripts using the upsert. An outside example would be cutting your hair should brin back the same results no matter how many times you do it.
2. Grain: A grain is what one row in your database represents. In the coin flow database 1 row represents the coins information. 