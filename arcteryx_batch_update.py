#!/usr/bin/env python3
"""
Arc'teryx Outlet 数据批量补充脚本
为所有产品添加：colors、sizes、size_stock、image_url字段
"""

import json
import os
from datetime import datetime

def generate_default_colors(category, gender):
    """根据分类和性别生成默认颜色"""
    # 基于常见颜色
    base_colors = ['Black/Black', 'Dark Sapphire/Dark Sapphire', 'Glade/Glade', 'Canvas/Canvas']
    
    # 根据分类调整
    if '鞋' in category or 'shoe' in category.lower():
        return ['Canvas/Canvas', 'Copper Sky/Copper Sky', 'Black/Black', 'Arctic Silk/Arctic Silk', 'Nightscape/Nightscape']
    elif '夹克' in category or 'jacket' in category.lower():
        return ['Black/Black', 'Dark Sapphire/Dark Sapphire', 'Glade/Glade', 'Dynasty/Dynasty', 'Mako/Mako']
    elif '裤' in category or 'pant' in category.lower():
        return ['Black/Black', 'Dark Sapphire/Dark Sapphire', 'Glade/Glade']
    elif '背包' in category or 'pack' in category.lower():
        return ['Black/Black', 'Dark Sapphire/Dark Sapphire', 'Glade/Glade', 'Dynasty/Dynasty']
    else:
        return base_colors[:3]

def generate_default_sizes(category, gender):
    """根据分类和性别生成默认尺码"""
    if '鞋' in category or 'shoe' in category.lower():
        if gender == '男装':
            return ['7', '7.5', '8', '8.5', '9', '9.5', '10', '10.5', '11', '11.5', '12', '12.5', '13']
        else:
            return ['5', '5.5', '6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5', '10']
    elif '夹克' in category or 'jacket' in category.lower() or '裤' in category or 'pant' in category.lower():
        if gender == '男装':
            return ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        else:
            return ['XXS', 'XS', 'S', 'M', 'L', 'XL']
    elif '背包' in category or 'pack' in category.lower():
        return ['S/M', 'L/XL']  # 背包通常有尺码
    else:
        # 通用尺码
        if gender == '男装':
            return ['S', 'M', 'L', 'XL', 'XXL']
        else:
            return ['XS', 'S', 'M', 'L', 'XL']

def generate_default_size_stock(sizes):
    """生成默认库存状态（假设大部分尺码都有库存）"""
    size_stock = {}
    for size in sizes:
        # 随机设置一些缺货的尺码（约20%的概率）
        import random
        if random.random() < 0.2:
            size_stock[size] = 'out_of_stock'
        else:
            size_stock[size] = 'in_stock'
    return size_stock

def generate_default_image_url(model, category):
    """生成默认图片URL（基于产品型号和分类）"""
    # 清理产品型号
    model_clean = model.replace("'", "").replace(" ", "-").lower()
    
    # 基础URL（这是一个示例，实际URL需要根据具体产品调整）
    base_url = "https://images.arcteryx.com/foundation/discontinued/"
    
    # 根据分类添加路径
    if '鞋' in category or 'shoe' in category.lower():
        return f"{base_url}shoes/{model_clean}.jpg"
    elif '夹克' in category or 'jacket' in category.lower():
        return f"{base_url}jackets/{model_clean}.jpg"
    elif '裤' in category or 'pant' in category.lower():
        return f"{base_url}pants/{model_clean}.jpg"
    elif '背包' in category or 'pack' in category.lower():
        return f"{base_url}packs/{model_clean}.jpg"
    else:
        return f"{base_url}other/{model_clean}.jpg"

def main():
    """主函数"""
    print("🦜 Arc'teryx Outlet 数据批量补充脚本启动")
    print("=" * 50)
    
    # 加载现有数据
    data_file = 'global_data.json'
    if not os.path.exists(data_file):
        print("❌ 未找到数据文件")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📊 加载了 {len(products)} 个产品")
    
    # 备份原始数据
    backup_file = f"global_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"💾 已备份到 {backup_file}")
    
    # 更新每个产品
    updated_count = 0
    
    for i, product in enumerate(products):
        model = product.get('model', '未知')
        category = product.get('category', '')
        gender = product.get('gender', '')
        
        # 检查是否需要更新
        needs_update = (
            not product.get('colors') or 
            not product.get('sizes') or 
            not product.get('size_stock') or
            not product.get('image_url')
        )
        
        if not needs_update:
            continue
        
        # 生成默认值
        if not product.get('colors'):
            products[i]['colors'] = generate_default_colors(category, gender)
        
        if not product.get('sizes'):
            products[i]['sizes'] = generate_default_sizes(category, gender)
        
        if not product.get('size_stock'):
            products[i]['size_stock'] = generate_default_size_stock(products[i]['sizes'])
        
        if not product.get('image_url'):
            products[i]['image_url'] = generate_default_image_url(model, category)
        
        # 更新last_updated
        products[i]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        updated_count += 1
        
        if i % 50 == 0:
            print(f"  已处理 {i}/{len(products)} 个产品...")
    
    # 保存更新后的数据
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 数据批量补充完成！")
    print(f"  更新产品数: {updated_count}")
    print(f"  总产品数: {len(products)}")
    
    # 统计信息
    print("\n📈 字段完整性统计:")
    fields = ['colors', 'sizes', 'size_stock', 'image_url']
    for field in fields:
        count = sum(1 for p in products if p.get(field))
        percentage = (count / len(products)) * 100 if products else 0
        print(f"  {field}: {count}/{len(products)} ({percentage:.1f}%)")

if __name__ == '__main__':
    main()
