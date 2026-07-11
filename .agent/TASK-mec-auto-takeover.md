# TASK: GitHub MEC 自动接管（更新：2026-07-11 15:30 EDT）

## Why（一句话）

当 OCI MEC 主节点失败或超过一个抓取周期未成功时，由已验证可访问 MEC 的 GitHub runner 自动接管，同时保持单写者和完整性保护。

## 当前状态：进行中

## 已确认事实

- OCI MEC 每 3 小时在 `1,4,7,...:00 UTC` 执行；来源：生产 OCI crontab。
- GitHub hosted runner run `29163565662` 对 MEC 1/2/3 页返回 HTTP 200 和 52/52/24 条；来源：workflow 日志。
- MEC 使用独立 Supabase lease scope `mec`，完整生产抓取通常约 4 分钟；来源：`crawler_leases` 与生产运行日志。
- `main` 当前为数据提交 `8d99795`，最近一次 OCI MEC 于 19:04 UTC 成功；来源：`git fetch origin main` 和提交日志。

## 假设（未验证；验证后移入上区）

- GitHub runner 安装现有 `requirements.txt` 后可完成全量 MEC scrape、Supabase sync 和 Git push。
- `stale-hours=3.1` 能在当前周期成功时跳过，在错过一个 3 小时周期时接管。

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

## 下一步（按序）

1. 合并并发布 workflow。
2. 依次验证非 force skip 和 force takeover。
3. 复核生产租约、质量门与数据提交。

## 死路

- 暂无。
