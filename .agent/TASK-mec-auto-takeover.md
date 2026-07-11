# TASK: GitHub MEC 自动接管（完成：2026-07-11 15:38 EDT）

## Why（一句话）

当 OCI MEC 主节点失败或超过一个抓取周期未成功时，由已验证可访问 MEC 的 GitHub runner 自动接管，同时保持单写者和完整性保护。

## 当前状态：已完成并通过生产验收

## 已确认事实

- OCI MEC 每 3 小时在 `1,4,7,...:00 UTC` 执行；来源：生产 OCI crontab。
- GitHub hosted runner run `29163565662` 对 MEC 1/2/3 页返回 HTTP 200 和 52/52/24 条；来源：workflow 日志。
- MEC 使用独立 Supabase lease scope `mec`，完整生产抓取通常约 4 分钟；来源：`crawler_leases` 与生产运行日志。
- `main` 当前为数据提交 `8d99795`，最近一次 OCI MEC 于 19:04 UTC 成功；来源：`git fetch origin main` 和提交日志。
- PR #7 已合并，merge commit `a587f0a`；来源：`gh pr view 7`。
- 健康主节点测试 run `29165381483` 只运行 lease-gate，`refresh-mec` 为 skipped；来源：GitHub Actions job 状态。
- 强制接管 run `29165435922` 完成 128/128、Supabase upsert 128/128、质量门 OK、数据提交 `b559a25` 和 lease release success；来源：完整 workflow 日志、main 提交和生产 SQL。

## 假设（未验证；验证后移入上区）

- 无。

## 边界

- 不改变 OCI 主节点；GitHub 只做故障接管。
- 使用相同 `mec` lease、完整性闸门和全局 GitHub 写并发组。
- 不允许不完整 partial 或 0 条结果写入生产。

## 验收标准

1. 健康 OCI 状态下手动非 force workflow：lease-gate 成功、refresh job skipped。
2. 手动 force workflow：128/128、Supabase sync、质量门、Git push、lease release 全部成功。
3. 单元测试、shell 语法和 workflow YAML 解析通过。

## 已完成且已验证

- 已建立 `codex/mec-auto-takeover` 分支。
- 已新增独立 `Refresh MEC Data` workflow：每个 OCI 窗口后 20 分钟检查 `mec` scope，`stale-hours=3.1`，健康/运行中跳过，失败或错过本周期时接管。
- 已抽出共享 `tools/check_mec_partial.py`，OCI runner 与 GitHub fallback 使用同一 128/expected/full-complete 闸门。
- 已运行 14 个单元测试、Python 编译、shell 语法、全部 workflow YAML 解析和 `git diff --check`，均通过。
- 已验证非 force 健康跳过与 force 完整接管两条生产路径。
- 已验证生产 `crawler_leases.mec` owner 为 `github-actions-mec-29165435922`、状态 `success`、message 为 workflow success。
- 验收期间发现 Lightsail server runner 遇并发 Git 提交会 non-fatal push failure；已改为 pull --rebase 后严格 push，失败会让 lease 标记 failed。

## 下一步（按序）

1. 观察下一个定时窗口；健康 OCI 情况下 GitHub 应继续自动跳过。

## 死路

- 19:30 Lightsail dealer 数据提交首次 push 被 PR #7 并发更新拒绝；人工 rebase 后成功推送为 `24a363f`。因此补上 server runner 的严格 rebase/push 修复。
