#!/usr/bin/env python3
"""
始祖鸟全站数据批量爬取脚本
使用浏览器逐个国家爬取数据
"""
import json
import os
from datetime import datetime

DATA_FILE = "global_data.json"

# 需要爬取的国家
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
]

CATEGORIES = ["mens", "womens"]

def load_existing_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def merge_product(existing, new_product):
    """合并产品，返回是否新增"""
    for item in existing:
        if item.get('url') == new_product.get('url'):
            # 更新价格
            item['sale_price'] = new_product['sale_price']
            item['original_price'] = new_product['original_price']
            item['discount_pct'] = new_product['discount_pct']
            item['last_updated'] = new_product['last_updated']
            return False
    existing.append(new_product)
    return True

def main():
    print("始祖鸟全站数据爬取")
    print("=" * 50)
    
    # 加载现有数据
    existing = load_existing_data()
    print(f"现有数据: {len(existing)} 个产品")
    
    # 输出爬取指令
    print("\n请在浏览器中执行以下操作：")
    print("1. 访问 https://outlet.arcteryx.com/{region}/{lang}/shop/{category}")
    print("2. 滚动到页面底部加载所有产品")
    print("3. 打开浏览器控制台(F12)，执行以下代码：")
    print()
    
    extract_code = '''
// 提取产品数据
const products = [];
document.querySelectorAll('a').forEach(link => {
  const text = link.textContent || '';
  const href = link.href || '';
  if ((href.includes('/shop/mens/') || href.includes('/shop/womens/')) && text.includes('$')) {
    const prices = text.match(/\\$(\\d+\\.\\d{2})/g);
    if (prices && prices.length >= 2) {
      const img = link.querySelector('img') || link.parentElement.querySelector('img');
      products.push({
        url: href,
        name: text.match(/^(.*?(?:Men's|Women's))/)?.[1] || text.split('$')[0].trim(),
        original_price: Math.max(...prices.map(p => parseFloat(p.replace('$','')))),
        sale_price: Math.min(...prices.map(p => parseFloat(p.replace('$','')))),
        image_url: img?.src || ''
      });
    }
  }
});
console.log(JSON.stringify(products));
'''
    
    print(extract_code)
    print()
    print("4. 将输出的JSON数据保存到对应文件，如：us_mens.json")
    print("5. 然后运行: python3 merge_region_data.py <文件名>")

if __name__ == "__main__":
    main()
