#!/usr/bin/env python3
"""
Arc'teryx 全球 Outlet 数据采集器 (Playwright 版)
────────────────────────────────────────────────
抓取 outlet.arcteryx.com 各区域站点商品列表页：
  1. 遍历 15 个地区 × (mens + womens) 分类页
  2. 自动滚动加载全部商品瓦片
  3. 提取商品 URL、名称、价格、折扣等
  4. 合并写入 global_data.json（保留已有数据，新增/更新条目）

运行:
    python3 global_scraper.py           # 全量抓取
    python3 global_scraper.py --dry-run # 只抓第一个地区，不写文件
    python3 global_scraper.py --region us ca gb  # 只抓指定地区
"""

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ========== 配置 ==========
PROJECT   = Path(__file__).parent
DATA_FILE = PROJECT / "global_data.json"

REGIONS = [
    {"code": "us", "lang": "en", "name": "美国",   "currency": "USD", "symbol": "$"},
    {"code": "ca", "lang": "en", "name": "加拿大",  "currency": "CAD", "symbol": "C$"},
    {"code": "gb", "lang": "en", "name": "英国",    "currency": "GBP", "symbol": "£"},
    {"code": "au", "lang": "en", "name": "澳大利亚","currency": "AUD", "symbol": "A$"},
    {"code": "de", "lang": "de", "name": "德国",    "currency": "EUR", "symbol": "€"},
    {"code": "fr", "lang": "fr", "name": "法国",    "currency": "EUR", "symbol": "€"},
    {"code": "nl", "lang": "en", "name": "荷兰",    "currency": "EUR", "symbol": "€"},
    {"code": "se", "lang": "en", "name": "瑞典",    "currency": "SEK", "symbol": "kr"},
    {"code": "at", "lang": "de", "name": "奥地利",  "currency": "EUR", "symbol": "€"},
    {"code": "ch", "lang": "de", "name": "瑞士",    "currency": "CHF", "symbol": "CHF"},
    {"code": "jp", "lang": "ja", "name": "日本",    "currency": "JPY", "symbol": "¥"},
    {"code": "it", "lang": "it", "name": "意大利",  "currency": "EUR", "symbol": "€"},
    {"code": "es", "lang": "es", "name": "西班牙",  "currency": "EUR", "symbol": "€"},
    {"code": "dk", "lang": "da", "name": "丹麦",    "currency": "DKK", "symbol": "kr"},
    {"code": "be", "lang": "nl", "name": "比利时",  "currency": "EUR", "symbol": "€"},
]

GENDERS = ["mens", "womens"]

# 每次滚动后等待时间（秒）
SCROLL_PAUSE = 2.5
# 最多滚动轮次（每轮滚到底部）
MAX_SCROLL_ROUNDS = 40
# 两个地区之间间隔
REGION_PAUSE = 3.0


# ========== 工具函数 ==========

def load_json(path, default):
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]

def parse_price(text: str) -> float:
    """从含货币符号的字符串中提取数字，日元去逗号"""
    m = re.search(r"[\d,]+(?:\.\d+)?", text.replace("\u00a0", ""))
    if not m:
        return 0.0
    return float(m.group().replace(",", ""))

def infer_category(name: str, url: str) -> str:
    u = url.lower()
    n = (name or "").lower()
    if "veilance" in u or "veilance" in n:
        return "Veilance商务系列"
    if any(x in u for x in ["shell-jacket", "hardshell", "softshell"]):
        return "硬壳冲锋衣"
    if any(x in u for x in ["insulated", "down-jacket", "hoody"]):
        return "保暖夹克"
    if any(x in u for x in ["/pant", "-pant", "bib-"]):
        return "裤装"
    if any(x in u for x in ["shoe", "boot", "footwear", "sandal"]):
        return "鞋类"
    if any(x in u for x in ["/pack", "-pack", "backpack", "bag", "tote"]):
        return "背包"
    if any(x in u for x in ["base-layer", "rho-", "-rho", "phase-", "merino"]):
        return "排汗内衣"
    if any(x in u for x in ["fleece", "polar", "fortrez"]):
        return "抓绒/摇粒绒"
    if any(x in u for x in ["vest", "gilet"]):
        return "背心"
    if any(x in u for x in ["shirt", "polo", "tee", "top-"]):
        return "上衣/T恤"
    if any(x in u for x in ["dress", "skirt"]):
        return "裙装"
    if any(x in u for x in ["hat", "cap", "headwear", "glove", "sock", "buff"]):
        return "配件"
    return "其他"


