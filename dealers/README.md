# 经销商数据抓取（Scrapling）

基于 [Scrapling 0.4.7](https://github.com/D4Vinci/Scrapling)，对 Arc'teryx 经销商做品牌过滤抓取。

## 当前状态

| # | 站点 | 状态 | 抓到件数 | 备注 |
|---|---|---|---:|---|
| 1 | **SSENSE** (US) | ✅ 可用 | 26 | 纯 HTTP（Fetcher）+ JSON-LD |
| 2 | **MEC** (CA) | ✅ 可用 | 129 | StealthyFetcher + HTML |
| 3 | EVO | ❌ Cloudflare | — | Turnstile 顽抗，`solve_cloudflare` 也只通进首页 |
| 4 | Backcountry | ❌ Akamai | — | 所有 URL 返回 404 阻挡页（bot 检测） |
| 5 | Steep & Cheap | ❌ Akamai | — | 同 Backcountry（同公司） |
| 6 | Moosejaw | ❌ 已收购 | — | 重定向到 Public Lands，后者维护页 403 |
| 7 | REI Outlet | ❌ Akamai | — | 多 URL 返回 timeout 或 prods=0 |
| 8 | Sierra | ❌ 反爬 | — | EC2 us-west-2 也返回 403；TJX 屏蔽云厂商 IP 段（不仅是海外）。非 headless 能进首页，品牌页 0 商品 |
| 9 | The Last Hunt | ⚠️ 无库存 | 0 | 站点正常但已不售 Arc'teryx（搜索返回其他品牌） |
| 10 | Altitude Sports | ⚠️ 无库存 | 0 | 同上，搜索返回 Garmin/Sweet Protection 等 |
| 11 | SportsShoes (UK) | ⚠️ 无库存 | 0 | `?brands=Arc'teryx` 过滤器无效，返回 72 件全是 Saucony/Asics（**不售 Arc'teryx**） |
| 12 | Zalando Lounge | ❌ 需登录 | — | 闪购站，所有品牌页要会员登录 |
| 13 | 好日子 (CN) | ❌ SSL/不存在 | — | TLS connect error；域名疑似失效 |

**当前总量：155 件 (2/13 站点)**

## 文件结构

- `base.py` — DealerScraper 基类（统一 fetch、parse、价格归一化、字典输出）
- `recon.py` / `recon_stealthy.py` / `recon_v3.py` — 三轮侦察脚本
- `ssense.py` — SSENSE 抓取器（Fetcher tier）
- `mec.py` — MEC 抓取器（Stealthy tier）
- `run_all.py` — 并行运行所有 scraper，输出 `results.json`

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
```

## 后续要做

- [ ] EVO：尝试 [Camoufox](https://github.com/daijro/camoufox) 或 FlareSolverr 代理服务
- [ ] Backcountry/S&C：找他们的真实 brand URL 模式（可能藏在 sitemap.xml）
- [ ] REI Outlet：调用其 Algolia 搜索 API（需要 appId/apiKey）
- [ ] Sierra：海外 IP 测试（VPN 到美国）
- [ ] SportsShoes：手动浏览找到正确品牌 URL
- [ ] 落 Supabase 新表 `dealer_products`，前端 tab 切换"Outlet vs 经销商"
