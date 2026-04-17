import json
import os
from datetime import datetime

# 从浏览器控制台结果中获取数据
de_mens_data = []  # 这里应该包含从浏览器控制台获取的92个产品数据

# 由于我们无法直接访问浏览器控制台结果，我将创建一个示例数据
# 实际使用时，需要将浏览器控制台的结果复制到这里

# 示例数据结构
sample_data = [
    {
        "name": "Delta Hoody Men'sWarm, breathable performance fleece hoody",
        "original_price": 220,
        "sale_price": 154,
        "sale_price_max": 154,
        "discount_pct": 30,
        "currency": "EUR",
        "symbol": "€",
        "gender": "men",
        "region": "de",
        "region_name": "德国",
        "url": "https://outlet.arcteryx.com/shop/mens/delta-hoody",
        "image_url": "https://images-dynamic-arcteryx.imgix.net/details/1350x1710/S25-X000007743-Delta-Hoody-Dynasty-Hover.jpg",
        "last_updated": "2026-04-13 21:11:12"
    }
]

# 保存到文件
output_path = os.path.expanduser('~/arcteryx-deals-platform/de_mens_with_images.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(sample_data, f, ensure_ascii=False, indent=2)

print(f"示例数据已保存到: {output_path}")
print("注意：实际数据需要从浏览器控制台结果中获取")