# ========== 主抓取逻辑 ==========

async def dismiss_popups(page):
    """关闭 GDPR / Cookie 同意弹窗"""
    # Arc'teryx outlet uses 'Continue' for cookie consent (OneTrust-based)
    selectors = [
        "button:has-text('Continue')",       # Arc'teryx outlet primary
        "button:has-text('Continuer')",       # French
        "button:has-text('Weiter')",          # German
        "button:has-text('Continua')",        # Italian
        "button:has-text('Continuar')",       # Spanish
        "button:has-text('Doorgaan')",        # Dutch
        "button:has-text('Fortsæt')",         # Danish
        "button:has-text('続ける')",           # Japanese
        "button[id*='accept']",
        "button[class*='accept']",
        "#onetrust-accept-btn-handler",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('Akzeptieren')",
        "button:has-text('同意')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click(timeout=1000)
                await asyncio.sleep(1.0)
                return  # Only need to dismiss once
        except Exception:
            pass


async def scroll_to_load_all(page) -> int:
    """
    反复滚动到页面底部，直到：
    - 商品数量不再增长，或
    - 达到最大滚动轮次
    返回最终商品瓦片数量。
    """
    prev_count = 0
    stable_rounds = 0

    for i in range(MAX_SCROLL_ROUNDS):
        # 滚动到底部
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(SCROLL_PAUSE)

        # 也尝试点击"加载更多"按钮
        try:
            load_more = page.locator(
                "button:has-text('Load more'), button:has-text('Show more'), "
                "button:has-text('Mehr laden'), button:has-text('Voir plus'), "
                "button:has-text('もっと見る'), [data-testid='load-more']"
            ).first
            if await load_more.is_visible(timeout=500):
                await load_more.click(timeout=500)
                await asyncio.sleep(SCROLL_PAUSE)
        except Exception:
            pass

        # 数商品数 — Arc'teryx outlet links are /shop/mens/ or /shop/womens/ (no region prefix)
        count = await page.evaluate("""() => {
            const links = document.querySelectorAll(
                'a[href*="/shop/mens/"], a[href*="/shop/womens/"]'
            );
            const seen = new Set();
            links.forEach(a => {
                const url = a.href.split('?')[0];
                // Only count actual product pages (slug has a number or is long enough)
                const slug = url.split('/').pop();
                if (slug && slug.length > 5) seen.add(url);
            });
            return seen.size;
        }""")

        if count == prev_count:
            stable_rounds += 1
            if stable_rounds >= 4:
                break  # 连续4轮没变化，认为加载完毕
        else:
            stable_rounds = 0
            prev_count = count

        if count > 0:
            print(f"      滚动轮 {i+1}: {count} 个商品链接", flush=True)

    return prev_count


async def extract_tiles(page, region: dict, gender: str) -> list:
    """从已完全加载的列表页提取商品瓦片数据"""
    return await page.evaluate("""(args) => {
        const { regionCode, regionLang, regionName, currency, symbol, gender } = args;
        const results = [];
        const seen = new Set();

        // Arc'teryx outlet listing page links are /shop/mens/{slug} (no region prefix)
        const genderPath = gender === 'mens' ? '/shop/mens/' : '/shop/womens/';
        const links = [...document.querySelectorAll('a[href*="' + genderPath + '"]')];

        links.forEach(a => {
            let rawUrl = (a.href || '').split('?')[0];
            if (!rawUrl) return;
            const slug = rawUrl.split('/').pop();
            if (!slug || slug.length < 4) return;
            // Normalize: add region/lang prefix if missing
            // Raw link: https://outlet.arcteryx.com/shop/mens/{slug}
            // Needed:   https://outlet.arcteryx.com/{code}/{lang}/shop/mens/{slug}
            let url = rawUrl;
            if (!rawUrl.includes('/' + regionCode + '/')) {
                // Replace arcteryx.com/shop/ → arcteryx.com/{code}/{lang}/shop/
                url = rawUrl.replace('outlet.arcteryx.com/shop/',
                    'outlet.arcteryx.com/' + regionCode + '/' + regionLang + '/shop/');
            }
            if (seen.has(url)) return;
            seen.add(url);

            // 尝试找到包含价格的最近祖先容器
            let container = a;
            for (let depth = 0; depth < 6; depth++) {
                const p = container.parentElement;
                if (!p) break;
                container = p;
                if (container.querySelector('[class*="price"], [data-testid*="price"]')) break;
            }

            const text = container.textContent || a.textContent || '';

            // 提取所有价格数字（locale-aware: 支持 "1,299.99" / "1.299,00" / "9 990,00" / "1 299 kr" / "1'099.00" Swiss）
            const normalizeNum = (s) => {
                // 空格类 + Swiss apostrophes (U+0027, U+2019) 视作千分位分隔符
                s = s.replace(/[\s\u00a0\u0027\u2019]/g, '');
                const hasDot = s.includes('.'), hasComma = s.includes(',');
                if (hasDot && hasComma) {
                    // 两种分隔符都有 → 最后出现的是小数点
                    if (s.lastIndexOf(',') > s.lastIndexOf('.')) s = s.replace(/\./g, '').replace(',', '.');
                    else s = s.replace(/,/g, '');
                } else if (hasComma) {
                    const parts = s.split(',');
                    const last = parts[parts.length - 1];
                    if (parts.length === 2 && last.length <= 2) s = parts[0] + '.' + last; // 欧式小数
                    else s = parts.join(''); // 千分位
                } else if (hasDot) {
                    const parts = s.split('.');
                    const last = parts[parts.length - 1];
                    // "1.299" (EUR 千分位) vs "9.99" (USD 小数)
                    if (parts.length >= 2 && last.length === 3 && parts[0].length <= 3) s = parts.join('');
                }
                return parseFloat(s);
            };
            const allNums = [...text.matchAll(/\d+(?:[\s\u00a0.,\u0027\u2019]\d+)*/g)]
                .map(m => normalizeNum(m[0]))
                .filter(n => n > 0 && n < 1000000);

            // 去重并排序
            const uniqueNums = [...new Set(allNums)].sort((a, b) => a - b);

            // 通常规律：较大的是原价，较小的是售价
            // 但必须有合理折扣（售价 < 原价 * 0.99）
            let originalPrice = 0, salePrice = 0, discountPct = 0;
            if (uniqueNums.length >= 2) {
                // 找最常见的两个价格对 (原价 > 售价)
                // 尝试所有对，取折扣率最合理(10~90%)的
                for (let i = uniqueNums.length - 1; i >= 1; i--) {
                    for (let j = i - 1; j >= 0; j--) {
                        const orig = uniqueNums[i];
                        const sale = uniqueNums[j];
                        const disc = Math.round((1 - sale / orig) * 100);
                        if (disc >= 10 && disc <= 90) {
                            originalPrice = orig;
                            salePrice = sale;
                            discountPct = disc;
                            break;
                        }
                    }
                    if (salePrice > 0) break;
                }
            }
            if (salePrice === 0 && uniqueNums.length === 1) {
                salePrice = uniqueNums[0];
            }

            // 提取商品名称
            // 优先找 <img alt="">, <h2>, <h3>, [data-testid*="name"], [class*="name"]
            let name = '';
            const imgEl = container.querySelector('img[alt]');
            if (imgEl) name = imgEl.getAttribute('alt') || '';
            if (!name) {
                const hEl = container.querySelector('h2, h3, h4, [class*="product-name"], [class*="ProductName"], [data-testid*="name"]');
                if (hEl) name = hEl.textContent.trim();
            }
            if (!name) {
                // 用 URL slug 反推
                const slug2 = url.split('/').pop() || '';
                name = slug2.replace(/-\d+$/, '').replace(/-/g, ' ')
                    .replace(/\b\w/g, c => c.toUpperCase());
            }

            // 提取主图
            let imageUrl = '';
            const imgTag = container.querySelector('img[src*="imgix"], img[src*="arcteryx"]');
            if (imgTag) imageUrl = imgTag.src || '';

            // 推断性别
            const genderVal = url.includes('/mens/') ? 'men' : 'women';

            // 推断 model（去掉 Men's/Women's 后缀）
            const cleanName = name.replace(/\s*(?:Men's|Women's|Mens|Womens)\s*$/i, '').trim();
            const modelMatch = cleanName.match(/^([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})/);
            const model = modelMatch ? modelMatch[1] : cleanName;

            results.push({
                url,
                full_name: name || cleanName,
                model: model || cleanName,
                description: '',
                gender: genderVal,
                region: regionCode,
                region_name: regionName,
                currency,
                symbol,
                original_price: originalPrice,
                sale_price: salePrice,
                sale_price_max: salePrice,
                discount_pct: discountPct,
                category: '',       // sku_scraper 会重新填充
                outlet_category: '',
                image_url: imageUrl,
                colors: [],
                sizes: [],
                size_stock: {},
                images: [],
                local_image: '',
                color: '',
                sku_id: '',
                last_updated: new Date().toISOString().replace('T', ' ').substring(0, 19),
            });
        });

        return results;
    }""", {"regionCode": region["code"], "regionLang": region["lang"],
           "regionName": region["name"],
           "currency": region["currency"], "symbol": region["symbol"],
           "gender": gender})


async def scrape_region(browser, region: dict, genders: list, dry_run: bool) -> list:
    """抓取单个地区的所有性别分类页"""
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        viewport={"width": 1440, "height": 900},
    )
    page = await context.new_page()
    # Shorter navigation timeout to avoid hanging on slow regions
    page.set_default_navigation_timeout(45_000)
    page.set_default_timeout(10_000)
    all_products = []

    try:
        for gender in genders:
            # Arc'teryx outlet listing page is at /c/{gender}, not /shop/{gender}
            url = f"https://outlet.arcteryx.com/{region['code']}/{region['lang']}/c/{gender}"
            print(f"  → {url}", flush=True)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            except PWTimeout:
                print(f"    ⚠ 超时，跳过", flush=True)
                continue
            except Exception as e:
                print(f"    ⚠ 导航失败: {e}", flush=True)
                continue

            # 等待页面基本内容加载
            await asyncio.sleep(4.0)
            await dismiss_popups(page)
            await asyncio.sleep(2.0)

            # 等待商品出现 — product links on listing page are /shop/{gender}/
            try:
                await page.wait_for_selector(
                    f'a[href*="/shop/{gender}/"]', timeout=25_000
                )
            except PWTimeout:
                print(f"    ⚠ 未发现商品链接（25s超时），跳过", flush=True)
                continue

            # 滚动加载全部
            total = await scroll_to_load_all(page)
            print(f"    ✓ 加载完毕，共 {total} 个商品链接", flush=True)

            # 提取商品瓦片
            tiles = await extract_tiles(page, region, gender)

            # 补充 category（基于 URL 推断）
            for t in tiles:
                if not t["category"]:
                    t["category"] = infer_category(t["full_name"], t["url"])

            # 过滤掉分类导航链接（没有有效价格且 slug 太短）
            valid = []
            for t in tiles:
                slug = slug_from_url(t["url"])
                # 商品 slug 通常 > 5 chars 且不是纯分类名
                if len(slug) > 5 and t.get("sale_price", 0) > 0:
                    valid.append(t)
                elif len(slug) > 5:
                    # 即使价格为0也保留（sku_scraper 会重新抓详情）
                    valid.append(t)

            print(f"    ✓ 提取 {len(valid)} 个有效商品（{gender}）", flush=True)
            all_products.extend(valid)

            if dry_run:
                break  # dry-run 只抓第一个 gender

        return all_products

    finally:
        await context.close()


