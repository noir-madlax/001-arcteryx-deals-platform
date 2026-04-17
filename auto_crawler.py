#!/usr/bin/env python3
"""
始祖鸟全站数据爬虫 - 自动化版本
支持所有国家，自动爬取并合并数据
"""
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from collections import Counter

DATA_FILE = "global_data.json"
STATE_FILE = "crawl_state.json"

# 所有支持的国家
REGIONS = [
    {"code": "us", "lang": "en", "name": "美国", "currency": "USD", "symbol": "$"},
    {"code": "ca", "lang": "en", "name": "加拿大", "currency": "CAD", "symbol": "C$"},
    {"code": "gb", "lang": "en", "name": "英国", "currency": "GBP", "symbol": "£"},
    {"code": "de", "lang": "de", "name": "德国", "currency": "EUR", "symbol": "€"},
    {"code": "fr", "lang": "fr", "name": "法国", "currency": "EUR", "symbol": "€"},
    {"code": "nl", "lang": "en", "name": "荷兰", "currency": "EUR", "symbol": "€"},
    {"code": "se", "lang": "en", "name": "瑞典", "currency": "SEK", "symbol": "kr"},
    {"code": "at", "lang": "de", "name": "奥地利", "currency": "EUR", "symbol": "€"},
    {"code": "ch", "lang": "de", "name": "瑞士", "currency": "CHF", "symbol": "CHF"},
    {"code": "au", "lang": "en", "name": "澳大利亚", "currency": "AUD", "symbol": "A$"},
    {"code": "jp", "lang": "ja", "name": "日本", "currency": "JPY", "symbol": "¥"},
    {"code": "kr", "lang": "ko", "name": "韩国", "currency": "KRW", "symbol": "₩"},
    {"code": "it", "lang": "it", "name": "意大利", "currency": "EUR", "symbol": "€"},
    {"code": "es", "lang": "es", "name": "西班牙", "currency": "EUR", "symbol": "€"},
    {"code": "be", "lang": "nl", "name": "比利时", "currency": "EUR", "symbol": "€"},
    {"code": "fi", "lang": "en", "name": "芬兰", "currency": "EUR", "symbol": "€"},
    {"code": "dk", "lang": "en", "name": "丹麦", "currency": "DKK", "symbol": "kr"},
    {"code": "no", "lang": "en", "name": "挪威", "currency": "NOK", "symbol": "kr"},
    {"code": "pl", "lang": "en", "name": "波兰", "currency": "PLN", "symbol": "zł"},
    {"code": "cz", "lang": "en", "name": "捷克", "currency": "CZK", "symbol": "Kč"},
]

CATEGORIES = ["mens", "womens"]

# 品类推断
def infer_category(name, url):
    text = (name + " " + url).lower()
    if any(k in text for k in ["shell", "alpha", "beta", "gore-tex"]) and any(k in text for k in ["jacket", "coat", "anorak"]):
        return "硬壳冲锋衣"
    elif any(k in text for k in ["down", "insulated"]) and any(k in text for k in ["jacket", "coat", "parka", "vest", "pant"]):
        return "保暖羽绒"
    elif "fleece" in text or "delta" in text or "covert" in text:
        return "抓绒/连帽"
    elif "base" in text or "rho " in text or "rho-" in text:
        return "排汗内衣"
    elif any(k in text for k in ["pant", "bib", "bottom"]):
        return "裤装"
    elif any(k in text for k in ["shoe", "boot"]):
        return "鞋类"
    elif any(k in text for k in ["backpack", "pack", "bora"]):
        return "背包"
    elif "veilance" in text:
        return "Veilance商务"
    elif any(k in text for k in ["dress", "skirt"]):
        return "裙装"
    elif any(k in text for k in ["tank", "shirt", "top", "tee"]):
        return "上衣/T恤"
    elif any(k in text for k in ["glove", "hat", "beanie", "accessories", "cap"]):
        return "配件"
    elif any(k in text for k in ["hoody", "hoodie"]):
        return "连帽衫"
    elif "anorak" in text:
        return "套头外套"
    else:
        return "其他"

def infer_gender(category, url):
    if "womens" in url or "women" in url:
        return "women"
    elif "mens" in url or "men" in url:
        return "men"
    return "unisex"

