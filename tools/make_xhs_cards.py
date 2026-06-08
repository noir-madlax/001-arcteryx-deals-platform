#!/usr/bin/env python3
"""每日小红书爆款卡片生成器
从 Supabase 拉今日 top N 折扣 → 生成 1080×1440 PNG 首图.

用法:
    python3 tools/make_xhs_cards.py [N=5]

产物:
    xhs_cards/YYYY-MM-DD_{i:02d}_{slug}.png

每张卡片:
- 顶部: -XX% 巨大红字 + 地区/平台标签
- 中部: 商品图 (居中, 自适应)
- 底部: 商品名 + 折扣价/原价 (划线) + 二维码到详情页
"""
import os, sys, json, re, io
from pathlib import Path
from datetime import datetime, timezone

try:
    import requests
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import qrcode
except ImportError:
    sys.exit("需要: pip install Pillow qrcode requests")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "xhs_cards"

SUPA_URL = "https://bupqagkrcvrezjkdbald.supabase.co/rest/v1"
ANON = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHFhZ2tyY3ZyZXpqa2RiYWxkIiwicm9sZSI6ImFub24i"
        "LCJpYXQiOjE3NzY0NDU1NTMsImV4cCI6MjA5MjAyMTU1M30."
        "oszdUJIEKMCvpD9XFzTYTCYXj078uwjzFx84tfStfRU")

