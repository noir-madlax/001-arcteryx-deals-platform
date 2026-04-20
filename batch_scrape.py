#!/usr/bin/env python3
"""
批量抓取始祖鸟产品图片URL
使用浏览器自动化逐个访问产品页面并提取imgix图片URL
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
    
    with open(DATA_JS_FILE, 'w', encoding='utf-8') as f:
        f.write("const PRODUCTS = ")
        json.dump(products, f, ensure_ascii=False, indent=2)
        f.write(";")

def get_products_without_image(products):
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

def build_full_url(item):
    url = item['url']
    region = item['region']
    
    if '/shop/' in url and f'/{region}/' not in url:
        base = url.split('/shop/')[0]
        slug = url.split('/shop/')[-1]
        return f"{base}/{region}/en/shop/{slug}"
    return url

def main():
    print("=" * 60)
    print("始祖鸟产品图片URL批量抓取")
    print("=" * 60)
    
    products = load_data()
    needs_image = get_products_without_image(products)
    
    print(f"产品总数: {len(products)}")
    print(f"需要抓取: {len(needs_image)}")
    
    if not needs_image:
        print("所有产品都有图片URL")
        return
    
    # 输出需要抓取的产品URL列表
    print(f"\n需要抓取的产品URL:")
    for i, item in enumerate(needs_image[:20]):
        full_url = build_full_url(item)
        print(f"{i+1}. {item['model']}: {full_url}")

if __name__ == "__main__":
    main()
