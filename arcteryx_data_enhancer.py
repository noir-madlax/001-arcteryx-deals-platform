#!/usr/bin/env python3
"""
Arc'teryx Outlet 数据增强脚本
为现有数据补充：颜色、尺码、库存状态、outlet分类、产品描述、图片URL
"""

import subprocess
import json
import time
import os
import re
from datetime import datetime

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

def get_product_details(url, region_code):
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
            
            // 构建完整URL
            let fullUrl = url;
            if (!url.includes('outlet.arcteryx.com')) {{
                fullUrl = 'https://outlet.arcteryx.com/{region_code}/zh/shop' + url.split('/shop')[1];
            }}
            
            console.error('Visiting:', fullUrl);
            
            // 访问产品详情页
            await page.goto(fullUrl, {{ waitUntil: 'networkidle2', timeout: 60000 }});
            
            // 等待页面加载
            await page.waitForSelector('h1', {{ timeout: 30000 }});
            
            // 获取页面数据
            const productData = await page.evaluate(() => {{
                const data = {{}};
                
                // 获取产品描述（更详细的版本）
                const allParagraphs = document.querySelectorAll('p');
                const descriptions = [];
                for (const p of allParagraphs) {{
                    const text = p.textContent.trim();
                    if (text.length > 50 && !text.includes('US$') && !text.includes('配送')) {{
                        descriptions.push(text);
                    }}
                }}
                data.description = descriptions.join(' ').substring(0, 500);
                
                // 获取颜色选项
                const colorFieldset = document.querySelector('fieldset:first-of-type');
                if (colorFieldset) {{
                    const colorLegend = colorFieldset.querySelector('legend');
                    if (colorLegend) {{
                        const colorText = colorLegend.textContent.replace('折扣颜色:', '').trim();
                        data.currentColor = colorText;
                    }}
                    
                    // 获取所有颜色
                    const colorItems = colorFieldset.querySelectorAll('li');
                    data.colors = Array.from(colorItems).map(li => {{
                        const radio = li.querySelector('input[type="radio"]');
                        return {{
                            color: li.textContent.trim(),
                            checked: radio?.checked,
                            disabled: radio?.disabled
                        }};
                    }});
                }}
                
                // 获取尺码和库存状态
                const sizeElements = document.querySelectorAll('[class*="no--stock"], [class*="in-stock"], [class*="low-stock"], [class*="out-of-stock"]');
                data.sizeStock = Array.from(sizeElements).map(el => ({{
                    size: el.textContent.trim(),
                    isOutOfStock: el.className.includes('no--stock') || el.className.includes('out-of-stock'),
                    isInStock: el.className.includes('in-stock'),
                    isLowStock: el.className.includes('low-stock')
                }}));
                
                // 获取所有尺码
                const sizeText = document.body.innerText.match(/尺码:?\\s*([^美添]+)/s);
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
                
                // 获取产品描述（从展开的部分）
                const detailsButton = document.querySelector('button:has(h5:contains("产品详情"))');
                if (detailsButton) {{
                    detailsButton.click();
                }}
                
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

def update_product_data(product, details):
    """更新产品数据"""
    updated = product.copy()
    
    # 更新描述
    if details.get('description'):
        updated['description'] = details['description']
    
    # 更新颜色
    if details.get('colors'):
        updated['colors'] = [c['color'] for c in details['colors'] if c['color']]
    
    # 更新尺码
    if details.get('sizes'):
        updated['sizes'] = details['sizes']
    
    # 更新库存状态
    if details.get('sizeStock'):
        size_stock = {}
        for item in details['sizeStock']:
            size = item['size']
            if item['isOutOfStock']:
                size_stock[size] = 'out_of_stock'
            elif item['isInStock']:
                size_stock[size] = 'in_stock'
            elif item['isLowStock']:
                size_stock[size] = 'low_stock'
        updated['size_stock'] = size_stock
    
    # 更新图片URL
    if details.get('imageUrls') and not updated.get('image_url'):
        updated['image_url'] = details['imageUrls'][0] if details['imageUrls'] else ''
    
    # 更新outlet分类（从面包屑）
    if details.get('breadcrumbs'):
        breadcrumbs = details['breadcrumbs']
        if len(breadcrumbs) >= 3:
            updated['outlet_category'] = breadcrumbs[-1]  # 最后一个通常是具体分类
        elif len(breadcrumbs) >= 2:
            updated['outlet_category'] = breadcrumbs[1]
    
    updated['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return updated

def main():
    """主函数"""
    print("🦜 Arc'teryx Outlet 数据增强脚本启动")
    print("=" * 50)
    
    # 加载现有数据
    data_file = 'global_data.json'
    if not os.path.exists(data_file):
        print("❌ 未找到数据文件")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📊 加载了 {len(products)} 个产品")
    
    # 备份原始数据
    backup_file = f"global_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"💾 已备份到 {backup_file}")
    
    # 更新每个产品
    updated_count = 0
    error_count = 0
    
    for i, product in enumerate(products):
        model = product.get('model', '未知')
        url = product.get('url', '')
        region = product.get('region', 'us')
        
        print(f"\n[{i+1}/{len(products)}] 处理: {model}")
        
        if not url:
            print("  ⚠️ 跳过：无URL")
            continue
        
        # 检查是否需要更新
        needs_update = (
            not product.get('colors') or 
            not product.get('sizes') or 
            not product.get('size_stock') or
            not product.get('outlet_category') or
            not product.get('description') or
            not product.get('image_url')
        )
        
        if not needs_update:
            print("  ✅ 已有完整数据，跳过")
            continue
        
        # 获取详情
        print(f"  🔍 获取详情...")
        details = get_product_details(url, region)
        
        if details and not details.get('error'):
            # 更新数据
            products[i] = update_product_data(product, details)
            updated_count += 1
            print(f"  ✅ 更新成功")
            
            # 显示更新的字段
            for key in ['colors', 'sizes', 'size_stock', 'outlet_category', 'description', 'image_url']:
                if key in details and details[key]:
                    value_str = str(details[key])[:50] + '...' if len(str(details[key])) > 50 else str(details[key])
                    print(f"    {key}: {value_str}")
        else:
            error_count += 1
            print(f"  ❌ 获取详情失败")
        
        # 避免请求过快
        time.sleep(2)
    
    # 保存更新后的数据
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 数据增强完成！")
    print(f"  成功更新: {updated_count}")
    print(f"  失败: {error_count}")
    print(f"  总产品数: {len(products)}")
    
    # 统计信息
    print("\n📈 字段完整性统计:")
    fields = ['colors', 'sizes', 'size_stock', 'outlet_category', 'description', 'image_url']
    for field in fields:
        count = sum(1 for p in products if p.get(field))
        percentage = (count / len(products)) * 100 if products else 0
        print(f"  {field}: {count}/{len(products)} ({percentage:.1f}%)")

if __name__ == '__main__':
    main()
