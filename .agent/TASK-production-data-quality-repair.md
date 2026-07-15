# TASK: 生产数据质量门修复（更新：2026-07-15 12:02 EDT）

## Why（一句话）

让生产质量门只在真实数据不健康时失败，并让 Dealer、URL 状态和各上游抓取器能够从暂时失败中自动恢复。

## 当前状态：已合并、已刷新生产数据、最终质量硬门已通过

## 已确认事实（每条带来源）

- 当前实现基线为 `origin/main` 的 `92d7344e243118c70136f804a8516ecc77ee743c`；来源：`git worktree add ... origin/main` 输出。
- 2026-07-12 以来 Production Freshness Monitor 13 次失败 11 次，Refresh Dealer Data 23 次失败 21 次，Refresh Outlet Data 21 次失败 2 次；来源：`gh run list --limit 100 --json ...` 汇总。
- 当前生产中 Evo 有 152 条、SSENSE 有 53 条 active 商品超过 72 小时；SSENSE 最新数据约 84.5 小时；来源：2026-07-15 只读 Supabase 探针。
- Dealer 同步对本轮未出现的商品保留 14 天，但质量门在 active 商品超过 72 小时时失败；来源：`origin/main:dealers/supabase_sync.py` 与 `origin/main:tools/check_data_quality.py`。
- Outlet 有 1 条 active 商品保留历史 `url_http_status=404`，但同 URL 当前直接 GET 返回 HTTP 200；来源：2026-07-15 Supabase 探针与 `curl -L`。
- Outlet 工作流只运行 `check_product_urls.py --status missing`，不会复查 active+404/410；来源：`origin/main:.github/workflows/refresh-outlet.yml`。
- 最新 Dealer fallback 中 Evo 六个 Shopify JSON 入口全部 HTTP 403，REI 的 Camoufox/Playwright 在 `Browser.setDefaultViewport` 协议校验失败，SSENSE 两个列表页均抓取失败；来源：GitHub Actions run 29389288868。
- 当前依赖仅用宽范围 `camoufox[geoip]>=0.4,<1` 与 `playwright>=1.50,<2`；来源：`origin/main:requirements.txt`。
- 已确认 `camoufox 0.4.11 + playwright 1.58.0 + patchright 1.58.2 + curl_cffi 0.15.0` 在 Lightsail 生产爬虫机可运行；同一组合已在本地 Python 3.12 隔离环境重复安装成功；来源：远端 `pip show` 与本轮 `uv pip install -r requirements.txt` 输出。
- Evo 新站统一入口 `/collections/arcteryx` 暴露 7 页（40×6+12）；新回退完整抓到 252 个唯一商品，且 HTTP 路径在第 2 页 403 后会立即切换浏览器；来源：本地真实 Camoufox 全流程输出 `EVO_FULL_LIVE ... count=252`。
- SSENSE 在本机出口仍对浏览器返回 403，但 Lightsail 同一锁定浏览器组合对男/女页均返回 200，现有解析器分别得到 35/10 个商品；来源：2026-07-15 远端只读 Camoufox 探针。
- REI 在 Lightsail 同一锁定组合得到 23 个唯一商品；来源：2026-07-15 远端只读 `ReiScraper().scrape()` 探针。
- 修复已通过 PR #20 和 PR #21 squash 合并至 `main`；生产代码提交为 `7c53d4d` 和 `9fb6596`；来源：`gh pr view 20/21` 与 `git log origin/main`。
- Outlet 生产全量作业 `29425062293` 成功：4,940 条同步、0 批次错误，最终可见 active 4,843 条，陈旧 active+404 从 1 降为 0；来源：GitHub Actions 原始日志与同步后 `tools/check_data_quality.py --online ...` 输出。
- Dealer 生产全量作业 `29427012307` 成功：Evo 252、REI 23、SSENSE 45，共 320 条全部写入且 0 批次错误；加上 MEC 156 后完整 Dealer active 为 476；来源：GitHub Actions 原始日志与同步后在线质量检查。
- 最终 Production Freshness Monitor `29430572325` 中 Outlet、Dealer、Static fallbacks 三个独立步骤均为 `success`，聚合步骤输出 `All production checks passed.`；来源：GitHub Actions 原始日志。
- 最终只读生产全量画像为 5,319 条 active：Outlet 4,843、Evo 252、MEC 156、REI 23、SSENSE 45；重复键、必填字段、价格、折扣、币种、JP 禁入、陈旧 active、active+404/410 均未产生错误；来源：`.venv/bin/python tools/check_data_quality.py --online --max-age-hours 36 --max-product-age-hours 72 --min-rows 5000 --forbid-region jp`。

