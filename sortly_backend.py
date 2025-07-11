# sortly_backend.py

import pandas as pd
import requests
import time
import os
import json
from datetime import datetime, timedelta
from collections import deque

# --- Configuration (These can stay here) ---
API_BASE = "https://api.sortly.co/api/v1"
STOCK_NUMBER_COLUMN = "Stock #"
PRICE_COLUMN = "Value"
SKIP_ROWS = 4
CACHE_FILE_NAME = "sortly_map_cache.json"
CACHE_DURATION_SECONDS = 3600 # Cache valid for 1 hour

class RateLimiter:
    # ... (no changes to this class, it's perfect as is) ...
    def __init__(self, max_requests=1000, time_window=15*60, safety_buffer=50):
        self.max_requests = max_requests - safety_buffer
        self.time_window = time_window
        self.requests = deque()
    def wait_if_needed(self):
        now = datetime.now()
        while self.requests and self.requests[0] <= now - timedelta(seconds=self.time_window):
            self.requests.popleft()
        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_time = (oldest_request + timedelta(seconds=self.time_window) - now).total_seconds()
            if wait_time > 0:
                # This will now be handled by the callback
                pass
                #print(f"⏳ Rate limit reached. Waiting for {wait_time:.1f} seconds...")
                time.sleep(wait_time + 1)
    def record_request(self):
        self.requests.append(datetime.now())


# --- API & Map Functions (Modified to accept a callback for logging) ---

def fetch_sortly_items_and_build_map(limiter, headers, output_callback):
    output_callback("🚀 Starting to fetch all items to build a map from Stock # (first word of item name)...")
    stock_number_map = {}
    page = 1
    items_with_no_name = 0
    while True:
        limiter.wait_if_needed()
        url = f"{API_BASE}/items"
        params = {"per_page": 100, "page": page} 
        try:
            response = requests.get(url, headers=headers, params=params)
            limiter.record_request()
            response.raise_for_status()
            data = response.json().get("data", [])
            if not data:
                output_callback("✅ Finished fetching all items.")
                break 
            for item in data:
                if item.get("type") == "item":
                    full_name = item.get("name")
                    if full_name:
                        stock_number = full_name.split()[0]
                        if stock_number.endswith(".0"): stock_number = stock_number[:-2]
                        stock_number_map[stock_number] = {"id": item["id"], "name": full_name}
                    else: items_with_no_name += 1
            output_callback(f"📄 Fetched page {page}. Total items mapped so far: {len(stock_number_map)}")
            page += 1
        except requests.exceptions.RequestException as e:
            output_callback(f"❌ Error fetching items on page {page}: {e}")
            if hasattr(e.response, 'text'): output_callback(f"Response: {e.response.text}")
            return None
    if items_with_no_name > 0:
        output_callback(f"⚠️  Note: {items_with_no_name} items in Sortly had no name and were skipped.")
    return stock_number_map

def get_or_create_stock_map(limiter, headers, output_callback):
    if os.path.exists(CACHE_FILE_NAME):
        file_age = time.time() - os.path.getmtime(CACHE_FILE_NAME)
        if file_age < CACHE_DURATION_SECONDS:
            output_callback(f"✅ Found recent cache file. Loading map from '{CACHE_FILE_NAME}'...")
            with open(CACHE_FILE_NAME, 'r') as f: return json.load(f)
    output_callback("ℹ️ Cache is old or missing. Fetching new map from Sortly API.")
    stock_map = fetch_sortly_items_and_build_map(limiter, headers, output_callback)
    if stock_map:
        output_callback(f"💾 Saving new map to cache file: '{CACHE_FILE_NAME}'")
        with open(CACHE_FILE_NAME, 'w') as f: json.dump(stock_map, f, indent=4)
    return stock_map

def update_item_price(item_id, item_name, new_price, limiter, headers, output_callback):
    limiter.wait_if_needed()
    if len(limiter.requests) >= limiter.max_requests:
         output_callback(f"⏳ Rate limit reached. Waiting for a moment...")

    url = f"{API_BASE}/items/{item_id}"
    payload = {"name": item_name, "price": new_price, "type": "item"}
    try:
        response = requests.put(url, headers=headers, json=payload)
        limiter.record_request()
        response.raise_for_status()
        output_callback(f"✅ Successfully updated '{item_name}' (ID: {item_id}) to price: {new_price}")
        return True
    except requests.exceptions.RequestException as e:
        output_callback(f"❌ Error updating '{item_name}' (ID: {item_id}): {e}")
        if hasattr(e.response, 'text'): output_callback(f"   Response Body: {e.response.text}")
        return False

# --- Main Callable Function for the App ---

def run_update_process(api_token, uploaded_file, output_callback):
    """The main entry point for the Streamlit app to call."""
    headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {api_token}"}
    rate_limiter = RateLimiter()
    
    # 1. Get the Stock # to Item ID map
    stock_to_item_data_map = get_or_create_stock_map(rate_limiter, headers, output_callback)
    if not stock_to_item_data_map:
        output_callback("Halting script: could not load or create the item map.")
        return

    # 2. Read the uploaded Excel file from memory
    try:
        output_callback(f"\n📖 Reading uploaded Excel file...")
        # pandas can read the uploaded file object directly
        df = pd.read_excel(uploaded_file, skiprows=SKIP_ROWS)
        
        if STOCK_NUMBER_COLUMN not in df.columns or PRICE_COLUMN not in df.columns:
            output_callback(f"❌ Error: Excel file must contain columns named '{STOCK_NUMBER_COLUMN}' and '{PRICE_COLUMN}'.")
            output_callback(f"   Available columns found: {list(df.columns)}")
            return
            
    except Exception as e:
        output_callback(f"❌ Error reading Excel file: {e}")
        return

    # 3. Iterate through Excel rows and update prices
    output_callback("\n🔄 Starting to process Excel rows and update prices in Sortly...")
    items_not_found, successful_updates, failed_updates = [], 0, 0
    
    for index, row in df.iterrows():
        stock_number, new_price = row.get(STOCK_NUMBER_COLUMN), row.get(PRICE_COLUMN)
        if pd.isna(stock_number) or pd.isna(new_price): continue

        stock_number_str = str(stock_number).strip()
        if stock_number_str.endswith(".0"): stock_number_str = stock_number_str[:-2]
        
        item_data = stock_to_item_data_map.get(stock_number_str)
        if item_data:
            if update_item_price(item_data['id'], item_data['name'], new_price, rate_limiter, headers, output_callback):
                successful_updates += 1
            else:
                failed_updates += 1
        else:
            output_callback(f"⚠️  Stock # from Excel not found in Sortly map: '{stock_number_str}'")
            items_not_found.append(stock_number_str)

    # 4. Final Report
    output_callback("\n\n--- 📊 Update Complete ---")
    output_callback(f"✅ Successful updates: {successful_updates}")
    output_callback(f"❌ Failed updates: {failed_updates}")
    output_callback(f"❓ Stock #s in Excel not found in Sortly map: {len(items_not_found)}")
    if items_not_found:
        output_callback("   - " + "\n   - ".join(items_not_found))
    output_callback("--------------------------")