import os
import pandas as pd
from openai import OpenAI  # Updated import for openai>=1.0.0
from utils import portfolio, settings, secrets, is_crypto

# Initialize OpenAI client with the API key from environment variables
client = OpenAI(
    api_key=secrets.get('openai_api_key')  # Optional: Defaults to environment variable
)

# Verify that the OpenAI API key is set
if not client.api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

def generate_summary_for_asset(asset, source="portfolio", lookback_days=30):
    """
    Generate a summary that uses historical data for context but focuses on immediate actionable insights.
    Includes specific crypto indicators such as volume and market cap for cryptocurrency assets.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    asset_file = os.path.join(data_dir, f"{asset}_data.csv")
    if not os.path.exists(asset_file):
        print(f"No processed data file found for {asset}. Unable to generate summary.")
        return "No data available."

    df_asset = pd.read_csv(asset_file)
    if df_asset.empty:
        return "No data available."

    # Set index based on available date column
    if 'Date' in df_asset.columns:
        df_asset['Date'] = pd.to_datetime(df_asset['Date'], errors='coerce')
        df_asset.set_index('Date', inplace=True)
    elif 'datetime' in df_asset.columns:
        df_asset['datetime'] = pd.to_datetime(df_asset['datetime'], errors='coerce')
        df_asset.set_index('datetime', inplace=True)
    else:
        print(f"No recognized date/datetime column in {asset} data. Cannot process.")
        return "No data available."

    df_asset.sort_index(inplace=True)

    # Extract indicators
    latest = df_asset.iloc[-1]
    close_prices = df_asset['price'] if is_crypto(asset) else df_asset['Close']
    if close_prices.empty:
        return "No close price data available."

    # Extract crypto-specific indicators
    if is_crypto(asset):
        volume = latest['volume'] if 'volume' in df_asset.columns else None
        market_cap = latest['market_cap'] if 'market_cap' in df_asset.columns else None
    else:
        volume = latest['Volume'] if 'Volume' in df_asset.columns else None
        market_cap = None  # Market cap is not typically available for stocks/ETFs in this data set

    # Extract RSI and MACD indicators if available
    rsi_value = next((latest[c] for c in df_asset.columns if 'RSI' in c), None)
    macd_line = latest['MACD_line'] if 'MACD_line' in df_asset.columns else None
    macd_signal = latest['MACD_signal'] if 'MACD_signal' in df_asset.columns else None

    # Recent data for short-term view
    end_date = df_asset.index[-1]
    start_date = end_date - pd.Timedelta(days=lookback_days)
    recent_data = close_prices[close_prices.index >= start_date]

    # Long-term data (about a year)
    one_year_ago = end_date - pd.Timedelta(days=365)
    long_term_data = close_prices[close_prices.index >= one_year_ago]

    # Short-term performance
    if len(recent_data) > 1:
        start_price = recent_data.iloc[0]
        end_price = recent_data.iloc[-1]
        pct_change_recent = ((end_price - start_price) / start_price) * 100
    else:
        pct_change_recent = None

    # Load news
    news_file = os.path.join(data_dir, f"news_{asset}_data.csv")
    news_headlines = []
    if os.path.exists(news_file):
        df_news = pd.read_csv(news_file)
        news_headlines = df_news.head(5)[['title', 'description', 'url']].to_dict('records')

    # Load Reddit
    reddit_file = os.path.join(data_dir, f"reddit_{asset}_data.csv")
    reddit_posts = []
    if os.path.exists(reddit_file):
        df_reddit = pd.read_csv(reddit_file)
        df_reddit.sort_values('score', ascending=False, inplace=True)
        reddit_posts = df_reddit.head(5)[['title', 'score', 'subreddit']].to_dict('records')

    # Source-based action context
    if source == "portfolio":
        action_context = (
            "You currently hold this asset. Provide direct instructions based on current conditions. "
            "Do not ask the user to monitor or watch anything; simply state what to do right now, "
            "such as 'Add to position', 'Hold steady', 'Reduce your stake by X%', or 'Sell immediately' if warranted."
        )
    else:
        action_context = (
            "This asset is on the watchlist. Provide direct instructions on whether to buy now, wait, "
            "or avoid entirely based on current conditions. Do not tell the user to monitor or watch; "
            "just give a direct recommended action."
        )

    # Construct the prompt
    prompt = f"""
You are a top-tier financial analyst. Provide a heading with the asset and its source category:

Heading: "{asset.upper()} ({source.capitalize()})"

You have about a year of historical data and recent indicators for {asset}.
For cryptocurrencies, include volume (latest: {volume}), market cap (latest: {market_cap}), and price change (~{pct_change_recent:.2f}% recent change if available).
Use long-term data to identify patterns that matter now, and short-term indicators (last {lookback_days} days) for immediate action.

Incorporate recent news and Reddit sentiment if relevant.
Reference exact indicators (RSI={rsi_value}, MACD_line={macd_line}, MACD_signal={macd_signal}).

Your final recommendation must be a direct action:
- If portfolio: e.g. "Add more now", "Hold at current levels", "Reduce your position by X%", or "Sell immediately".
- If watchlist: e.g. "Buy now", "Begin a small initial position", "Wait for a pullback before buying", or "Avoid entry at this time".

Do not tell the user to monitor or watch conditions, as this analysis runs daily and the AI will surface changes as needed.
Just give a direct, current action based on the synthesis of all data.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial assistant who provides precise, timely, and data-driven market insights without telling the user to watch or monitor anything."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1200,
            temperature=0.7
        )
    except Exception as e:
        print(f"OpenAI API request failed: {e}")
        return "Failed to generate summary."

    summary = response.choices[0].message.content.strip()
    return summary
