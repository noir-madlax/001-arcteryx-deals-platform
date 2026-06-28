"""把 dealers/_partial/<key>.json 合并成 dealers/results.json (前端读取的格式)"""
import json, time, os, glob

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
            prev = json.load(open(OUT))
            for key, block in (prev.get("dealers") or {}).items():
                out["dealers"][key] = block
            print(f"  (seeded from previous results.json: {', '.join(out['dealers']) or 'none'})")
        except Exception as e:
            print(f"  (could not seed from previous results.json: {e})")

    fresh_keys = []
    for path in sorted(glob.glob(f"{PARTIAL_DIR}/*.json")):
        d = json.load(open(path))
        key = KEY_BY_NAME.get(d.get("name"), os.path.basename(path).replace(".json",""))
        out["dealers"][key] = {
            "name":   d.get("name"),
            "region": d.get("region"),
            "count":  d.get("count", 0),
            "items":  d.get("items", []),
        }
        fresh_keys.append(key)
        print(f"  {key}: {d.get('count')} 件 ({d.get('saved_at')}) [fresh]")

    stale_keys = [k for k in out["dealers"] if k not in fresh_keys]
    for key in stale_keys:
        block = out["dealers"][key]
        print(f"  {key}: {block.get('count')} 件 [kept from previous — 本轮无新数据]")

    total = sum((b.get("count") or 0) for b in out["dealers"].values())
    out["total"] = total
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n=== TOTAL: {total} 件 → {OUT} (fresh: {len(fresh_keys)}, kept: {len(stale_keys)}) ===")

if __name__ == "__main__":
    main()
