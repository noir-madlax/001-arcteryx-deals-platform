import requests
from bs4 import BeautifulSoup
import json
import re
import random
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def clean_price(price_str):
    if not price_str: return 0.0
    # Remove currency symbols and commas
    nums = re.findall(r"[\d,]+\.?\d*", price_str.replace("$", "").replace(",", ""))
    return float(nums[0]) if nums else 0.0

def scrape_slickdeals():
    print("[1/2] Scraping Slickdeals for Arc'teryx deals...")
    url = "https://slickdeals.net/newsearch/search/?q=arcteryx&searcharea=0&searchin=1&sortby=1"
    deals = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            print(f"   ⚠️ Slickdeals blocked (Status {res.status_code})")
            return deals
        
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.select('.sd-tile') # Slickdeals class name for deal cards
        
        for card in cards[:10]:
            title_el = card.select_one('.sd-tile-title a')
            price_el = card.select_one('.sd-price-value')
            img_el = card.select_one('img')
            
            title = title_el.text.strip() if title_el else "Unknown"
            price = clean_price(price_el.text.strip()) if price_el else 0
            
            deals.append({
                "model": re.sub(r'\$.*', '', title).strip(),
                "source": "Slickdeals",
                "sale_price": price,
                "original_price": price * 1.4, # Estimate original if not found
                "image_url": img_el['src'] if img_el else "",
                "source_url": "https://slickdeals.net" + (title_el['href'] if title_el else ""),
                "year": 2025,
                "category": "Apparel",
                "sizes": ["Unknown"]
            })
        print(f"   ✅ Found {len(deals)} deals.")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    return deals

def scrape_ebay():
    print("[2/2] Scraping eBay for Arc'teryx Outlet...")
    url = "https://www.ebay.com/sch/i.html?_nkw=arcteryx+jacket&_sacat=0&LH_BIN=1&rt=nc&_udhi=500"
    deals = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            print(f"   ⚠️ eBay blocked (Status {res.status_code})")
            return deals
            
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.s-item')
        
        for item in items[1:6]: # Skip first placeholder
            title_el = item.select_one('.s-item__title')
            price_el = item.select_one('.s-item__price')
            img_el = item.select_one('.s-item__image-img')
            link_el = item.select_one('.s-item__link')
            
            title = title_el.text.strip() if title_el else ""
            price = clean_price(price_el.text.strip()) if price_el else 0
            
            deals.append({
                "model": re.sub(r'New Listing|Arc\'teryx', '', title, flags=re.IGNORECASE).strip(),
                "source": "eBay Outlet",
                "sale_price": price,
                "original_price": price * 1.3,
                "image_url": img_el['src'] if img_el else "",
                "source_url": link_el['href'] if link_el else "",
                "year": 2025,
                "category": "Jacket",
                "sizes": ["Various"]
            })
        print(f"   ✅ Found {len(deals)} deals.")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    return deals

if __name__ == "__main__":
    all_deals = scrape_slickdeals() + scrape_ebay()
    
    # Save raw data
    with open("raw_data.json", "w") as f:
        json.dump(all_deals, f, indent=2)
    
    print(f"\n🎉 Scraper finished. Total raw items: {len(all_deals)}")
    print("   -> Saved to raw_data.json")
