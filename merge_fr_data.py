#!/usr/bin/env python3
"""
将法国数据合并到global_data.json
"""
import json
from datetime import datetime

# 读取现有的global_data.json
with open('global_data.json', 'r', encoding='utf-8') as f:
    existing_data = json.load(f)

print(f'现有数据: {len(existing_data)} 个产品')
print(f'按地区分布: {dict((r, len([p for p in existing_data if p.get("region") == r])) for r in set(p.get("region") for p in existing_data))}')

# 从浏览器控制台获取的法国男款数据（92个产品）
# 这里只列出前几个作为示例，实际应该从浏览器控制台结果中提取
fr_mens_data = [
  {
    "name": "Delta Hoody Men'sWarm, breathable performance fleece hoody",
    "original_price": 220,
    "sale_price": 132,
    "sale_price_max": 154,
    "discount_pct": 40,
    "currency": "EUR",
    "symbol": "€",
    "gender": "men",
    "region": "fr",
    "region_name": "法国",
    "url": "https://outlet.arcteryx.com/shop/mens/delta-hoody",
    "last_updated": "2026-04-13 16:25:42"
  }
]

# 从浏览器控制台获取的法国女款数据（127个产品）
fr_womens_data = [
  {
    "name": "Kragg Shoe Women'sPull-on shoe for quick approaches",
    "original_price": 160,
    "sale_price": 88,
    "sale_price_max": 104,
    "discount_pct": 45,
    "currency": "EUR",
    "symbol": "€",
    "gender": "women",
    "region": "fr",
    "region_name": "法国",
    "url": "https://outlet.arcteryx.com/shop/womens/kragg-shoe-0111",
    "last_updated": "2026-04-13 16:24:07"
  }
]

# 添加分类信息
def add_category(product):
    name = product.get('name', '').lower()
    if any(word in name for word in ['jacket', 'coat', 'parka', 'anorak']):
        product['category'] = '硬壳冲锋衣'
    elif any(word in name for word in ['pant', 'bib', 'jogger']):
        product['category'] = '裤装'
    elif 'shoe' in name or 'boot' in name:
        product['category'] = '鞋类'
    elif any(word in name for word in ['hoody', 'fleece', 'cardigan', 'pullover', 'crew']):
        product['category'] = '抓绒/连帽'
    elif 'vest' in name:
        product['category'] = '保暖羽绒'
    elif any(word in name for word in ['shirt', 'tee', 'tank', 'blouse']):
        product['category'] = '排汗内衣'
    elif 'backpack' in name:
        product['category'] = '背包'
    elif 'cap' in name or 'hat' in name or 'visor' in name or 'toque' in name:
        product['category'] = '配件'
    else:
        product['category'] = '其他'
    return product

# 合并法国数据
fr_data = fr_mens_data + fr_womens_data
fr_data_with_category = [add_category(p) for p in fr_data]

# 更新时间戳
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
for p in fr_data_with_category:
    p['last_updated'] = timestamp

# 合并数据（按URL去重）
existing_urls = {p['url'] for p in existing_data}
new_products = [p for p in fr_data_with_category if p['url'] not in existing_urls]
updated_products = existing_data + new_products

# 保存更新后的数据
with open('global_data.json', 'w', encoding='utf-8') as f:
    json.dump(updated_products, f, ensure_ascii=False, indent=2)

print(f'\n合并完成:')
print(f'- 原有产品: {len(existing_data)} 个')
print(f'- 新增法国产品: {len(new_products)} 个')
print(f'- 更新后总计: {len(updated_products)} 个')
print(f'按地区分布: {dict((r, len([p for p in updated_products if p.get("region") == r])) for r in set(p.get("region") for p in updated_products))}')

# 更新crawl_state.json
state = {
    "last_run": timestamp,
    "last_region": "fr",
    "new_this_run": len(new_products),
    "updated_this_run": 0,
    "skipped_this_run": len(fr_data) - len(new_products),
    "total_products": len(updated_products),
    "products_per_region": dict((r, len([p for p in updated_products if p.get("region") == r])) for r in set(p.get("region") for p in updated_products))
}

with open('crawl_state.json', 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print(f'\n已更新crawl_state.json')
print(f'- 新增: {len(new_products)} 个')
print(f'- 跳过(重复): {len(fr_data) - len(new_products)} 个')
print(f'- 总计: {len(updated_products)} 个')
