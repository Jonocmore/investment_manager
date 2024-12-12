import os
import datetime
import requests
import pandas as pd
import yfinance as yf
from utils import portfolio, settings, secrets, is_crypto

def fetch_data_for_asset(asset):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)

    if is_crypto(asset):
        print(f"Fetching crypto data for {asset}...")
        url = f"https://api.coingecko.com/api/v3/coins/{asset}/market_chart"
        params = {'vs_currency': 'usd', 'days': '365'}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('prices', [])
            if data:
                df = pd.DataFrame(data, columns=['timestamp', 'price'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.drop('timestamp', axis=1, inplace=True)
                file_path = os.path.join(data_dir, f"{asset}_data.csv")
                df.to_csv(file_path, index=False)
                print(f"Saved crypto data for {asset} to {file_path}")
            else:
                print(f"No crypto data returned for {asset}")
        else:
            print(f"Error fetching crypto data for {asset}: {response.status_code}")
    else:
        print(f"Fetching stock/ETF data for {asset}...")
        df = yf.download(asset, start=start_date.isoformat(), end=end_date.isoformat())

        if not df.empty:
            # Since the Ticker is at level 1, drop level 1
            if isinstance(df.columns, pd.MultiIndex):
                # Drop the Ticker level to get proper column names
                df.columns = df.columns.droplevel(1)
                # Now columns should be ['Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']

            df.reset_index(inplace=True)
            file_path = os.path.join(data_dir, f"{asset}_data.csv")
            df.to_csv(file_path, index=False)
            print(f"Saved stock/ETF data for {asset} to {file_path}")

            # Quick sanity check
            print("CSV Header:", pd.read_csv(file_path, nrows=0).columns.tolist())
        else:
            print(f"No data returned for {asset}. Check if ticker is correct.")

def fetch_news_for_asset(asset, limit=20):
    """
    Fetch recent news headlines related to the asset using NewsAPI.
    Saves to data/news_<asset>_data.csv.
    """
    api_key = secrets.get('newsapi_key')
    if not api_key:
        print("No NewsAPI key found. Skipping news fetch for asset.")
        return

    query = f"{asset} {'crypto' if is_crypto(asset) else 'stock'}"
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': query,
        'sortBy': 'publishedAt',
        'apiKey': api_key,
        'language': 'en',
        'pageSize': limit
    }

    print(f"Fetching news for {asset} with query: {query}")
    response = requests.get(url, params=params)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        if articles:
            df = pd.DataFrame(articles)
            columns_to_keep = ['title', 'description', 'url', 'publishedAt']
            df = df[columns_to_keep]
            file_path = os.path.join(data_dir, f"news_{asset}_data.csv")
            df.to_csv(file_path, index=False)
            print(f"News data fetched for {asset} and saved to {file_path}")
        else:
            print(f"No articles found for {asset}.")
    else:
        print(f"NewsAPI error for {asset}: {response.status_code}")
