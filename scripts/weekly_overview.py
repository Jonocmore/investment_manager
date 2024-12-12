# weekly_overview.py

import os
import pandas as pd
import datetime
from openai import OpenAI  # Updated import for openai>=1.0.0
import requests
from utils import portfolio, settings, secrets

# Initialize OpenAI client with the API key from environment variables
client = OpenAI(
    api_key=secrets.get('openai_api_key')  # Optional: Defaults to environment variable
)

# Verify that the OpenAI API key is set
if not client.api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")


def send_telegram_message(message, bot_token, chat_id):
    """
    Send a message to a Telegram chat using the provided bot token and chat ID.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # Optional: for better formatting
    }
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        print("Weekly overview sent to Telegram.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message to Telegram: {e}")


def generate_weekly_overview():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    daily_summary_file = os.path.join(data_dir, "daily_summaries.csv")

    if not os.path.exists(daily_summary_file):
        return "No daily summaries found."

    try:
        df = pd.read_csv(daily_summary_file)
    except Exception as e:
        print(f"Failed to read daily summaries: {e}")
        return "Failed to read daily summaries."

    # Ensure the 'date' column is in datetime format
    if 'date' not in df.columns:
        print("The 'date' column is missing from daily_summaries.csv.")
        return "Invalid daily summaries format."

    try:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    except Exception as e:
        print(f"Failed to parse dates: {e}")
        return "Invalid date format in daily summaries."

    # Filter for the last 7 days
    today = datetime.datetime.now()
    one_week_ago = today - datetime.timedelta(days=7)
    recent_data = df[df['date'] >= one_week_ago]

    if recent_data.empty:
        return "No recent summaries to analyze."

    # Separate portfolio and watchlist summaries
    portfolio_summaries = recent_data[recent_data['source'] == 'portfolio']
    watchlist_summaries = recent_data[recent_data['source'] == 'watchlist']

    # Check if there are summaries to analyze
    if portfolio_summaries.empty and watchlist_summaries.empty:
        return "No portfolio or watchlist summaries available for the past week."

    # Construct prompt for GPT-4
    prompt = f"""
You are a sophisticated financial analyst. Below are the daily summaries from the past week for all assets in the portfolio and watchlist.

**Portfolio Assets Summaries (Past Week):**
{portfolio_summaries[['date', 'asset', 'summary']].to_string(index=False)}

**Watchlist Assets Summaries (Past Week):**
{watchlist_summaries[['date', 'asset', 'summary']].to_string(index=False)}

Use this data to:
1. Identify key trends or shifts in the portfolio assets.
2. Determine if any watchlist assets have shown enough positive signs to justify adding them to the portfolio.
3. Provide a strategic-level recommendation. For example, if certain portfolio assets are underperforming consistently, consider rotating out of them. If some watchlist assets are showing strong signs, advise adding them to the portfolio now.
4. Provide direct strategic suggestions rather than telling the user to monitor conditions.

Your response should be a single comprehensive summary message, focusing on strategic actions to take at this point in time. Be clear and direct, leveraging the patterns observed in these daily summaries.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strategic financial advisor who synthesizes multiple asset insights into a coherent strategy."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
    except Exception as e:
        print(f"OpenAI API request failed: {e}")
        return "Failed to generate weekly overview."

    overview = response.choices[0].message.content.strip()
    return overview


if __name__ == "__main__":
    try:
        overview = generate_weekly_overview()
        print("=== Weekly Overview ===")
        print(overview)

        # Send to Telegram
        bot_token = secrets.get('telegram_bot_token')
        chat_id = secrets.get('telegram_chat_id')

        if not bot_token or not chat_id:
            print("Telegram bot token or chat ID is not set. Skipping Telegram message.")
        else:
            send_telegram_message(overview, bot_token, chat_id)

    except Exception as e:
        print(f"Weekly overview generation failed: {e}")
