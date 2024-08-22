import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, Integer, Float, String
from sqlalchemy.engine import URL

# Setup the connection to PostgreSQL
connection_url = URL.create(
    "postgresql",
    username="postgres",
    password="Abcd@1234",
    host="192.168.3.55",
    port=5432,
    database="Test_DB",
)
engine = create_engine(connection_url)

# Get the secrets from the environment
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

# Login to screener.in
login_url = "https://www.screener.in/login/"
session = requests.Session()

# Set User-Agent and Referer headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Referer': login_url
}

# Fetch the login page to get the CSRF token
response = session.get(login_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

# Login payload with CSRF token
login_payload = {
    "username": EMAIL,
    "password": PASSWORD,
    "csrfmiddlewaretoken": csrf_token,
}

# Perform login
login_response = session.post(login_url, data=login_payload, headers=headers)
if login_response.status_code != 200:
    print("Login failed!")
    print(login_response.content)  # Print the response content for debugging
    exit()

# URL for Reliance Industries' Profit & Loss data
reliance_url = "https://www.screener.in/company/RELIANCE/consolidated/"

# Fetch the Reliance Industries page
response = session.get(reliance_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract Profit & Loss data (assuming it's in a table with id 'profit-loss')
profit_loss_section = soup.find('section', {'id': 'profit-loss'})
table = profit_loss_section.find('table', {'class': 'data-table'})
df = pd.read_html(str(table))[0]

# Reformat the data
df = df.transpose()
df.columns = df.iloc[0].str.strip().str.replace('+', '').str.replace('%', '')
df = df.iloc[1:]
df.index.name = 'Financial Metric'

# Cleaning the data

# Remove '%' sign and convert numeric columns to appropriate types
for column in df.columns:
    if df[column].dtype == 'object':
        df[column] = df[column].str.replace('%', '')  # Remove percentage signs
        df[column] = pd.to_numeric(df[column], errors='coerce')  # Convert to numeric (float or int)

# Ensure the appropriate data types for each column
# Convert float columns to integers where applicable (e.g., no decimals in the data)
for col in df.columns:
    if df[col].notna().all() and (df[col] % 1 == 0).all():
        df[col] = df[col].astype('int')

# Save the DataFrame to a CSV file
csv_file = 'reliance_profit_loss.csv'
df.to_csv(csv_file)
print(f"Data saved to {csv_file}")

# Save the DataFrame to a Postgres table
df.to_sql('reliance_profit_loss', engine, if_exists='replace', index=True, dtype={
    "Sales": Integer(),
    "Expenses": Integer(),
    "Operating Profit": Integer(),
    "OPM ": Float(),
    "Other Income": Integer(),
    "Interest": Integer(),
    "Depreciation": Integer(),
    "Profit before tax": Integer(),
    "Tax ": Float(),
    "Net Profit": Integer(),
    "EPS in Rs": Float(),
    "Dividend Payout ": Float()
})

print("Data saved to Postgres table")
