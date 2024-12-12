import os
import datetime
import requests
import pandas as pd
import yfinance as yf
from utils import portfolio, settings, secrets, is_crypto

def fetch_data_for_asset(asset):
    """
    Fetch market data for a given asset (stock or cryptocurrency).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)

    if is_crypto(asset):
        print(f"Fetching crypto data for {asset}...")
        # Fetch price, volume, and market cap data from CoinGecko
        url = f"https://api.coingecko.com/api/v3/coins/{asset}/market_chart"
        params = {'vs_currency': 'usd', 'days': '365'}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                # Parse historical prices and volume
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                market_caps = data.get('market_caps', [])

                df = pd.DataFrame({
                    'datetime': [pd.to_datetime(p[0], unit='ms') for p in prices],
                    'price': [p[1] for p in prices],
                    'volume': [v[1] for v in volumes],
                    'market_cap': [mc[1] for mc in market_caps]
                })

                file_path = os.path.join(data_dir, f"{asset}_data.csv")
                df.to_csv(file_path, index=False)
                print(f"Saved crypto data for {asset} to {file_path}")
            else:
                print(f"No crypto data returned for {asset}")
        else:
            print(f"Error fetching crypto data for {asset}: {response.status_code}")
    else:
        print(f"Fetching stock/ETF data for {asset}...")
        # Fetch stock/ETF data from Yahoo Finance
        df = yf.download(asset, start=start_date.isoformat(), end=end_date.isoformat())

        if not df.empty:
            # Fix column names for multi-index columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

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

def process_data_for_asset(asset):
    """
    Perform basic analysis on the fetched data, e.g., calculating SMA, RSI, etc.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    file_path = os.path.join(data_dir, f"{asset}_data.csv")

    if not os.path.exists(file_path):
        print(f"Data file for {asset} does not exist. Skipping processing.")
        return

    df = pd.read_csv(file_path, parse_dates=['datetime'] if is_crypto(asset) else ['Date'])
    if is_crypto(asset):
        df.set_index('datetime', inplace=True)
    else:
        df.set_index('Date', inplace=True)

    # Add moving averages
    df['SMA_20'] = df['price'].rolling(window=20).mean() if is_crypto(asset) else df['Close'].rolling(window=20).mean()
    df['EMA_20'] = df['price'].ewm(span=20, adjust=False).mean() if is_crypto(asset) else df['Close'].ewm(span=20, adjust=False).mean()

    # Add RSI (14-period)
    delta = df['price'].diff() if is_crypto(asset) else df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    # Save processed data
    df.to_csv(file_path)
    print(f"Processed data for {asset} and saved to {file_path}.")
