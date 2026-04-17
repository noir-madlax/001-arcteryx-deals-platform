#!/usr/bin/env python3
"""
始祖鸟SKU数据批量提取脚本
从产品详情页提取颜色、尺码、库存等信息
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

def generate_extraction_script(product):
    """生成浏览器提取脚本"""
    url = product.get('url', '')
    name = product.get('full_name', '')
    
    script = f'''
// 访问: {url}
// 产品: {name}
// 滚动页面后执行：

async function extractProductDetail() {{
  const detail = {{
    url: '{url}',
    name: document.querySelector('h1')?.textContent || '',
    description: '',
    colors: [],
    sizes: [],
    size_stock: {{}},
    price: {{}},
    images: []
  }};
  
  // 提取描述
  document.querySelectorAll('p').forEach(p => {{
    if (p.textContent.length > 50 && !detail.description) {{
      detail.description = p.textContent;
    }}
  }});
  
  // 提取颜色
  document.querySelectorAll('fieldset').forEach(fs => {{
    const legend = fs.querySelector('legend')?.textContent || '';
    if (legend.includes('颜色') || legend.includes('color') || legend.includes('Color')) {{
      fs.querySelectorAll('li').forEach(li => {{
        const colorName = li.textContent.trim();
        if (colorName) detail.colors.push(colorName);
      }});
    }}
  }});
  
  // 提取尺码和库存
  document.querySelectorAll('input[type="radio"]').forEach(radio => {{
    const label = radio.closest('label')?.textContent?.trim() || radio.value;
    const group = radio.closest('fieldset')?.querySelector('legend')?.textContent || '';
    
    if (['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL'].includes(label)) {{
      detail.sizes.push(label);
      // 检查是否禁用（缺货）
      const isDisabled = radio.disabled || radio.closest('label')?.classList.contains('disabled');
      detail.size_stock[label] = isDisabled ? 'out_of_stock' : 'in_stock';
    }}
  }});
  
  // 提取价格
  const priceText = document.body.innerText;
  const prices = priceText.match(/US\\$([\d,]+\.?\d*)/g);
  if (prices && prices.length >= 2) {{
    detail.price = {{
      sale: parseFloat(prices[0].replace('US$', '').replace(',', '')),
      original: parseFloat(prices[1].replace('US$', '').replace(',', ''))
    }};
  }}
  
  // 提取图片
  document.querySelectorAll('img').forEach(img => {{
    if (img.src.includes('imgix') && img.alt?.includes(detail.name.split(' ')[0])) {{
      detail.images.push(img.src);
    }}
  }});
  
  return detail;
}}

extractProductDetail().then(data => {{
  console.log(JSON.stringify(data, null, 2));
}});
'''
    return script

def main():
    print("=" * 60)
    print("始祖鸟SKU数据批量提取")
    print("=" * 60)
    
    # 加载数据
    products = load_data()
    
    # 过滤美国产品（优先处理）
    us_products = [p for p in products if p.get('region') == 'us']
    
    print(f"\n美国产品总数: {len(us_products)}")
    print(f"  男款: {len([p for p in us_products if p.get('gender') == 'men'])}")
    print(f"  女款: {len([p for p in us_products if p.get('gender') == 'women'])}")
    
    # 生成提取脚本
    print("\n生成浏览器提取脚本...")
    print("-" * 60)
    
    # 选择几个示例产品
    sample_products = us_products[:5]
    
    for i, product in enumerate(sample_products, 1):
        print(f"\n[{i}] {product.get('full_name')}")
        print(f"URL: {product.get('url')}")
        print(f"当前数据: colors={len(product.get('colors', []))}, sizes={len(product.get('sizes', []))}")
    
    print("\n" + "=" * 60)
    print("使用方法：")
    print("1. 打开上面的URL")
    print("2. 滚动页面加载所有内容")
    print("3. 打开控制台(F12)，执行提取脚本")
    print("4. 复制输出的JSON数据")
    print("5. 保存到文件: sku_data_{product_id}.json")
    print("6. 运行: python3 batch_extract_skus.py merge <file>")
    print("=" * 60)
    
    # 输出第一个产品的提取脚本
    if sample_products:
        print("\n示例提取脚本（复制到浏览器控制台）:")
        print("-" * 60)
        print(generate_extraction_script(sample_products[0]))

if __name__ == "__main__":
    main()
