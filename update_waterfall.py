#!/usr/bin/env python3
"""
更新 waterfall.html，添加系列筛选和人民币汇率显示
"""
import json
import re

# 读取数据文件，提取所有系列
with open('global_data.json', 'r') as f:
    data = json.load(f)

# 提取系列名称
def extract_series(name):
    """从产品名称中提取系列"""
    series_list = [
        'Alpha', 'Beta', 'Gamma', 'Delta', 'Zeta', 'Sigma',
        'Atom', 'Cerium', 'Thorium', 'Proton', 'Nuclei',
        'Sabre', 'Rush', 'Fissile', 'Sentinel',
        'Aerios', 'Norvan', 'Konseal', 'Kopec', 'Sylan',
        'Mantis', 'Granville', 'Brize', 'Index',
        'Covert', 'Kyanite', 'Rho', 'Phase',
        'Squamish', 'Houdini', 'Incendo',
        'Veilance', 'LEAF', 'Kragg'
    ]
    name_lower = name.lower()
    for series in series_list:
        if series.lower() in name_lower:
            return series
    return '其他'

# 统计系列
series_count = {}
for item in data:
    name = item.get('full_name', '') or item.get('model', '')
    series = extract_series(name)
    series_count[series] = series_count.get(series, 0) + 1

# 按数量排序
sorted_series = sorted(series_count.items(), key=lambda x: -x[1])
print("系列统计:")
for series, count in sorted_series:
    print(f"  {series}: {count}")

# 读取HTML
with open('waterfall.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 在类别筛选后添加系列筛选
series_options = '\n'.join([
    f'                    <option value="{s}">🏔️ {s} ({c})</option>'
    for s, c in sorted_series if s != '其他'
])

series_filter_html = f'''
            <div class="filter-group">
                <label>系列</label>
                <select id="series-filter">
                    <option value="">全部系列</option>
{series_options}
                    <option value="其他">📦 其他</option>
                </select>
            </div>
'''

# 在类别筛选后插入系列筛选
html = html.replace(
    '''                </select>
            </div>

            <div class="filter-group">
                <label>价格范围''',
    '''                </select>
            </div>
''' + series_filter_html + '''            <div class="filter-group">
                <label>价格范围'''
)

# 2. 添加汇率常量和转换函数
exchange_rate_js = '''
        // 汇率（对人民币）
        const EXCHANGE_RATES = {
            'USD': 7.25,
            'EUR': 7.85,
            'GBP': 9.15,
            'CAD': 5.30
        };

        // 货币符号到代码的映射
        const SYMBOL_TO_CURRENCY = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            'CA$': 'CAD'
        };

        // 转换为人民币
        function toCNY(price, symbol) {
            const currency = SYMBOL_TO_CURRENCY[symbol] || 'EUR';
            const rate = EXCHANGE_RATES[currency] || 7.85;
            return Math.round(price * rate);
        }
'''

# 在 regionFlags 之前插入汇率代码
html = html.replace(
    '''            const regionFlags = {''',
    exchange_rate_js + '''            const regionFlags = {'''
)

# 3. 修改价格显示，添加人民币
html = html.replace(
    '''<span class="price-original">${product.symbol || '€'}${originalPrice}</span>
                                <span class="price-sale">${product.symbol || '€'}${price}</span>''',
    '''<span class="price-original">${product.symbol || '€'}${originalPrice}</span>
                                <span class="price-sale">${product.symbol || '€'}${price}</span>
                                <span class="price-cny">¥${toCNY(price, product.symbol || '€')}</span>'''
)

# 4. 添加系列筛选逻辑
# 首先添加系列字段到产品数据
series_field_js = '''
        // 提取产品系列
        function getSeries(product) {
            const name = (product.full_name || product.model || '').toLowerCase();
            const seriesList = [
                'Alpha', 'Beta', 'Gamma', 'Delta', 'Zeta', 'Sigma',
                'Atom', 'Cerium', 'Thorium', 'Proton', 'Nuclei',
                'Sabre', 'Rush', 'Fissile', 'Sentinel',
                'Aerios', 'Norvan', 'Konseal', 'Kopec', 'Sylan',
                'Mantis', 'Granville', 'Brize', 'Index',
                'Covert', 'Kyanite', 'Rho', 'Phase',
                'Squamish', 'Houdini', 'Incendo',
                'Veilance', 'LEAF', 'Kragg'
            ];
            for (const series of seriesList) {
                if (name.includes(series.toLowerCase())) {
                    return series;
                }
            }
            return '其他';
        }
'''

# 在 applyFilters 函数之前插入
html = html.replace(
    '''        // 筛选和排序''',
    series_field_js + '''        // 筛选和排序'''
)

# 5. 更新筛选逻辑，添加系列筛选
html = html.replace(
    '''            const category = document.getElementById('category-filter').value;''',
    '''            const category = document.getElementById('category-filter').value;
            const series = document.getElementById('series-filter').value;'''
)

html = html.replace(
    '''                // 类别筛选
                if (category && product.category !== category) return false;''',
    '''                // 类别筛选
                if (category && product.category !== category) return false;
                
                // 系列筛选
                if (series && getSeries(product) !== series) return false;'''
)

# 6. 更新重置函数
html = html.replace(
    '''            document.getElementById('category-filter').value = '';''',
    '''            document.getElementById('category-filter').value = '';
            document.getElementById('series-filter').value = '';'''
)

# 7. 添加事件监听
html = html.replace(
    '''        document.getElementById('category-filter').addEventListener('change', applyFilters);''',
    '''        document.getElementById('category-filter').addEventListener('change', applyFilters);
        document.getElementById('series-filter').addEventListener('change', applyFilters);'''
)

# 8. 添加人民币价格样式
cny_style = '''
        .price-cny {
            display: block;
            font-size: 0.85rem;
            color: #ff6b6b;
            margin-top: 3px;
        }
'''

html = html.replace(
    '''        .discount-badge {''',
    cny_style + '''        .discount-badge {'''
)

# 保存更新后的HTML
with open('waterfall.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("\n已更新 waterfall.html:")
print("  ✓ 添加系列筛选下拉框")
print("  ✓ 添加人民币价格显示")
print("  ✓ 添加系列提取逻辑")
print("  ✓ 更新筛选功能")
