"""把 dealers/_partial/<key>.json 合并成 dealers/results.json (前端读取的格式)"""
import json, time, os, glob
from pathlib import Path

PARTIAL_DIR = "dealers/_partial"
OUT = "dealers/results.json"
KEY_BY_NAME = {"SSENSE":"ssense","MEC":"mec","EVO":"evo","REI":"rei"}

def main():
    out = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "dealers": {}}
    # 用上一轮 results.json 播种：某个 dealer 本轮抓取失败（没产出 partial）时，
    # 保留它上次的数据，避免该 dealer 从静态文件 / supabase_sync 里凭空消失。
    # (Supabase 侧 supabase_sync 对缺失 dealer 本就跳过，靠 14 天 stale buffer 兜底；
    #  这里同步保住静态 results.json 的完整性，REI 偶发崩溃不再清空它的区块。)
    if os.path.exists(OUT):
        try:
            prev = json.loads(Path(OUT).read_text())
            for key, block in (prev.get("dealers") or {}).items():
                out["dealers"][key] = block
            print(f"  (seeded from previous results.json: {', '.join(out['dealers']) or 'none'})")
        except Exception as e:
            print(f"  (could not seed from previous results.json: {e})")

    fresh_keys = []
    for path in sorted(glob.glob(f"{PARTIAL_DIR}/*.json")):
        d = json.loads(Path(path).read_text())
        key = KEY_BY_NAME.get(d.get("name"), os.path.basename(path).replace(".json",""))
        items = d.get("items") or []
        # 空 partial（dealer 成功退出但抓到 0 件, 如 EVO 偶发被限流）也当"无新数据":
        # 保留上一轮的非空区块, 不让静态 results.json 退化成 0 件。
        # (Supabase 侧 supabase_sync 对 0 行本就跳过 stale cleanup, 存量行不动。)
        if not items and key in out["dealers"] and (out["dealers"][key].get("items")):
            print(f"  {key}: 0 件 [empty scrape — 保留上一轮 {out['dealers'][key].get('count')} 件]")
            continue
        out["dealers"][key] = {
            "name":   d.get("name"),
            "region": d.get("region"),
            "count":  d.get("count", 0),
            "items":  items,
            "refreshed_at": d.get("saved_at"),
        }
        fresh_keys.append(key)
        print(f"  {key}: {d.get('count')} 件 ({d.get('saved_at')}) [fresh]")

    stale_keys = [k for k in out["dealers"] if k not in fresh_keys]
    for key in stale_keys:
        block = out["dealers"][key]
        print(f"  {key}: {block.get('count')} 件 [kept from previous — 本轮无新数据]")

    total = sum((b.get("count") or 0) for b in out["dealers"].values())
    out["total"] = total
    # supabase_sync 只允许本轮真实产出非空 partial 的 dealer 更新时间。
    # 缺失/空抓取仍保留静态快照，但不能伪装成本轮新鲜数据。
    out["fresh_dealers"] = fresh_keys
    Path(OUT).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"\n=== TOTAL: {total} 件 → {OUT} (fresh: {len(fresh_keys)}, kept: {len(stale_keys)}) ===")

if __name__ == "__main__":
    main()
