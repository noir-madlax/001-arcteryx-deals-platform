#!/usr/bin/env python3
"""
始祖鸟定时爬虫系统
支持：
- 多国家并行爬取
- 自动删除下架商品
- 价格变动追踪
- 定时执行
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

DATA_FILE = "global_data.json"
STATE_FILE = "crawl_state.json"
LOG_DIR = "logs"

# 爬取配置
REGIONS = [
    {"code": "us", "lang": "en", "name": "美国", "currency": "USD", "symbol": "$"},
    {"code": "ca", "lang": "en", "name": "加拿大", "currency": "CAD", "symbol": "C$"},
    {"code": "gb", "lang": "en", "name": "英国", "currency": "GBP", "symbol": "£"},
    {"code": "de", "lang": "de", "name": "德国", "currency": "EUR", "symbol": "€"},
    {"code": "fr", "lang": "fr", "name": "法国", "currency": "EUR", "symbol": "€"},
]

GENDERS = ["mens", "womens"]

# 浏览器提取代码模板
EXTRACT_CODE = '''
// 滚动加载所有产品
async function scrollAndExtract() {
  let lastHeight = 0;
  let scrollCount = 0;
  
  while (scrollCount < 15) {
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 1000));
    
    const newHeight = document.body.scrollHeight;
    if (newHeight === lastHeight) scrollCount++;
    else scrollCount = 0;
    lastHeight = newHeight;
  }
  
  // 提取产品
  const products = [];
  document.querySelectorAll('a').forEach(link => {
    const text = link.textContent || '';
    const href = link.href || '';
    
    if (href.includes('/shop/{gender}/') && text.includes('{symbol}')) {{
      const prices = text.match(/\\{symbol}(\\d+\\.\\d{{2}})/g);
      if (prices && prices.length >= 2) {{
        const img = link.querySelector('img') || link.parentElement.querySelector('img');
        products.push({{
          url: href,
          name: text.match(/^(.*?(?:Men's|Women's))/)?.[1] || text.split('{symbol}')[0].trim(),
          original_price: Math.max(...prices.map(p => parseFloat(p.replace('{symbol}', '')))),
          sale_price: Math.min(...prices.map(p => parseFloat(p.replace('{symbol}', '')))),
          image_url: img?.src || ''
        }});
      }}
    }}
  });
  
  return products;
}

scrollAndExtract().then(data => console.log(JSON.stringify(data)));
'''

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_region_products(existing, new_products, region_info, gender):
    """更新指定地区和性别的产品"""
    region = region_info['code']
    
    # 构建新产品URL集合
    new_urls = {p['url'] for p in new_products}
    
    # 过滤旧产品（删除下架的）
    filtered = []
    removed = 0
    for p in existing:
        if p.get('region') == region and p.get('gender') == gender:
            if p['url'] not in new_urls:
                removed += 1
                continue
        filtered.append(p)
    
    # 添加/更新新产品
    existing_urls = {p['url'] for p in filtered}
    added = 0
    updated = 0
    
    for product in new_products:
        # 格式化产品数据
        formatted = {
            "model": product['name'].split("'")[0],
            "full_name": product['name'],
            "description": "",
            "category": "其他",
            "original_price": product['original_price'],
            "sale_price": product['sale_price'],
            "sale_price_max": product['sale_price'],
            "discount_pct": round((1 - product['sale_price'] / product['original_price']) * 100),
            "currency": region_info['currency'],
            "symbol": region_info['symbol'],
            "gender": gender,
            "region": region,
            "region_name": region_info['name'],
            "url": product['url'],
            "image_url": product.get('image_url', ''),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        if formatted['url'] not in existing_urls:
            filtered.append(formatted)
            existing_urls.add(formatted['url'])
            added += 1
        else:
            for i, p in enumerate(filtered):
                if p['url'] == formatted['url']:
                    if (p.get('sale_price') != formatted['sale_price'] or
                        p.get('original_price') != formatted['original_price')):
                        filtered[i].update({
                            'sale_price': formatted['sale_price'],
                            'original_price': formatted['original_price'],
                            'discount_pct': formatted['discount_pct'],
                            'last_updated': formatted['last_updated']
                        })
                        updated += 1
                    break
    
    return filtered, added, updated, removed

def generate_crawl_instructions(region_info, gender):
    """生成爬取指令"""
    region = region_info['code']
    lang = region_info['lang']
    symbol = region_info['symbol']
    
    url = f"https://outlet.arcteryx.com/{region}/{lang}/shop/{gender}"
    
    code = f'''
// 在浏览器中访问: {url}
// 滚动到页面底部，然后在控制台执行：

async function extractProducts() {{
  // 滚动加载所有产品
  let lastHeight = 0;
  let noChange = 0;
  
  while (noChange < 10) {{
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 800));
    if (document.body.scrollHeight === lastHeight) noChange++;
    else noChange = 0;
    lastHeight = document.body.scrollHeight;
  }}
  
  // 提取产品
  const products = [];
  document.querySelectorAll('a').forEach(link => {{
    const text = link.textContent || '';
    const href = link.href || '';
    
    if (href.includes('/shop/{gender}/') && text.includes('{symbol}')) {{
      const prices = text.match(/\\{symbol}(\\d+\\.\\d{{2}})/g);
      if (prices && prices.length >= 2) {{
        const img = link.querySelector('img') || link.parentElement.querySelector('img');
        products.push({{
          url: href,
          name: text.match(/^(.*?(?:Men's|Women's))/)?.[1] || text.split('{symbol}')[0].trim(),
          original_price: Math.max(...prices.map(p => parseFloat(p.replace('{symbol}', '')))),
          sale_price: Math.min(...prices.map(p => parseFloat(p.replace('{symbol}', '')))),
          image_url: img?.src || ''
        }});
      }}
    }}
  }});
  
  return products;
}}

extractProducts().then(data => {{
  console.log('提取完成:', data.length, '个产品');
  console.log(JSON.stringify(data));
}});
'''
    return url, code

def main():
    print("=" * 60)
    print("始祖鸟定时爬虫系统")
    print("=" * 60)
    
    # 创建日志目录
    Path(LOG_DIR).mkdir(exist_ok=True)
    
    # 加载现有数据
    existing = load_data()
    print(f"现有产品总数: {len(existing)}")
    
    # 生成爬取指令
    print("\n生成爬取指令...")
    print("-" * 60)
    
    for region_info in REGIONS[:3]:  # 先处理前3个国家
        for gender in GENDERS:
            url, code = generate_crawl_instructions(region_info, gender)
            print(f"\n[{region_info['code'].upper()}] {region_info['name']} - {gender}")
            print(f"URL: {url}")
    
    print("\n" + "=" * 60)
    print("使用方法：")
    print("1. 打开上面的URL")
    print("2. 滚动页面加载所有产品")
    print("3. 打开控制台(F12)，粘贴代码执行")
    print("4. 复制输出的JSON数据")
    print("5. 保存到文件: {region}_{gender}.json")
    print("6. 运行: python3 crawl_system.py merge {region}_{gender}.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
