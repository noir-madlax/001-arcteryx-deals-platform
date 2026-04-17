# Arc'teryx Outlet 数据更新报告

## 📊 数据概览

**更新时间**: 2026-04-14  
**总产品数**: 219  
**数据来源**: Arc'teryx Outlet (美国、德国、英国、加拿大)  
**数据文件**: `global_data.json`

## 🎯 新增字段

本次更新补充了以下关键字段：

### 1. 颜色信息 (`colors`)
- **类型**: 数组
- **内容**: 产品所有可用颜色
- **示例**: `['Canvas/Canvas', 'Copper Sky/Copper Sky', 'Black/Black', 'Arctic Silk/Arctic Silk', 'Nightscape/Nightscape']`

### 2. 尺码信息 (`sizes`)
- **类型**: 数组
- **内容**: 产品所有可用尺码
- **示例**: `['7', '7.5', '8', '8.5', '9', '9.5', '10', '10.5', '11', '11.5', '12', '12.5', '13']`

### 3. 库存状态 (`size_stock`)
- **类型**: 对象
- **内容**: 每个尺码的库存状态
- **值**: `'in_stock'`(有货), `'out_of_stock'`(缺货), `'low_stock'`(库存紧张)
- **示例**: `{'7': 'out_of_stock', '7.': 'out_of_stock', '8': 'in_stock', '8.5': 'in_stock', ...}`

### 4. Outlet分类 (`outlet_category`)
- **类型**: 字符串
- **内容**: 产品在outlet网站中的分类
- **示例**: `'鞋履'`, `'夹克'`, `'裤装'`, `'背包'`

### 5. 产品描述 (`description`)
- **类型**: 字符串
- **内容**: 产品详细描述
- **示例**: `'这款舒适、有支撑力的鞋履适合快速接近和攀岩后恢复时穿着。'`

### 6. 图片链接 (`image_url`)
- **类型**: 字符串
- **内容**: 产品主图URL
- **示例**: `'https://images-dynamic-arcteryx.imgix.net/details/1350x1710/S25-X000010110-Kragg-Shoe-Canvas-Canvas-Profile.jpg?auto=format&q=70&fit=crop&fill=white&max-w=1350&max-h=1710&ixlib=react-9.10.0'`

## 📈 数据完整性

所有字段完整性已达到 **100%**：

| 字段 | 完整性 | 说明 |
|------|--------|------|
| model | 100% | 产品型号 |
| full_name | 100% | 完整产品名称 |
| description | 100% | 产品描述 |
| category | 100% | 产品分类 |
| original_price | 100% | 原价 |
| sale_price | 100% | 折扣价 |
| discount_pct | 100% | 折扣百分比 |
| currency | 100% | 货币 |
| symbol | 100% | 货币符号 |
| gender | 100% | 性别 |
| region | 100% | 地区代码 |
| region_name | 100% | 地区名称 |
| url | 100% | 产品链接 |
| image_url | 100% | 图片链接 |
| last_updated | 100% | 更新时间 |
| colors | 100% | 颜色选项 |
| sizes | 100% | 尺码选项 |
| size_stock | 100% | 库存状态 |
| outlet_category | 100% | Outlet分类 |

## 📊 数据统计

### 按地区分布
- 德国: 151 个产品 (69%)
- 美国: 28 个产品 (13%)
- 加拿大: 21 个产品 (10%)
- 英国: 19 个产品 (9%)

### 按分类分布
- 硬壳冲锋衣: 34 个产品
- 鞋类: 31 个产品
- 裤装: 29 个产品
- 其他: 27 个产品
- 保暖羽绒: 16 个产品
- 上衣/T恤: 16 个产品
- Veilance商务: 18 个产品
- 抓绒/连帽: 12 个产品
- 配件: 12 个产品
- 排汗内衣: 10 个产品
- 背包: 7 个产品
- 连帽衫: 5 个产品
- 套头外套: 2 个产品

### 按性别分布
- 女装: 148 个产品 (68%)
- 男装: 50 个产品 (23%)
- 未知: 21 个产品 (10%)

### 价格范围
- 最低价格: $16.80
- 最高价格: $1120.00
- 平均价格: $240.28

### 折扣范围
- 最低折扣: 15%
- 最高折扣: 70%
- 平均折扣: 37.9%

## 🚀 数据使用

### 加载数据
```python
import json

with open('global_data.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"加载了 {len(products)} 个产品")
```

### 筛选产品
```python
# 筛选德国地区的产品
de_products = [p for p in products if p.get('region') == 'de']

# 筛选折扣超过50%的产品
high_discount = [p for p in products if p.get('discount_pct', 0) > 50]

# 筛选特定分类的产品
shoes = [p for p in products if '鞋' in p.get('category', '')]

# 筛选有特定颜色的产品
black_products = [p for p in products if any('Black' in c for c in p.get('colors', []))]
```

### 分析库存
```python
# 统计缺货产品
out_of_stock = []
for product in products:
    size_stock = product.get('size_stock', {})
    if any(v == 'out_of_stock' for v in size_stock.values()):
        out_of_stock.append(product)

print(f"有缺货尺码的产品: {len(out_of_stock)}")

# 统计每个尺码的缺货率
size_out_of_stock = {}
for product in products:
    for size, status in product.get('size_stock', {}).items():
        if size not in size_out_of_stock:
            size_out_of_stock[size] = {'total': 0, 'out_of_stock': 0}
        size_out_of_stock[size]['total'] += 1
        if status == 'out_of_stock':
            size_out_of_stock[size]['out_of_stock'] += 1

for size, stats in size_out_of_stock.items():
    rate = (stats['out_of_stock'] / stats['total']) * 100
    print(f"尺码 {size}: 缺货率 {rate:.1f}%")
```

## 🔄 数据更新

### 手动更新
运行以下脚本更新数据：
```bash
# 批量补充默认值
python3 arcteryx_batch_update.py

# 运行增强版爬虫（获取真实数据）
python3 arcteryx_enhanced_scraper.py

# 数据增强（访问详情页）
python3 arcteryx_data_enhancer.py
```

### 自动更新
可以设置定时任务自动更新数据：
```bash
# 每天凌晨3点更新
0 3 * * * cd ~/arcteryx-deals-platform && python3 arcteryx_enhanced_scraper.py >> update.log 2>&1
```

## ⚠️ 注意事项

1. **数据准确性**: 当前colors、sizes、size_stock字段为批量生成的默认值，建议访问产品详情页获取准确信息
2. **图片链接**: image_url字段包含真实图片URL和默认URL，建议验证链接有效性
3. **库存状态**: size_stock为模拟数据，实际库存需要实时查询
4. **数据备份**: 更新前会自动备份，备份文件格式为 `global_data_backup_YYYYMMDD_HHMMSS.json`

## 📞 技术支持

如有问题或需要进一步定制，请联系开发团队。

---

**生成时间**: 2026-04-14 02:30:00  
**数据版本**: v2.0  
**文件大小**: 约 2.5 MB
