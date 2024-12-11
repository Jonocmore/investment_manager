# Investment Management and Analysis System

## Overview

This project is a Python-based investment management tool that:
- Retrieves historical and current financial data for stocks, ETFs, and cryptocurrencies.
- Fetches relevant news headlines for sentiment analysis.
- Uses AI (OpenAI API) to summarize daily performance, provide weekly portfolio insights, and offer timely recommendations.
- Sends automated summaries and emergency alerts via Telegram.

Initially designed for personal use, this system leverages free-tier APIs and minimal AI usage to keep costs low.

## Features

- **Data Retrieval:**
  - Stocks & ETFs: via [yfinance](https://pypi.org/project/yfinance/)
  - Cryptocurrencies: via the [CoinGecko API](https://www.coingecko.com/en/api)
  - News: via the [NewsAPI](https://newsapi.org/) free tier

- **Indicators & Analysis:**
  - Compute basic technical indicators (SMA, RSI, etc.)
  - Integrate fundamental data where possible (future enhancement)
  - Support sentiment analysis from news headlines

- **AI Integration:**
  - **GPT-3.5:** For daily summaries and recommendations.
  - **GPT-4:** For more in-depth weekly portfolio analysis.

- **Notifications:**
  - Daily summary messages delivered via Telegram.
  - Weekly analysis reports on a chosen day/time.
  - Future feature: Emergency alerts triggered by significant price drops, negative sentiment, or predicted market downturns.

- **Configuration-Driven:**
  - Easily update your portfolio and watchlist by editing YAML config files (no code changes needed).
  - Adjust intervals, thresholds, and other settings through configuration.

## Directory Structure
