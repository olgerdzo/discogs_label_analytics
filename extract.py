import os
import time
import logging
from datetime import datetime
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
TOKEN = os.getenv("DISCOGS_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

BASE_URL = "https://api.discogs.com"
HEADERS = {
    "Authorization": f"Discogs token={TOKEN}",
    "User-Agent": "CDLabelAnalytics/1.0"
}

def fetch_year_data(session: requests.Session, year: int) -> list:
    releases = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        query_params = {
            'type': 'release',
            'year': year,
            'format': 'cd',
            'country': 'us',
            'per_page': 100,
            'page': page
        }

        response = None

        for attempt in range(1,4):
            try:
                response = session.get(f"{BASE_URL}/database/search", headers=HEADERS, params=query_params, timeout=10)
                if response.status_code == 200:
                    break
                elif response.status_code == 429:
                    logging.warning(f"Hit rate limit (429). Waiting 60 seconds, {attempt} attempt...")
                    time.sleep(60)
                else:
                    logging.error(f"Error fetching year {year}, page {page}: {response.status_code}. Waiting 5 seconds, {attempt} attempt...")
                    time.sleep(5)
            except Exception as e:
                logging.error(f"Network error: {e}. Waiting 10 seconds, {attempt} attempt...")
                time.sleep(10)

        if response == None:
            logging.error(f"Critaical error fetching year {year}, page {page}. Reading next page ({page + 1})...")
            page +=1
            continue
        elif response.status_code != 200:
            logging.error(f"Error fetching year {year}, page {page}: {response.status_code}. Reading next page ({page + 1})...")
            page += 1
            continue

        data = response.json()
        
        if total_pages == 1:
            total_pages = data.get('pagination', {}).get('pages', 1)
            logging.info(f"Year {year}: found {total_pages} pages.")

        for release in data.get('results', []):
            community = release.get('community', {})
            releases.append({
                'label': release.get('label', []),
                'want': community.get('want', 0),
                'have': community.get('have', 0)
            })

        if page % 5 == 0 or page == total_pages:
            logging.info(f"Year {year}: {page} of {total_pages} pages read.")

        page += 1
        time.sleep(1)

    return releases

def run_pipeline():
    current_year = datetime.now().year
    all_releases = []
    
    with requests.Session() as session:
        for year in range(current_year - 20, current_year + 1):
            year_data = fetch_year_data(session, year)
            all_releases.extend(year_data)

    if not all_releases:
        logging.error("No data collected. Pipeline aborted.")
        return

    df_raw = pd.DataFrame(all_releases)
    df_clean = df_raw.explode('label')
    df_clean = df_clean.groupby('label')[['want', 'have']].sum()
    df_clean = df_clean.sort_values(by='have', ascending=False)
    df_clean = df_clean[(df_clean['want'] != 0) | (df_clean['have'] != 0)]

    engine = create_engine(DATABASE_URL)
    
    with engine.begin() as conn:
        logging.info("Truncating table and inserting new data...")
        conn.execute(text('TRUNCATE TABLE label_data;'))
        
        df_clean.to_sql(
            name='label_data',
            con=conn,
            if_exists='append',
            index=True,
            index_label='label_name'
        )
        
        logging.info("Refreshing Materialized View...")
        conn.execute(text('REFRESH MATERIALIZED VIEW label_analytics_view;'))
    
    logging.info("ETL Pipeline completed successfully!")

if __name__ == '__main__':
    run_pipeline()