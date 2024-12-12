# daily_run.py
import os
import asyncio
import pandas as pd
from utils import portfolio, secrets
from fetch_data import fetch_data_for_asset, fetch_news_for_asset
from fetch_reddit import fetch_reddit_data_for_asset
from process_data import process_data_for_asset
from ai_analysis import generate_summary_for_asset, send_telegram_message
from datetime import datetime

async def run_pipeline_for_asset(asset):
    print(f"Starting pipeline for {asset}...")

    # Determine source (portfolio or watchlist)
    portfolio_data = portfolio.get('portfolio', {})
    watchlist_data = portfolio.get('watchlist', {})

    if (asset in portfolio_data.get('stocks', []) or
        asset in portfolio_data.get('etfs', []) or
        asset in portfolio_data.get('crypto', [])):
        source = "portfolio"
    elif (asset in watchlist_data.get('stocks', []) or
          asset in watchlist_data.get('crypto', [])):
        source = "watchlist"
    else:
        source = "watchlist"

    # 1. Fetch Data
    fetch_data_for_asset(asset)
    fetch_news_for_asset(asset, limit=20)
    fetch_reddit_data_for_asset(asset, limit=20)

    # 2. Process Data
    process_data_for_asset(asset)

    # 3. Generate daily summary
    summary = generate_summary_for_asset(asset, source=source, lookback_days=30)
    print(summary)

    # 4. Send to Telegram (optional)
    bot_token = secrets.get('telegram_bot_token')
    chat_id = secrets.get('telegram_chat_id')

    if not bot_token or not chat_id:
        print("Telegram bot token or chat ID is not set. Skipping Telegram message.")
    else:
        send_telegram_message(summary, bot_token, chat_id)

    # 5. Store daily summary for weekly aggregation
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    daily_summary_file = os.path.join(data_dir, "daily_summaries.csv")

    today_str = datetime.now().strftime("%Y-%m-%d")
    row = {
        "date": today_str,
        "asset": asset,
        "source": source,
        "summary": summary
    }

    if not os.path.exists(daily_summary_file):
        df = pd.DataFrame([row])
        df.to_csv(daily_summary_file, index=False)
    else:
        try:
            df_existing = pd.read_csv(daily_summary_file)
            df_new = pd.DataFrame([row])
            # Use pd.concat instead of append
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(daily_summary_file, index=False)
        except Exception as e:
            print(f"Failed to update daily summaries: {e}")

    print(f"Pipeline completed for {asset}.\n")

async def daily_workflow():
    portfolio_data = portfolio.get('portfolio', {})
    watchlist_data = portfolio.get('watchlist', {})

    portfolio_assets = portfolio_data.get('stocks', []) + \
                       portfolio_data.get('etfs', []) + \
                       portfolio_data.get('crypto', [])
    watchlist_assets = watchlist_data.get('stocks', []) + \
                       watchlist_data.get('crypto', [])

    all_assets = portfolio_assets + watchlist_assets

    for asset in all_assets:
        try:
            await run_pipeline_for_asset(asset)
        except Exception as e:
            print(f"Error processing {asset}: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(daily_workflow())
        print("Daily workflow complete!")
    except Exception as e:
        print(f"Daily workflow failed: {e}")
