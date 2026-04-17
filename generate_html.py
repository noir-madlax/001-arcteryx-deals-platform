#!/usr/bin/env python3
"""从 global_data.json 生成 index.html demo 页面（支持真实图片 URL）"""
import json
from collections import Counter, defaultdict
from datetime import datetime
import urllib.parse

DATA_FILE = '/Users/J/arcteryx-deals-platform/global_data.json'
OUTPUT_FILE = '/Users/J/arcteryx-deals-platform/index.html'

with open(DATA_FILE) as f:
    data = json.load(f)

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

regions = Counter(p.get('region', 'unknown') for p in data)
categories = Counter(p.get('category', 'unknown') for p in data)
total = len(data)

REGION_INFO = {
    'us': {'name': '美国', 'flag': '🇺🇸', 'currency': 'USD', 'symbol': '$'},
    'ca': {'name': '加拿大', 'flag': '🇨🇦', 'currency': 'CAD', 'symbol': 'C$'},
    'gb': {'name': '英国', 'flag': '🇬🇧', 'currency': 'GBP', 'symbol': '£'},
    'de': {'name': '德国', 'flag': '🇩🇪', 'currency': 'EUR', 'symbol': '€'},
    'fr': {'name': '法国', 'flag': '🇫🇷', 'currency': 'EUR', 'symbol': '€'},
    'nl': {'name': '荷兰', 'flag': '🇳🇱', 'currency': 'EUR', 'symbol': '€'},
}

def make_placeholder_svg(product_name):
    """生成 SVG 占位图"""
    encoded_name = urllib.parse.quote(product_name[:30], safe='')
    return f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect fill='%231a1a1a' width='400' height='300'/%3E%3Ctext x='50%25' y='45%25' fill='%23334155' text-anchor='middle' font-size='40'%3E%F0%9F%8F%94%EF%B8%8F%3C/text%3E%3Ctext x='50%25' y='65%25' fill='%2364748b' text-anchor='middle' font-size='13' font-family='Arial'%3E{encoded_name}%3C/text%3E%3C/svg%3E"

def get_image(product):
    """获取产品图片，优先用 image_url，否则用占位图"""
    image_url = product.get('image_url', '').strip()
    if image_url and image_url.startswith('http'):
        return image_url
    return make_placeholder_svg(product.get('model', product.get('name', ''))[:60])

def format_price(price, symbol):
    if price == 0:
        return f"{symbol}0"
    if price == int(price):
        return f"{symbol}{int(price):,}"
    return f"{symbol}{price:,.2f}"

# 按国家分组
by_region = defaultdict(list)
for p in data:
    by_region[p.get('region', 'unknown')].append(p)

# 统计
has_image = sum(1 for p in data if p.get('image_url', '').strip())
no_image = total - has_image

# 生成卡片 HTML
def render_card(p):
    symbol = p.get('symbol', '$')
    orig = format_price(p.get('original_price', 0), symbol)
    sale = format_price(p.get('sale_price', 0), symbol)
    disc = p.get('discount_pct', 0)
    save_amt = p.get('original_price', 0) - p.get('sale_price', 0)
    save = format_price(save_amt, symbol)
    model = p.get('model', p.get('name', 'Unknown'))[:60]
    category = p.get('category', '其他')
    region_name = REGION_INFO.get(p.get('region', ''), {}).get('name', p.get('region', ''))
    img_src = get_image(p)
    is_real_image = img_src.startswith('http')
    
    if is_real_image:
        img_html = f'<img class="card-img" src="{img_src}" alt="{model}" loading="lazy" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';"><div class="card-img-placeholder" style="display:none;">🏔️<br>{model}</div>'
    else:
        img_html = f'<div class="card-img-placeholder">🏔️<br><span style="font-size:0.8rem;">{model}</span></div>'
    
    return f'''<div class="card">
                {img_html}
                <div class="card-body">
                    <div class="card-model" title="{model}">{model}</div>
                    <div class="card-meta">
                        <span class="badge badge-cat">{category}</span>
                        <span class="badge badge-disc">-{disc}%</span>
                    </div>
                    <div class="price-row">
                        <span class="orig-price">{orig}</span>
                        <span class="sale-price">{sale}</span>
                    </div>
                    <div class="save-tag">立省 {save}</div>
                    <div class="card-source">Outlet {region_name}</div>
                    <a class="card-link" href="{p.get('url', '#')}" target="_blank">查看商品 →</a>
                </div>
            </div>'''

