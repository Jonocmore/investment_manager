# utils.py
import os
import yaml

def load_config(file_path):
    """
    Load a YAML configuration file.
    """
    if not os.path.exists(file_path):
        print(f"Configuration file {file_path} does not exist.")
        return {}
    with open(file_path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file_path}: {e}")
            return {}

# Define the base directory as the parent of the current directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load portfolio and settings configurations
portfolio = load_config(os.path.join(base_dir, 'config', 'portfolio.yaml'))
settings = load_config(os.path.join(base_dir, 'config', 'settings.yaml'))

# Load secrets from environment variables
secrets = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "newsapi_key": os.getenv("NEWSAPI_KEY"),
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
    "reddit_client_id": os.getenv("REDDIT_CLIENT_ID"),
    "reddit_client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "reddit_user_agent": os.getenv("REDDIT_USER_AGENT"),
}

def is_crypto(asset):
    """
    Check if the asset is listed under crypto in either portfolio or watchlist.
    """
    crypto_assets = portfolio.get('portfolio', {}).get('crypto', []) + \
                    portfolio.get('watchlist', {}).get('crypto', [])
    return asset in crypto_assets
