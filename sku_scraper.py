#!/usr/bin/env python3
"""
Arc'teryx Outlet SKU 爬虫 (Playwright 版)
────────────────────────────────────────────
对每个商品详情页：
  1. 获取所有颜色选项（radio 按钮）
  2. 逐一点击颜色 → 抓取对应图片列表 + 尺码库存
  3. 每个颜色作为独立 SKU 写入 arcteryx_skus.json
  4. 同步更新 global_data.json / data.js 为"每色一条"格式

运行前请确保 Playwright Chromium 已安装:
    playwright install chromium

使用方法:
    python3 sku_scraper.py               # 抓全部（断点续抓）
    python3 sku_scraper.py --limit 20    # 只抓前 20 个 slug
    python3 sku_scraper.py --slug sabre-pant-8928  # 只抓指定商品
"""
import argparse
import asyncio
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ── 路径 ────────────────────────────────────────────────────────────────────
PROJECT = Path(__file__).parent
DATA_FILE    = PROJECT / "global_data.json"
SKU_FILE     = PROJECT / "arcteryx_skus.json"
ROOT_DATA_JS = PROJECT / "data.js"
H5_DATA_JS   = PROJECT / "h5" / "data.js"
PROGRESS_FILE = PROJECT / ".sku_progress.json"

# ── 每请求间隔（秒）──────────────────────────────────────────────────────────
DELAY_BETWEEN_PRODUCTS = 2.0
DELAY_BETWEEN_COLORS   = 0.8

# ── 工具函数 ─────────────────────────────────────────────────────────────────
def slug_from_url(url: str) -> str:
    return url.rstrip('/').split('/')[-1]

