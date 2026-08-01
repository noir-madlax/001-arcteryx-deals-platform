# TASK: automation-5 继续修复（更新：2026-08-01 11:41 UTC）

## Why（一句话）

让生产数据健康结论真正由用户要求的硬门和同一批官方价格证据决定，而不是由被绕过的聚合下限或替换样本决定。

## 当前状态：已停止自动修复（生产仍不健康）

## 边界

- 所有写入只在最新 `origin/main` 的干净临时 worktree 中进行，不修改用户主 checkout。
- 不直接或手工写生产数据库；只使用仓库正式刷新、复核和校验链路。
- 不为通过审计而强行恢复已下架或不再 active 的商品。
- 本轮属于用户明确要求“继续修复”后的新修复周期；仍以最小 diff、两轮代码修复为上限。

## 已确认事实（每条带来源）

- 2026-08-01T11:41Z fetch 后 `origin/main=7501f49509171ad664b4113adbebd8f3ec4962c3`；来源：`git fetch origin --prune && git rev-parse origin/main`。
- 用户主 checkout `HEAD=ffd565d2acaadbcfa4574000c8da3b44250d3d49`，工作树干净且落后远端 23 个提交；来源：`git status --short --branch` 与 `git rev-parse HEAD`。
- 本轮工作树 `/tmp/arcteryx-a5-continue-20260801.Jd8dOA`，分支 `codex/auto-fix-data-health-20260801-gates-static`；来源：`git worktree add` 与 `git switch -c` 输出。
- 上一轮 automation memory 记录：当前代码 full run 不执行正数聚合 `--min-rows 5000`，首次固定样本有 3 个 SKU 失资格；这些仅是历史线索，必须在本轮 live 重验。
- 2026-08-01T11:44Z 三个实时门：Outlet 3980（通过）；dealer 309（Evo 50/MEC 148/REI 67/SSENSE 44，通过当前 dealer 门）；full 4289（失败，Evo/us 50<100）。来源：本 worktree 的三个正式 `tools/check_data_quality.py --online` 命令原始输出。
- 最新静态端点均 HTTP 200；`data.js` 4321 条，其中 111 条超过 72h；`dealers/results.json` 498 条（Evo 242/MEC 148/REI 64/SSENSE 44）。来源：2026-08-01T11:44Z `curl` 只读解析。
- Lightsail dealer 主任务的 cron 是 `10:30Z`，生产 Evo/REI/SSENSE active 行都在 `10:35:56Z` 被同秒刷新为 50/67/44；上一个 GitHub dealer fallback 曾在 10:14Z 发布 Evo 242。来源：`ops/cron/lightsail-dealers.cron`、Supabase anon 只读行与 GitHub run `30694326819` 日志。
- Evo 直接 Shopify 分类 JSON 会把仅 50 条的结果标记完整；渲染后的正式 collection fallback 能产出 242 条。来源：`dealers/evo.py` 调用链、生产两次快照及 run `30694326819` 日志。
- MEC run `30697976158` 原始错误是 Camoufox `version.json` 缺失，而 `refresh-mec.yml` 安装步骤没有执行 `python -m camoufox fetch`。来源：`gh run view --log-failed` 与 workflow 当前内容。
- 当前 `arcteryx_skus.json` 4238 条按 manifest/lifecycle 规则投影后恰好 3980 条 eligible，与生产 Outlet active 完全一致；来源：本 worktree 只读投影脚本与在线 API。
- 修复提交 `b8a3e6138279c351d348adff42be212df0ca411a` 已直接快进到 `main`；dealer/MEC 数据提交 `8712188`、`85816cd` 均以它为祖先。来源：push 原始输出、`git log origin/main`。
- Dealer fallback run `30698389256` 成功，正式产出 Evo 249、REI 65、SSENSE 44；生产 dealer active 从 309 恢复到 506。来源：workflow 原始日志与在线质量门。
- MEC run `30698972147` 在修复 head 上成功，preflight 输出 `[mec] browser fallback runtime OK`，抓取/partial/sync 均为 148/148。来源：workflow 原始日志。
- 最终 active 4486：Outlet 3980、Evo 249、MEC 148、REI 65、SSENSE 44；时间范围 `2026-08-01T03:06:26Z .. 2026-08-01T12:12:14Z`。Outlet 与 dealer 门 exit 0；严格 full 门 exit 1，原始错误 `too_few_rows 4486 < 5000`。来源：2026-08-01T12:13Z 三个正式在线命令。
- 固定样本 replay 在最新 dealer/MEC 刷新后仍 exit 2：`rei:236297`、`rei:243366` 不再 eligible；未换样。原唯一确认错价 Evo 279633 的生产值已为 450/600 USD，独立两次官方 PDP 读取均为 450/600。来源：正式 `--sample-file` 输出、目标在线行与两次现有读取函数输出。
- 线上 `data.js` 仍 4321 条且 111 条超过 72h；新生成器的临时投影为 3980 条、最旧 `2026-08-01 03:06:26`。非强制 Outlet run `30699308546` 因 OCI 主 lease 正在运行而安全 skipped。来源：端点解析、投影命令与 workflow jobs。
- 只读 freshness monitor run `30699342191` 按预期失败：Outlet/Dealer/静态可访问检查成功，strict full check 输出 `too_few_rows`，aggregate step exit 1。来源：workflow 原始日志。

