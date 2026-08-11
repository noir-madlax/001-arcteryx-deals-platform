# GearDrop 经销商数据抓取

抓取结果统一写入 `dealers/results.json`，目前支持 Arc'teryx、Burton 与 Patagonia。所有新商品必须携带 `brand` canonical key：`arcteryx`、`burton` 或 `patagonia`。

## 当前状态

| # | 站点 | 状态 | 抓到件数 | 备注 |
|---|---|---|---:|---|
| 1 | **SSENSE** (US) | ✅ 可用 | 26 | StealthySession + solve_cloudflare（Camoufox 单飞过不了 CF）；列表 + 详情页颜色都有，sizes 待补 |
| 2 | **MEC** (CA) | ✅ 可用 | 127 | StealthyFetcher + JSON-LD `productGroupId/hasVariant` 拿到完整 sizes/colors |
| 3 | **EVO** (US) | ✅ 三品牌入口 | 动态 | Shopify JSON 优先；被 Cloudflare 阻断时，用 Camoufox 逐页渲染 `/collections/arcteryx`、`/collections/burton`、`/collections/patagonia`。每个品牌独立做最低数量与完整分页门禁 |
| 4 | Backcountry | ⚠️ 已停售 | 0 | Camoufox 进得去并且看到 1240 件 mens-jackets，但 `?ftxt=arcteryx` 返回 2 件 Outdoor Research 替代品（"找不到 → 推荐"）。**Arc'teryx 已撤出 Backcountry** |
| 5 | Steep & Cheap | ⚠️ 已停售 | 0 | Backcountry 同公司同情况 |
| 6 | Moosejaw | ❌ 已收购 | — | 重定向到 Public Lands，后者维护页 403 |
| 7 | **REI** (US) | ✅ 可用 | 10 | Camoufox 真 Firefox + 详情页 size-selector / color-swatch 抓 sizes/colors |
| 8 | Sierra | ❌ 反爬 | — | EC2 us-west-2 也返回 403；TJX 屏蔽云厂商 IP 段（不仅是海外）。非 headless 能进首页，品牌页 0 商品 |
| 9 | The Last Hunt | ⚠️ 无库存 | 0 | 站点正常但已不售 Arc'teryx（搜索返回其他品牌） |
| 10 | Altitude Sports | ⚠️ 无库存 | 0 | 同上，搜索返回 Garmin/Sweet Protection 等 |
| 11 | SportsShoes (UK) | ⚠️ 无库存 | 0 | `?brands=Arc'teryx` 过滤器无效，返回 72 件全是 Saucony/Asics（**不售 Arc'teryx**） |
| 12 | Zalando Lounge | ❌ 需登录 | — | 闪购站，所有品牌页要会员登录 |
| 13 | 好日子 (CN) | ❌ SSL/不存在 | — | TLS connect error；域名疑似失效 |

表内历史数量仅作旧调查记录；当前数量必须以本次 `dealers/results.json`、Supabase readback 和质量门禁输出为准。

## 文件结构

- `base.py` — DealerScraper 基类（统一 fetch、parse、价格归一化、字典输出）
- `brands.py` — 三品牌 canonical key、旧数据兼容与来源一致性校验
- `recon.py` / `recon_stealthy.py` / `recon_v3.py` — 三轮侦察脚本
- `ssense.py` — SSENSE 抓取器（Fetcher tier）
- `mec.py` — MEC 抓取器（Stealthy tier）
- `run_all.py` — 并行运行所有 scraper，输出 `results.json`
- `supabase_migration_brand.sql` — `products.brand` 回填、约束与索引迁移

## 使用

```bash
# 安装依赖
pip3 install --user "scrapling[fetchers]"
~/Library/Python/3.13/bin/scrapling install

# 跑所有可用站点
python3 -m dealers.run_all

# 单站调试
python3 -m dealers.ssense
python3 -m dealers.mec
python3 -m dealers.evo
```

## Burton / Patagonia 发布顺序

1. 先在 Supabase 执行 `dealers/supabase_migration_brand.sql`，确认三品牌分组查询成功。
2. 再部署读取 `brand` 的 Web/App 与同步代码。
3. 跑 EVO 抓取和 `merge_partial`；只有 `crawl_complete=true` 且 Arc'teryx ≥100、Burton ≥20、Patagonia ≥20 才允许进入同步。
4. 同步后运行 `tools/check_data_quality.py`；门禁按 `dealer/brand` 复核，不能只看 EVO 总量。

本仓库改动本身不会执行生产迁移或写入。Patagonia 官方站当前在自动化出口返回 Akamai 故障/拦截页面，因此首版数据入口采用 EVO 的 Patagonia 官方品牌集合；不要把故障页解析成商品。

## 后续要做

- [x] EVO：Shopify JSON + Camoufox 渲染回退，并按品牌隔离与分页完整性检查
- [ ] Backcountry/S&C：找他们的真实 brand URL 模式（可能藏在 sitemap.xml）
- [ ] REI Outlet：调用其 Algolia 搜索 API（需要 appId/apiKey）
- [ ] Sierra：海外 IP 测试（VPN 到美国）
- [ ] SportsShoes：手动浏览找到正确品牌 URL
- [ ] 落 Supabase 新表 `dealer_products`，前端 tab 切换"Outlet vs 经销商"
