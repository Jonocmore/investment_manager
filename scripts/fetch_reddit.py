import os
import asyncio
import asyncpraw
import pandas as pd
from utils import secrets
import logging
from asyncprawcore.exceptions import Redirect, Forbidden, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_reddit_data_for_asset(asset, limit=20):
    """
    Fetches the top Reddit posts for a given asset and saves them to a CSV file.

    Parameters:
    - asset (str): The asset symbol or name (e.g., 'AAPL', 'bitcoin').
    - limit (int): The number of top posts to fetch.
    """
    reddit_client_id = secrets.get('reddit_client_id')
    reddit_client_secret = secrets.get('reddit_client_secret')
    reddit_user_agent = secrets.get('reddit_user_agent')

    logger.info(f"Fetching Reddit data for asset: {asset}")

    if not reddit_client_id or not reddit_client_secret or not reddit_user_agent:
        logger.error("Reddit API credentials are not set. Skipping Reddit data fetch.")
        return

    try:
        reddit = asyncpraw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent
        )

        # Await the subreddit coroutine to get the actual Subreddit object
        subreddit = await reddit.subreddit(asset)

        posts = []
        logger.info(f"Fetching top {limit} hot posts from r/{asset}...")
        async for submission in subreddit.hot(limit=limit):
            posts.append({
                "title": submission.title,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "url": submission.url,
                "subreddit": submission.subreddit.display_name,
            })

        if not posts:
            logger.warning(f"No posts found for subreddit: r/{asset}")
        else:
            # Save to CSV
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            os.makedirs(data_dir, exist_ok=True)
            reddit_file = os.path.join(data_dir, f"reddit_{asset}_data.csv")
            df_posts = pd.DataFrame(posts)
            df_posts.to_csv(reddit_file, index=False)
            logger.info(f"Saved Reddit data for {asset} to {reddit_file}")
    except Redirect:
        logger.error(f"Subreddit r/{asset} does not exist.")
    except Forbidden:
        logger.error(f"Access to subreddit r/{asset} is forbidden.")
    except NotFound:
        logger.error(f"Subreddit r/{asset} not found.")
    except Exception as e:
        logger.exception(f"Failed to fetch Reddit data for {asset}: {e}")
    finally:
        await reddit.close()
        logger.info("Reddit client closed.")

async def fetch_all_reddit_data(limit=20):
    """
    Fetches Reddit data for all assets in portfolio.yaml.
    """
    from utils import portfolio  # Import dynamically to avoid circular imports

    portfolio_data = portfolio.get('portfolio', {})
    watchlist_data = portfolio.get('watchlist', {})

    # Combine portfolio and watchlist assets
    portfolio_assets = portfolio_data.get('stocks', []) + \
                       portfolio_data.get('etfs', []) + \
                       portfolio_data.get('crypto', [])
    watchlist_assets = watchlist_data.get('stocks', []) + \
                       watchlist_data.get('crypto', [])

    all_assets = portfolio_assets + watchlist_assets
    logger.info(f"Assets to process for Reddit data: {all_assets}")

    tasks = [fetch_reddit_data_for_asset(asset, limit) for asset in all_assets]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(fetch_all_reddit_data(limit=20))
        print("Reddit data fetch complete!")
    except Exception as e:
        print(f"Error fetching Reddit data: {e}")
