# TASK: 修正 EVO Burton Baker Down 女款可售价格（更新：2026-08-13 02:19 CST）

## Why（一句话）

GearDrop 不得把 EVO 已售罄变体的历史低价显示成当前可购买价格。

## 当前状态：已完成

生产价格、公开列表、详情页和防复发代码均已修正并验证；PR #26 已合入 `main`。

## 边界

- 只修 EVO 可售变体定价与报告商品 `evo:products/174895-burton-ak-baker-down-jacket-women-s`。
- 不手工改 Supabase，不取消或并发打断已有定时刷新。
- 使用正式 `revalidate-dealer-prices.yml` 回写，并在工作流外独立读回。

## 已确认事实

- 两次独立请求 EVO 官方 `/products/174895-burton-ak-baker-down-jacket-women-s.js` 均显示：顶层 `price_min=5999`，但四个 `available=true` 的 Chestnut Brown XS/S/M/L 变体均为 `24499`，`compare_at_price=27495`。来源：2026-08-13 本会话两次 `curl | jq` 输出。
- 修正前生产 `products` 行为 `$59.99 / $274.95 / 78%`，状态 active。来源：2026-08-13 本会话 Supabase REST anon 只读查询。
- 修正前公开网页搜索该商品实际渲染 `$59.99 / $274.95 / -78%`。来源：2026-08-13 本会话浏览器 DOM 快照。
- `dealers.revalidate.parse_evo_browser_snapshot()` 原先把 `igProductData.lowestVariantPrice` 混入已筛选的可售变体价格；该字段可属于售罄清仓变体。来源：`dealers/revalidate.py` 修改前 diff 与官方样本。
- 分支 `codex/fix-evo-available-variant-price` 的提交 `cebe5a0` 已推送；PR 为 `#26`。来源：本会话 `git commit`、`git push`、`gh pr create` 输出。
- 生产单 SKU 工作流 `31624191672` 使用 `cebe5a0` 并成功完成；日志为 `loaded 1 dealer rows`、`evo ok=1 价变=1 缺货=0 隔离=0 错=0`、`[quality] OK`。来源：本会话 `gh run view --log`。
- 工作流外 Supabase 读回为 `$244.99 / $274.95 / 11%`、HTTP 200，并新增同值价格历史；旧 `$59.99 / 78%` 历史仍保留用于审计。来源：2026-08-13 本会话 REST anon 只读查询。
- 公开列表卡和详情页均实测显示 `$244.99 / $274.95 / -11%`，购买 CTA 仍指向 EVO SKU 174895。来源：2026-08-13 本会话浏览器 DOM 快照。
- PR #26 于 `2026-08-12T18:18:20Z` 合并，merge commit `41e1cc4`；`cebe5a0` 已由 `git merge-base --is-ancestor` 确认在 `origin/main`。来源：本会话 `gh pr view`、`git fetch` 和祖先检查。

## 假设

- 无。

## 已完成且已验证

- 浏览器解析只使用 `isOutOfStock=false` 的变体；已知全部售罄时返回 unavailable，不再使用产品级最低价。验证：新增两条精确回归测试。
- `python3 -m unittest discover -s tests -p 'test_dealer_revalidation.py' -v`：`Ran 31 tests ... OK`。
- 合并后的 `uv run --with-requirements requirements.txt python -m unittest discover -s tests -p 'test_*.py' -v`：`Ran 163 tests ... OK`。
- 合并后的 Web Node 测试为 10/10，App 测试为 35/35，App TypeScript `tsc --noEmit` 退出 0。
- `uvx ruff check --select E9,F63,F7,F82 ...`：`All checks passed!`；`git diff --check` 通过。

## 下一步

- 无，本任务验收完成。

## 死路

- 直接抓 EVO PDP HTML 返回 Cloudflare HTTP 403；同商品官方 `.js` 端点可稳定读取，故改用该权威结构化入口做双读。
- 系统 Python 跑 `test_dealer_scrapers.py` 时因缺少 `scrapling` 未启动；按仓库要求改用 `uv run --with-requirements requirements.txt` 后 21/21 及全量 162/162 通过。
- 全规则 Ruff 命中 `dealers/revalidate.py` 既有 42 条风格/宽泛异常问题；未扩大范围清理，改跑关键错误规则并通过。
