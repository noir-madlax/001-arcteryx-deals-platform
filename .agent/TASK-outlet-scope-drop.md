# TASK: Outlet 女性范围数量骤降（更新：2026-07-12 02:45 EDT）

## Why（一句话）

恢复 Outlet 各地区完整列表发现，使女性范围不再因滚动未完成而触发 scope count guard，同时保留拒绝残缺数据覆盖生产的安全边界。

## 当前状态：进行中

## 已确认事实

- 生产 active Outlet 4,659 条，最新更新时间 2026-07-11 16:05 UTC；在线质量门仍为 `OK`；来源：生产 Supabase 与 `check_data_quality.py --online`。
- 最近三轮 GitHub Outlet fallback 在 `Refresh Outlet scrape and sync` 失败，OCI 03:00 轮也被 guard 拒绝；来源：Actions jobs 与 OCI `update.log`。
- guard 报告 us/ca/fr/at/it/es women 从约 99–124 降到 52–86；生产写入被拒绝，因此旧有效数据未被覆盖；来源：运行日志。
- `global_scraper.scroll_to_load_all` 每轮直接 `scrollTo(document.body.scrollHeight)`，仅以链接数连续 4 轮不变作为停止条件，最后才读取一次 tiles；来源：`global_scraper.py`。
- OCI US Women 增量滚动实验中，DOM 唯一链接从 15 持续增长到第 30 轮的 80，页面仍未到底；来源：2026-07-12 只读 Playwright 实验。
- 修复后本机只读运行结果：US=98、CA=94、FR/AT/IT/ES=134 women URLs，全部高于原 guard 的 70% 比例要求；来源：本机 Playwright `scrape_region` 实跑。

## 假设（未验证；验证后移入上区）

- 无。

## 边界

- 不降低 `MIN_SCOPE_RATIO`，不绕过 scope count guard。
- 不在验证前写 Supabase 或覆盖生产数据。
- 先用只读区域实验验证，再发布和生产实跑。

## 验收标准

1. US/CA/FR/AT/IT/ES women 列表发现不再触发当前 drop guard。
2. 单元测试、Python 编译、workflow YAML 与 shell 检查通过。
3. 生产 Outlet 完整运行通过 guard、Supabase sync 和在线质量门。

## 已完成且已验证

- 已建立 `codex/fix-outlet-scope-drop` 分支并完成根因级只读实验。
- 已实现逐屏增量滚动，只在真正位于底部且 DOM 数量与页面高度连续稳定时停止。
- 已验证六个触发 guard 的 women scopes 均恢复到 94–134 条，不需要放宽安全阈值。

## 下一步（按序）

1. 实现增量滚动和底部稳定停止条件。
2. 在 OCI 临时目录对受影响 women scopes 做只读运行时验证。
3. 合并部署后执行一次生产 Outlet 刷新。
4. 复核 manifest、数据库时间戳、质量门和租约。

## 死路

- 直接放宽 scope ratio 被排除：会允许残缺列表覆盖生产数据。
