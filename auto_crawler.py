#!/usr/bin/env python3
"""
始祖鸟全站数据爬虫 - 自动化版本
支持所有国家，自动爬取并合并数据
"""
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from collections import Counter

DATA_FILE = "global_data.json"
STATE_FILE = "crawl_state.json"
IMAGE_MAP_FILE = "product_image_map.json"

# 所有支持的国家
REGIONS = [
    {"code": "us", "lang": "en", "name": "美国",   "currency": "USD", "symbol": "$"},
    {"code": "ca", "lang": "en", "name": "加拿大", "currency": "CAD", "symbol": "C$"},
    {"code": "gb", "lang": "en", "name": "英国",   "currency": "GBP", "symbol": "£"},
    {"code": "de", "lang": "de", "name": "德国",   "currency": "EUR", "symbol": "€"},
    {"code": "fr", "lang": "fr", "name": "法国",   "currency": "EUR", "symbol": "€"},
    {"code": "nl", "lang": "en", "name": "荷兰",   "currency": "EUR", "symbol": "€"},
    {"code": "se", "lang": "en", "name": "瑞典",   "currency": "SEK", "symbol": "kr"},
    {"code": "at", "lang": "de", "name": "奥地利", "currency": "EUR", "symbol": "€"},
    {"code": "ch", "lang": "de", "name": "瑞士",   "currency": "CHF", "symbol": "CHF"},
    {"code": "au", "lang": "en", "name": "澳大利亚","currency": "AUD", "symbol": "A$"},
    {"code": "jp", "lang": "ja", "name": "日本",   "currency": "JPY", "symbol": "¥"},
    {"code": "kr", "lang": "ko", "name": "韩国",   "currency": "KRW", "symbol": "₩"},
    {"code": "it", "lang": "it", "name": "意大利", "currency": "EUR", "symbol": "€"},
    {"code": "es", "lang": "es", "name": "西班牙", "currency": "EUR", "symbol": "€"},
    {"code": "be", "lang": "nl", "name": "比利时", "currency": "EUR", "symbol": "€"},
    {"code": "fi", "lang": "en", "name": "芬兰",   "currency": "EUR", "symbol": "€"},
    {"code": "dk", "lang": "en", "name": "丹麦",   "currency": "DKK", "symbol": "kr"},
    {"code": "no", "lang": "en", "name": "挪威",   "currency": "NOK", "symbol": "kr"},
    {"code": "pl", "lang": "en", "name": "波兰",   "currency": "PLN", "symbol": "zł"},
    {"code": "cz", "lang": "en", "name": "捷克",   "currency": "CZK", "symbol": "Kč"},
]

CATEGORIES = ["mens", "womens"]

# ── 图片映射表（slug → 图片 URL） ──────────────────────────────────────────
_IMAGE_MAP: dict = {}

def load_image_map():
    global _IMAGE_MAP
    if os.path.exists(IMAGE_MAP_FILE):
        with open(IMAGE_MAP_FILE, 'r', encoding='utf-8') as f:
            _IMAGE_MAP = json.load(f)
        print(f"已加载图片映射: {len(_IMAGE_MAP)} 条")
    else:
        print(f"⚠ 图片映射文件不存在: {IMAGE_MAP_FILE}")

def slug_from_url(url: str) -> str:
    """从完整 URL 中提取末尾 slug，例如 '.../sabre-pant-8928' → 'sabre-pant-8928'"""
    return url.rstrip('/').split('/')[-1]

def image_from_map(url: str) -> str:
    """用 slug 在 product_image_map.json 里查图片"""
    return _IMAGE_MAP.get(slug_from_url(url), "")


# ── 品类推断 ────────────────────────────────────────────────────────────────
def infer_category(name, url):
    text = (name + " " + url).lower()
    if any(k in text for k in ["shell", "alpha", "beta", "gore-tex"]) and \
       any(k in text for k in ["jacket", "coat", "anorak"]):
        return "硬壳冲锋衣"
    if any(k in text for k in ["down", "insulated"]) and \
       any(k in text for k in ["jacket", "coat", "parka", "vest", "pant"]):
        return "保暖羽绒"
    if "fleece" in text or "delta" in text or "covert" in text:
        return "抓绒/连帽"
    if "base" in text or "rho " in text or "rho-" in text:
        return "排汗内衣"
    if any(k in text for k in ["pant", "bib", "bottom"]):
        return "裤装"
    if any(k in text for k in ["shoe", "boot"]):
        return "鞋类"
    if any(k in text for k in ["backpack", "pack", "bora"]):
        return "背包"
    if "veilance" in text:
        return "Veilance商务"
    if any(k in text for k in ["tank", "shirt", "top", "tee"]):
        return "上衣/T恤"
    if any(k in text for k in ["glove", "hat", "beanie", "cap"]):
        return "配件"
    if any(k in text for k in ["hoody", "hoodie"]):
        return "连帽衫"
    if "anorak" in text:
        return "套头外套"
    return "其他"

