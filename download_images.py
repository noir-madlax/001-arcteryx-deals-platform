#!/usr/bin/env python3
"""
下载始祖鸟产品图片到本地，避免外部CDN加载问题
"""
import json
import os
import hashlib
import urllib.request
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
DATA_FILE = "global_data.json"
IMAGE_DIR = "images"
MAX_WORKERS = 5
TIMEOUT = 15
RETRY = 2

def url_to_filename(url):
    """将URL转换为本地文件名"""
    # 使用URL的MD5作为文件名，保留原始扩展名
    ext = ".jpg"
    if ".png" in url.lower():
        ext = ".png"
    elif ".webp" in url.lower():
        ext = ".webp"
    
    hash_str = hashlib.md5(url.encode()).hexdigest()[:16]
    return f"{hash_str}{ext}"

def download_image(url, save_path):
    """下载单张图片"""
    if os.path.exists(save_path):
        return True, "exists"
    
    for attempt in range(RETRY + 1):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            })
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
                with open(save_path, 'wb') as f:
                    f.write(data)
                return True, len(data)
        except Exception as e:
            if attempt < RETRY:
                time.sleep(1)
            else:
                return False, str(e)

def main():
    # 创建图片目录
    Path(IMAGE_DIR).mkdir(exist_ok=True)
    
    # 加载数据
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    # 收集所有唯一图片URL
    url_map = {}  # url -> filename
    for item in data:
        url = item.get('image_url', '')
        if url:
            url_map[url] = url_to_filename(url)
    
    print(f"总共需要下载 {len(url_map)} 张图片")
    
    # 检查已存在的图片
    existing = sum(1 for fn in url_map.values() if os.path.exists(os.path.join(IMAGE_DIR, fn)))
    print(f"已存在 {existing} 张，需下载 {len(url_map) - existing} 张")
    
    # 并发下载
    success = 0
    failed = 0
    skipped = existing
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for url, filename in url_map.items():
            save_path = os.path.join(IMAGE_DIR, filename)
            if not os.path.exists(save_path):
                future = executor.submit(download_image, url, save_path)
                futures[future] = (url, filename)
        
        for i, future in enumerate(as_completed(futures), 1):
            url, filename = futures[future]
            ok, result = future.result()
            if ok:
                success += 1
                if result != "exists":
                    print(f"[{i}/{len(futures)}] ✓ {filename} ({result} bytes)")
            else:
                failed += 1
                print(f"[{i}/{len(futures)}] ✗ {filename}: {result}")
    
    print(f"\n完成！成功: {success}, 失败: {failed}, 跳过: {skipped}")
    
    # 更新数据文件，添加 local_image 字段
    url_to_local = {url: os.path.join(IMAGE_DIR, fn) for url, fn in url_map.items()}
    for item in data:
        url = item.get('image_url', '')
        if url in url_to_local:
            item['local_image'] = url_to_local[url]
    
    # 保存更新后的数据
    backup = DATA_FILE.replace('.json', '_with_local_images.json')
    with open(backup, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存更新后的数据到 {backup}")

if __name__ == "__main__":
    main()
