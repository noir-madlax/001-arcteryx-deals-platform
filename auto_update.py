#!/usr/bin/env python3
"""
Arc'teryx 全球爬虫
自动更新数据并部署到Vercel
"""
import json
import subprocess
import sys
import os
from datetime import datetime

# 项目路径
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
H5_DIR = os.path.join(PROJECT_DIR, "h5")
DATA_FILE = os.path.join(PROJECT_DIR, "global_data.json")
H5_DATA_FILE = os.path.join(H5_DIR, "data.js")

def run_crawler():
    """运行爬虫并更新数据"""
    print(f"[{datetime.now()}] 开始运行爬虫...")
    
    # 这里调用现有的爬虫脚本
    # 可以根据需要选择global_scraper或其他爬虫
    from global_scraper import scrape_all_regions
    
    data = scrape_all_regions()
    
    if data:
        # 保存原始数据
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成前端data.js
        js_content = f"const PRODUCTS = {json.dumps(data, ensure_ascii=False)};"
        with open(H5_DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        print(f"[{datetime.now()}] 爬取完成，共 {len(data)} 个产品")
        return True
    
    return False

def deploy_to_vercel():
    """部署到Vercel"""
    print(f"[{datetime.now()}] 开始部署...")
    
    # Git commit
    subprocess.run(["git", "add", "-A"], cwd=PROJECT_DIR)
    subprocess.run(["git", "commit", "-m", f"update: auto crawl {datetime.now().strftime('%Y-%m-%d %H:%M')}"], cwd=PROJECT_DIR)
    
    # Vercel deploy
    result = subprocess.run(
        ["npx", "--yes", "vercel", "--prod", "--yes"],
        cwd=H5_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"[{datetime.now()}] 部署成功!")
        # 提取URL
        for line in result.stdout.split('\n'):
            if 'https://' in line and 'vercel.app' in line:
                print(f"  上线地址: {line.strip()}")
        return True
    else:
        print(f"[{datetime.now()}] 部署失败: {result.stderr}")
        return False

if __name__ == "__main__":
    if run_crawler():
        deploy_to_vercel()
    else:
        print("爬虫失败，跳过部署")
        sys.exit(1)
