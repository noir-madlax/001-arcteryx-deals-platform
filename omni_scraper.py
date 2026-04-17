#!/usr/bin/env python3
"""
Arc'teryx 全球官网折扣爬虫
每天自动抓取各国家 Outlet 站的折扣商品
支持多国数据、增量更新、价格变动追踪
"""

import json
import os
import re
from datetime import datetime
from collections import Counter

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'global_data.json')) else os.path.expanduser('~/arcteryx-deals-platform')
DATA_FILE = os.path.join(DATA_DIR, 'global_data.json')
STATE_FILE = os.path.join(DATA_DIR, 'crawl_state.json')

# 国家站点配置
# 根据实测：US, CA, GB 可直接访问；DE, JP 等可能被重定向
REGIONS = [
    {"code": "us", "lang": "en", "name": "美国", "currency": "USD", "symbol": "$", "category": "us"},
    {"code": "ca", "lang": "en", "name": "加拿大", "currency": "CAD", "symbol": "C$", "category": "ca"},
    {"code": "gb", "lang": "en", "name": "英国", "currency": "GBP", "symbol": "£", "category": "gb"},
    {"code": "de", "lang": "de", "name": "德国", "currency": "EUR", "symbol": "€", "category": "de"},
    {"code": "fr", "lang": "fr", "name": "法国", "currency": "EUR", "symbol": "€", "category": "fr"},
    {"code": "nl", "lang": "en", "name": "荷兰", "currency": "EUR", "symbol": "€", "category": "nl"},
    {"code": "se", "lang": "en", "name": "瑞典", "currency": "SEK", "symbol": "kr", "category": "se"},
    {"code": "at", "lang": "de", "name": "奥地利", "currency": "EUR", "symbol": "€", "category": "at"},
    {"code": "ch", "lang": "de", "name": "瑞士", "currency": "CHF", "symbol": "CHF", "category": "ch"},
    {"code": "au", "lang": "en", "name": "澳大利亚", "currency": "AUD", "symbol": "A$", "category": "au"},
    {"code": "jp", "lang": "ja", "name": "日本", "currency": "JPY", "symbol": "¥", "category": "jp"},
    {"code": "kr", "lang": "ko", "name": "韩国", "currency": "KRW", "symbol": "₩", "category": "kr"},
    {"code": "it", "lang": "it", "name": "意大利", "currency": "EUR", "symbol": "€", "category": "it"},
    {"code": "es", "lang": "es", "name": "西班牙", "currency": "EUR", "symbol": "€", "category": "es"},
    {"code": "be", "lang": "nl", "name": "比利时", "currency": "EUR", "symbol": "€", "category": "be"},
    {"code": "fi", "lang": "en", "name": "芬兰", "currency": "EUR", "symbol": "€", "category": "fi"},
    {"code": "dk", "lang": "en", "name": "丹麦", "currency": "DKK", "symbol": "kr", "category": "dk"},
    {"code": "no", "lang": "en", "name": "挪威", "currency": "NOK", "symbol": "kr", "category": "no"},
    {"code": "pl", "lang": "en", "name": "波兰", "currency": "PLN", "symbol": "zł", "category": "pl"},
    {"code": "cz", "lang": "en", "name": "捷克", "currency": "CZK", "symbol": "Kč", "category": "cz"},
]

# 分类
GENDERS = ["mens", "womens"]

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


def calculate_discount(original, sale):
    if original <= 0 or sale <= 0:
        return 0
    return round((1 - sale / original) * 100)


