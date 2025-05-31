import requests
import json
import time
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

class NotionPageStockUpdater:
    def __init__(self, notion_token: str, page_id: str, alpha_vantage_api_key: str):
        self.notion_token = notion_token
        self.page_id = page_id
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
            url = f"{self.alpha_vantage_base_url}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if "Error Message" in data:
                print(f"API Error for {symbol}: {data['Error Message']}")
                return None
            
            if "Note" in data:
                print(f"API Limit reached: {data['Note']}")
                return None
            
            quote = data.get("Global Quote", {})
            
            if not quote:
                print(f"No quote data found for {symbol}")
                return None
            
            current_price = float(quote.get("05. price", "0"))
            previous_close = float(quote.get("08. previous close", "0"))
            change = float(quote.get("09. change", "0"))
            change_percent = quote.get("10. change percent", "0%").replace("%", "")
            volume = int(float(quote.get("06. volume", "0")))
            
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
        
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def clear_page_content(self):
        """Clear existing content from the page"""
        try:
            # Get current page content
            url = f"{self.base_url}/blocks/{self.page_id}/children"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                blocks = response.json().get("results", [])
                
                # Delete existing blocks
                for block in blocks:
                    block_id = block["id"]
                    delete_url = f"{self.base_url}/blocks/{block_id}"
                    requests.delete(delete_url, headers=self.headers)
                    
                print("   🧹 Cleared existing page content")
            
        except Exception as e:
            print(f"   ⚠️ Could not clear page content: {str(e)}")
    
    def add_stock_content_to_page(self, stock_data_list: List[Dict]):
        """Add stock data as content blocks to the Notion page"""
        try:
            # Clear existing content first
            self.clear_page_content()
            time.sleep(1)  # Brief pause after clearing
            
            # Create content blocks
            blocks = []
            
            # Add title
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"📈 Stock Portfolio Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        }
                    ]
                }
            })
            
            # Add each stock as a section
            for stock_data in stock_data_list:
                if not stock_data:
                    continue
                    
                # Stock header
                change_emoji = "📈" if stock_data["price_change"] > 0 else "📉" if stock_data["price_change"] < 0 else "➡️"
                
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{change_emoji} {stock_data['symbol']} - ${stock_data['current_price']}"
                                }
                            }
                        ]
                    }
                })
                
                # Stock details
                price_color = "green" if stock_data["price_change"] > 0 else "red" if stock_data["price_change"] < 0 else "default"
                
                details_text = f"""
💰 Current Price: ${stock_data['current_price']}
📊 Change: ${stock_data['price_change']} ({stock_data['percent_change']:+.2f}%)
📈 High: ${stock_data['high_price']:.2f} | 📉 Low: ${stock_data['low_price']:.2f}
🏁 Open: ${stock_data['open_price']:.2f} | 🔒 Previous Close: ${stock_data['previous_close']:.2f}
📦 Volume: {stock_data['volume']:,}
📅 Trading Day: {stock_data['latest_trading_day']}
"""
                
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": details_text.strip()
                                }
                            }
                        ]
                    }
                })
                
                # Add divider
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
            
            # Add footer
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"🤖 Updated automatically via GitHub Actions | ⚡ Powered by Alpha Vantage API"
                            }
                        }
                    ]
                }
            })
            
            # Add all blocks to the page
            url = f"{self.base_url}/blocks/{self.page_id}/children"
            data = {"children": blocks}
            
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            print(f"✅ Successfully updated Notion page with {len(stock_data_list)} stocks")
            return True
            
        except Exception as e:
            print(f"❌ Error updating page content: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def update_stocks(self, stock_symbols: List[str]):
        """Main function to update stocks on the Notion page"""
        print(f"\n🚀 Starting GitHub Actions page update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        stock_data_list = []
        successful_updates = 0
        failed_updates = 0
        
        for i, symbol in enumerate(stock_symbols):
            print(f"\n📊 Processing {symbol.upper()} ({i+1}/{len(stock_symbols)})...")
            
            stock_data = self.get_stock_data(symbol)
            if stock_data:
                stock_data_list.append(stock_data)
                successful_updates += 1
                
                # Display current data
                change_indicator = "📈" if stock_data["price_change"] > 0 else "📉" if stock_data["price_change"] < 0 else "➡️"
                print(f"   💰 Current Price: ${stock_data['current_price']} {change_indicator}")
                print(f"   📊 Change: ${stock_data['price_change']} ({stock_data['percent_change']:+.2f}%)")
                print(f"   📦 Volume: {stock_data['volume']:,}")
            else:
                failed_updates += 1
            
            # Rate limiting
            if i < len(stock_symbols) - 1:
                print("   ⏳ Waiting 12 seconds (API rate limit)...")
                time.sleep(12)
        
        # Update the Notion page with all stock data
        if stock_data_list:
            self.add_stock_content_to_page(stock_data_list)
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully processed: {successful_updates}")
        print(f"❌ Failed updates: {failed_updates}")
        print(f"📅 Page update completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    # Get configuration from environment variables
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    PAGE_ID = os.getenv('PAGE_ID', '200b57d2b3868050a94ac87c6704d57c')  # Your page ID
    
    # Validate required environment variables
    if not ALPHA_VANTAGE_API_KEY:
        print("❌ Error: ALPHA_VANTAGE_API_KEY environment variable not set")
        exit(1)
    
    if not NOTION_TOKEN:
        print("❌ Error: NOTION_TOKEN environment variable not set")
        exit(1)
    
    # Stock symbols to track
    STOCK_SYMBOLS = [
        "AAPL",    # Apple
        "GOOGL",   # Google
        "MSFT",    # Microsoft
        "TSLA",    # Tesla
        "AMZN",    # Amazon
    ]
    
    print("🤖 GitHub Actions Page Stock Updater")
    print("⚡ Using Alpha Vantage Global Quote API")
    print("📄 Updating Notion page content")
    print(f"📊 Tracking {len(STOCK_SYMBOLS)} stocks")
    print("=" * 50)
    
    # Initialize the updater
    updater = NotionPageStockUpdater(NOTION_TOKEN, PAGE_ID, ALPHA_VANTAGE_API_KEY)
    
    # Run the update
    updater.update_stocks(STOCK_SYMBOLS)
    
    print("\n🎉 GitHub Actions page update completed!")

if __name__ == "__main__":
    main()