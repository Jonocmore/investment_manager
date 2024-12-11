import os
import datetime
import time
import requests
import pandas as pd
import yfinance as yf
from utils import portfolio, settings, secrets

def fetch_stock_etf_data():
    start_date = settings.get('data_start_date', '2022-01-01')
    end_date = datetime.date.today().isoformat()

    stock_list = portfolio.get('portfolio', {}).get('stocks', [])
    etf_list = portfolio.get('portfolio', {}).get('etfs', [])

    watchlist_stocks = portfolio.get('watchlist', {}).get('stocks', [])

    # Combine portfolio stocks, ETFs, and watchlist stocks
    assets = stock_list + etf_list + watchlist_stocks

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    for asset in assets:
        print(f"Fetching data for {asset}...")
        df = yf.download(asset, start=start_date, end=end_date)
        if not df.empty:
            file_path = os.path.join(data_dir, f"{asset}_data.csv")
            df.to_csv(file_path)
        else:
            print(f"No data returned for {asset}. Check if ticker is correct.")

def fetch_crypto_data():
    start_date = settings.get('data_start_date', '2022-01-01')
    start_dt = datetime.datetime.fromisoformat(start_date)
    today = datetime.datetime.today()
    delta = today - start_dt
    num_days = delta.days

    crypto_list = portfolio.get('portfolio', {}).get('crypto', [])
    watchlist_crypto = portfolio.get('watchlist', {}).get('crypto', [])
    all_cryptos = set(crypto_list + watchlist_crypto)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    for coin in all_cryptos:
        # Ensure these are CoinGecko IDs (e.g. "bitcoin", "ethereum", "cardano")
        print(f"Fetching crypto data for {coin}...")
        url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': '365'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            prices = data.get('prices', [])
            if prices:
                df = pd.DataFrame(prices, columns=['timestamp', 'price'])
                # Convert timestamp to datetime
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('datetime', inplace=True)
                df.drop('timestamp', axis=1, inplace=True)
                file_path = os.path.join(data_dir, f"{coin}_data.csv")
                df.to_csv(file_path)
            else:
                print(f"No price data returned for {coin}")
        else:
            print(f"Error fetching data for {coin}, status code {response.status_code}")
        time.sleep(1)  # Respect CoinGecko's rate limits

def fetch_news():
    api_key = secrets.get('newsapi_key')
    if not api_key:
        print("No NewsAPI key found. Skipping news fetch.")
        return

    # Adjust query as desired. You could loop through stocks/crypto from portfolio.
    query = "stocks OR crypto"
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': query,
        'sortBy': 'publishedAt',
        'apiKey': api_key,
        'language': 'en',
        'pageSize': 50
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        if articles:
            df = pd.DataFrame(articles)
            # Keep key fields
            columns_to_keep = ['title', 'description', 'url', 'publishedAt']
            df = df[columns_to_keep]

            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
            file_path = os.path.join(data_dir, "news_data.csv")
            df.to_csv(file_path, index=False)
            print("News data fetched and saved.")
        else:
            print("No articles found.")
    else:
        print(f"NewsAPI error: {response.status_code}")

if __name__ == "__main__":
    # Fetch Stocks & ETFs
    fetch_stock_etf_data()
    # Fetch Cryptos
    fetch_crypto_data()
    # Fetch News
    fetch_news()
    print("Data fetching complete.")
    print("Portfolio:", portfolio)