def normalize_color(color: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', '_', color).strip('_')

def sku_id(slug: str, color: str, region: str = '') -> str:
    base = f"{slug}_{normalize_color(color)}"
    return f"{base}_{region}" if region else base

def is_junk_color(color: str) -> bool:
    """Reject entries that look like mis-scraped size values or placeholders."""
    import re as _re
    c = (color or '').strip()
    if not c or c.lower() in ('unknown', 'default', ''):
        return True
    # Matches "size0", "size1", ..., "size12"
    if _re.match(r'^size\d+$', c, _re.IGNORECASE):
        return True
    return False

def load_json(path, default):
    if Path(path).exists():
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(path, data, indent=None):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


# ── 从 global_data.json 按 slug 整理，支持多地区 ──────────────────────────────
REGION_PRIORITY = ['us', 'ca', 'gb', 'au', 'de', 'fr', 'nl', 'se', 'at', 'ch', 'jp', 'it', 'es', 'dk', 'be']

def best_product_per_slug(products: list) -> dict:
    """返回 {slug: product_record}，每个商品只保留最优地区版本（用于确定访问哪个 URL）"""
    by_slug: dict = {}
    for p in products:
        s = slug_from_url(p.get('url', ''))
        if not s:
            continue
        if s not in by_slug:
            by_slug[s] = p
        else:
            existing = by_slug[s]
            try:
                pr_new = REGION_PRIORITY.index(p.get('region', ''))
            except ValueError:
                pr_new = 99
            try:
                pr_old = REGION_PRIORITY.index(existing.get('region', ''))
            except ValueError:
                pr_old = 99
            if pr_new < pr_old:
                by_slug[s] = p
    return by_slug


def all_regions_per_slug(products: list) -> dict:
    """返回 {slug: {region: product_record}}，每个 slug 保留所有地区版本的价格信息"""
    by_slug: dict = {}
    for p in products:
        s = slug_from_url(p.get('url', ''))
        region = p.get('region', '')
        if not s or not region:
            continue
        if s not in by_slug:
            by_slug[s] = {}
        existing = by_slug[s].get(region)
        # 同地区有多条时，保留折扣最高的（通常 sale_price 最低）
        if existing is None or p.get('discount_pct', 0) >= existing.get('discount_pct', 0):
            by_slug[s][region] = p
    return by_slug


# ── 页面抓取 ─────────────────────────────────────────────────────────────────
async def scrape_product(page, product: dict) -> list[dict]:
    """
    访问一个商品 URL，抓取所有颜色 SKU。
    返回 SKU 列表（可能为空，若页面加载失败）。
    """
    url = product['url']
    slug = slug_from_url(url)
    skus = []

    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=60_000)
        # 等待商品标题出现
        await page.wait_for_selector('h1, [data-testid="product-title"]', timeout=30_000)
        await asyncio.sleep(2.0)   # 等待动态渲染
    except PWTimeout:
        print(f"    ⚠ 超时: {url}")
        return []
    except Exception as e:
        print(f"    ⚠ 加载失败: {e}")
        return []

    # ── 读取基础信息 ────────────────────────────────────────────────────────
    base_info = await page.evaluate("""() => {
        const title = document.querySelector('h1')?.textContent?.trim() || '';
        // description
        const descEl = document.querySelector('[data-testid="product-description"] p, .product-description p, .pdp-description p');
        const desc = descEl?.textContent?.trim() || '';
        // prices (locale-aware: "1,299.99" / "1.299,00" / "9 990,00")
        const normalizeNum = (s) => {
            // 空格 + Swiss apostrophes (U+0027, U+2019) = 千分位
            s = s.replace(/[\s\u00a0\u0027\u2019]/g, '');
            const hasDot = s.includes('.'), hasComma = s.includes(',');
            if (hasDot && hasComma) {
                if (s.lastIndexOf(',') > s.lastIndexOf('.')) s = s.replace(/\./g, '').replace(',', '.');
                else s = s.replace(/,/g, '');
            } else if (hasComma) {
                const parts = s.split(',');
                if (parts.length === 2 && parts[1].length <= 2) s = parts[0] + '.' + parts[1];
                else s = parts.join('');
            } else if (hasDot) {
                const parts = s.split('.');
                if (parts.length >= 2 && parts[parts.length-1].length === 3 && parts[0].length <= 3) s = parts.join('');
            }
            return parseFloat(s);
        };
        const prices = [];
        document.querySelectorAll('[data-testid*="price"] [class*="price"], .price, [class*="Price"]').forEach(el => {
            const t = el.textContent.trim();
            const m = t.match(/\d+(?:[\s\u00a0.,\u0027\u2019]\d+)*/);
            if (m) {
                const v = normalizeNum(m[0]);
                if (v > 0 && v < 1000000) prices.push(v);
            }
        });
        // breadcrumb / outlet category
        const crumbs = [...document.querySelectorAll('nav a, [data-testid="breadcrumb"] a')]
            .map(a => a.textContent.trim()).filter(Boolean);
        return { title, desc, prices, crumbs };
    }""")

    # ── 颜色选项 ─────────────────────────────────────────────────────────────
    # Arc'teryx Outlet structure (as of 2026-04):
    #   button[data-colour-value="ColorName"]  — one per color swatch
    color_options = await page.evaluate("""() => {
        // Most specific: buttons with data-colour-value attribute
        const btns = [...document.querySelectorAll('button[data-colour-value]')];
        if (btns.length > 0) {
            return btns.map(b => ({
                value: b.getAttribute('data-colour-value'),
                selector: 'button[data-colour-value="' +
                           b.getAttribute('data-colour-value').replace(/"/g, '\\"') + '"]',
            })).filter(c => c.value && c.value.length > 0);
        }
        // Fallback: li[aria-label] in the colour fieldset (legend contains "colour")
        const colorFieldset = [...document.querySelectorAll('fieldset')].find(
            f => /colour|color/i.test(f.querySelector('legend')?.textContent || '')
        );
        if (colorFieldset) {
            return [...colorFieldset.querySelectorAll('li[aria-label]')].map(li => ({
                value: li.getAttribute('aria-label'),
                selector: null,
            })).filter(c => c.value && !c.value.startsWith('size'));
        }
        return [];
    }""")

    # 若无颜色选项，把当前页面当作单色处理
    if not color_options:
        color_options = [{"value": "Default", "inputId": None, "available": True}]

    print(f"    颜色数: {len(color_options)}")

    for color_opt in color_options:
        color_name = color_opt['value'].strip()
        if not color_name or color_name in ('', 'Default'):
            # 无法区分颜色，直接抓当前状态
            color_name = await page.evaluate("() => { const el = document.querySelector('[class*=\"color\"] legend, [data-testid*=\"color\"] legend'); return el?.textContent?.trim() || 'Unknown'; }")

        # ── 点击该颜色以切换 ──
        selector = color_opt.get('selector', '')
        if selector:
            try:
                await page.click(selector, timeout=4000)
                await asyncio.sleep(DELAY_BETWEEN_COLORS)
            except Exception:
                pass  # 若点击失败，用当前状态

        # ── 抓图片（从 hero gallery） ─────────────────────────────────────
        images = await page.evaluate("""() => {
            // Primary: hero gallery figures (authoritative product images)
            const hero = [...document.querySelectorAll(
                '[data-testid^="hero-gallery-figure"] img, [data-testid="hero-gallery"] img'
            )].map(i => i.src).filter(s => s && s.includes('imgix') && s.includes('details'));
            if (hero.length > 0) return [...new Set(hero)].slice(0, 8);
            // Fallback: any product imgix image
            return [...new Set(
                [...document.querySelectorAll('img')]
                    .map(i => i.src)
                    .filter(s => s && s.includes('imgix.net') && s.includes('details') && s.length > 60)
            )].slice(0, 8);
        }""")

        # ── 抓尺码与库存 ────────────────────────────────────────────────────
        # Arc'teryx Outlet structure:
        #   [data-testid="size-list"] > li > button[data-size-value][class*="no--stock"]
        size_data = await page.evaluate("""() => {
            const sizes = [];
            const size_stock = {};

            // Primary: data-testid="size-list"
            const sizeButtons = [...document.querySelectorAll(
                '[data-testid="size-list"] button[data-size-value], .qa--size-list button[data-size-value]'
            )];
            sizeButtons.forEach(btn => {
                const sz = btn.getAttribute('data-size-value') || btn.textContent.trim();
                if (!sz) return;
                sizes.push(sz);
                const cls = btn.className || '';
                if (cls.includes('no--stock') || cls.includes('out-of-stock') ||
                    btn.disabled || btn.getAttribute('aria-disabled') === 'true') {
                    size_stock[sz] = 'out_of_stock';
                } else if (cls.includes('low-stock') || cls.includes('low_stock')) {
                    size_stock[sz] = 'low_stock';
                } else {
                    size_stock[sz] = 'in_stock';
                }
            });

            // Fallback: second fieldset buttons
            if (sizes.length === 0) {
                const fallback = [...document.querySelectorAll(
                    'fieldset:nth-of-type(2) button[role="radio"]'
                )];
                fallback.forEach(btn => {
                    const sz = btn.textContent.trim() || btn.getAttribute('aria-label');
                    if (!sz || sz.length > 10) return;
                    sizes.push(sz);
                    size_stock[sz] = btn.className.includes('no--stock') ? 'out_of_stock' : 'in_stock';
                });
            }

            return { sizes: [...new Set(sizes)], size_stock };
        }""")

        # ── 主图 ────────────────────────────────────────────────────────────
        primary_image = images[0] if images else product.get('image_url', '')

        # ── 发售季度 (Arc'teryx image filename convention: F25-/S25-/W25-) ──
        # F/W = Fall/Winter, S = Spring, followed by 2-digit year.
        release_year = None
        release_season = None  # "Fall" | "Spring" | "Winter"
        for u in [primary_image] + list(images or []):
            m = re.search(r'/([FSWfsw])(\d{2})[-_]', u or "")
            if m:
                release_year = 2000 + int(m.group(2))
                release_season = {'F':'Fall','W':'Winter','S':'Spring'}[m.group(1).upper()]
                break

        sku = {
            "sku_id":        sku_id(slug, color_name),
            "model":         product.get('model', ''),
            "full_name":     product.get('full_name', ''),
            "color":         color_name,
            "sizes":         size_data.get('sizes', []),
            "size_stock":    size_data.get('size_stock', {}),
            "original_price": product.get('original_price', 0),
            "sale_price":    product.get('sale_price', 0),
            "discount_pct":  product.get('discount_pct', 0),
            "currency":      product.get('currency', ''),
            "symbol":        product.get('symbol', ''),
            "gender":        product.get('gender', ''),
            "region":        product.get('region', ''),
            "region_name":   product.get('region_name', ''),
            "category":      product.get('category', ''),
            "url":           url,
            "image_url":     primary_image,
            "images":        images,
            "description":   base_info.get('desc', '') or product.get('description', ''),
            "release_year":  release_year,
            "release_season": release_season,
            "last_updated":  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        skus.append(sku)
        print(f"      + {color_name[:40]} | {len(images)} imgs | {len(size_data['sizes'])} sizes")

    return skus


# ── 主异步任务 ────────────────────────────────────────────────────────────────
async def run(args):
    # 加载现有数据
    products_raw = load_json(DATA_FILE, [])
    product_map   = best_product_per_slug(products_raw)   # {slug: best_product} 用于访问页面
    regions_map   = all_regions_per_slug(products_raw)    # {slug: {region: product}} 用于展开多地区
    print(f"商品总数（去重后）: {len(product_map)}")
    print(f"地区版本总数: {sum(len(v) for v in regions_map.values())}")

    # 加载已有 SKU（支持断点续抓）
    existing_skus: list = load_json(SKU_FILE, [])
    done_slugs: set = set()
    if os.path.exists(PROGRESS_FILE):
        done_slugs = set(load_json(PROGRESS_FILE, []))
    print(f"已完成 slug: {len(done_slugs)}")

    # 过滤目标
    if args.slug:
        targets = {args.slug: product_map[args.slug]} if args.slug in product_map else {}
    else:
        targets = {s: p for s, p in product_map.items() if s not in done_slugs}
    if args.limit:
        keys = list(targets.keys())[:args.limit]
        targets = {k: targets[k] for k in keys}

    print(f"待抓取: {len(targets)} 个商品\n")

    if not targets:
        print("无待抓取商品，退出。")
        # 仍输出当前 SKU 总数
        print(f"\n✅ 抓取完成! 总 SKU: {len(existing_skus)}")
        return

    # sku_id 格式：{slug}_{color}_{region}
    new_skus_map = {s['sku_id']: s for s in existing_skus if s.get('sku_id')}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage'],
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='zh-CN',
        )
        page = await context.new_page()

        processed = 0
        for slug, product in targets.items():
            processed += 1
            print(f"[{processed}/{len(targets)}] {slug} ({product.get('region','')})")
            skus = await scrape_product(page, product)

            if skus:
                # 获取该 slug 的所有地区价格信息
                region_variants = regions_map.get(slug, {})

                added = 0
                for sku in skus:
                    if is_junk_color(sku.get('color', '')):
                        print(f"    ⚠ 跳过无效颜色: {sku.get('color','')!r}")
                        continue

                    if region_variants:
                        # 方案B：为每个地区生成一条 SKU 记录
                        for region_code, region_product in region_variants.items():
                            sid = sku_id(slug, sku['color'], region_code)
                            new_skus_map[sid] = {
                                **sku,
                                "sku_id":         sid,
                                "region":         region_code,
                                "region_name":    region_product.get('region_name', ''),
                                "original_price": region_product.get('original_price') or sku.get('original_price', 0),
                                "sale_price":     region_product.get('sale_price')     or sku.get('sale_price', 0),
                                "sale_price_max": region_product.get('sale_price_max') or sku.get('sale_price', 0),
                                "discount_pct":   region_product.get('discount_pct')   or sku.get('discount_pct', 0),
                                "currency":       region_product.get('currency', sku.get('currency', '')),
                                "symbol":         region_product.get('symbol',   sku.get('symbol', '')),
                                "url":            region_product.get('url',      sku.get('url', '')),
                            }
                            added += 1
                    else:
                        # 无多地区数据，退回单条
                        sid = sku_id(slug, sku['color'], sku.get('region', ''))
                        new_skus_map[sid] = {**sku, "sku_id": sid}
                        added += 1

                # 标记完成
                done_slugs.add(slug)
                save_json(PROGRESS_FILE, list(done_slugs))

                # 增量保存 SKU 文件
                save_json(SKU_FILE, list(new_skus_map.values()), indent=2)
                print(f"  → +{added} 条（{len(region_variants)} 地区 × 颜色），共 {len(new_skus_map)} SKU")
            else:
                print(f"  → 无法提取 SKU（页面可能需要认证或已下架）")

            if processed < len(targets):
                await asyncio.sleep(DELAY_BETWEEN_PRODUCTS)

        await browser.close()

    final_skus = list(new_skus_map.values())
    save_json(SKU_FILE, final_skus, indent=2)
    print(f"\n✅ 抓取完成! 总 SKU: {len(final_skus)}")

    # ── 用 SKU 数据更新 data.js（每色一条，含多图） ──────────────────────────
    if args.update_data:
        expand_data_js(final_skus, products_raw)