# ========== 主函数 ==========

async def run(args):
    # 确定要抓取的地区
    if args.region:
        regions = [r for r in REGIONS if r["code"] in args.region]
        if not regions:
            print(f"[ERROR] 未知地区代码: {args.region}", file=sys.stderr)
            sys.exit(1)
    else:
        regions = REGIONS

    if args.start_from and not args.region:
        codes = [r["code"] for r in REGIONS]
        if args.start_from in codes:
            start_idx = codes.index(args.start_from)
            regions = REGIONS[start_idx:]
            print(f"[global_scraper] 从 {args.start_from} 开始，跳过前 {start_idx} 个地区")

    if args.dry_run:
        regions = regions[:1]
        print("[dry-run] 只抓第一个地区，不写文件")

    # 加载现有数据（用于合并）
    existing: list = load_json(DATA_FILE, [])
    # 构建 {url: index} 索引，用于快速更新
    existing_by_url: dict = {p["url"]: i for i, p in enumerate(existing)}
    print(f"[global_scraper] 现有 {len(existing)} 条记录")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        total_new = 0
        total_updated = 0

        for region in regions:
            print(f"\n🌍 [{region['code'].upper()}] {region['name']} ({region['currency']})", flush=True)

            try:
                products = await scrape_region(
                    browser, region,
                    genders=GENDERS,
                    dry_run=args.dry_run,
                )
            except Exception as e:
                print(f"  ⚠ 地区抓取失败: {e}", flush=True)
                products = []

            for p in products:
                url = p["url"]
                if url in existing_by_url:
                    # 更新现有条目（保留 sku_scraper 已填充的字段）
                    idx = existing_by_url[url]
                    old = existing[idx]
                    # 只更新价格、折扣等动态字段
                    old.update({
                        "original_price": p["original_price"] or old.get("original_price", 0),
                        "sale_price":     p["sale_price"]     or old.get("sale_price", 0),
                        "sale_price_max": p["sale_price_max"] or old.get("sale_price_max", 0),
                        "discount_pct":   p["discount_pct"]   or old.get("discount_pct", 0),
                        "image_url":      p["image_url"]      or old.get("image_url", ""),
                        "last_updated":   p["last_updated"],
                    })
                    existing[idx] = old
                    total_updated += 1
                else:
                    # 新商品
                    existing.append(p)
                    existing_by_url[url] = len(existing) - 1
                    total_new += 1

            print(f"  → 新增 {total_new} / 更新 {total_updated}", flush=True)

            # ── 每完成一个地区立即保存（防止中途崩溃丢失数据）──
            if not args.dry_run:
                save_json(DATA_FILE, existing)
                print(f"  💾 已保存 global_data.json ({len(existing)} 条)", flush=True)

            if not args.dry_run and len(regions) > 1:
                await asyncio.sleep(REGION_PAUSE)

        await browser.close()

    print(f"\n{'='*60}")
    print(f"✅ 全球抓取完成！")
    print(f"   新增商品: {total_new}")
    print(f"   更新商品: {total_updated}")
    print(f"   总计记录: {len(existing)}")
    print(f"{'='*60}")

    if args.dry_run:
        print("[dry-run] 不写文件，前3条样本:")
        new_items = [p for p in existing if p not in load_json(DATA_FILE, [])]
        import pprint
        pprint.pprint((new_items or existing)[:3])
        return

    save_json(DATA_FILE, existing)
    print(f"[global_scraper] 已写入 {DATA_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Arc'teryx 全球 Outlet 商品列表爬虫")
    parser.add_argument("--dry-run", action="store_true",
                        help="只抓第一个地区，不写 global_data.json")
    parser.add_argument("--region", nargs="+", metavar="CODE",
                        help="只抓指定地区代码，如 --region us ca gb")
    parser.add_argument("--start-from", metavar="CODE",
                        help="从指定地区代码开始（跳过之前的地区）")
    args = parser.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
