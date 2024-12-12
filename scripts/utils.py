# utils.py
import yaml
import os

def load_config(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
portfolio = load_config(os.path.join(base_dir, 'config', 'portfolio.yaml'))
settings = load_config(os.path.join(base_dir, 'config', 'settings.yaml'))
secrets = load_config(os.path.join(base_dir, 'config', 'secrets.yaml'))

def is_crypto(asset):
    """Check if the asset is listed under crypto in either portfolio or watchlist."""
    crypto_assets = portfolio['portfolio'].get('crypto', []) + portfolio['watchlist'].get('crypto', [])
    return asset in crypto_assets
