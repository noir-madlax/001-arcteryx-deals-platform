#!/usr/bin/env python3
"""
始祖鸟图片下载 - 使用curl绕过SSL和代理问题
"""
import json
import os
import subprocess
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

IMAGE_DIR = "images"
MAX_WORKERS = 4

def url_to_filename(url, model):
    ext = ".jpg"
    if ".png" in url.lower():
        ext = ".png"
    # ASCII only for filename
    safe_model = model.encode('ascii', 'ignore').decode('ascii')
    safe_model = safe_model.replace(" ", "_").replace("'", "").replace("/", "_")[:30]
    hash_str = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{safe_model}_{hash_str}{ext}"

def download_image(args):
    url, save_path = args
    
    if os.path.exists(save_path) and os.path.getsize(save_path) > 5000:
        return True, "exists"
    
    try:
        # curl with SSL verify disabled and no proxy
        result = subprocess.run([
            'curl', '-s', '-L', 
            '--max-time', '20',
            '-k',  # skip SSL verify
            '-o', save_path,
            url
        ], capture_output=True, env={**os.environ, 'NO_PROXY': '*'})
        
        if os.path.exists(save_path):
            size = os.path.getsize(save_path)
            if size > 5000:
                return True, size
            else:
                os.remove(save_path)
                return False, f"too small: {size}"
        return False, "download failed"
    except Exception as e:
        return False, str(e)

def main():
    Path(IMAGE_DIR).mkdir(exist_ok=True)
    
    with open('global_data.json', 'r') as f:
        data = json.load(f)
    
    # 按model去重
    model_images = {}
    for item in data:
        model = item.get('model', '')
        url = item.get('image_url', '')
        if model and url and model not in model_images:
            model_images[model] = url
    
    print(f"总共 {len(model_images)} 个唯一图片")
    
    # 构建下载列表
    download_list = []
    url_to_local = {}
    existing = 0
    
    for model, url in model_images.items():
        filename = url_to_filename(url, model)
        save_path = os.path.join(IMAGE_DIR, filename)
        url_to_local[url] = save_path
        
        if os.path.exists(save_path) and os.path.getsize(save_path) > 5000:
            existing += 1
        else:
            download_list.append((url, save_path))
    
    print(f"已存在: {existing}")
    print(f"需下载: {len(download_list)}")
    
    if download_list:
        print("\n开始下载...")
        success = 0
        failed = 0
        
        for i, (url, save_path) in enumerate(download_list, 1):
            ok, result = download_image((url, save_path))
            filename = os.path.basename(save_path)
            
            if ok:
                success += 1
                print(f"[{i}/{len(download_list)}] ✓ {filename}")
            else:
                failed += 1
                if i <= 10 or i % 20 == 0:
                    print(f"[{i}/{len(download_list)}] ✗ {filename}: {result}")
        
        print(f"\n下载完成: 成功 {success}, 失败 {failed}")
    
    # 更新数据
    for item in data:
        url = item.get('image_url', '')
        if url in url_to_local:
            local_path = url_to_local[url]
            if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
                item['local_image'] = local_path
    
    with open('global_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 统计
    with_local = sum(1 for item in data if item.get('local_image'))
    print(f"\n最终: {with_local}/{len(data)} 产品有本地图片")

if __name__ == "__main__":
    main()