# ── Font (macOS PingFang, fallback STHeiti) ─────────────────────────────────
FONT_CANDIDATES = [
    "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if not FONT_PATH:
    sys.exit("未找到中文字体, 请装 PingFang 或 STHeiti")

def font(size, weight="medium"):
    """加载中文字体. PingFang.ttc 索引: 0=Thin 1=Light 3=Regular 5=Medium 7=Semibold 9=Bold"""
    idx_map = {"thin": 0, "light": 1, "regular": 3, "medium": 5, "semibold": 7, "bold": 9}
    idx = idx_map.get(weight, 5)
    try:
        return ImageFont.truetype(FONT_PATH, size, index=idx)
    except OSError:
        return ImageFont.truetype(FONT_PATH, size)


# ── Brand-friendly palette ──────────────────────────────────────────────────
BG       = (250, 248, 244)  # 浅米
ACCENT   = (212, 47, 47)    # 折扣红
DARK     = (28, 28, 30)     # 主文字
SUB      = (130, 130, 138)  # 次文字
GREEN    = (22, 100, 80)    # 始祖鸟绿

DEALER_LABEL = {
    "arcteryx_outlet": "官方 Outlet",
    "ssense":          "SSENSE",
    "mec":             "MEC",
    "rei":             "REI",
    "evo":             "EVO",
}

REGION_FLAG = {
    "us":"🇺🇸","ca":"🇨🇦","gb":"🇬🇧","de":"🇩🇪","fr":"🇫🇷","nl":"🇳🇱",
    "at":"🇦🇹","ch":"🇨🇭","it":"🇮🇹","es":"🇪🇸","be":"🇧🇪","dk":"🇩🇰",
    "se":"🇸🇪","no":"🇳🇴","fi":"🇫🇮","ie":"🇮🇪","pl":"🇵🇱","jp":"🇯🇵","au":"🇦🇺",
}


# ── Data fetch ──────────────────────────────────────────────────────────────
def fetch_top(n=5, min_disc=30, today_only=True):
    """拉今日 (或近 N 天) discount_pct >= min_disc 的 top N, 去重 model+region"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = f"{SUPA_URL}/products?select=*&discount_pct=gte.{min_disc}"
    if today_only:
        base += f"&last_updated=gte.{today}T00:00:00"
    base += f"&order=discount_pct.desc&limit={n*5}"  # over-fetch 留 dedupe 余量
    r = requests.get(base, headers={"apikey": ANON, "Authorization": f"Bearer {ANON}"}, timeout=15)
    r.raise_for_status()
    rows = r.json()
    # dedupe by model (不同区域同款只取折扣最大那个 / 第一个出现的)
    seen, out = set(), []
    for row in rows:
        key = (row.get("model","").lower().strip(), row.get("region",""))
        if key in seen: continue
        # 进一步: 同一 model 不同 region 也只取一次 (取折扣最大)
        m = row.get("model","").lower().strip()
        if any(o.get("model","").lower().strip() == m for o in out):
            continue
        seen.add(key)
        out.append(row)
        if len(out) >= n: break
    return out


# ── Card composer ───────────────────────────────────────────────────────────
W, H = 1080, 1440

def fetch_image(url, max_side=820, retries=3):
    """REI/部分 CDN 偶发慢, 加 retry + 完整浏览器 UA."""
    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0 Safari/537.36"),
        "Accept": "image/avif,image/webp,image/png,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for i in range(retries):
        try:
            r = requests.get(url, timeout=20, headers=headers)
            if r.status_code != 200:
                continue
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img.thumbnail((max_side, max_side), Image.LANCZOS)
            return img
        except Exception as e:
            if i == retries - 1:
                print(f"  [img-err after {retries}x] {type(e).__name__}: {str(e)[:60]}")
    return None

def make_qr(url, box_size=4):
    qr = qrcode.QRCode(box_size=box_size, border=1, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(url)
    qr.make()
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

def clean_model_name(s):
    if not s: return ""
    s = re.sub(r"^Arc'?teryx\s*", "", s, flags=re.I)
    s = re.sub(r"\s*-\s*(Men's|Women's|Unisex).*$", "", s, flags=re.I)
    return s.strip()

def fmt_price(symbol, val):
    if val is None: return ""
    s = symbol or "$"
    if val == int(val):
        return f"{s}{int(val)}"
    return f"{s}{val:.2f}".rstrip("0").rstrip(".")

def make_card(item, idx, total, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # ── 装饰: 左上角小条纹 ──
    d.rectangle([(0, 0), (12, H)], fill=GREEN)

    # ── 顶部: 标题 ──
    d.text((W//2, 80), f"今日鸟厂炸价 · {idx}/{total}",
           fill=GREEN, font=font(38, "semibold"), anchor="mm")

    # ── 大折扣 ──
    disc = item.get("discount_pct") or 0
    d.text((W//2, 230), f"-{disc}%",
           fill=ACCENT, font=font(200, "bold"), anchor="mm")

    # ── 地区 + 平台 ──
    flag = REGION_FLAG.get(item.get("region",""), "🌍")
    region_cn = item.get("region_name") or item.get("region","").upper()
    dealer = DEALER_LABEL.get(item.get("dealer",""), item.get("dealer","").upper())
    tag = f"{flag}  {region_cn}  ·  {dealer}"
    d.text((W//2, 365), tag, fill=SUB, font=font(36, "regular"), anchor="mm")

    # ── 中部: 商品图 ──
    img_url = item.get("image_url")
    product_img = fetch_image(img_url, max_side=720) if img_url else None
    if product_img:
        pw, ph = product_img.size
        px, py = (W - pw) // 2, 440
        img.paste(product_img, (px, py))
    else:
        d.rectangle([(180, 440), (900, 1080)], outline=SUB, width=2)
        d.text((W//2, 760), "(无商品图)", fill=SUB, font=font(40), anchor="mm")

    # ── 底部分隔 ──
    d.line([(80, 1190), (W-80, 1190)], fill=(220, 220, 218), width=2)

    # ── 商品名 ──
    name = clean_model_name(item.get("full_name") or item.get("model") or "")
    if name:
        if len(name) > 22:
            name = name[:22] + "…"
        d.text((W//2, 1240), name, fill=DARK, font=font(46, "semibold"), anchor="mm")

    # ── 价格行 ──
    sym = item.get("symbol", "$")
    sale_txt = fmt_price(sym, item.get("sale_price"))
    orig_txt = fmt_price(sym, item.get("original_price"))

    sale_font = font(72, "bold")
    orig_font = font(36, "regular")
    sale_w = d.textlength(sale_txt, font=sale_font)
    orig_w = d.textlength(orig_txt, font=orig_font)
    gap = 30
    total_w = sale_w + gap + orig_w
    base_x = (W - total_w) // 2
    px_y = 1330

    d.text((base_x, px_y), sale_txt, fill=ACCENT, font=sale_font, anchor="lm")
    orig_x = base_x + sale_w + gap
    d.text((orig_x, px_y + 8), orig_txt, fill=SUB, font=orig_font, anchor="lm")
    # 划线
    line_y = px_y + 8
    d.line([(orig_x - 2, line_y), (orig_x + orig_w + 2, line_y)], fill=SUB, width=3)

    # ── 二维码 (右下) ──
    detail_url = item.get("url","")
    site_url = f"https://001.100app.dev/product-detail.html?url={requests.utils.quote(detail_url)}"
    qr = make_qr(site_url, box_size=4)
    img.paste(qr, (W - qr.width - 36, H - qr.height - 36))
    # 二维码下小字
    d.text((W - qr.width//2 - 36, H - 24), "扫码看历史价",
           fill=SUB, font=font(20, "regular"), anchor="mm")

    # ── 左下角站点 ──
    d.text((50, H - 50), "001.100app.dev", fill=GREEN, font=font(28, "semibold"), anchor="lm")
    d.text((50, H - 20), "22 国 outlet 实时追价", fill=SUB, font=font(20, "regular"), anchor="lm")

    img.save(out_path, "PNG", optimize=True)
    print(f"  → {out_path.name}  ({disc}% off, {name[:24]})")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    OUT_DIR.mkdir(exist_ok=True)
    items = fetch_top(n=n)
    if not items:
        print("没拉到今天的折扣商品 (>= 30% 折扣). 试降阈值或加 --all.")
        return
    today_tag = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n生成 {len(items)} 张卡片 → {OUT_DIR}/")
    for i, it in enumerate(items, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", clean_model_name(it.get("model","")).lower())[:30].strip("-")
        out = OUT_DIR / f"{today_tag}_{i:02d}_{slug}.png"
        make_card(it, i, len(items), out)
    print(f"\n完成. 复制到小红书 App 直接发布即可.")


if __name__ == "__main__":
    main()
