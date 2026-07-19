import os 
import requests
from dotenv import load_dotenv
import pandas as pd
import time
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCOGS_TOKEN")

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

# ----------- temporary >>>
data = get_releases(1,2026)

for release in data['results']:
    row = {
        # 'title': release['title'],
        'label': release['label'],
        'want': release['community']['want'],
        'have': release['community']['have']
    }
    releases_info.append(row)
# ---------- temporary <<<<

# for year in range(current_year-1, current_year+1):
#     for page in range(1,pages(year)+1):
#         data = get_releases(page,year)
#         for release in data['results']:
#             row = {
#                 # 'title': release['title'],
#                 'label': release['label'],
#                 'want': release['community']['want'],
#                 'have': release['community']['have']
#             }
#             releases_info.append(row)
#         time.sleep(1)

df_raw = pd.DataFrame(releases_info)
df_clean = df_raw.explode('label')
df_analytics = df_clean.groupby('label')[['want','have']].sum()
df_analytics = df_analytics.sort_values(by='have', ascending=False)
df_analytics['want-to-have-ratio']=df_analytics['want']/df_analytics['have']
print(df_analytics)