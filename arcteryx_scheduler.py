#!/usr/bin/env python3
"""
始祖鸟定时爬取脚本
每天自动更新库存和价格
"""
import json
import os
import sys
from datetime import datetime

DATA_FILE = "global_data.json"
SKU_FILE = "arcteryx_skus.json"
LOG_FILE = "crawl_log.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return []

def save_json(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_crawl(action, details):
    """记录爬取日志"""
    logs = load_json(LOG_FILE)
    logs.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'details': details
    })
    # 只保留最近100条日志
    logs = logs[-100:]
    save_json(logs, LOG_FILE)

def update_product_prices():
    """更新产品价格（模拟）"""
    products = load_json(DATA_FILE)
    updated = 0
    
    for product in products:
        # 这里可以添加实际的价格检查逻辑
        # 目前只是更新时间戳
        product['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        updated += 1
    
    save_json(products, DATA_FILE)
    log_crawl('update_prices', f'更新了 {updated} 个产品')
    return updated

def update_sku_stock():
    """更新SKU库存（模拟）"""
    skus = load_json(SKU_FILE)
    updated = 0
    
    for sku in skus:
        # 这里可以添加实际的库存检查逻辑
        # 目前只是更新时间戳
        sku['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        updated += 1
    
    save_json(skus, SKU_FILE)
    log_crawl('update_stock', f'更新了 {updated} 个SKU')
    return updated

def generate_browser_script(region='us', gender='mens'):
    """生成浏览器提取脚本"""
    url = f"https://outlet.arcteryx.com/{region}/en/shop/{gender}"
    
    script = f'''
// 定时爬取脚本
// 访问: {url}

async function crawlProducts() {{
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
  const imgs = {{}};
  
  // 收集图片
  document.querySelectorAll('img').forEach(img => {{
    if (img.src.includes('imgix') && img.alt) imgs[img.alt] = img.src;
  }});
  
  // 提取产品链接
  document.querySelectorAll('a').forEach(link => {{
    const text = link.textContent || '';
    const href = link.href || '';
    
    if (href.includes('/shop/{gender}/') && text.includes('$')) {{
      const prices = text.match(/\\$(\\d+\\.\\d{{2}})/g);
      if (prices && prices.length >= 2) {{
        const name = text.match(/^(.*?(?:Men's|Women's))/)?.[1] || text.split('$')[0].trim();
        const nameShort = name.split("'")[0];
        
        // 查找图片
        let imgUrl = '';
        for (const [alt, src] of Object.entries(imgs)) {{
          if (alt.includes(nameShort)) {{ imgUrl = src; break; }}
        }}
        
        products.push({{
          url: href,
          name: name,
          original_price: Math.max(...prices.map(p => parseFloat(p.replace('$', '')))),
          sale_price: Math.min(...prices.map(p => parseFloat(p.replace('$', '')))),
          image_url: imgUrl
        }});
      }}
    }}
  }});
  
  return products;
}}

crawlProducts().then(data => {{
  console.log(JSON.stringify({{
    region: '{region}',
    gender: '{gender}',
    timestamp: new Date().toISOString(),
    products: data
  }}));
}});
'''
    return url, script

def main():
    print("=" * 50)
    print("始祖鸟定时爬取")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'update':
            # 更新价格和库存
            print("\n更新产品价格...")
            products_updated = update_product_prices()
            print(f"  更新了 {products_updated} 个产品")
            
            print("\n更新SKU库存...")
            skus_updated = update_sku_stock()
            print(f"  更新了 {skus_updated} 个SKU")
            
            print(f"\n完成！日志已记录到 {LOG_FILE}")
        
        elif command == 'script':
            # 生成浏览器脚本
            region = sys.argv[2] if len(sys.argv) > 2 else 'us'
            gender = sys.argv[3] if len(sys.argv) > 3 else 'mens'
            
            url, script = generate_browser_script(region, gender)
            print(f"\nURL: {url}")
            print("\n浏览器脚本：")
            print(script)
        
        else:
            print(f"未知命令: {command}")
            print("用法: python3 arcteryx_scheduler.py [update|script] [region] [gender]")
    else:
        print("\n用法:")
        print("  python3 arcteryx_scheduler.py update          - 更新价格和库存")
        print("  python3 arcteryx_scheduler.py script us mens  - 生成浏览器脚本")
        print("\n定时任务设置（crontab）:")
        print("  # 每天凌晨2点更新")
        print("  0 2 * * * cd ~/arcteryx-deals-platform && python3 arcteryx_scheduler.py update")

if __name__ == "__main__":
    main()
