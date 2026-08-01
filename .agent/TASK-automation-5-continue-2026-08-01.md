# TASK: automation-5 继续修复（更新：2026-08-01 11:41 UTC）

## Why（一句话）

让生产数据健康结论真正由用户要求的硬门和同一批官方价格证据决定，而不是由被绕过的聚合下限或替换样本决定。

## 当前状态：进行中

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

## 假设（未验证；验证后移入上区）

- GitHub dealer fallback run `30698389256` 正在执行；预计可再次把 Evo 从 50 恢复到完整 collection 数量，需等待 live readback。
- 在不引入非官方地区/不可购买记录的前提下，当前官方 active 供给可能不足 5000；必须由严格门和刷新后的实时总数确认，不能调低用户门槛。

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

1. 跑完整 unittest 与静态 fallback 临时投影，审阅第一轮 diff。
2. 等待 run `30698389256`，对 live dealer rows 独立读回。
3. 提交/推送第一轮修复，触发 MEC、Dealer、Outlet 必要 workflow 并等待。
4. 生产三个门、静态端点、首次固定样本复核；更新记忆与清理。

## 死路

- 不能用当前 public anon API读取 missing/inactive 行：RLS 明确只公开 `status=active`；改用 lifecycle 时间戳、静态快照和正式 workflow 日志交叉定位，没有尝试绕过 RLS。