def expand_data_js(skus: list, fallback_products: list):
    """
    把所有 SKU 扁平化为 data.js 格式（每个颜色独立一条）。
    若某商品无 SKU（未抓到详情），保留原始记录。
    """
    slug_has_sku = set(slug_from_url(s['url']) for s in skus)

    # SKU → PRODUCTS 格式
    def sku_to_product(s):
        return {
            "model":          s['model'],
            "full_name":      s['full_name'],
            "description":    s['description'],
            "category":       s['category'],
            "original_price": s['original_price'],
            "sale_price":     s['sale_price'],
            "sale_price_max": s['sale_price'],
            "discount_pct":   s['discount_pct'],
            "currency":       s['currency'],
            "symbol":         s['symbol'],
            "gender":         s['gender'],
            "region":         s['region'],
            "region_name":    s['region_name'],
            "url":            s['url'],
            "image_url":      s['image_url'],
            "last_updated":   s['last_updated'],
            "colors":         [s['color']],
            "sizes":          s['sizes'],
            "size_stock":     s['size_stock'],
            "outlet_category":"",
            "local_image":    "",
            # SKU-specific extras
            "color":          s['color'],
            "images":         s['images'],
            "sku_id":         s['sku_id'],
        }

    expanded = [sku_to_product(s) for s in skus if not is_junk_color(s.get('color', ''))]

    # 补充未抓到 SKU 的原始商品
    fallback_map = best_product_per_slug(fallback_products)
    for slug, p in fallback_map.items():
        if slug not in slug_has_sku:
            expanded.append(p)

    print(f"\n📦 写入 data.js: {len(expanded)} 条（{len(skus)} SKU + {len(expanded)-len(skus)} 无SKU原始条目）")
    js_payload = f"const PRODUCTS = {json.dumps(expanded, ensure_ascii=False)};\n"
    with open(ROOT_DATA_JS, 'w', encoding='utf-8') as f:
        f.write(js_payload)
    with open(H5_DATA_JS, 'w', encoding='utf-8') as f:
        f.write(js_payload)
    save_json(DATA_FILE, expanded, indent=2)
    print("✅ data.js / global_data.json 已更新（每色一条）")


# ── 入口 ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Arc'teryx Outlet SKU Scraper")
    parser.add_argument('--limit',  type=int,  default=0,     help="只抓前 N 个商品（0=全部）")
    parser.add_argument('--slug',   type=str,  default='',    help="只抓指定 slug")
    parser.add_argument('--update-data', action='store_true', help="抓完后更新 data.js")
    parser.add_argument('--reset',  action='store_true',      help="清除进度，从头开始")
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        if os.path.exists(SKU_FILE):
            os.remove(SKU_FILE)
        print("进度已重置（进度文件 + SKU 文件已清空，将从头全量抓取）")

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
