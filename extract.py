import os 
import requests
from dotenv import load_dotenv
import pandas as pd
import time
from datetime import datetime
from sqlalchemy import create_engine

load_dotenv()
TOKEN = os.getenv("DISCOGS_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

BASE_URL = "https://api.discogs.com"
headers = {
    "Authorization": f"Discogs token={TOKEN}",
    "User-Agent": "MusicInflationAnalytics/1.0"
}

current_year = datetime.now().year

def get_releases(page, year):
    url = f"{BASE_URL}/database/search"
    query_params = {
        'type': 'release',
        'year': year,
        'per_page':100,
        'page': page
    }
    response = requests.get(url, headers=headers, params=query_params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Page {page} in {year} reading error.\n{response.text}")

def pages(year):
    url = f"{BASE_URL}/database/search"
    query_params = {
        'type': 'release',
        'year': year,
        'per_page':100,
    }
    response = requests.get(url, headers=headers, params=query_params)
    if response.status_code == 200:
        data = response.json()
        pages = data['pagination']['pages']
        print(f"Number of pages in {year} successfuly read:{pages}!")
        return pages
    else:
        print(f"Error reading the number of pages in {year}.\n{response.text}")

releases_info = []

for year in range(current_year-2, current_year+1):
    for page in range(1,pages(year)+1):
        data = get_releases(page,year)
        if data:
            for release in data['results']:
                row = {
                    'label': release['label'],
                    'want': release['community']['want'],
                    'have': release['community']['have']
                }
                releases_info.append(row)
        time.sleep(1)
        print('.', end='',flush=True)
    print()

df_raw = pd.DataFrame(releases_info)

df_clean = df_raw.explode('label')
df_clean = df_clean.groupby('label')[['want','have']].sum()
df_clean = df_clean.sort_values(by='have', ascending=False)
df_clean['want_to_have_ratio']=df_clean['want']/df_clean['have']
df_clean = df_clean[(df_clean['want'] != 0) | (df_clean['have'] != 0)]
print(df_clean)

engine = create_engine(DATABASE_URL)

df_clean.to_sql(
    name='want_and_have_by_label',
    con=engine,
    if_exists='replace',
    index=True,
    index_label='label_name'
)