def infer_gender(category, url):
    if "womens" in url or "women" in url:
        return "women"
    if "mens" in url or "men" in url:
        return "men"
    return "unknown"


# ── HTTP ─────────────────────────────────────────────────────────────────────
def fetch_page(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  获取失败: {e}")
        return None


# ── URL 修复工具（修补历史遗留的缺地区前缀 URL） ─────────────────────────────
def fix_url(url: str, region_code: str, region_lang: str) -> str:
    """
    将旧格式 URL 修复为带地区/语言前缀的格式。
    旧: https://outlet.arcteryx.com/shop/mens/xxx
    新: https://outlet.arcteryx.com/{code}/{lang}/shop/mens/xxx
    """
    prefix = f"https://outlet.arcteryx.com/{region_code}/{region_lang}"
    if url.startswith("https://outlet.arcteryx.com/shop/"):
        path = url[len("https://outlet.arcteryx.com"):]  # → /shop/...
        return prefix + path
    return url  # 已经是正确格式，不动


# ── 主提取逻辑 ────────────────────────────────────────────────────────────────
def extract_products_from_html(html, region_info, category):
    """从 HTML 提取产品列表数据"""
    products = []
    code = region_info["code"]
    lang = region_info["lang"]

    pattern = r'<a[^>]*href="([^"]*(?:/shop/[^"]+))"[^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)

    for url_path, content in matches:
        if '/shop/' not in url_path:
            continue
        if len(content) < 20:
            continue

        # ── 价格 ──
        price_patterns = [
            r'[\$£€]\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*kr',
            r'₩\s*([\d,]+)',
            r'¥\s*([\d,]+)',
        ]
        prices = []
        for pat in price_patterns:
            for p in re.findall(pat, content):
                try:
                    prices.append(float(p.replace(',', '')))
                except Exception:
                    pass
        if len(prices) < 2:
            continue

        # ── 产品名称 ──
        name_match = re.match(r'^(.*?)\s*[\$£€¥₩\d]', content.strip())
        name = name_match.group(1).strip() if name_match else content[:50].strip()
        name = re.sub(r'\s+', ' ', name).replace('\n', ' ').strip()
        if len(name) < 5:
            continue

        # ── URL：带地区前缀（Bug Fix #1） ──────────────────────────────
        if url_path.startswith('/'):
            # 若路径已包含地区前缀（如 /de/de/shop/...），直接拼接
            if url_path.startswith(f'/{code}/'):
                full_url = f"https://outlet.arcteryx.com{url_path}"
            else:
                # 路径是 /shop/... 或其他，手动加地区前缀
                full_url = f"https://outlet.arcteryx.com/{code}/{lang}{url_path}"
        elif url_path.startswith('http'):
            full_url = url_path
        else:
            continue

        # ── 图片：先尝试 HTML 内联，再查映射表（Bug Fix #2） ──────────
        img_match = re.search(r'<img[^>]*src="([^"]+)"', content)
        image_url = img_match.group(1) if img_match else ""
        # 过滤掉无关小图（追踪像素、SVG、data: URI 等）
        if image_url and (image_url.startswith('data:') or
                          '/icon' in image_url or
                          '.svg' in image_url or
                          len(image_url) < 30):
            image_url = ""
        if not image_url:
            image_url = image_from_map(full_url)

        # ── 价格 ──
        original_price = max(prices)
        sale_price = min(prices)
        discount_pct = round((1 - sale_price / original_price) * 100) if original_price > 0 else 0

        product = {
            "model":         name.split("'")[0] if "'" in name else name,
            "full_name":     name,
            "description":   name,           # 原始全名，前端会解析描述后缀
            "category":      infer_category(name, full_url),
            "original_price": original_price,
            "sale_price":    sale_price,
            "sale_price_max": sale_price,
            "discount_pct":  discount_pct,
            "currency":      region_info["currency"],
            "symbol":        region_info["symbol"],
            "gender":        infer_gender(category, full_url),
            "region":        code,
            "region_name":   region_info["name"],
            "url":           full_url,
            "image_url":     image_url,
            "last_updated":  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "colors":        [],
            "sizes":         [],
            "size_stock":    {},
            "outlet_category": "",
        }
        products.append(product)

    return products


# ── 合并 ──────────────────────────────────────────────────────────────────────
def merge_products(existing, new_products):
    """
    合并新抓取的产品到现有列表。
    以 URL slug（末尾路径段）为主键去重，避免因地区前缀变化产生重复条目。
    """
    # 索引：slug → 列表下标
    slug_index = {}
    for i, p in enumerate(existing):
        slug_index[slug_from_url(p.get('url', ''))] = i

    new_count = updated_count = 0

    for product in new_products:
        url = product.get('url', '')
        if not url:
            continue
        s = slug_from_url(url)

        if s not in slug_index:
            existing.append(product)
            slug_index[s] = len(existing) - 1
            new_count += 1
        else:
            idx = slug_index[s]
            ex = existing[idx]
            changed = False

            # 价格变化 → 更新
            if product.get('sale_price') != ex.get('sale_price'):
                ex['sale_price'] = product['sale_price']
                ex['original_price'] = product['original_price']
                ex['discount_pct'] = product['discount_pct']
                changed = True

            # 修正旧的错误 URL（缺地区前缀）
            if ex.get('url', '') != url and '/shop/' in ex.get('url', ''):
                ex['url'] = url
                changed = True

            # 回填缺失图片
            if not ex.get('image_url') and product.get('image_url'):
                ex['image_url'] = product['image_url']
                changed = True

            if changed:
                ex['last_updated'] = product['last_updated']
                updated_count += 1

    return new_count, updated_count


# ── 数据校验 ──────────────────────────────────────────────────────────────────
def validate_products(products, region_codes):
    """校验产品数据，打印警告"""
    bad_url = bad_img = 0
    for p in products:
        url = p.get('url', '')
        region = p.get('region', '')
        # URL 应包含地区代码
        if region and f'/{region}/' not in url:
            bad_url += 1
        if not p.get('image_url'):
            bad_img += 1
    total = len(products)
    print(f"\n📋 数据校验: {total} 条产品")
    print(f"  URL 缺地区前缀: {bad_url} ({bad_url/total*100:.1f}%)" if bad_url
          else "  ✅ 所有 URL 格式正确")
    print(f"  缺图片: {bad_img} ({bad_img/total*100:.1f}%)" if bad_img
          else "  ✅ 所有产品有图片")


# ── 历史数据一次性修复 ────────────────────────────────────────────────────────
def migrate_existing(existing):
    """修复已有数据中的旧格式 URL 和缺失图片"""
    # 构建 region_code → lang 映射
    region_map = {r['code']: r['lang'] for r in REGIONS}
    fixed_url = fixed_img = 0

    for p in existing:
        code = p.get('region', '')
        lang = region_map.get(code, 'en')
        old_url = p.get('url', '')

        # 修复 URL
        new_url = fix_url(old_url, code, lang)
        if new_url != old_url:
            p['url'] = new_url
            fixed_url += 1

        # 回填图片
        if not p.get('image_url'):
            img = image_from_map(p['url'])
            if img:
                p['image_url'] = img
                fixed_img += 1

    if fixed_url or fixed_img:
        print(f"  迁移修复: URL {fixed_url} 条, 图片 {fixed_img} 条")


# ── 主流程 ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("始祖鸟全站数据爬虫")
    print("=" * 60)

    load_image_map()

    # 加载现有数据
    existing = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f"现有数据: {len(existing)} 个产品")

    # 一次性修复历史数据
    print("\n🔧 修复历史数据...")
    migrate_existing(existing)

    # 按地区统计
    regions_count = Counter(p.get('region', 'unknown') for p in existing)
    print("现有地区分布:")
    for region, count in sorted(regions_count.items()):
        print(f"  {region}: {count}")

    print("\n开始爬取...")
    print("-" * 60)

    total_new = 0
    total_updated = 0

    for region_info in REGIONS:
        region_code = region_info['code']
        print(f"\n[{region_code.upper()}] {region_info['name']}")

        products = []
        for category in CATEGORIES:
            url = f"https://outlet.arcteryx.com/{region_code}/{region_info['lang']}/shop/{category}"
            print(f"  爬取 {category}: {url}")
            html = fetch_page(url)
            if html:
                found = extract_products_from_html(html, region_info, category)
                print(f"    找到 {len(found)} 个产品")
                products.extend(found)
            else:
                print(f"    获取失败")
            time.sleep(1)

        if products:
            new_count, updated_count = merge_products(existing, products)
            total_new += new_count
            total_updated += updated_count
            print(f"  合并完成: 新增 {new_count}, 更新 {updated_count}")
        else:
            print(f"  无数据")

        # 每个地区保存一次
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    # 校验
    validate_products(existing, {r['code'] for r in REGIONS})

    # 保存状态
    state = {
        "last_run":          datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_products":    len(existing),
        "new_this_run":      total_new,
        "updated_this_run":  total_updated,
        "products_per_region": dict(Counter(p.get('region', 'unknown') for p in existing)),
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"爬取完成! 总产品数: {len(existing)}, 新增: {total_new}, 更新: {total_updated}")
    print("=" * 60)


if __name__ == "__main__":
    main()
