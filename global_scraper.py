#!/usr/bin/env python3
"""
Arc'teryx 全球 Outlet 数据采集器
抓取 outlet.arcteryx.com 各区域站点的商品数据
"""

import json
import time
import re
import os
from datetime import datetime

# ========== 区域站点配置 ==========
REGIONS = [
    {"code": "us", "lang": "en", "name": "美国", "currency": "USD", "symbol": "$"},
    {"code": "ca", "lang": "en", "name": "加拿大", "currency": "CAD", "symbol": "C$"},
    {"code": "gb", "lang": "en", "name": "英国", "currency": "GBP", "symbol": "£"},
    {"code": "au", "lang": "en", "name": "澳大利亚", "currency": "AUD", "symbol": "A$"},
    {"code": "de", "lang": "de", "name": "德国", "currency": "EUR", "symbol": "€"},
    {"code": "fr", "lang": "fr", "name": "法国", "currency": "EUR", "symbol": "€"},
    {"code": "nl", "lang": "en", "name": "荷兰", "currency": "EUR", "symbol": "€"},
    {"code": "se", "lang": "en", "name": "瑞典", "currency": "SEK", "symbol": "kr"},
    {"code": "at", "lang": "de", "name": "奥地利", "currency": "EUR", "symbol": "€"},
    {"code": "ch", "lang": "de", "name": "瑞士", "currency": "CHF", "symbol": "CHF"},
]

# 分类路径
CATEGORIES = [
    "mens",
    "womens",
    # 子分类（如果主分类有分页问题，可以用子分类精确抓取）
    # "mens/shell-jackets",
    # "mens/insulated-jackets",
    # "mens/pants",
    # "mens/base-layer",
    # "mens/packs",
    # "mens/footwear",
    # "mens/veilance",
    # "womens/shell-jackets",
    # "womens/insulated-jackets",
    # "womens/pants",
    # "womens/base-layer",
    # "womens/dresses-skirts",
    # "womens/packs",
    # "womens/footwear",
    # "womens/veilance",
]

# 子分类映射（用于数据分类）
SUB_CATEGORIES = {
    "mens": {
        "shell-jackets": "硬壳冲锋衣",
        "insulated-jackets": "保暖夹克",
        "pants": "裤装",
        "base-layer": "排汗内衣",
        "shirts-tops": "上衣/T恤",
        "packs": "背包",
        "footwear": "鞋类",
        "veilance": "Veilance商务系列",
        "deeper-discounts": "深度折扣",
        "just-landed": "新上架",
    },
    "womens": {
        "shell-jackets": "硬壳冲锋衣",
        "insulated-jackets": "保暖夹克",
        "pants": "裤装",
        "base-layer": "排汗内衣",
        "shirts-tops": "上衣/T恤",
        "dresses-skirts": "裙装",
        "packs": "背包",
        "footwear": "鞋类",
        "veilance": "Veilance商务系列",
        "deeper-discounts": "深度折扣",
        "just-landed": "新上架",
    },
}


def build_url(region_code, lang_code, category=""):
    """构建区域站点URL"""
    if category:
        return f"https://outlet.arcteryx.com/{region_code}/{lang_code}/shop/{category}"
    return f"https://outlet.arcteryx.com/{region_code}/{lang_code}/shop"


