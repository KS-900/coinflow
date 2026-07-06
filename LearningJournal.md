Key Definitions:
Ideompotency: When your code can be run multiple time and provide the same output no matter how many times it is run. One example outside of coding is pressing an elevator button. Pressing it once or ten times results in the same state — the elevator is called. Additional presses don't change anything.
Grain: A grain is simply what 1 row in the database represents. Mostly this is a one line explination. One database can have multiple grains in one.

.gitignore: In a '.gitignore' you put file extentions or folders of all files you do not want git to track. Keep in mind the file that hold either big data or sensitive information are the files you do not want git to keep track of.

README.md: This is the file that guides other Users of the technical requirements of the program and how to use your program and all the testing credentials. This is also where the documentation and guide for your project lives.

docker-compose.yml: This is a file that runs all the required software for your project the same way it would on any other machine. Before running file you download docker desktop and install it best practice is using the command line. After installation accept terms and conditions. 
Troubleshooting:
1. Should docker desktop not start engine insure that you downloaded the correct version.
2. If correct version is installed check if settings file is corrupted. If not sure delete file and docker will auto create a new file. 
3. Should that not work install and update wsl with the following commands in your command prompt wsl --install, wsl --update.
4. If that does not wark delete and reinstall the docker desktop and if that does not work conduct deep reasearch on stack overflow, Medium, and redit.

Writting a docker-compose.yml file: 
yml works like a python dictionary which if you forget is key:value (ALWAYS REMEBER THAT)
yml is case sensitive(lowercase). yml uses spaces and not tabs.  
1. Version:[def]
2. services: this is where you load all the software you are using e.g. postgresSQL before writting it you will first use a very impotant key(FIND BELOW)
3. image:[def] then the value of the service you want in this case we will be using  postgres:16 the '16' is the version of the postgres you would like to use
container_name: this is the name you provide for your docker container in the docker desktop this is how you will identify the container you are using incase you are working on multiple projects.
4. evironment: this is where you create the login info for that specific service in our example we are working with postgres:16 so we need the following:
5. POSTGRES_USER:[USERNAME to be used uppon login]
6. POSTGRES_PASWORRD:[PASSWORD to be used uppon login]
7. POSTGRES_DB:[This is the name you give your database for when you connect to the database] should you forget this field POSTGRES uses a default name called postgres to connect.
8. ports: ports are use if you are running it locally on your device this is where you can find your database on 'localhost:[port number]for postgres its 5432:5432.[fill in for cloud hosting]
9. volume: this is where your data and changes are stored because without the volume we would have to always reload our data because it would not be saved. give your volume a name e.g. my_data_database: [location]
10. load or call your volumes to be in use just using the key.
11. including a pgadmin in docker we need the image, container_name, when does it restart using the restart key, environment which includes the admin email and password, ports are after , dependency which is what does it depend on [side not do not use the database name here] use value as database from the services.

Creating Schemas 
1. create a seed.sql file in the file directory. when creating a schema or table or database always use 'IF NOT EXISTS' so for schema: CREATE SCHEMA IF NOT EXISTS [name_of_schema]
2. check in the database connection if schemas already exists.

Mandually downloading data.JSON
1. Create a demo account and create a new key
2. base URL:https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&x_cg_demo_api_key=CG-YOUR_API_KEY
3. Download with ctrl + S 

Manual Load with python script:
1. Import all libraries needed
2.
3. use the request with api key and url
4. save the data into json format
5. connect to database 
6. create cursor
7. use for loop to iterate throught each item in the list of records
8. save each to a veriable 
9. insert data into databse table
10. commit 
11. close cursor 
12. close connection

.env file
1. holds all the sensitive information
2. API_KEY
3. Database connection details

requirements.txt

Ingest_coin_markets.py
1. Import all libraries needed
2. load the getenv function
3. create the get request wrapped in a try statment. Then after saves it in json format and returns the json data
4. Create the transforming function where the data is saved into a pandas format. Create an injested at field. check for duplicates in the data from the api then drop the duplicates
5. Create the load function that saves the data into the database. So we first need to connect to the database using the env file. After connecting to the database we move to using the insert function and also on conflict using the unique key we want to update if the id matches rather than inserting a new one it will update. 
6. Commit 
7. close connection
8. run all functions using 'if __name__ == "__main__":'

Ingest_coin_history.py
1. Import all libraries needed

Tech Stack:
PostgresSQL
Python

# dbt test#
this is the table i use for dbt built in tests
Model	unique	not_null (specific cols)	accepted_values	relationships (to → column)
stg_coin_markets	name_id	name_id, ???	???	(none — top of DAG)
stg_coin_price_history	(coin_id, coin_date)	???	—	coin_id → stg_coin_markets.name_id
int_coin_daily_metrics	(coin_id, coin_date)	???	—	coin_id → ???
int_coin_categories	(coin_id, category)	???	—	coin_id → ???
dim_coins	???	???	—	(usually none — dims are terminal)
fct_market_summary	date_stamp	???	—	(depends on dim_date)

# Challanges #
1. how to use unique on 2 fields in one table ?
    dbt built-in unique won't work because it will only check one field in the table and we need two.
    fix:

    