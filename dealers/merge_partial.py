"""把 dealers/_partial/<key>.json 合并成 dealers/results.json (前端读取的格式)"""
import json, time, os, glob

PARTIAL_DIR = "dealers/_partial"
OUT = "dealers/results.json"
KEY_BY_NAME = {"SSENSE":"ssense","MEC":"mec","EVO":"evo","REI":"rei"}

def main():
    out = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "dealers": {}}
    total = 0
    for path in sorted(glob.glob(f"{PARTIAL_DIR}/*.json")):
        d = json.load(open(path))
        key = KEY_BY_NAME.get(d.get("name"), os.path.basename(path).replace(".json",""))
        out["dealers"][key] = {
            "name":   d.get("name"),
            "region": d.get("region"),
            "count":  d.get("count", 0),
            "items":  d.get("items", []),
        }
        total += d.get("count", 0)
        print(f"  {key}: {d.get('count')} 件 ({d.get('saved_at')})")
    out["total"] = total
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n=== TOTAL: {total} 件 → {OUT} ===")

if __name__ == "__main__":
    main()
