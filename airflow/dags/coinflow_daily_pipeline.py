# airflow/dags/coinflow_daily_pipeline.py
# This DAG is designed to run daily and orchestrate the data ingestion and transformation processes for CoinFlow. 
# It includes tasks for extracting market coin data, coin history data, and coin categories data, followed by transforming the data using dbt and testing the transformed data.

# Import necessary modules
from airflow import DAG     # Import the DAG class from Airflow
from airflow.operators.bash import BashOperator     # Import the BashOperator for executing bash commands
from datetime import datetime, timedelta    # Import datetime and timedelta for scheduling and timing

# Define default arguments for the DAG
default_args = {                    
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

# Define the DAG
with DAG(
    'coinflow_daily_pipeline',          # Set the DAG ID
    default_args=default_args,          # Set the default arguments for the DAG from the dictionary defined above
    description='A daily pipeline for CoinFlow data processing',    # Provide a description for the DAG
    schedule='0 6 * * *' ,                      # Set the schedule to run daily
    start_date=datetime(2026, 7, 10),       # Set the start date for the DAG
    catchup=False,          # Set to False to avoid running past dates when the DAG is first deployed
    tags=['coinflow'],      # Add a tag for easier identification in the Airflow UI
) as dag:
    
    # Define the tasks
    extract_market_coin_data = BashOperator(
        task_id='extract_market_coin_data',
        bash_command='python /opt/airflow/scripts/ingest_coin_markets.py',  # Set the bash command to execute the script for extracting market coin data
    )

    extract_coin_history_data = BashOperator(
        task_id='extract_coin_history_data',
        bash_command='python /opt/airflow/scripts/ingest_coin_history.py',  # Set the bash command to execute the script for extracting coin history data
    )

    extract_coin_categories_data = BashOperator(
        task_id='extract_coin_categories_data',
        bash_command='python /opt/airflow/scripts/ingest_coin_categories.py',  # Set the bash command to execute the script for extracting coin categories data
    )

    # Transform and test the data using dbt
    dbt_run_task = BashOperator(
        task_id='dbt_run_task',
        bash_command='cd /opt/airflow/coinflow_dbt && dbt run',    # Set the bash command to execute the dbt run command for transforming the data using dbt models
    )

    dbt_test_data = BashOperator(
        task_id='dbt_test_data',
        bash_command='cd /opt/airflow/coinflow_dbt && dbt test',   # Set the bash command to execute the dbt test command for testing the transformed data using dbt models
    )
    # Define the task dependencies
    extract_market_coin_data >> extract_coin_history_data >> extract_coin_categories_data >> dbt_run_task >> dbt_test_data