#!/usr/bin/env python3
"""
Arc'teryx 全球 Outlet 增量数据采集器
支持断点续传、增量更新
"""

import json
import os
import sys
import re
from datetime import datetime

# 支持多种运行环境路径
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
# 如果文件不在当前目录，尝试用户主目录
if not os.path.exists(os.path.join(DATA_DIR, 'crawl_state.json')):
    HOME_DIR = os.path.expanduser('~')
    ALT_DIR = os.path.join(HOME_DIR, 'arcteryx-deals-platform')
    if os.path.exists(ALT_DIR):
        DATA_DIR = ALT_DIR

STATE_FILE = os.path.join(DATA_DIR, 'crawl_state.json')
DATA_FILE = os.path.join(DATA_DIR, 'global_data.json')

# 区域站点配置
REGIONS = [
    {"code": "us", "lang": "en", "name": "美国", "currency": "USD", "symbol": "$", "url_base": "https://outlet.arcteryx.com/us/en/shop"},
    {"code": "ca", "lang": "en", "name": "加拿大", "currency": "CAD", "symbol": "C$", "url_base": "https://outlet.arcteryx.com/ca/en/shop"},
    {"code": "gb", "lang": "en", "name": "英国", "currency": "GBP", "symbol": "£", "url_base": "https://outlet.arcteryx.com/gb/en/shop"},
    {"code": "au", "lang": "en", "name": "澳大利亚", "currency": "AUD", "symbol": "A$", "url_base": "https://outlet.arcteryx.com/au/en/shop"},
    {"code": "de", "lang": "de", "name": "德国", "currency": "EUR", "symbol": "€", "url_base": "https://outlet.arcteryx.com/de/de/shop"},
    {"code": "fr", "lang": "fr", "name": "法国", "currency": "EUR", "symbol": "€", "url_base": "https://outlet.arcteryx.com/fr/fr/shop"},
    {"code": "nl", "lang": "en", "name": "荷兰", "currency": "EUR", "symbol": "€", "url_base": "https://outlet.arcteryx.com/nl/en/shop"},
    {"code": "se", "lang": "en", "name": "瑞典", "currency": "SEK", "symbol": "kr", "url_base": "https://outlet.arcteryx.com/se/en/shop"},
    {"code": "at", "lang": "de", "name": "奥地利", "currency": "EUR", "symbol": "€", "url_base": "https://outlet.arcteryx.com/at/de/shop"},
    {"code": "ch", "lang": "de", "name": "瑞士", "currency": "CHF", "symbol": "CHF", "url_base": "https://outlet.arcteryx.com/ch/de/shop"},
]

# 分类路径
GENDERS = ["mens", "womens"]


def load_state():
    """加载抓取状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_run": None,
        "regions_done": [],
        "products_seen": [],  # 已抓取的商品URL列表
        "total_products": 0,
        "errors": []
    }


def save_state(state):
    """保存抓取状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_existing_data():
    """加载已有数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []


def save_data(data):
    """保存数据"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def infer_category_from_name_and_url(name, url):
    """根据产品名称和URL推断中文品类"""
    text = (name + " " + url).lower()
    
    # 按优先级判断
    if "shell" in text and ("jacket" in text or "coat" in text):
        return "硬壳冲锋衣"
    elif "alpha" in text and ("jacket" in text or "parka" in text or "anorak" in text):
        return "硬壳冲锋衣"
    elif "beta" in text and ("jacket" in text or "coat" in text):
        return "硬壳冲锋衣"
    elif "gore-tex" in text and ("jacket" in text or "coat" in text or "shell" in text):
        return "硬壳冲锋衣"
    elif "down" in text and ("jacket" in text or "coat" in text or "parka" in text or "vest" in text):
        return "保暖羽绒"
    elif "insulated" in text and ("jacket" in text or "pant" in text or "coat" in text):
        return "保暖夹克"
    elif "fleece" in text or "delta" in text:
        return "抓绒/连帽"
    elif "base" in text or "rho" in text:
        return "排汗内衣"
    elif "pant" in text or "bib" in text or "bottom" in text:
        return "裤装"
    elif "shoe" in text or "boot" in text:
        return "鞋类"
    elif "backpack" in text or "pack" in text or "bora" in text:
        return "背包"
    elif "veilance" in text or "blazer" in text:
        return "Veilance商务"
    elif "dress" in text or "skirt" in text:
        return "裙装"
    elif "one-piece" in text or "jumpsuit" in text:
        return "连体服"
    elif "tank" in text or "shirt" in text or "top" in text or "tee" in text:
        return "上衣/T恤"
    elif "glove" in text or "hat" in text or "beanie" in text or "accessories" in text:
        return "配件"
    elif "hoody" in text or "hoodie" in text:
        return "连帽衫"
    elif "anorak" in text:
        return "套头外套"
    else:
        return "其他"


