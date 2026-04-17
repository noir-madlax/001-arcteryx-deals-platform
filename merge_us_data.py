#!/usr/bin/env python3
"""
合并美国数据到 global_data.json
- 删除旧的美国数据
- 添加新的男款81个 + 女款91个
"""
import json
import os
from datetime import datetime

DATA_FILE = "global_data.json"
REGION = "us"
REGION_NAME = "美国"
CURRENCY = "USD"
SYMBOL = "$"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_product(raw, gender):
    """格式化产品数据"""
    return {
        "model": raw['name'].split("'")[0],
        "full_name": raw['name'],
        "description": "",
        "category": "其他",
        "original_price": raw['original_price'],
        "sale_price": raw['sale_price'],
        "sale_price_max": raw['sale_price'],
        "discount_pct": round((1 - raw['sale_price'] / raw['original_price']) * 100),
        "currency": CURRENCY,
        "symbol": SYMBOL,
        "gender": gender,
        "region": REGION,
        "region_name": REGION_NAME,
        "url": raw['url'],
        "image_url": raw.get('image_url', ''),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

def main():
    print("=" * 50)
    print("合并美国数据")
    print("=" * 50)
    
    # 加载现有数据
    existing = load_data()
    old_count = len(existing)
    print(f"现有数据: {old_count} 个产品")
    
    # 统计旧的美国数据
    old_us = [p for p in existing if p.get('region') == REGION]
    print(f"旧的美国数据: {len(old_us)} 个")
    
    # 删除旧的美国数据
    non_us = [p for p in existing if p.get('region') != REGION]
    print(f"删除 {len(old_us)} 个旧的美国数据")
    
    # 读取新数据（需要从浏览器复制）
    # 这里假设数据已经保存到文件
    new_products = []
    
    # 如果有男款数据文件
    if os.path.exists("us_mens_data.json"):
        with open("us_mens_data.json", 'r') as f:
            mens_data = json.load(f)
            for item in mens_data:
                new_products.append(format_product(item, 'men'))
        print(f"加载男款: {len(mens_data)} 个")
    
    # 如果有女款数据文件
    if os.path.exists("us_womens_data.json"):
        with open("us_womens_data.json", 'r') as f:
            womens_data = json.load(f)
            for item in womens_data:
                new_products.append(format_product(item, 'women'))
        print(f"加载女款: {len(womens_data)} 个")
    
    # 合并
    final_data = non_us + new_products
    
    # 保存
    save_data(final_data)
    
    print(f"\n合并完成:")
    print(f"  非美国数据: {len(non_us)}")
    print(f"  新美国数据: {len(new_products)}")
    print(f"  总计: {len(final_data)}")

if __name__ == "__main__":
    main()
