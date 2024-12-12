import os
import praw
import pandas as pd
from utils import is_crypto, secrets

def fetch_reddit_data_for_asset(asset, limit=20):
    """
    Fetch recent Reddit posts related to the given asset.
    Saves results to data/reddit_<asset>_data.csv.
    """
    reddit = praw.Reddit(
        client_id=secrets['REDDIT_CLIENT_ID'],
        client_secret=secrets['REDDIT_CLIENT_SECRET'],
        user_agent=secrets['REDDIT_USER_AGENT']
    )

    # Decide on query keywords
    query = f"{asset} {'crypto' if is_crypto(asset) else 'stock'}"
    subreddit_name = "stocks+CryptoCurrency"
    print(f"Fetching Reddit data for {asset} with query: '{query}'")

    posts = reddit.subreddit(subreddit_name).search(query, limit=limit)

    data = []
    for post in posts:
        data.append({
            "title": post.title,
            "score": post.score,
            "num_comments": post.num_comments,
            "created_utc": post.created_utc,
            "url": post.url,
            "subreddit": post.subreddit.display_name
        })

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    file_path = os.path.join(data_dir, f"reddit_{asset}_data.csv")
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print(f"Reddit data for {asset} saved to {file_path}")