def fetch_page(url, timeout=15):
    """获取页面内容"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  获取失败: {e}")
        return None

def extract_products_from_html(html, region_info, category):
    """从HTML中提取产品数据"""
    products = []
    
    # 匹配产品链接和信息
    # 格式类似: <a href="/shop/mens/xxx">Product Name ... $price</a>
    pattern = r'<a[^>]*href="([^"]*(?:/shop/[^"]+))"[^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    for url_path, content in matches:
        # 过滤产品链接
        if '/shop/' not in url_path:
            continue
        if len(content) < 20:
            continue
            
        # 提取价格
        price_patterns = [
            r'[\$£€]\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*kr',
            r'₩\s*([\d,]+)',
            r'¥\s*([\d,]+)',
        ]
        
        prices = []
        for pattern in price_patterns:
            found = re.findall(pattern, content)
            for p in found:
                try:
                    prices.append(float(p.replace(',', '')))
                except:
                    pass
        
        if len(prices) < 2:
            continue
        
        # 提取产品名称
        name_match = re.match(r'^(.*?)\s*[\$£€¥₩\d]', content.strip())
        name = name_match.group(1).strip() if name_match else content[:50].strip()
        
        # 清理名称
        name = re.sub(r'\s+', ' ', name)
        name = name.replace('\n', ' ').strip()
        
        if len(name) < 5:
            continue
        
        # 构建完整URL
        if url_path.startswith('/'):
            full_url = f"https://outlet.arcteryx.com{url_path}"
        elif url_path.startswith('http'):
            full_url = url_path
        else:
            continue
        
        # 提取图片
        img_match = re.search(r'<img[^>]*src="([^"]+)"', content)
        image_url = img_match.group(1) if img_match else ""
        
        # 价格处理
        original_price = max(prices) if prices else 0
        sale_price = min(prices) if prices else 0
        
        product = {
            "model": name.split("'")[0] if "'" in name else name,
            "full_name": name,
            "description": "",
            "category": infer_category(name, full_url),
            "original_price": original_price,
            "sale_price": sale_price,
            "sale_price_max": sale_price,
            "discount_pct": round((1 - sale_price / original_price) * 100) if original_price > 0 else 0,
            "currency": region_info["currency"],
            "symbol": region_info["symbol"],
            "gender": infer_gender(category, full_url),
            "region": region_info["code"],
            "region_name": region_info["name"],
            "url": full_url,
            "image_url": image_url,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        products.append(product)
    
    return products

def crawl_region(region_info):
    """爬取单个国家的数据"""
    all_products = []
    
    for category in CATEGORIES:
        url = f"https://outlet.arcteryx.com/{region_info['code']}/{region_info['lang']}/shop/{category}"
        print(f"  爬取 {category}: {url}")
        
        html = fetch_page(url)
        if html:
            products = extract_products_from_html(html, region_info, category)
            print(f"    找到 {len(products)} 个产品")
            all_products.extend(products)
        else:
            print(f"    获取失败")
        
        time.sleep(1)  # 避免请求太快
    
    return all_products

def merge_products(existing, new_products):
    """合并产品数据"""
    existing_urls = {p.get('url', '') for p in existing}
    new_count = 0
    updated_count = 0
    
    for product in new_products:
        url = product.get('url', '')
        if not url:
            continue
        
        if url not in existing_urls:
            existing.append(product)
            existing_urls.add(url)
            new_count += 1
        else:
            # 更新已有产品
            for i, ex in enumerate(existing):
                if ex.get('url') == url:
                    # 更新价格信息
                    if product.get('sale_price') != ex.get('sale_price'):
                        existing[i]['sale_price'] = product['sale_price']
                        existing[i]['original_price'] = product['original_price']
                        existing[i]['discount_pct'] = product['discount_pct']
                        existing[i]['last_updated'] = product['last_updated']
                        updated_count += 1
                    break
    
    return new_count, updated_count

def main():
    print("=" * 60)
    print("始祖鸟全站数据爬虫")
    print("=" * 60)
    
    # 加载现有数据
    existing = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            existing = json.load(f)
    
    print(f"现有数据: {len(existing)} 个产品")
    
    # 按地区统计
    regions_count = Counter(p.get('region', 'unknown') for p in existing)
    print("现有地区分布:")
    for region, count in sorted(regions_count.items()):
        print(f"  {region}: {count}")
    
    print("\n开始爬取...")
    print("-" * 60)
    
    total_new = 0
    total_updated = 0
    
    for region_info in REGIONS:
        region_code = region_info['code']
        print(f"\n[{region_code.upper()}] {region_info['name']}")
        
        # 爬取数据
        products = crawl_region(region_info)
        
        if products:
            # 合并数据
            new_count, updated_count = merge_products(existing, products)
            total_new += new_count
            total_updated += updated_count
            print(f"  合并完成: 新增 {new_count}, 更新 {updated_count}")
        else:
            print(f"  无数据")
        
        # 每爬完一个地区保存一次
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    # 更新状态
    state = {
        "last_run": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_products": len(existing),
        "new_this_run": total_new,
        "updated_this_run": total_updated,
        "products_per_region": dict(Counter(p.get('region', 'unknown') for p in existing))
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"爬取完成!")
    print(f"总产品数: {len(existing)}")
    print(f"新增: {total_new}")
    print(f"更新: {total_updated}")
    print("=" * 60)

if __name__ == "__main__":
    main()