def extract_products_from_dom(browser_console_eval):
    """
    从页面DOM提取商品数据
    返回提取到的商品列表
    """
    js_code = """
    (function() {
      const allLinks = Array.from(document.querySelectorAll('a'));
      const productLinks = allLinks.filter(a => {
        const h = a.href || '';
        const t = a.textContent.trim();
        return (h.includes('/shop/mens/') || h.includes('/shop/womens/')) 
               && t.includes('$') && t.length > 20;
      });
      
      const seen = new Set();
      const results = [];
      productLinks.forEach(link => {
        const href = link.href;
        if (seen.has(href)) return;
        seen.add(href);
        
        const text = link.textContent.trim();
        
        // 提取价格 - 支持 $, €, £, kr 等符号
        const priceMatch = text.match(/[\$€£]\s*([\d,]+\.?\d*)|([\d,]+\.?\d*)\s*kr/gi);
        const prices = priceMatch || [];
        const numericPrices = prices.map(p => {
          const num = p.replace(/[^\\d.]/g, '');
          return parseFloat(num);
        }).filter(n => !isNaN(n));
        
        // 提取产品名称和描述
        const lines = text.split('\\n').filter(l => l.trim());
        let name = lines[0] || '';
        let description = '';
        
        // 去掉价格行后的内容是描述
        const priceStartIdx = lines.findIndex(l => /[\$€£]/.test(l) || /kr/.test(l));
        if (priceStartIdx > 1) {
          description = lines.slice(1, priceStartIdx).join(' ').trim();
        }
        
        // 判断性别
        const isMens = href.includes('/mens/');
        const gender = isMens ? 'men' : 'women';
        
        // 判断子类
        let subCategory = '';
        const urlParts = href.split('/');
        if (urlParts.length >= 5) {
          subCategory = urlParts[urlParts.length - 1].split('-').slice(0, -1).join('-');
        }
        
        results.push({
          name: name,
          description: description,
          originalPrice: numericPrices[0] || 0,
          salePrice: numericPrices[1] || 0,
          salePriceMax: numericPrices.length > 2 ? numericPrices[2] : (numericPrices[1] || 0),
          gender: gender,
          subCategory: subCategory,
          url: href,
          rawText: text.substring(0, 300)
        });
      });
      
      return results;
    })()
    """
    return browser_console_eval(js_code)


def scroll_to_load_all(browser_scroll, max_scrolls=10):
    """滚动页面加载所有商品"""
    for i in range(max_scrolls):
        browser_scroll("down")
        time.sleep(1.5)


def parse_product_name(name_str):
    """解析产品名称，分离型号和性别标识"""
    # 去掉 Men's / Women's 后缀
    clean = re.sub(r"\s*(Men's|Women's)\s*$", "", name_str).strip()
    # 提取核心型号名（通常是第一个词）
    model_match = re.match(r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)", clean)
    model = model_match.group(1) if model_match else clean
    return {
        "full_name": name_str,
        "clean_name": clean,
        "model": model,
    }


def calculate_discount(original, sale):
    """计算折扣百分比"""
    if original <= 0 or sale <= 0:
        return 0
    return round((1 - sale / original) * 100)


def infer_category_from_url(url, sub_category_map):
    """根据URL推断中文品类"""
    for key, label in sub_category_map.items():
        if key in url:
            return label
    # 根据URL中的关键词推断
    url_lower = url.lower()
    if "shell" in url_lower or "jacket" in url_lower:
        return "硬壳冲锋衣"
    elif "insulated" in url_lower or "down" in url_lower:
        return "保暖夹克/羽绒"
    elif "pant" in url_lower or "bib" in url_lower:
        return "裤装"
    elif "shoe" in url_lower or "boot" in url_lower:
        return "鞋类"
    elif "pack" in url_lower or "backpack" in url_lower:
        return "背包"
    elif "base" in url_lower or "rho" in url_lower:
        return "排汗内衣"
    elif "veilance" in url_lower:
        return "Veilance商务系列"
    elif "blazer" in url_lower or "coat" in url_lower:
        return "商务外套"
    elif "vest" in url_lower:
        return "背心"
    else:
        return "其他"


def main():
    """
    主函数：使用浏览器自动化抓取数据
    需要在浏览器环境中运行
    """
    print("=" * 60)
    print("Arc'teryx 全球 Outlet 数据采集器")
    print("=" * 60)

    all_products = []
    stats = {}

    for region in REGIONS:
        region_key = f'{region["code"]}/{region["lang"]}'
        base_url = build_url(region["code"], region["lang"])
        print(f"\n🌍 开始抓取: {region['name']} ({region_key})")
        print(f"   URL: {base_url}")

        # 这里需要通过浏览器自动化工具导航和提取
        # 实际执行时由 browser_navigate + browser_console 完成
        print(f"   [待实现: 浏览器自动化抓取]")

    print(f"\n{'=' * 60}")
    print(f"采集完成! 总计 {len(all_products)} 款商品")
    print(f"{'=' * 60}")

    return all_products


if __name__ == "__main__":
    main()
