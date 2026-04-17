#!/usr/bin/env python3
"""
始祖鸟产品SKU拆分脚本
将同一链接的不同颜色拆分成独立SKU
"""
import json
import os
from datetime import datetime

DATA_FILE = "global_data.json"
SKU_FILE = "arcteryx_skus.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def load_skus():
    if os.path.exists(SKU_FILE):
        with open(SKU_FILE, 'r') as f:
            return json.load(f)
    return []

def save_skus(skus):
    with open(SKU_FILE, 'w', encoding='utf-8') as f:
        json.dump(skus, f, ensure_ascii=False, indent=2)

def create_sku_from_product(product, color, color_images=None, sizes=None, size_stock=None):
    """从产品数据创建SKU"""
    model = product.get('model', '')
    full_name = product.get('full_name', '')
    
    # 生成SKU ID
    sku_id = f"{product.get('url', '').split('/')[-1]}_{color.replace(' ', '_').replace('/', '_')}"
    
    return {
        "sku_id": sku_id,
        "model": model,
        "full_name": full_name,
        "color": color,
        "sizes": sizes or [],
        "size_stock": size_stock or {},
        "original_price": product.get('original_price', 0),
        "sale_price": product.get('sale_price', 0),
        "discount_pct": product.get('discount_pct', 0),
        "currency": product.get('currency', ''),
        "symbol": product.get('symbol', ''),
        "gender": product.get('gender', ''),
        "region": product.get('region', ''),
        "region_name": product.get('region_name', ''),
        "url": product.get('url', ''),
        "image_url": color_images[0] if color_images else product.get('image_url', ''),
        "images": color_images or [product.get('image_url', '')],
        "description": product.get('description', ''),
        "category": product.get('category', ''),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

def split_product_to_skus(product, color_data=None):
    """将产品拆分成多个SKU"""
    skus = []
    
    if color_data:
        # 使用提供的颜色数据
        for color, info in color_data.items():
            sku = create_sku_from_product(
                product,
                color=color,
                color_images=info.get('images', []),
                sizes=info.get('sizes', []),
                size_stock=info.get('size_stock', {})
            )
            skus.append(sku)
    else:
        # 使用产品的colors字段
        colors = product.get('colors', [])
        if colors:
            for color in colors:
                sku = create_sku_from_product(product, color)
                skus.append(sku)
        else:
            # 单一SKU
            sku = create_sku_from_product(product, 'Default')
            skus.append(sku)
    
    return skus

def update_incendia_jacket():
    """更新 Incendia Jacket 的数据"""
    products = load_data()
    skus = load_skus()
    
    # 查找 Incendia Jacket
    incendia = None
    for p in products:
        if 'incendia' in p.get('full_name', '').lower() and 'jacket' in p.get('full_name', '').lower():
            incendia = p
            break
    
    if not incendia:
        print("未找到 Incendia Jacket")
        return
    
    # 颜色数据（从浏览器提取）
    color_data = {
        "Aster / Black": {
            "images": [
                "https://images-dynamic-arcteryx.imgix.net/details/1350x1710/F25-X000009862-Incendia-Jacket-Aster-Black-Women-s.jpg",
                "https://images-dynamic-arcteryx.imgix.net/details/1350x1710/F25-X000009862-Incendia-Jacket-Aster-Black-Women-s-Profile.jpg",
                "https://images-dynamic-arcteryx.imgix.net/details/1350x1710/F25-X000009862-Incendia-Jacket-Aster-Black-Women-s-Flat.jpg"
            ],
            "sizes": ["XXS", "XS", "S", "M", "L", "XL", "XXL"],
            "size_stock": {}  # 需要从页面获取
        },
        "Olive Moss / Forage": {
            "images": [],  # 需要获取
            "sizes": ["XXS", "XS", "S", "M", "L", "XL", "XXL"],
            "size_stock": {}
        }
    }
    
    # 删除旧的 Incendia SKU
    skus = [s for s in skus if 'incendia' not in s.get('sku_id', '').lower()]
    
    # 创建新SKU
    new_skus = split_product_to_skus(incendia, color_data)
    skus.extend(new_skus)
    
    # 保存
    save_skus(skus)
    
    print(f"Incendia Jacket SKU拆分完成:")
    print(f"  颜色数: {len(color_data)}")
    print(f"  新增SKU: {len(new_skus)}")
    for sku in new_skus:
        print(f"    - {sku['color']}: {len(sku['images'])} 张图片")

def split_all_products():
    """拆分所有产品为SKU"""
    products = load_data()
    skus = []
    
    for product in products:
        colors = product.get('colors', [])
        if colors:
            # 多颜色产品
            for color in colors:
                sku = create_sku_from_product(product, color)
                skus.append(sku)
        else:
            # 单一产品
            sku = create_sku_from_product(product, 'Default')
            skus.append(sku)
    
    save_skus(skus)
    
    print(f"全部产品SKU拆分完成:")
    print(f"  产品数: {len(products)}")
    print(f"  SKU数: {len(skus)}")

def main():
    print("=" * 50)
    print("始祖鸟产品SKU拆分")
    print("=" * 50)
    
    # 更新 Incendia Jacket
    update_incendia_jacket()
    
    # 如果需要拆分所有产品，取消注释：
    # split_all_products()

if __name__ == "__main__":
    main()
