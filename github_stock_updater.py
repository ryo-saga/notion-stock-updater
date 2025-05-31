import requests
import json
import time
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

class NotionStockUpdater:
    def __init__(self, notion_token: str, database_id: str, alpha_vantage_api_key: str):
        self.notion_token = notion_token
        self.database_id = database_id
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch current stock data using Alpha Vantage API"""
        try:
            # Alpha Vantage Global Quote API call
            url = f"{self.alpha_vantage_base_url}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                print(f"API Error for {symbol}: {data['Error Message']}")
                return None
            
            if "Note" in data:
                print(f"API Limit reached: {data['Note']}")
                return None
            
            # Extract data from Global Quote
            quote = data.get("Global Quote", {})
            
            if not quote:
                print(f"No quote data found for {symbol}")
                return None
            
            # Parse the data
            current_price = float(quote.get("05. price", "0"))
            previous_close = float(quote.get("08. previous close", "0"))
            change = float(quote.get("09. change", "0"))
            change_percent = quote.get("10. change percent", "0%").replace("%", "")
            volume = int(float(quote.get("06. volume", "0")))
            
            # Clean up percent change (remove % and convert to float)
            try:
                percent_change = float(change_percent)
            except ValueError:
                percent_change = 0.0
            
            return {
                "symbol": quote.get("01. symbol", symbol.upper()),
                "current_price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "price_change": round(change, 2),
                "percent_change": round(percent_change, 2),
                "volume": volume,
                "open_price": float(quote.get("02. open", "0")),
                "high_price": float(quote.get("03. high", "0")),
                "low_price": float(quote.get("04. low", "0")),
                "latest_trading_day": quote.get("07. latest trading day", ""),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching data for {symbol}: {str(e)}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Data parsing error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching data for {symbol}: {str(e)}")
            return None
    
    def query_database(self) -> List[Dict]:
        """Query the Notion database to get existing entries"""
        url = f"{self.base_url}/databases/{self.database_id}/query"
        
        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            print(f"Error querying database: {str(e)}")
            return []
    
    def create_database_entry(self, stock_data: Dict) -> bool:
        """Create a new entry in the Notion database"""
        url = f"{self.base_url}/pages"
        
        # Create the page properties
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": f"{stock_data['symbol']} Stock Quote"
                        }
                    }
                ]
            },
            "Symbol": {
                "rich_text": [
                    {
                        "text": {
                            "content": stock_data["symbol"]
                        }
                    }
                ]
            },
            "Current Price": {
                "number": stock_data["current_price"]
            },
            "Previous Close": {
                "number": stock_data["previous_close"]
            },
            "Price Change": {
                "number": stock_data["price_change"]
            },
            "Percent Change": {
                "number": stock_data["percent_change"]
            },
            "Volume": {
                "number": stock_data["volume"]
            },
            "Open Price": {
                "number": stock_data["open_price"]
            },
            "High Price": {
                "number": stock_data["high_price"]
            },
            "Low Price": {
                "number": stock_data["low_price"]
            },
            "Trading Day": {
                "rich_text": [
                    {
                        "text": {
                            "content": stock_data["latest_trading_day"]
                        }
                    }
                ]
            },
            "Last Updated": {
                "date": {
                    "start": stock_data["last_updated"]
                }
            }
        }
        
        data = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            print(f"✅ Created entry for {stock_data['symbol']}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating entry for {stock_data['symbol']}: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False
    
    def update_database_entry(self, page_id: str, stock_data: Dict) -> bool:
        """Update an existing entry in the Notion database"""
        url = f"{self.base_url}/pages/{page_id}"
        
        properties = {
            "Current Price": {
                "number": stock_data["current_price"]
            },
            "Previous Close": {
                "number": stock_data["previous_close"]
            },
            "Price Change": {
                "number": stock_data["price_change"]
            },
            "Percent Change": {
                "number": stock_data["percent_change"]
            },
            "Volume": {
                "number": stock_data["volume"]
            },
            "Open Price": {
                "number": stock_data["open_price"]
            },
            "High Price": {
                "number": stock_data["high_price"]
            },
            "Low Price": {
                "number": stock_data["low_price"]
            },
            "Trading Day": {
                "rich_text": [
                    {
                        "text": {
                            "content": stock_data["latest_trading_day"]
                        }
                    }
                ]
            },
            "Last Updated": {
                "date": {
                    "start": stock_data["last_updated"]
                }
            }
        }
        
        data = {"properties": properties}
        
        try:
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            print(f"📝 Updated entry for {stock_data['symbol']}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating entry for {stock_data['symbol']}: {str(e)}")
            return False
    
    def find_existing_entry(self, symbol: str, existing_entries: List[Dict]) -> Optional[str]:
        """Find if a stock symbol already exists in the database"""
        for entry in existing_entries:
            try:
                # Check if Symbol property exists and matches
                symbol_prop = entry.get("properties", {}).get("Symbol", {})
                if symbol_prop.get("rich_text"):
                    existing_symbol = symbol_prop["rich_text"][0]["text"]["content"]
                    if existing_symbol.upper() == symbol.upper():
                        return entry["id"]
            except (KeyError, IndexError):
                continue
        return None
    
    def update_stocks(self, stock_symbols: List[str]):
        """Main function to update all stocks in the database"""
        print(f"\n🚀 Starting GitHub Actions stock update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Get existing database entries
        existing_entries = self.query_database()
        
        successful_updates = 0
        failed_updates = 0
        
        for i, symbol in enumerate(stock_symbols):
            print(f"\n📊 Processing {symbol.upper()} ({i+1}/{len(stock_symbols)})...")
            
            # Get stock data
            stock_data = self.get_stock_data(symbol)
            if not stock_data:
                failed_updates += 1
                continue
            
            # Display current data
            change_indicator = "📈" if stock_data["price_change"] > 0 else "📉" if stock_data["price_change"] < 0 else "➡️"
            print(f"   💰 Current Price: ${stock_data['current_price']} {change_indicator}")
            print(f"   📊 Change: ${stock_data['price_change']} ({stock_data['percent_change']:+.2f}%)")
            print(f"   📈 High: ${stock_data['high_price']:.2f} | 📉 Low: ${stock_data['low_price']:.2f}")
            print(f"   📦 Volume: {stock_data['volume']:,}")
            print(f"   📅 Trading Day: {stock_data['latest_trading_day']}")
            
            # Check if entry already exists
            existing_page_id = self.find_existing_entry(symbol, existing_entries)
            
            if existing_page_id:
                # Update existing entry
                if self.update_database_entry(existing_page_id, stock_data):
                    successful_updates += 1
                else:
                    failed_updates += 1
            else:
                # Create new entry
                if self.create_database_entry(stock_data):
                    successful_updates += 1
                else:
                    failed_updates += 1
            
            # Rate limiting - Alpha Vantage free tier allows 5 API calls per minute
            if i < len(stock_symbols) - 1:  # Don't wait after the last symbol
                print("   ⏳ Waiting 12 seconds (API rate limit)...")
                time.sleep(12)  # 12 seconds = 5 calls per minute
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully updated: {successful_updates}")
        print(f"❌ Failed updates: {failed_updates}")
        print(f"📅 GitHub Actions update completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    # Get configuration from environment variables (GitHub secrets)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    DATABASE_ID = os.getenv('DATABASE_ID', '200b57d2b3868022b198d81144167217')  # Default from your URL
    
    # Validate required environment variables
    if not ALPHA_VANTAGE_API_KEY:
        print("❌ Error: ALPHA_VANTAGE_API_KEY environment variable not set")
        exit(1)
    
    if not NOTION_TOKEN:
        print("❌ Error: NOTION_TOKEN environment variable not set")
        exit(1)
    
    # Stock symbols to track - ADD YOUR DESIRED STOCKS HERE
    STOCK_SYMBOLS = [
        "AAPL",    # Apple
        "GOOGL",   # Google
        "MSFT",    # Microsoft
        "TSLA",    # Tesla
        "AMZN",    # Amazon
        "META",    # Meta (Facebook)
        "NVDA",    # NVIDIA
        "NFLX",    # Netflix
        # Add more stocks here as needed
        # "JPM",   # JPMorgan Chase
        # "V",     # Visa
        # "WMT",   # Walmart
    ]
    
    print("🤖 GitHub Actions Stock Updater")
    print("⚡ Using Alpha Vantage Global Quote API")
    print("☁️ Running in GitHub Actions environment")
    print(f"📊 Tracking {len(STOCK_SYMBOLS)} stocks")
    print("=" * 50)
    
    # Initialize the updater
    updater = NotionStockUpdater(NOTION_TOKEN, DATABASE_ID, ALPHA_VANTAGE_API_KEY)
    
    # Run the update
    updater.update_stocks(STOCK_SYMBOLS)
    
    print("\n🎉 GitHub Actions stock update completed!")

if __name__ == "__main__":
    main()