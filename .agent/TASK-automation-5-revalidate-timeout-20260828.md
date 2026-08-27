# TASK: automation-5 revalidate timeout（更新：2026-08-28 03:50 Asia/Taipei）

## Why（一句话）

让每日 dealer PDP 重验证在 GitHub Actions 的 120 分钟预算内完成，同时保留精确 SKU 修复入口和跨日覆盖。

## 当前状态：待远端验证

## 已确认事实（每条带来源：file:line 或命令+输出摘要）

- GitHub Actions run `33099920613` 在 EVO 处理到 `300/1558` 后于 120 分钟 job timeout 被取消；本轮 `gh run view --log` 原始日志。
- `.github/workflows/revalidate-dealer-prices.yml` 的 schedule 原先没有行数边界，job `timeout-minutes` 为 120。
- `dealers/revalidate.py` 对无输入的 schedule 加载全部 dealer rows，并按 EVO、REI、MEC、SSENSE 串行处理。
- 成功 PDP 更新会刷新 `last_updated`，因此按 `last_updated` 最旧优先可形成跨日轮转；`dealers/revalidate.py:update_row`。

## 假设（未验证；验证后移入上区）

- 每 dealer 每日最多 50 条可在 120 分钟内完成；依据失败 run 中 EVO 每 50 条约 19 分钟，仍需下一次真实 schedule 运行确认。

## 已完成且已验证（附验证方式）

- 已加入 schedule-only 的每 dealer 50 条边界，并以 `last_updated, sku_id` 稳定最旧优先轮转。
- 精确 SKU allowlist 显式优先于 schedule cohort 限制。
- `git diff --check` 通过。
- `uv run python -m unittest tests.test_dealer_revalidation tests.test_workflow_guards tests.test_server_run_leases`：42 tests，OK。
- `uv run --with-requirements requirements.txt python -m unittest discover -s tests`：216 tests，OK。
- 使用仓库 requirements 中的 PyYAML 回读 workflow：`workflow_yaml=OK`，schedule 表达式保持为 50。

## 下一步（按序）

1. 为 schedule 注入每 dealer 50 条边界，并在脚本中按最旧更新时间稳定选取。
2. 保证精确 SKU allowlist 不受 schedule cohort 限制。
3. 推送修复分支；仅在 `origin/main` 仍是本轮基线时快进 main。
4. 下一次真实 schedule 验证 120 分钟终态。

## 死路（试过不行的，附失败原因——防止绕圈重试）

- 无界全量 schedule：EVO 仅处理 300/1558 即耗尽 120 分钟，后续 dealer 未执行。