## 假设（未验证；验证后移入上区）

- 当前官方 active 供给可能低于 5000；已确认正规 Outlet/Dealer/MEC 刷新后的生产总数为 4486，但未扩大到新的官方地区来源，不能把“暂无 514 条”断言为永久供给上限。

## 验收标准

1. `tools/check_data_quality.py --online --min-rows 5000 ...` 对 active 少于 5000 的 full run 必须非零退出，对满足下限的数据保持通过；dealer override 语义不能回归。
2. 生产实际 active 总数必须达到 5000 才能把全量门判绿；若正规刷新后仍不足，照实保留失败。
3. 静态 fallback 的生成规则与实时 Supabase-first 语义一致；若 72 小时过期记录不应展示，加入确定性测试并通过正式发布链路验证。
4. 修复后重跑首次审计 JSON 的 `--sample-file`；任何 SKU 不再 eligible 都必须失败关闭，不换样。
5. 至少通过受影响定向测试、完整 unittest、Python compile、workflow YAML 解析和 `git diff --check`；推远端后验收对应 workflow 与实时端点。

## 已完成且已验证

- 已读取 automation memory、Obsidian 项目记忆与长任务协议。
- 已 fetch 并建立最新远端基线的独立分支/worktree。
- 第一轮代码修复已落在临时分支：严格执行 full aggregate floor；Evo 小 HTTP 快照转 browser；dealer snapshot 70% 骤降保护；MEC workflow 安装 Camoufox；静态 fallback 对成功 scope 移除/72h 过期行 fail-closed。
- 定向 51 个 unittest 通过；`compileall`、7 个 workflow YAML 解析、`git diff --check` 均通过。尚未推远端，不能称生产已修复。

## 下一步（按序）

1. 下次 Outlet 主 lease 结束后，让基于 `b8a3e61` 的正式 Outlet run 发布已修静态 fallback，再读回 72h 尾部应为 0。
2. 后续 run 继续保留同一首批 100 SKU；两条 REI 重新符合 active 官方候选前不得关闭固定样本门。
3. 若业务坚持 5000 硬门，需要通过新的、逐 SKU 官方可验证地区/来源补足 514 条，不能降低门或恢复历史 inactive 行。
4. 更新 automation/Obsidian 记忆，清理临时 worktree。

## 死路

- 不能用当前 public anon API读取 missing/inactive 行：RLS 明确只公开 `status=active`；改用 lifecycle 时间戳、静态快照和正式 workflow 日志交叉定位，没有尝试绕过 RLS。