def extract_product_from_name(name_str):
    """从产品名称中提取信息"""
    # 去掉价格部分（$xxx.xx）
    clean = re.sub(r"\s*\$[\d,]+\.?\d*", "", name_str).strip()
    # 去掉 Men's / Women's 后缀
    clean = re.sub(r"\s*(Men's|Women's)\s*$", "", clean).strip()
    # 去掉多余的标点
    clean = clean.rstrip('.,')
    # 提取核心型号名（前两个单词通常是品牌和型号）
    model_match = re.match(r"([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-zA-Z]+)*)", clean)
    model = model_match.group(1) if model_match else clean
    return {
        "full_name": name_str,
        "clean_name": clean,
        "model": model,
    }


def calculate_discount(original, sale):
    """计算折扣百分比"""
    if original <= 0 or sale <= 0:
        return 0
    return round((1 - sale / original) * 100)


def main():
    """
    主函数：从标准输入读取浏览器提取的JSON数据
    增量更新到全局数据文件
    """
    # 读取从 stdin 传入的浏览器数据
    try:
        new_products = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        sys.exit(1)

    state = load_state()
    existing_data = load_existing_data()
    
    # 构建已有商品的URL集合
    existing_urls = set(p.get('url', '') for p in existing_data)
    products_seen = set(state.get('products_seen', []))

    new_count = 0
    updated_count = 0
    
    for p in new_products:
        url = p.get('url', '')
        if not url:
            continue
        
        # 检查是否是新商品
        is_new = url not in existing_urls and url not in products_seen
        
        # 提取产品信息
        name_info = extract_product_from_name(p.get('name', ''))
        category = infer_category_from_name_and_url(p.get('name', ''), url)
        
        # 确定区域和货币
        region_code = p.get('region', 'us')
        region_info = next((r for r in REGIONS if r['code'] == region_code), REGIONS[0])
        
        product = {
            "model": name_info['clean_name'],
            "full_name": name_info['full_name'],
            "description": p.get('description', ''),
            "category": category,
            "original_price": p.get('originalPrice', 0),
            "sale_price": p.get('salePrice', 0),
            "sale_price_max": p.get('salePriceMax', 0),
            "discount_pct": calculate_discount(p.get('originalPrice', 0), p.get('salePrice', 0)),
            "currency": region_info['currency'],
            "symbol": region_info['symbol'],
            "gender": p.get('gender', 'unknown'),
            "region": region_code,
            "region_name": region_info['name'],
            "url": url,
            "image_url": "",  # 需要后续抓取
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        if is_new:
            existing_data.append(product)
            products_seen.add(url)
            new_count += 1
        else:
            # 更新已有商品的价格
            for i, existing in enumerate(existing_data):
                if existing.get('url') == url:
                    existing['sale_price'] = product['sale_price']
                    existing['sale_price_max'] = product['sale_price_max']
                    existing['original_price'] = product['original_price']
                    existing['discount_pct'] = product['discount_pct']
                    existing['last_updated'] = product['last_updated']
                    updated_count += 1
                    break

    # 更新状态
    state['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    state['products_seen'] = list(products_seen)
    state['total_products'] = len(existing_data)
    state['new_this_run'] = new_count
    state['updated_this_run'] = updated_count

    save_state(state)
    save_data(existing_data)

    print(f"✅ 增量更新完成: 新增 {new_count} 款, 更新 {updated_count} 款")
    print(f"📊 总计: {len(existing_data)} 款商品")
    print(f"📁 数据文件: {DATA_FILE}")
    print(f"💾 状态文件: {STATE_FILE}")


if __name__ == "__main__":
    main()
