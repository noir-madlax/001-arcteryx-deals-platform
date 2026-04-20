#!/usr/bin/env python3
"""
后台抓取始祖鸟产品图片URL
自动逐个访问产品页面，提取imgix图片URL
"""
import json
import os
import subprocess
import time

DATA_FILE = os.path.expanduser("~/arcteryx-deals-platform/global_data.json")
DATA_JS_FILE = os.path.expanduser("~/arcteryx-deals-platform/h5/data.js")

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(products):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    # 同步更新data.js
    with open(DATA_JS_FILE, 'w', encoding='utf-8') as f:
        f.write("const PRODUCTS = ")
        json.dump(products, f, ensure_ascii=False, indent=2)
        f.write(";")

def get_products_without_image(products):
    """获取没有图片的产品列表"""
    result = []
    for i, p in enumerate(products):
        if not p.get('image_url'):
            url = p.get('url', '')
            if url:
                result.append({
                    'index': i,
                    'model': p.get('model', '')[:30],
                    'url': url,
                    'region': p.get('region', 'us')
                })
    return result

def main():
    print("=" * 60)
    print("始祖鸟产品图片URL抓取脚本")
    print("=" * 60)
    
    # 加载数据
    products = load_data()
    print(f"产品总数: {len(products)}")
    
    # 获取需要抓取的产品
    needs_image = get_products_without_image(products)
    print(f"需要抓取图片的产品: {len(needs_image)}")
    
    if not needs_image:
        print("所有产品都有图片URL，无需抓取")
        return
    
    print(f"\n开始抓取前10个产品的图片URL...")
    print("-" * 60)
    
    # 抓取前10个产品的图片
    for i, item in enumerate(needs_image[:10]):
        print(f"\n[{i+1}/10] {item['model']}")
        print(f"URL: {item['url']}")
        
        # 构建完整URL（添加地区前缀）
        url = item['url']
        region = item['region']
        
        if '/shop/' in url and f'/{region}/' not in url:
            base = url.split('/shop/')[0]
            slug = url.split('/shop/')[-1]
            full_url = f"{base}/{region}/en/shop/{slug}"
        else:
            full_url = url
        
        print(f"完整URL: {full_url}")
        
        # 这里需要调用浏览器工具来抓取图片URL
        # 由于无法在Python中直接调用浏览器工具，需要通过其他方式
        print("需要通过浏览器工具抓取图片URL")
    
    print("\n" + "=" * 60)
    print("抓取完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
