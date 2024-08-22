import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Get the secrets from the environment
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

# Login to screener.in
login_url = "https://www.screener.in/login/"
session = requests.Session()

login_payload = {
    "username": EMAIL,
    "password": PASSWORD,
}

# Perform login
login_response = session.post(login_url, data=login_payload)
if login_response.status_code != 200:
    print("Login failed!")
    exit()

# URL for Reliance Industries' Profit & Loss data
reliance_url = "https://www.screener.in/company/RELIANCE/consolidated/"

# Fetch the Reliance Industries page
response = session.get(reliance_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract Profit & Loss data (assuming it's in a table)
table = soup.find('table', {'class': 'data-table'})
df = pd.read_html(str(table))[0]

# Save the DataFrame to a CSV file
csv_file = 'reliance_profit_loss.csv'
df.to_csv(csv_file, index=False)
print(f"Data saved to {csv_file}")

# Connect to PostgreSQL and insert data into a table
db_user = 'your_postgres_user'
db_password = 'your_postgres_password'
db_host = 'localhost'
db_port = '5432'
db_name = 'your_database_name'

conn_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(conn_string)

# Insert data into the PostgreSQL database
df.to_sql('reliance_profit_loss', engine, if_exists='replace', index=False)
print("Data inserted into PostgreSQL database successfully.")