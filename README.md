# 📈 Notion Stock Price Updater

Automatically updates your Notion database with real-time stock prices using Alpha Vantage API and GitHub Actions.

## 🚀 Features

- ✅ **Automated scheduling**: Runs weekdays at 4:30 PM EST
- ✅ **Real-time data**: Alpha Vantage Global Quote API
- ✅ **Cloud-based**: Runs on GitHub Actions (free)
- ✅ **Secure**: API keys stored as GitHub secrets
- ✅ **Smart updates**: Creates new entries or updates existing ones
- ✅ **Rate limiting**: Respects API limits (5 calls/minute)
- ✅ **Comprehensive data**: Price, volume, change, high/low, etc.

## 📊 Stock Data Tracked

- Current Price
- Previous Close
- Price Change ($ and %)
- Volume
- Open/High/Low prices
- Latest Trading Day
- Last Updated timestamp

## 🏗️ Setup

### 1. Notion Database Structure

Make sure your Notion database has these columns:
- **Name** (Title)
- **Symbol** (Text)
- **Current Price** (Number)
- **Previous Close** (Number)
- **Price Change** (Number)
- **Percent Change** (Number)
- **Volume** (Number)
- **Open Price** (Number)
- **High Price** (Number)
- **Low Price** (Number)
- **Trading Day** (Text)
- **Last Updated** (Date)

### 2. Required API Keys

- **Alpha Vantage API Key**: Get from [alphavantage.co](https://www.alphavantage.co/support/#api-key)
- **Notion Integration Token**: Create at [notion.so/my-integrations](https://www.notion.so/my-integrations)
- **Database ID**: Extract from your Notion database URL

### 3. GitHub Secrets Configuration

Add these secrets to your repository:
- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `NOTION_TOKEN`: Your Notion integration token
- `DATABASE_ID`: Your Notion database ID

## ⚙️ Configuration

Edit the `STOCK_SYMBOLS` list in `github_stock_updater.py` to track your desired stocks:

```python
STOCK_SYMBOLS = [
    "AAPL",    # Apple
    "GOOGL",   # Google
    "MSFT",    # Microsoft
    "TSLA",    # Tesla
    "AMZN",    # Amazon
    # Add more stocks here...
]
```

## 🕒 Schedule

- **Automatic**: Monday-Friday at 4:30 PM EST (21:30 UTC)
- **Manual**: Click "Run workflow" in GitHub Actions tab

## 🛠️ Manual Testing

1. Go to **Actions** tab in your repository
2. Click **Stock Price Updater**
3. Click **Run workflow** → **Run workflow**
4. Watch the logs for real-time updates

## 📝 Logs Example

```
🤖 GitHub Actions Stock Updater
⚡ Using Alpha Vantage Global Quote API
☁️ Running in GitHub Actions environment
📊 Tracking 5 stocks

📊 Processing AAPL (1/5)...
   💰 Current Price: $173.50 📈
   📊 Change: $2.15 (+1.26%)
   📈 High: $174.30 | 📉 Low: $171.77
   📦 Volume: 54,091,700
   📅 Trading Day: 2024-01-15
✅ Updated entry for AAPL
```

## 🔧 Troubleshooting

- **API Limits**: Free Alpha Vantage allows 5 calls/minute, 500/day
- **Rate Limiting**: Script automatically waits 12 seconds between calls
- **Failed Updates**: Check API keys and Notion permissions
- **Missing Data**: Verify database column names match exactly

## 📈 Free Tier Limits

- **GitHub Actions**: 2,000 minutes/month (plenty for daily updates)
- **Alpha Vantage**: 5 API calls/minute, 500 calls/day
- **Notion API**: 3 requests/second (no daily limit)

## 🔒 Security

- API keys stored as encrypted GitHub secrets
- No sensitive data in public code
- Secrets automatically masked in logs
- Environment variables used exclusively

---

**Happy Trading! 📊💰**