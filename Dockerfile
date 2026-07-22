FROM apache/airflow:2.9.3

# Switch to root to install system packages
USER root

# Install git (needed by dbt for packages)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user for pip installs (security best practice)
USER airflow

# Install Python packages
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres \
    dbt-postgres==1.7.13 \
    requests \
    psycopg2-binary \
    python-dotenv