import json
import requests
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
TIMEOUT = 5  # Seconds to wait for a response
MAX_WORKERS = 5  # Parallel checks

def check_url(url, type_name):
    """Check if a URL is accessible."""
    if not url or url == "#":
        return False, f"{type_name} missing"
    
    try:
        # HEAD request is faster and uses less data
        response = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        
        # Some sites block HEAD but allow GET, fallback to GET if 405 Method Not Allowed
        if response.status_code == 405:
            response = requests.get(url, timeout=TIMEOUT, stream=True)
            response.close() # Don't download content
            
        if response.status_code == 200:
            return True, "OK"
        else:
            return False, f"Status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Error: {str(e)}"

def validate_data(data):
    print(f"\n🔍 Starting Audit on {len(data)} items...")
    print("-" * 40)
    
    results = []
    
    # Check links in parallel for speed
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for idx, item in enumerate(data):
            # Check Source Link
            futures.append(executor.submit(check_url, item.get('source_url'), 'Link'))
            # Check Image Link
            futures.append(executor.submit(check_url, item.get('image_url'), 'Image'))
            
        for future in as_completed(futures):
            results.append(future.result())

    # Analyze results
    # Since results are mixed (link, image, link, image...), let's re-map to items
    valid_count = 0
    broken_count = 0
    
    for idx, item in enumerate(data):
        link_ok, link_msg = results[idx * 2]
        img_ok, img_msg = results[idx * 2 + 1]
        
        status = "✅"
        issues = []
        
        if not link_ok:
            status = "❌"
            broken_count += 1
            issues.append(f"Broken Link ({link_msg})")
        if not img_ok:
            status = "⚠️"
            if not issues: broken_count += 1 # Only count as broken item if link also broken? Or just count issues. Let's count issues.
            issues.append(f"Broken Image ({img_msg})")
            
        if not issues:
            valid_count += 1
            
        print(f"{status} [{idx+1}/{len(data)}] {item['model']}")
        for issue in issues:
            print(f"   -> {issue}")

    print("-" * 40)
    print(f"📊 Audit Report:")
    print(f"   ✅ Fully Valid: {valid_count}")
    print(f"   ❌ Issues Found: {broken_count}")
    
    return valid_count, broken_count

if __name__ == "__main__":
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        validate_data(data)
    except Exception as e:
        print(f"❌ Validation Failed: {e}")