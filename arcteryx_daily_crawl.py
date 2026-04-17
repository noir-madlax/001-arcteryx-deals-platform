#!/usr/bin/env python3
"""
始祖鸟定时爬虫 - 自动更新数据
用法: python3 arcteryx_daily_crawl.py [--region us] [--gender all]
"""
import json
import os
import sys
import argparse
from datetime import datetime

DATA_FILE = "global_data.json"

REGIONS = [
    {"code": "us", "name": "美国", "currency": "USD", "symbol": "$"},
    {"code": "ca", "name": "加拿大", "currency": "CAD", "symbol": "C$"},
    {"code": "gb", "name": "英国", "currency": "GBP", "symbol": "£"},
    {"code": "de", "name": "德国", "currency": "EUR", "symbol": "€"},
    {"code": "fr", "name": "法国", "currency": "EUR", "symbol": "€"},
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_region_info(code):
    for r in REGIONS:
        if r['code'] == code:
            return r
    return REGIONS[0]

def merge_region_data(existing, new_products, region_code, gender):
    """合并地区数据，删除下架商品"""
    region_info = get_region_info(region_code)
    
    # 构建新产品URL集合
    new_urls = {p['url'] for p in new_products}
    
    # 过滤旧产品（删除下架的）
    filtered = []
    removed = 0
    for p in existing:
        if p.get('region') == region_code and p.get('gender') == gender:
            if p['url'] not in new_urls:
                removed += 1
                continue
        filtered.append(p)
    
    # 添加/更新新产品
    existing_urls = {p['url'] for p in filtered}
    added = 0
    updated = 0
    
    for product in new_products:
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
            "region": region_code,
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
                        p.get('original_price') != formatted['original_price']):
                        filtered[i].update({
                            'sale_price': formatted['sale_price'],
                            'original_price': formatted['original_price'],
                            'discount_pct': formatted['discount_pct'],
                            'last_updated': formatted['last_updated']
                        })
                        updated += 1
                    break
    
    return filtered, added, updated, removed

def generate_browser_script(region_code, gender, symbol):
    """生成浏览器提取脚本"""
    url = f"https://outlet.arcteryx.com/{region_code}/en/shop/{gender}"
    
    script = f'''
// 访问: {url}
// 滚动页面后执行：

async function extractProducts() {{
  let lastHeight = 0;
  let noChange = 0;
  
  while (noChange < 10) {{
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 800));
    if (document.body.scrollHeight === lastHeight) noChange++;
    else noChange = 0;
    lastHeight = document.body.scrollHeight;
  }}
  
  const products = [];
  const imgs = {{}};
  document.querySelectorAll('img').forEach(img => {{
    if (img.src.includes('imgix') && img.alt) imgs[img.alt] = img.src;
  }});
  
  document.querySelectorAll('a').forEach(link => {{
    const text = link.textContent || '';
    const href = link.href || '';
    
    if (href.includes('/shop/{gender}/') && text.includes('{symbol}')) {{
      const prices = text.match(/\\{symbol}(\\d+\\.\\d{{2}})/g);
      if (prices && prices.length >= 2) {{
        const name = text.match(/^(.*?(?:Men's|Women's))/)?.[1] || text.split('{symbol}')[0].trim();
        const nameShort = name.split("'")[0];
        let imgUrl = '';
        for (const [alt, src] of Object.entries(imgs)) {{
          if (alt.includes(nameShort)) {{ imgUrl = src; break; }}
        }}
        
        products.push({{
          url: href,
          name: name,
          original_price: Math.max(...prices.map(p => parseFloat(p.replace('{symbol}', '')))),
          sale_price: Math.min(...prices.map(p => parseFloat(p.replace('{symbol}', '')))),
          image_url: imgUrl
        }});
      }}
    }}
  }});
  
  return products;
}}

extractProducts().then(data => {{
  console.log(JSON.stringify({{region: '{region_code}', gender: '{gender}', products: data}}));
}});
'''
    return url, script

def main():
    parser = argparse.ArgumentParser(description='始祖鸟定时爬虫')
    parser.add_argument('--region', default='us', help='地区代码 (us/ca/gb/de/fr)')
    parser.add_argument('--gender', default='all', help='性别 (mens/womens/all)')
    parser.add_argument('--merge', help='合并数据文件 (JSON)')
    args = parser.parse_args()
    
    print("=" * 50)
    print("始祖鸟定时爬虫")
    print("=" * 50)
    
    # 如果指定了合并文件
    if args.merge:
        if not os.path.exists(args.merge):
            print(f"文件不存在: {args.merge}")
            return
        
        with open(args.merge, 'r') as f:
            merge_data = json.load(f)
        
        region = merge_data.get('region', 'us')
        products = merge_data.get('products', [])
        gender = merge_data.get('gender', 'unknown')
        
        existing = load_data()
        final, added, updated, removed = merge_region_data(existing, products, region, gender)
        save_data(final)
        
        print(f"合并完成 [{region.upper()}] {gender}:")
        print(f"  新增: {added}")
        print(f"  更新: {updated}")
        print(f"  删除: {removed}")
        print(f"  总计: {len(final)}")
        return
    
    # 生成爬取脚本
    genders = ['mens', 'womens'] if args.gender == 'all' else [args.gender]
    region_info = get_region_info(args.region)
    
    print(f"\n地区: {region_info['name']} ({args.region.upper()})")
    print(f"性别: {', '.join(genders)}")
    
    for gender in genders:
        url, script = generate_browser_script(args.region, gender, region_info['symbol'])
        print(f"\n{'='*50}")
        print(f"[{gender.upper()}]")
        print(f"URL: {url}")
        print(f"{'='*50}")
        print(script)
    
    print("\n" + "=" * 50)
    print("使用方法：")
    print("1. 打开URL")
    print("2. 滚动加载所有产品")
    print("3. 执行脚本，复制输出")
    print("4. 保存为 JSON 文件")
    print("5. 运行: python3 arcteryx_daily_crawl.py --merge <file>.json")
    print("=" * 50)

if __name__ == "__main__":
    main()
