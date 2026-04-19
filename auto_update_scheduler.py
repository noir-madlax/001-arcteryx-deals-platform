#!/usr/bin/env python3
"""
始祖鸟数据自动更新脚本
运行爬虫 → 更新 global_data.json → 同步到 data.js（根目录）和 h5/data.js
"""
import subprocess
import sys
import os
import json
from datetime import datetime


PROJECT_DIR = os.path.expanduser('~/Desktop/hermes projects/001-arcteryx-deals-platform')
DATA_FILE   = os.path.join(PROJECT_DIR, 'global_data.json')
ROOT_DATA_JS = os.path.join(PROJECT_DIR, 'data.js')          # 主网站数据源
H5_DATA_JS   = os.path.join(PROJECT_DIR, 'h5', 'data.js')   # H5 版数据源


def run_crawler():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始更新始祖鸟数据...")
    os.chdir(PROJECT_DIR)

    try:
        result = subprocess.run(
            [sys.executable, 'auto_crawler.py'],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            print("✅ 爬虫执行成功")
            tail = result.stdout[-800:] if len(result.stdout) > 800 else result.stdout
            print(tail)
            return True
        else:
            print(f"❌ 爬虫执行失败 (返回码: {result.returncode})")
            print(f"错误: {result.stderr[-500:]}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 爬虫超时")
        return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False


def write_data_js(src_json: str, dst_js: str) -> bool:
    """将 global_data.json 写成 const PRODUCTS = [...]; 形式"""
    try:
        with open(src_json, 'r', encoding='utf-8') as f:
            products = json.load(f)

        # 校验: URL 格式 + 图片
        bad_url = sum(1 for p in products
                      if p.get('region') and f'/{p["region"]}/' not in p.get('url', ''))
        bad_img = sum(1 for p in products if not p.get('image_url'))
        print(f"  [{os.path.basename(dst_js)}] {len(products)} 条 | "
              f"URL 异常: {bad_url} | 缺图片: {bad_img}")

        with open(dst_js, 'w', encoding='utf-8') as f:
            f.write(f"const PRODUCTS = {json.dumps(products, ensure_ascii=False)};\n")

        print(f"  ✅ 已写入: {dst_js}")
        return True
    except Exception as e:
        print(f"  ❌ 写入失败 {dst_js}: {e}")
        return False


def sync_data_files():
    """把 global_data.json 同步到所有前端数据文件"""
    if not os.path.exists(DATA_FILE):
        print(f"❌ 找不到数据源: {DATA_FILE}")
        return False

    print("\n📦 同步前端数据文件...")
    ok1 = write_data_js(DATA_FILE, ROOT_DATA_JS)
    ok2 = write_data_js(DATA_FILE, H5_DATA_JS)
    return ok1 and ok2


if __name__ == "__main__":
    success = run_crawler()
    if success:
        sync_data_files()
    sys.exit(0 if success else 1)
