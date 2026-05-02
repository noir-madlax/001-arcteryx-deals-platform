"""跑所有 dealer scraper，汇总到 dealers/results.json。"""
from __future__ import annotations
import importlib, json, time, traceback
from pathlib import Path

DEALER_KEYS = [
    "ssense",
    "mec",
    # 后续加：rei, backcountry, steepandcheap, sportsshoes
]

def main():
    out = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "dealers": {}}
    total = 0
    for k in DEALER_KEYS:
        print(f"\n=== {k} ===")
        try:
            mod = importlib.import_module(f"dealers.{k}")
            scraper = mod.Scraper()
            items = scraper.scrape()
            out["dealers"][k] = {
                "name": scraper.NAME,
                "region": scraper.REGION,
                "count": len(items),
                "items": items,
            }
            total += len(items)
            print(f"  → {len(items)} 件")
        except Exception:
            print(f"  ERR\n{traceback.format_exc()[:600]}")
            out["dealers"][k] = {"error": traceback.format_exc()[:600]}
    out["total"] = total
    Path("dealers/results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n=== TOTAL: {total} 件 across {len(DEALER_KEYS)} dealers ===")
    print("→ dealers/results.json")

if __name__ == "__main__":
    main()
