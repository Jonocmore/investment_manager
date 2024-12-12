import pandas as pd
import numpy as np

def compute_sma(df, column='Close', window=20):
    df[f'SMA_{window}'] = df[column].rolling(window=window).mean()
    return df

def compute_ema(df, column='Close', window=20):
    df[f'EMA_{window}'] = df[column].ewm(span=window, adjust=False).mean()
    return df

def compute_rsi(df, column='Close', period=14):
    delta = df[column].diff(1)
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    df[f'RSI_{period}'] = 100 - (100 / (1.0 + rs))
    return df

def compute_macd(df, column='Close', fast=12, slow=26, signal=9):
    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()
    df['MACD_line'] = ema_fast - ema_slow
    df['MACD_signal'] = df['MACD_line'].ewm(span=signal, adjust=False).mean()
    df['MACD_histogram'] = df['MACD_line'] - df['MACD_signal']
    return df

def compute_bollinger_bands(df, column='Close', window=20, num_std=2):
    rolling_mean = df[column].rolling(window=window, min_periods=1).mean()
    rolling_std = df[column].rolling(window=window, min_periods=1).std()
    df['Bollinger_Middle'] = rolling_mean
    df['Bollinger_Upper'] = rolling_mean + (rolling_std * num_std)
    df['Bollinger_Lower'] = rolling_mean - (rolling_std * num_std)
    return df

def compute_atr(df, high_col='High', low_col='Low', close_col='Close', period=14):
    df['Prev_Close'] = df[close_col].shift(1)
    df['TR'] = df.apply(
        lambda row: max(row[high_col] - row[low_col],
                        abs(row[high_col] - row['Prev_Close']),
                        abs(row[low_col] - row['Prev_Close'])), axis=1)
    df[f'ATR_{period}'] = df['TR'].ewm(span=period, adjust=False).mean()
    df.drop(['Prev_Close', 'TR'], axis=1, inplace=True)
    return df
