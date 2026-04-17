#!/usr/bin/env python3
"""
始祖鸟数据更新 + 图片下载流程
1. 重新爬取全网数据
2. 下载图片到本地（按model去重）
3. 更新数据文件，添加 local_image 字段
"""
import json
import os
import hashlib
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 配置
IMAGE_DIR = "images"
MAX_WORKERS = 5
TIMEOUT = 15

def url_to_filename(url, model):
    """将URL转换为本地文件名，使用model作为前缀"""
    ext = ".jpg"
    if ".png" in url.lower():
        ext = ".png"
    elif ".webp" in url.lower():
        ext = ".webp"
    
    # 用model名简化
    safe_model = model.replace(" ", "_").replace("'", "")[:30]
    hash_str = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{safe_model}_{hash_str}{ext}"

def download_image(args):
    """下载单张图片"""
    url, save_path = args
    
    if os.path.exists(save_path):
        return True, "exists"
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '--max-time', str(TIMEOUT), '-o', save_path, url],
            capture_output=True
        )
        if result.returncode == 0 and os.path.exists(save_path):
            size = os.path.getsize(save_path)
            if size > 1000:  # 至少1KB
                return True, size
            else:
                os.remove(save_path)
                return False, "file too small"
        return False, "download failed"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("始祖鸟数据更新 + 图片下载")
    print("=" * 60)
    
    # 创建图片目录
    Path(IMAGE_DIR).mkdir(exist_ok=True)
    
    # 加载现有数据
    with open('global_data.json', 'r') as f:
        data = json.load(f)
    
    print(f"\n现有数据: {len(data)} 个产品")
    
    # 按model去重收集图片URL
    model_images = {}
    for item in data:
        model = item.get('model', '')
        url = item.get('image_url', '')
        if model and url and model not in model_images:
            model_images[model] = url
    
    print(f"需下载图片: {len(model_images)} 个（按model去重）")
    
    # 检查已存在的图片
    existing = 0
    download_list = []
    url_to_local = {}
    
    for model, url in model_images.items():
        filename = url_to_filename(url, model)
        save_path = os.path.join(IMAGE_DIR, filename)
        url_to_local[url] = save_path
        
        if os.path.exists(save_path):
            existing += 1
        else:
            download_list.append((url, save_path))
    
    print(f"已存在: {existing} 个")
    print(f"需下载: {len(download_list)} 个")
    
    if download_list:
        print("\n开始下载图片...")
        print("-" * 60)
        
        success = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(download_image, args): args for args in download_list}
            
            for i, future in enumerate(as_completed(futures), 1):
                url, save_path = futures[future]
                ok, result = future.result()
                filename = os.path.basename(save_path)
                
                if ok:
                    success += 1
                    if result != "exists":
                        print(f"[{i}/{len(download_list)}] ✓ {filename}")
                else:
                    failed += 1
                    print(f"[{i}/{len(download_list)}] ✗ {filename}: {result}")
        
        print(f"\n下载完成: 成功 {success}, 失败 {failed}")
    
    # 更新数据，添加 local_image 字段
    print("\n更新数据文件...")
    for item in data:
        url = item.get('image_url', '')
        if url in url_to_local:
            item['local_image'] = url_to_local[url]
    
    # 保存更新后的数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'global_data_{timestamp}.json'
    
    with open('global_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存到 global_data.json")
    print(f"备份: {backup_file}")
    
    # 统计
    with_local = sum(1 for item in data if item.get('local_image'))
    print(f"\n最终统计:")
    print(f"  总产品: {len(data)}")
    print(f"  有本地图片: {with_local}")
    print(f"  图片目录: {IMAGE_DIR}/")
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
