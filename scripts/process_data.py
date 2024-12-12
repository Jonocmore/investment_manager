import os
import pandas as pd
from utils import is_crypto
from indicators import (
    compute_sma, compute_ema, compute_rsi,
    compute_macd, compute_bollinger_bands, compute_atr
)

def process_data_for_asset(asset):
    """
    Process historical data for a single asset by computing various indicators.
    Assumes a CSV file for the asset exists in data/<asset>_data.csv.
    After processing, the CSV is overwritten with columns for the computed indicators.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    file_path = os.path.join(data_dir, f"{asset}_data.csv")

    if not os.path.exists(file_path):
        print(f"No data file found for {asset}, skipping processing.")
        return

    # Load the asset data
    df = pd.read_csv(file_path)

    # Handle date/datetime columns for indexing
    if 'Date' in df.columns:
        # Stocks/ETFs from yfinance typically have a 'Date' column
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    elif 'datetime' in df.columns:
        # Crypto data from CoinGecko often has 'datetime'
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
    else:
        print(f"No recognized date column in {asset} data. Cannot process.")
        return

    df.sort_index(inplace=True)

    # If crypto, rename 'price' column to 'Close'
    if 'price' in df.columns:
        df.rename(columns={'price': 'Close'}, inplace=True)

    # Ensure that we have a 'Close' column for indicators
    if 'Close' not in df.columns:
        print(f"No 'Close' column found for {asset}, cannot compute indicators.")
        return

    # Compute indicators
    df = compute_sma(df, column='Close', window=20)
    df = compute_ema(df, column='Close', window=20)
    df = compute_rsi(df, column='Close', period=14)
    df = compute_macd(df, column='Close', fast=12, slow=26, signal=9)
    df = compute_bollinger_bands(df, column='Close', window=20, num_std=2)

    # Compute ATR only if High, Low, Close columns exist (usually only for stocks/ETFs)
    if all(col in df.columns for col in ['High', 'Low', 'Close']):
        df = compute_atr(df, high_col='High', low_col='Low', close_col='Close', period=14)

    # Save the processed data back to the CSV
    df.to_csv(file_path)
    print(f"Processed and updated data for {asset} with indicators.")