# 构建完整的 HTML
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arc'teryx 全球折扣监控平台</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #e5e5e5; min-height: 100vh; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 2rem; text-align: center; border-bottom: 2px solid #0f3460; }}
        .header h1 {{ font-size: 2rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }}
        .header p {{ color: #94a3b8; font-size: 0.9rem; }}
        .stats {{ display: flex; justify-content: center; gap: 2rem; padding: 1rem 2rem; background: #111; flex-wrap: wrap; }}
        .stat-item {{ text-align: center; }}
        .stat-item .num {{ font-size: 1.5rem; font-weight: 700; color: #38bdf8; }}
        .stat-item .label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; }}
        .country-section {{ padding: 1.5rem 2rem; }}
        .country-header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #333; }}
        .country-header h2 {{ font-size: 1.3rem; color: #fff; }}
        .country-header .count {{ background: #1e293b; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.8rem; color: #94a3b8; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }}
        .card {{ background: #1a1a1a; border-radius: 12px; overflow: hidden; border: 1px solid #2a2a2a; transition: all 0.2s; }}
        .card:hover {{ border-color: #38bdf8; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(56,189,248,0.1); }}
        .card-img {{ width: 100%; height: 220px; object-fit: cover; background: #111; }}
        .card-img-placeholder {{ width: 100%; height: 220px; background: linear-gradient(135deg, #1e293b, #0f172a); display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 0.5rem; color: #475569; font-size: 2.5rem; padding: 1rem; text-align: center; }}
        .card-body {{ padding: 1rem; }}
        .card-model {{ font-size: 0.95rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .card-meta {{ display: flex; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; }}
        .badge {{ font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 4px; }}
        .badge-cat {{ background: #1e293b; color: #94a3b8; }}
        .badge-disc {{ background: #064e3b; color: #34d399; }}
        .price-row {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem; }}
        .orig-price {{ font-size: 0.85rem; color: #64748b; text-decoration: line-through; }}
        .sale-price {{ font-size: 1.2rem; font-weight: 700; color: #38bdf8; }}
        .save-tag {{ font-size: 0.75rem; color: #34d399; margin-bottom: 0.5rem; }}
        .card-source {{ font-size: 0.7rem; color: #4b5563; margin-bottom: 0.5rem; }}
        .card-link {{ display: inline-block; font-size: 0.8rem; color: #38bdf8; text-decoration: none; }}
        .card-link:hover {{ text-decoration: underline; }}
        .footer {{ text-align: center; padding: 2rem; color: #4b5563; font-size: 0.8rem; border-top: 1px solid #222; }}
        .footer p {{ margin: 0.3rem 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Arc'teryx 全球折扣监控平台</h1>
        <p>实时追踪全球 Outlet 折扣信息</p>
    </div>
    <div class="stats">
        <div class="stat-item">
            <div class="num">{total}</div>
            <div class="label">总商品数</div>
        </div>
        <div class="stat-item">
            <div class="num">{has_image}</div>
            <div class="label">有图片</div>
        </div>
        <div class="stat-item">
            <div class="num">{no_image}</div>
            <div class="label">无图片</div>
        </div>
        <div class="stat-item">
            <div class="num">{len(regions)}</div>
            <div class="label">覆盖国家</div>
        </div>
        <div class="stat-item">
            <div class="num">{len(categories)}</div>
            <div class="label">商品品类</div>
        </div>
        <div class="stat-item">
            <div class="num">{max(p.get("discount_pct", 0) for p in data)}%</div>
            <div class="label">最高折扣</div>
        </div>
    </div>
'''

# 按国家渲染
for region_code in sorted(by_region.keys()):
    products = by_region[region_code]
    info = REGION_INFO.get(region_code, {'name': region_code, 'flag': '', 'currency': '', 'symbol': '$'})
    
    html += f'''<div class="country-section">
    <div class="country-header">
        <h2>{info['flag']} {info['name']} ({region_code.upper()})</h2>
        <span class="count">{len(products)} 款</span>
        <span class="count">{info['currency']}</span>
    </div>
    <div class="grid">
'''
    for p in products:
        html += render_card(p)
    
    html += '''</div></div>\n'''

html += f'''<div class="footer">
        <p>数据来源：Arc'teryx Outlet 官方站点 | 最后更新：{now}</p>
        <p>© 2026 Arc'teryx 折扣监控平台</p>
    </div>
</body>
</html>'''

with open(OUTPUT_FILE, 'w') as f:
    f.write(html)

print(f"Generated index.html with {total} products ({has_image} with images, {no_image} placeholders)")
print(f"File size: {len(html):,} bytes")
