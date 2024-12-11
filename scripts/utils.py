import yaml
import os

def load_config(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

# Load all configs at module load (optional, or you can load in each script)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
portfolio = load_config(os.path.join(base_dir, 'config', 'portfolio.yaml'))
settings = load_config(os.path.join(base_dir, 'config', 'settings.yaml'))
secrets = load_config(os.path.join(base_dir, 'config', 'secrets.yaml'))
