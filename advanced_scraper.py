import requests
from bs4 import BeautifulSoup
import os
import json
import re
import time
from urllib.parse import urljoin

# Configuration
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(OUTPUT_DIR, 'images')
os.makedirs(IMAGE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def download_image(url, filename):
    """Download image to local 'images' dir with retries."""
    filepath = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(filepath):
        return filename  # Already downloaded
        
    try:
        # eBay and Amazon images often need specific headers or referer
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(res.content)
            return filename
    except Exception as e:
        print(f"   ⚠️ Image download failed: {e}")
    return None

def scrape_ebay():
    print("[1/2] Scraping eBay Outlet (High Success Rate)...")
    # Use eBay search URL for Arcteryx Jackets on sale
    url = "https://www.ebay.com/sch/i.html?_nkw=arcteryx+jacket&_sacat=0&LH_BIN=1&rt=nc&_udhi=500"
    items = []
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # eBay listing structure
        for card in soup.select('.s-item')[:8]: # Top 8 results
            title_el = card.select_one('.s-item__title span') or card.select_one('.s-item__title')
            price_el = card.select_one('.s-item__price')
            img_el = card.select_one('.s-item__image-img')
            link_el = card.select_one('.s-item__link')
            
            title = title_el.text.strip() if title_el else ""
            price_str = price_el.text.strip().split(' ')[0] if price_el else "0"
            price = float(re.sub(r'[^\d.]', '', price_str)) if price_str else 0
            
            if not title or 'shop on ebay' in title.lower(): continue

            # Extract Image URL
            img_url = img_el.get('src', '') if img_el else ""
            # Sometimes img is in style attribute
            if not img_url and img_el:
                style = img_el.get('style', '')
                match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if match: img_url = match.group(1)

            if img_url and not img_url.startswith('http'):
                img_url = 'https:' + img_url

            items.append({
                "title": title,
                "sale_price": price,
                "image_url": img_url,
                "source_url": link_el['href'] if link_el else "",
                "source": "eBay Outlet"
            })
        print(f"   ✅ Found {len(items)} raw items.")
    except Exception as e:
        print(f"   ❌ Error scraping eBay: {e}")
    return items

def scrape_slickdeals():
    print("[2/2] Scraping Slickdeals (Real User Deals)...")
    url = "https://slickdeals.net/newsearch/search/?q=arcteryx&searcharea=0&searchin=1&sortby=1"
    items = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Slickdeals structure
        for card in soup.select('.sd-tile')[:5]:
            title_el = card.select_one('.sd-tile-title a')
            price_el = card.select_one('.sd-price-value')
            img_el = card.select_one('img')
            
            title = title_el.text.strip() if title_el else ""
            price_str = price_el.text.strip() if price_el else ""
            price = float(re.sub(r'[^\d.]', '', price_str)) if price_str else 0
            
            img_url = img_el['src'] if img_el and img_el.get('src') else ""
            if img_url and not img_url.startswith('http'):
                img_url = 'https:' + img_url

            items.append({
                "title": title,
                "sale_price": price,
                "image_url": img_url,
                "source_url": "https://slickdeals.net" + (title_el['href'] if title_el else ""),
                "source": "Slickdeals"
            })
        print(f"   ✅ Found {len(items)} raw items.")
    except Exception as e:
        print(f"   ❌ Error scraping Slickdeals: {e}")
    return items

def process_data(raw_items):
    print("\n🧹 Processing Data & Downloading Images...")
    final_data = []
    seen_titles = set()
    
    for i, item in enumerate(raw_items):
        title = item['title']
        # Simple deduplication
        clean_title = re.sub(r'\d+|new listing|arc.?teryx|men|women', '', title, flags=re.IGNORECASE).strip()
        if clean_title in seen_titles or len(clean_title) < 3:
            continue
        seen_titles.add(clean_title)
        
        # Determine Model Name (Simplified)
        model = title.replace("New Listing", "").strip()
        
        # Download Image
        # Generate a safe filename
        safe_name = re.sub(r'[^\w\-_\. ]', '_', f"item_{i}_{clean_title[:15]}.jpg")
        local_img = download_image(item['image_url'], safe_name)
        
        # Estimate original price (if only sale price available, assume ~30% discount for display)
        sale_price = item.get('sale_price', 0)
        orig_price = round(sale_price * 1.4, 2)
        discount = round((1 - sale_price/orig_price) * 100)
        
        # Category extraction
        category = "Apparel"
        if "jacket" in title.lower(): category = "Hard Shell / Jacket"
        elif "hoody" in title.lower(): category = "Mid Layer"
        elif "shoe" in title.lower(): category = "Footwear"

        # Create the final object
        final_data.append({
            "model": model,
            "year": 2025, # Assumption based on current date
            "category": category,
            "original_price": orig_price,
            "sale_price": sale_price,
            "discount_pct": discount,
            "sizes": ["Various"], # eBay listings usually show various sizes in text, hard to parse reliably without deep scraping
            "image_url": f"./images/{local_img}" if local_img else "",
            "source": item.get('source', 'Unknown'),
            "source_url": item.get('source_url', ''),
            "currency": "USD",
            "last_updated": "2026-04-10"
        })
        
        if local_img:
            print(f"   📸 Saved image for: {clean_title}")
        else:
            print(f"   ⚠️ No image for: {clean_title}")
            
    return final_data

if __name__ == "__main__":
    all_items = scrape_ebay() + scrape_slickdeals()
    if not all_items:
        print("❌ No items found. Check your network connection or anti-bot settings.")
    else:
        final_data = process_data(all_items)
        with open(os.path.join(OUTPUT_DIR, 'data.json'), 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Success! Saved {len(final_data)} items with local images to data.json")