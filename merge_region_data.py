#!/usr/bin/env python3
"""
始祖鸟数据合并脚本
将浏览器提取的数据合并到 global_data.json
"""
import json
import os
from datetime import datetime

DATA_FILE = "global_data.json"

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def merge_products(existing, new_products):
    """合并产品，按URL去重"""
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
                    if (product.get('sale_price') != ex.get('sale_price') or
                        product.get('original_price') != ex.get('original_price')):
                        existing[i].update({
                            'sale_price': product['sale_price'],
                            'original_price': product['original_price'],
                            'discount_pct': product['discount_pct'],
                            'last_updated': product['last_updated']
                        })
                        updated_count += 1
                    break
    
    return new_count, updated_count

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 merge_region_data.py <json_file>")
        print("例如: python3 merge_region_data.py us_mens.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"文件不存在: {json_file}")
        sys.exit(1)
    
    # 加载新数据
    with open(json_file, 'r') as f:
        new_products = json.load(f)
    
    print(f"加载 {len(new_products)} 个产品从 {json_file}")
    
    # 加载现有数据
    existing = load_existing()
    print(f"现有数据: {len(existing)} 个产品")
    
    # 合并
    new_count, updated_count = merge_products(existing, new_products)
    
    # 保存
    save_data(existing)
    
    print(f"合并完成:")
    print(f"  新增: {new_count}")
    print(f"  更新: {updated_count}")
    print(f"  总计: {len(existing)}")

if __name__ == "__main__":
    main()
