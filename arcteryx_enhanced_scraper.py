#!/usr/bin/env python3
"""
Arc'teryx Outlet 增强版爬虫 - 支持多地区、多分类
新增功能：颜色、尺码、库存状态、outlet分类、产品描述、图片URL
"""

import subprocess
import json
import time
import os
from datetime import datetime

# 配置
REGIONS = [
    {"code": "us", "name": "美国", "currency": "USD", "symbol": "$"},
    {"code": "de", "name": "德国", "currency": "EUR", "symbol": "€"},
    {"code": "gb", "name": "英国", "currency": "GBP", "symbol": "£"},
]

GENDERS = [
    {"code": "mens", "name": "男装"},
    {"code": "womens", "name": "女装"},
]

# 定义分类
CATEGORIES = [
    {"slug": "shells-jackets", "name": "硬壳/软壳夹克"},
    {"slug": "insulated-jackets", "name": "保暖夹克"},
    {"slug": "pants", "name": "裤装"},
    {"slug": "tops", "name": "上衣"},
    {"slug": "accessories", "name": "配件"},
    {"slug": "packs", "name": "背包"},
    {"slug": "shoes", "name": "鞋履"},
]

def run_js_code(code):
    """执行 JavaScript 并返回结果"""
    proc = subprocess.Popen(
        ["node", "-e", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate(timeout=180)
    if proc.returncode != 0:
        print(f"JS Error: {err[:200]}")
        return None
    try:
        return json.loads(out)
    except:
        return None

def get_product_details(url, region):
    """获取产品详情页信息"""
    js_code = f"""
    const puppeteer = require('puppeteer-extra');
    const StealthPlugin = require('puppeteer-extra-plugin-stealth');
    puppeteer.use(StealthPlugin());

    (async () => {{
        const browser = await puppeteer.launch({{
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }});
        
        try {{
            const page = await browser.newPage();
            await page.setViewport({{ width: 1280, height: 720 }});
            
            // 访问产品详情页
            const fullUrl = 'https://outlet.arcteryx.com/{region["code"]}/zh/shop' + url.split('/shop')[1];
            await page.goto(fullUrl, {{ waitUntil: 'networkidle2', timeout: 60000 }});
            
            // 等待页面加载
            await page.waitForSelector('h1', {{ timeout: 30000 }});
            
            // 获取页面数据
            const productData = await page.evaluate(() => {{
                const data = {{}};
                
                // 获取产品描述
                const paragraphs = document.querySelectorAll('p');
                for (const p of paragraphs) {{
                    if (p.textContent.includes('这款') || p.textContent.includes('适合')) {{
                        data.description = p.textContent.trim();
                        break;
                    }}
                }}
                
                // 获取颜色选项
                const colorFieldset = document.querySelector('fieldset:first-of-type');
                if (colorFieldset) {{
                    const colorLegend = colorFieldset.querySelector('legend');
                    if (colorLegend) {{
                        const colorText = colorLegend.textContent.replace('折扣颜色:', '').trim();
                        data.currentColor = colorText;
                    }}
                }}
                
                // 获取所有颜色选项
                const colorInputs = document.querySelectorAll('fieldset:first-of-type input[type="radio"]');
                data.colors = Array.from(colorInputs).map(input => {{
                    const label = input.closest('li') || input.parentElement;
                    return {{
                        color: label?.textContent?.trim() || input.value,
                        checked: input.checked,
                        disabled: input.disabled
                    }};
                }});
                
                // 获取尺码和库存状态
                const sizeElements = document.querySelectorAll('[class*="no--stock"], [class*="in-stock"], [class*="low-stock"], [class*="out-of-stock"]');
                data.sizeStock = Array.from(sizeElements).map(el => ({{
                    size: el.textContent?.trim(),
                    isOutOfStock: el.className.includes('no--stock') || el.className.includes('out-of-stock'),
                    isInStock: el.className.includes('in-stock'),
                    isLowStock: el.className.includes('low-stock')
                }}));
                
                // 获取所有尺码
                const sizeText = document.body.innerText.match(/尺码:?\s*([^美添]+)/s);
                if (sizeText) {{
                    data.sizes = sizeText[1].split('\\n').filter(s => s.trim() && !isNaN(s.trim()));
                }}
                
                // 获取图片URL
                const images = Array.from(document.querySelectorAll('img[src*="arcteryx"]')).filter(img => 
                    img.src.includes('details') || img.src.includes('product')
                );
                data.imageUrls = images.map(img => img.src);
                
                // 获取outlet分类（从面包屑导航）
                const breadcrumbs = document.querySelectorAll('nav[aria-label="Breadcrumbs"] a, nav[aria-label="breadcrumbs"] a');
                data.breadcrumbs = Array.from(breadcrumbs).map(a => a.textContent.trim());
                
                return data;
            }});
            
            await browser.close();
            console.log(JSON.stringify(productData));
            
        }} catch (error) {{
            console.error('Error:', error.message);
            await browser.close();
            console.log(JSON.stringify({{ error: error.message }}));
        }}
    }})();
    """
    
    return run_js_code(js_code)

def scrape_category_page(region, gender, category):
    """抓取分类页面的所有产品"""
    js_code = f"""
    const puppeteer = require('puppeteer-extra');
    const StealthPlugin = require('puppeteer-extra-plugin-stealth');
    puppeteer.use(StealthPlugin());

    (async () => {{
        const browser = await puppeteer.launch({{
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }});
        
        try {{
            const page = await browser.newPage();
            await page.setViewport({{ width: 1280, height: 720 }});
            
            // 访问分类页面
            const url = 'https://outlet.arcteryx.com/{region["code"]}/zh/shop/{gender["code"]}/{category["slug"]}';
            await page.goto(url, {{ waitUntil: 'networkidle2', timeout: 60000 }});
            
            // 等待产品加载
            await page.waitForSelector('a[href*="/shop/"]', {{ timeout: 30000 }});
            
            // 获取所有产品
            const products = await page.evaluate(() => {{
                const items = [];
                
                // 查找所有产品链接
                const productLinks = document.querySelectorAll('a[href*="/shop/"]');
                
                for (const link of productLinks) {{
                    const href = link.getAttribute('href');
                    if (!href || !href.includes('/shop/')) continue;
                    
                    // 提取产品信息
                    const text = link.textContent.trim();
                    const img = link.querySelector('img');
                    
                    items.push({{
                        url: href,
                        fullText: text,
                        imageUrl: img ? img.src : null
                    }});
                }}
                
                return items;
            }});
            
            await browser.close();
            console.log(JSON.stringify(products));
            
        }} catch (error) {{
            console.error('Error:', error.message);
            await browser.close();
            console.log(JSON.stringify([]));
        }}
    }})();
    """
    
    return run_js_code(js_code)

def parse_product_data(raw_data, region, gender, category):
    """解析产品数据"""
    products = []
    
    for item in raw_data:
        text = item.get('fullText', '')
        url = item.get('url', '')
        
        if not text or not url:
            continue
        
        # 解析价格
        import re
        prices = re.findall(r'US\$[\d.]+', text)
        
        if len(prices) >= 2:
            sale_price = float(prices[0].replace('US$', ''))
            original_price = float(prices[1].replace('US$', ''))
            discount_pct = round((1 - sale_price / original_price) * 100)
        elif len(prices) == 1:
            sale_price = float(prices[0].replace('US$', ''))
            original_price = sale_price
            discount_pct = 0
        else:
            continue
        
        # 解析产品名称和描述
        parts = text.split('US$')
        name_desc = parts[0].strip()
        
        # 提取产品名称
        name_match = re.match(r'^(.+?(?:男装|女装))', name_desc)
        if name_match:
            full_name = name_match.group(1).strip()
            description = name_desc[len(full_name):].strip()
        else:
            full_name = name_desc
            description = ''
        
        # 提取产品型号
        model = re.sub(r'(男装|女装)$', '', full_name).strip()
        
        product = {
            'model': model,
            'full_name': full_name,
            'description': description,
            'category': category['name'],
            'original_price': original_price,
            'sale_price': sale_price,
            'discount_pct': discount_pct,
            'currency': region['currency'],
            'symbol': region['symbol'],
            'gender': gender['name'],
            'region': region['code'],
            'region_name': region['name'],
            'url': url,
            'image_url': item.get('imageUrl'),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        products.append(product)
    
    return products

def main():
    """主函数"""
    all_products = []
    
    print("🦜 Arc'teryx Outlet 增强版爬虫启动")
    print("=" * 50)
    
    for region in REGIONS:
        print(f"\n🌍 正在抓取地区: {region['name']} ({region['code']})")
        
        for gender in GENDERS:
            print(f"\n👤 性别: {gender['name']}")
            
            for category in CATEGORIES:
                print(f"  📂 分类: {category['name']}...")
                
                # 抓取分类页面
                raw_products = scrape_category_page(region, gender, category)
                
                if raw_products:
                    # 解析产品数据
                    products = parse_product_data(raw_products, region, gender, category)
                    all_products.extend(products)
                    print(f"    ✅ 抓取到 {len(products)} 个产品")
                else:
                    print(f"    ⚠️ 未找到产品")
                
                time.sleep(2)
    
    print(f"\n🎉 总共抓取到 {len(all_products)} 个产品")
    print("=" * 50)
    
    # 保存数据
    output_file = 'global_data.json'
    
    # 加载现有数据
    existing_data = []
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
    
    # 合并数据（按URL去重）
    existing_urls = {item.get('url') for item in existing_data}
    new_products = [p for p in all_products if p.get('url') not in existing_urls]
    
    if new_products:
        existing_data.extend(new_products)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 保存了 {len(new_products)} 个新产品到 {output_file}")
        print(f"📊 数据集中共有 {len(existing_data)} 个产品")
    else:
        print(f"\n✨ 没有新产品需要添加")
    
    return existing_data

if __name__ == '__main__':
    data = main()
    
    # 打印统计信息
    if data:
        print("\n📈 数据集统计:")
        print(f"  总产品数: {len(data)}")
        
        regions = {}
        categories = {}
        
        for item in data:
            region_name = item.get('region_name', '未知')
            category = item.get('category', '未知')
            
            regions[region_name] = regions.get(region_name, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        print("\n  按地区:")
        for region, count in sorted(regions.items()):
            print(f"    {region}: {count}")
        
        print("\n  按分类:")
        for category, count in sorted(categories.items()):
            print(f"    {category}: {count}")
