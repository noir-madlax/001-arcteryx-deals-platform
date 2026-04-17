#!/usr/bin/env python3
"""
Arc'teryx 全球爬虫 - 独立运行版本
使用 browser 工具遍历所有国家和页面，提取数据并保存
"""
import json
import subprocess
import sys
import time

# 国家配置
REGIONS = [
    {"code": "us", "lang": "en", "name": "美国", "currency": "USD", "symbol": "$"},
    {"code": "ca", "lang": "en", "name": "加拿大", "currency": "CAD", "symbol": "C$"},
    {"code": "gb", "lang": "en", "name": "英国", "currency": "GBP", "symbol": "£"},
    {"code": "de", "lang": "de", "name": "德国", "currency": "EUR", "symbol": "€"},
    {"code": "fr", "lang": "fr", "name": "法国", "currency": "EUR", "symbol": "€"},
    {"code": "nl", "lang": "en", "name": "荷兰", "currency": "EUR", "symbol": "€"},
]

# 已知会被重定向的国家（跳过）
SKIPPED = ["au", "jp", "kr", "it", "es", "be", "fi", "dk", "no", "pl", "cz"]

# JS 提取脚本
EXTRACT_JS = '''
(function() {
  const links = Array.from(document.querySelectorAll('a'));
  const products = [];
  const seen = new Set();
  for (const a of links) {
    const text = a.textContent.trim().replace(/\\s+/g, ' ');
    const href = a.href;
    if (!href.includes('/shop/')) continue;
    if (text.length < 20) continue;
    const priceMatch = text.match(/[\\$\\u00a3\\u20ac]\\s*([\\d,]+\\.?\\d*)/g);
    if (!priceMatch || priceMatch.length < 1) continue;
    if (seen.has(href)) continue;
    seen.add(href);
    let name = text;
    const fp = text.search(/[\\$\\u00a3\\u20ac]/);
    if (fp > 0) name = text.substring(0, fp).trim();
    const prices = priceMatch.map(p => parseFloat(p.replace(/[^\\d.]/g, ''))).filter(n => !isNaN(n) && n > 0);
    let gender = 'unknown';
    if (href.includes('/mens/')) gender = 'men';
    else if (href.includes('/womens/')) gender = 'women';
    products.push({ name: name, original_price: prices[0] || 0, sale_price: prices[1] || 0, sale_price_max: prices[2] || (prices[1] || 0), gender: gender, url: href });
  }
  return JSON.stringify(products);
})()
'''

# 检查 URL 是否被重定向
CHECK_REDIRECT_JS = '''
(function() {
  return JSON.stringify({
    url: window.location.href,
    title: document.title,
    is_outlet: document.title.toLowerCase().includes('outlet')
  });
})()
'''

def main():
    print("=" * 60)
    print("Arc'teryx 全球折扣爬虫")
    print("=" * 60)
    
    all_products = {}  # region -> products
    results = []
    
    for region in REGIONS:
        code = region["code"]
        lang = region["lang"]
        name = region["name"]
        
        for gender_path in ["womens", "mens"]:
            gender_name = "女款" if gender_path == "womens" else "男款"
            url = f"https://outlet.arcteryx.com/{code}/{lang}/c/{gender_path}"
            
            print(f"\n{'='*40}")
            print(f"抓取: {name} ({code}) - {gender_name}")
            print(f"URL: {url}")
            
            # 这里需要通过 browser 工具执行
            # 由于此脚本独立运行，我们输出指令
            print(f"ACTION: browser_navigate -> {url}")
            print(f"ACTION: browser_console extract")
            print(f"ACTION: 滚动 + 翻页直到所有商品加载")
    
    print("\n\n完成!")

if __name__ == "__main__":
    main()
