import os
import pandas as pd
import datetime
from openai import OpenAI
from utils import secrets

client = OpenAI(api_key=secrets['openai_api_key'])

def send_telegram_message(message, bot_token, chat_id):
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message
    }
    requests.post(url, params=params)
    print("Weekly overview sent to Telegram.")

def generate_weekly_overview():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    daily_summary_file = os.path.join(data_dir, "daily_summaries.csv")

    if not os.path.exists(daily_summary_file):
        return "No daily summaries found."

    df = pd.read_csv(daily_summary_file)

    # Filter for the last 7 days
    today = datetime.datetime.now()
    one_week_ago = today - datetime.timedelta(days=7)
    recent_data = df[df['date'] >= one_week_ago.strftime("%Y-%m-%d")]

    if recent_data.empty:
        return "No recent summaries to analyze."

    # Separate portfolio and watchlist summaries
    portfolio_summaries = recent_data[recent_data['source'] == 'portfolio']
    watchlist_summaries = recent_data[recent_data['source'] == 'watchlist']

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

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a strategic financial advisor who synthesizes multiple asset insights into a coherent strategy."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        temperature=0.7
    )

    overview = response.choices[0].message.content.strip()
    return overview

if __name__ == "__main__":
    overview = generate_weekly_overview()
    print("=== Weekly Overview ===")
    print(overview)

    # Send to Telegram
    bot_token = secrets['telegram_bot_token']
    chat_id = secrets['telegram_chat_id']
    send_telegram_message(overview, bot_token, chat_id)