## 假设（未验证；验证后移入上区）

- 无。

## 验收标准

1. Dealer 生命周期定向测试覆盖：完整成功、部分成功、零结果失败、两次缺失转 inactive、恢复为 active，全部通过。
2. active+404/410 会在质量门前被复查；HTTP 200 会清除陈旧状态，真实 404/410 才继续失败。
3. Evo、SSENSE、REI 各有确定性解析/回退单测；依赖版本可重复安装。
4. 新鲜度监控独立执行 Outlet、Dealers、静态兜底，最终聚合为单一硬门；即使前一步失败也能产出全部结果。
5. `python -m unittest discover -s tests -v`、Python 编译、workflow YAML 解析、`git diff --check` 全部退出 0。
6. 对三个 Dealer 上游执行只读真实探针；无法在当前网络通过的来源明确记录原始响应，不把单测通过冒充线上修复。

## 已完成且已验证

- 已建立独立工作树与分支 `codex/fix-production-data-quality`，未触碰原脏工作区。
- Dealer partial 只有 `crawl_complete=true` 且非空才会成为 fresh scope；成功快照驱动 `active → missing → inactive`，失败/空/部分快照保留旧状态。
- Outlet/Dealer 成功重新发现商品时清除陈旧 404/410；Outlet 工作流会在质量门前主动复查 active+404/410。
- Evo 已实现当前 7 页集合浏览器回退；SSENSE 已实现列表页浏览器回退；REI 及浏览器栈版本已锁定。
- 生产监控已拆成 Outlet、Dealer、静态兜底三个独立步骤，并保留最终聚合失败硬门。
- 最终完整测试 `.venv/bin/python -m unittest discover -s tests -v`：38 个测试全部通过。
- `.venv/bin/python -m compileall -q dealers tools supabase_sync.py tests`：退出 0。
- PyYAML 解析 `.github/workflows/*.yml`：`YAML_OK 6 workflows`。
- `.venv/bin/python tools/check_product_urls.py --help` 与 `git diff --check`：均退出 0。
- PR #20、#21 均已合并，合并后又执行了 38 个单测、Python 编译、6 个 workflow YAML 解析和 `git diff --check`，均退出 0。
- Outlet 和 Dealer 全量生产刷新均成功，且各自的 workflow 内部生产质量门与本地独立在线复测均为 `OK`。
- 最终汇总监控硬门已在最新 `main` 上执行，三个独立检查均成功，聚合硬门通过。

## 下一步（按序）

1. 无待修复项；按现有调度持续运行 Outlet、Dealer 和 Production Freshness Monitor。
2. 后续可单独升级 `actions/checkout@v4` / `actions/setup-python@v5` 以消除 GitHub Node 20 弃用提示；该提示不影响本次生产验收。

## 风险与回滚

- 不直接删除生产商品；生命周期仅由成功、可信快照驱动。
- 不修改生产凭证或 Supabase schema。
- 代码已合并至 `main`；若需回滚，对 `7c53d4d` 和 `9fb6596` 执行非破坏性 revert，不回滚随后生成的数据刷新提交。

## 死路

- Evo 旧的六个浏览器分类 slug 已返回 404，不能作为 HTML 回退；改用当前统一集合入口。
- Evo 集合仅加 `?page=N` 会回到相同首屏；真实分页需要同时带 `numResults=40&page=N`。
- SSENSE 本机出口即使用 Camoufox 仍为 403；同一代码路径在实际 Lightsail 出口返回 200，因此保留生产节点探针作为验收来源。
- GitHub 仓库共享并发策略只保留一个 pending 作业；同时手动触发 Outlet 和 Dealer 会让较早的 pending Dealer 自动取消。生产处置必须串行触发。
- Outlet 结束时已有一条定时 Dealer 作业等待并随即开始；重复的手动 Dealer `29430314013` 已取消，保留并验收定时作业 `29427012307`。
