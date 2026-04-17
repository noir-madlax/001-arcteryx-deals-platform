#!/usr/bin/env python3
"""
更新美国数据 - 删除下架商品，更新价格
"""
import json
import os
from datetime import datetime

DATA_FILE = "global_data.json"
REGION = "us"

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_region_data(existing, new_products, region, gender):
    """
    更新指定地区和性别的数据
    - 删除不在新产品列表中的商品（下架/售罄）
    - 更新价格变化
    - 添加新产品
    """
    # 构建新产品URL集合
    new_urls = {p['url'] for p in new_products}
    
    # 过滤掉该地区该性别的旧产品
    filtered = []
    removed = 0
    for p in existing:
        if p.get('region') == region and p.get('gender') == gender:
            if p['url'] not in new_urls:
                removed += 1
                continue  # 删除下架商品
        filtered.append(p)
    
    # 添加/更新新产品
    existing_urls = {p['url'] for p in filtered}
    added = 0
    updated = 0
    
    for product in new_products:
        if product['url'] not in existing_urls:
            filtered.append(product)
            added += 1
        else:
            # 更新已有产品
            for i, p in enumerate(filtered):
                if p['url'] == product['url']:
                    if (p.get('sale_price') != product.get('sale_price') or
                        p.get('original_price') != product.get('original_price')):
                        filtered[i].update({
                            'sale_price': product['sale_price'],
                            'original_price': product['original_price'],
                            'discount_pct': product['discount_pct'],
                            'last_updated': product['last_updated']
                        })
                        updated += 1
                    break
    
    return filtered, added, updated, removed

def main():
    print("=" * 50)
    print("更新美国数据")
    print("=" * 50)
    
    # 读取浏览器提取的男款数据（从之前的结果）
    # 这里需要手动粘贴或从文件读取
    us_mens_file = "us_mens_data.json"
    
    if os.path.exists(us_mens_file):
        with open(us_mens_file, 'r') as f:
            new_mens = json.load(f)
        
        print(f"加载 {len(new_mens)} 个美国男款产品")
        
        # 加载现有数据
        existing = load_data()
        old_count = len(existing)
        
        # 更新男款数据
        existing, added, updated, removed = update_region_data(
            existing, new_mens, REGION, 'men'
        )
        
        # 保存
        save_data(existing)
        
        print(f"\n更新结果:")
        print(f"  新增: {added}")
        print(f"  更新: {updated}")
        print(f"  删除(下架): {removed}")
        print(f"  总计: {len(existing)}")
    else:
        print(f"未找到 {us_mens_file}")
        print("请先从浏览器提取数据并保存到该文件")

if __name__ == "__main__":
    main()