def extract_product_from_text(text):
    """从产品文本中提取名称和价格"""
    # 匹配价格: $xxx.xx, £xxx.xx, €xxx.xx, xxx.xx kr, etc.
    price_patterns = [
        r'[\$£€]\s*([\d,]+\.?\d*)',
        r'([\d,]+\.?\d*)\s*kr',
        r'₩\s*([\d,]+)',
        r'¥\s*([\d,]+)',
    ]
    
    prices = []
    for pattern in price_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            try:
                prices.append(float(m.replace(',', '')))
            except ValueError:
                pass
    
    # 提取产品名称（价格之前的内容）
    # 格式通常是: "Product Name Description $original $sale"
    name_match = re.match(r'^(.*?)\s+[\$£€¥₩]|^(.*?)\s+[\d,]+\.?\d*\s*kr', text)
    if name_match:
        name = (name_match.group(1) or name_match.group(2)).strip()
    else:
        name = text.split('$')[0].split('£')[0].split('€')[0].strip()
    
    # 提取性别
    gender = 'unknown'
    if "men's" in text.lower():
        gender = 'men'
    elif "women's" in text.lower():
        gender = 'women'
    
    return {
        "name": name,
        "prices": prices[:3],  # 最多3个价格
        "gender": gender
    }


def merge_products(existing, new_products, region_info):
    """增量合并新产品"""
    existing_urls = {p.get('url', '') for p in existing}
    new_count = 0
    updated_count = 0
    skipped_count = 0
    
    for p in new_products:
        url = p.get('url', '')
        if not url:
            continue
        
        category = infer_category(p.get('name', ''), url)
        original_price = p.get('original_price', 0)
        sale_price = p.get('sale_price', 0)
        discount_pct = calculate_discount(original_price, sale_price)
        
        product = {
            "model": p.get('model', p.get('name', '')),
            "full_name": p.get('name', ''),
            "description": p.get('description', ''),
            "category": category,
            "original_price": original_price,
            "sale_price": sale_price,
            "sale_price_max": p.get('sale_price_max', sale_price),
            "discount_pct": discount_pct,
            "currency": region_info['currency'],
            "symbol": region_info['symbol'],
            "gender": p.get('gender', 'unknown'),
            "region": region_info['code'],
            "region_name": region_info['name'],
            "url": url,
            "image_url": p.get('image_url', ''),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        if url not in existing_urls:
            existing.append(product)
            existing_urls.add(url)
            new_count += 1
        else:
            # 更新已有商品
            for i, ex in enumerate(existing):
                if ex.get('url') == url:
                    if (ex.get('sale_price') != sale_price or 
                        ex.get('original_price') != original_price):
                        existing[i]['sale_price'] = sale_price
                        existing[i]['sale_price_max'] = product['sale_price_max']
                        existing[i]['original_price'] = original_price
                        existing[i]['discount_pct'] = discount_pct
                        existing[i]['last_updated'] = product['last_updated']
                        existing[i]['region'] = region_info['code']
                        existing[i]['region_name'] = region_info['name']
                        existing[i]['currency'] = region_info['currency']
                        existing[i]['symbol'] = region_info['symbol']
                        updated_count += 1
                    else:
                        skipped_count += 1
                    break
    
    return new_count, updated_count, skipped_count


def main():
    """
    主函数: 从 stdin 读取浏览器提取的 JSON 数据
    格式: {"region": "us", "products": [...]}
    """
    import sys
    
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        sys.exit(1)
    
    region_code = data.get('region', 'us')
    products = data.get('products', [])
    
    if not products:
        print(f"⚠️ {region_code.upper()} 无产品数据")
        sys.exit(0)
    
    region_info = next((r for r in REGIONS if r['code'] == region_code), REGIONS[0])
    
    # 加载现有数据
    existing = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            existing = json.load(f)
    
    # 合并
    new_count, updated_count, skipped_count = merge_products(existing, products, region_info)
    
    # 保存
    with open(DATA_FILE, 'w') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    
    # 更新状态
    state = {
        "last_run": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "last_region": region_code,
        "new_this_run": new_count,
        "updated_this_run": updated_count,
        "skipped_this_run": skipped_count,
        "total_products": len(existing),
        "products_per_region": dict(Counter(p.get('region', 'unknown') for p in existing))
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {region_info['name']}({region_code.upper()}) 完成: 新增 {new_count}, 更新 {updated_count}, 跳过 {skipped_count}")
    print(f"📊 总计: {len(existing)} 款商品")


if __name__ == "__main__":
    main()
