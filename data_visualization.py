#!/usr/bin/env python3
"""
Arc'teryx Outlet 数据可视化脚本
生成数据报告和图表
"""

import json
import os
from collections import Counter

def load_data():
    """加载数据"""
    data_file = 'global_data.json'
    if not os.path.exists(data_file):
        print("❌ 未找到数据文件")
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_report(products):
    """生成数据报告"""
    if not products:
        return
    
    print("=" * 60)
    print("🦜 Arc'teryx Outlet 数据可视化报告")
    print("=" * 60)
    
    # 1. 总体统计
    print(f"\n📊 总体统计")
    print(f"   总产品数: {len(products)}")
    
    # 2. 按地区统计
    regions = Counter(p.get('region_name', '未知') for p in products)
    print(f"\n🌍 地区分布")
    for region, count in regions.most_common():
        percentage = (count / len(products)) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {region:10} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 3. 按分类统计
    categories = Counter(p.get('category', '未知') for p in products)
    print(f"\n📂 分类分布")
    for category, count in categories.most_common(10):  # 只显示前10个
        percentage = (count / len(products)) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {category:15} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 4. 按性别统计
    genders = Counter(p.get('gender', '未知') for p in products)
    print(f"\n👤 性别分布")
    for gender, count in genders.most_common():
        percentage = (count / len(products)) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {gender:10} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 5. 价格分析
    prices = [p.get('sale_price', 0) for p in products if p.get('sale_price')]
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        print(f"\n💰 价格分析")
        print(f"   最低价格: ${min_price:.2f}")
        print(f"   最高价格: ${max_price:.2f}")
        print(f"   平均价格: ${avg_price:.2f}")
        
        # 价格分布
        price_ranges = [
            (0, 50, "$0-50"),
            (50, 100, "$50-100"),
            (100, 200, "$100-200"),
            (200, 300, "$200-300"),
            (300, 500, "$300-500"),
            (500, 1000, "$500-1000"),
            (1000, float('inf'), "$1000+")
        ]
        
        print(f"\n   价格分布:")
        for min_p, max_p, label in price_ranges:
            count = sum(1 for p in prices if min_p <= p < max_p)
            percentage = (count / len(prices)) * 100
            if count > 0:
                bar = "█" * int(percentage / 2)
                print(f"   {label:10} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 6. 折扣分析
    discounts = [p.get('discount_pct', 0) for p in products if p.get('discount_pct')]
    if discounts:
        min_discount = min(discounts)
        max_discount = max(discounts)
        avg_discount = sum(discounts) / len(discounts)
        
        print(f"\n🔥 折扣分析")
        print(f"   最低折扣: {min_discount}%")
        print(f"   最高折扣: {max_discount}%")
        print(f"   平均折扣: {avg_discount:.1f}%")
        
        # 折扣分布
        discount_ranges = [
            (0, 20, "0-20%"),
            (20, 30, "20-30%"),
            (30, 40, "30-40%"),
            (40, 50, "40-50%"),
            (50, 60, "50-60%"),
            (60, 100, "60%+")
        ]
        
        print(f"\n   折扣分布:")
        for min_d, max_d, label in discount_ranges:
            count = sum(1 for d in discounts if min_d <= d < max_d)
            percentage = (count / len(discounts)) * 100
            if count > 0:
                bar = "█" * int(percentage / 2)
                print(f"   {label:10} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 7. 颜色分析
    all_colors = []
    for product in products:
        all_colors.extend(product.get('colors', []))
    
    if all_colors:
        colors = Counter(all_colors)
        print(f"\n🎨 热门颜色 (前10)")
        for color, count in colors.most_common(10):
            percentage = (count / len(all_colors)) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {color:25} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 8. 尺码分析
    all_sizes = []
    for product in products:
        all_sizes.extend(product.get('sizes', []))
    
    if all_sizes:
        sizes = Counter(all_sizes)
        print(f"\n📏 热门尺码 (前10)")
        for size, count in sizes.most_common(10):
            percentage = (count / len(all_sizes)) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {size:10} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 9. 库存状态分析
    stock_status = Counter()
    for product in products:
        for status in product.get('size_stock', {}).values():
            stock_status[status] += 1
    
    if stock_status:
        print(f"\n📦 库存状态")
        for status, count in stock_status.most_common():
            percentage = (count / sum(stock_status.values())) * 100
            bar = "█" * int(percentage / 2)
            status_name = {
                'in_stock': '有货',
                'out_of_stock': '缺货',
                'low_stock': '库存紧张'
            }.get(status, status)
            print(f"   {status_name:10} {count:3} ({percentage:5.1f}%) {bar}")
    
    # 10. 数据质量
    print(f"\n✅ 数据质量")
    fields = ['colors', 'sizes', 'size_stock', 'image_url', 'description']
    for field in fields:
        count = sum(1 for p in products if p.get(field))
        percentage = (count / len(products)) * 100
        status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
        print(f"   {status} {field:15} {count}/{len(products)} ({percentage:.1f}%)")
    
    print("\n" + "=" * 60)
    print("报告生成完成")
    print("=" * 60)

def save_report_to_file(products, filename='data_report.txt'):
    """保存报告到文件"""
    import sys
    from io import StringIO
    
    # 捕获输出
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    
    generate_report(products)
    
    # 恢复标准输出
    sys.stdout = old_stdout
    
    # 获取输出内容
    output = buffer.getvalue()
    
    # 保存到文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"报告已保存到 {filename}")
    return output

def main():
    """主函数"""
    products = load_data()
    if not products:
        return
    
    # 生成并显示报告
    generate_report(products)
    
    # 保存报告到文件
    save_report_to_file(products)
    
    print(f"\n💡 提示:")
    print(f"   - 报告已保存到 data_report.txt")
    print(f"   - 如需更详细的数据分析，请使用 pandas 或其他数据可视化工具")
    print(f"   - 数据文件: global_data.json")

if __name__ == '__main__':
    main()
