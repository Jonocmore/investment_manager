# fetch_reddit.py

import os
import asyncio
import asyncpraw
import pandas as pd
from utils import secrets  # Ensure this imports your secrets correctly

async def fetch_reddit_data_for_asset(asset, limit=20):
    """
    Fetches the top Reddit posts for a given asset and saves them to a CSV file.

    Parameters:
    - asset (str): The asset symbol (e.g., 'AAPL', 'MSFT').
    - limit (int): The number of top posts to fetch.
    """
    reddit_client_id = secrets.get('reddit_client_id')
    reddit_client_secret = secrets.get('reddit_client_secret')
    reddit_user_agent = secrets.get('reddit_user_agent')

    if not reddit_client_id or not reddit_client_secret or not reddit_user_agent:
        print("Reddit API credentials are not set. Skipping Reddit data fetch.")
        return

    reddit = asyncpraw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent
    )

    try:
        subreddit = reddit.subreddit(asset)  # Do NOT await this
        posts = []
        async for submission in subreddit.hot(limit=limit):
            posts.append({
                "title": submission.title,
                "score": submission.score,
                "subreddit": submission.subreddit.display_name
            })
        # Save to CSV
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        reddit_file = os.path.join(data_dir, f"reddit_{asset}_data.csv")
        df_posts = pd.DataFrame(posts)
        df_posts.to_csv(reddit_file, index=False)
        print(f"Saved Reddit data for {asset} to {reddit_file}")
    except Exception as e:
        print(f"Failed to fetch Reddit data for {asset}: {e}")
    finally:
        await reddit.close()
