# TASK: Arc'teryx / Burton / Patagonia 三品牌正价产品手册目录（2026-08-12 Asia/Taipei）

## Why（一句话）

把三个品牌的官方正价商品归入与 Deals 隔离的 Yearbook 目录，为产品手册提供稳定、可追溯、可重复抓取的事实数据。

## 当前状态

本地实现、三站只读验收、最新数据基线合并和最终回归均已完成；未执行任何生产写入。

## 边界

- 继续在隔离工作树 `/private/tmp/geardrop-burton-patagonia-20260812.rs5mvZ/worktree` 和分支 `codex/integrate-burton-patagonia-20260812` 上开发，不触碰主工作树未提交改动。
- 正价目录只读/写入 `catalog_*` 边界，不混入 Deals `products` / `price_history`。
- 本任务不执行生产 migration、Supabase 同步、部署、push 或 PR。
- 只保留产品手册需要的事实字段；不批量复制官网描述、图片文件或其他受保护内容。

## 自拟验收标准

1. Arc'teryx、Burton、Patagonia 各有官方正价目录入口，产品行显式带 `brand`、稳定官方 ID/URL、基础价格、性别/分类和来源证据。
2. 三品牌均有独立完整性低水位、品牌隔离和分页/计数对账；任一品牌不完整时整次正式快照失败关闭。
3. 已有 Arc'teryx 幂等快照、missing/inactive lifecycle 和 partial-run 保护保持兼容，不因多品牌改造而误衰老其他品牌。
4. Yearbook Web/App 层能正确识别三品牌并提供品牌筛选；Deals 路径不受影响。
5. 三个官方入口都完成当前只读全量探针，并通过快照唯一性、字段边界、重复运行幂等性和全仓回归测试。

## 已确认事实

- 当前隔离分支工作树干净，较 `origin/main` ahead 2；最新两提交为 `58dee6d` 三品牌 Deals 接入和 `ac64f91` Burton 官网/Backcountry 来源。来源：本会话 `git status` / `git log`。
- 历史 Yearbook MVP 使用官方 feed、独立 `catalog_products` / `catalog_product_snapshots`、幂等快照和 partial-run 失败关闭；历史一次 Arc'teryx US 完整运行为 365 件/355 已分类。这是历史线索，当前数量必须重跑。来源：本会话已读 memory/rollout summary。
- CodeGraph 工具本会话未暴露，且该 clean worktree 历史已确认没有 `.codegraph/`；结构盘点将使用精确文件列表和已知入口的逐文件读取。
- 当前分支实际不含历史 Yearbook 文件；本次从历史架构重新落地，并直接升级为 `catalog_product_id = brand_key:official_product_id` 的三品牌隔离模型。
- Burton 官方 `agents.md` 明确允许只读 collection JSON；2026-08-12 全量为 1,027 个店铺商品，其中 vendor=Burton 917，最终 `Current` 正价款式 495（排除 Anon/Outlet/Future）。
- Patagonia 美国站在当前自动化出口返回 Akamai 404/故障页；Patagonia 澳洲官方 `agents.md` 明确允许只读 collection JSON。2026-08-12 全量为 1,455 个颜色商品页，按官方 group 聚合并保留 `flag:Order` 后为 488 个正价款式。
- Arc'teryx 官方 US feed 本轮为 370 个款式，360 个带官方分类（97.3%）。三品牌联合 dry-run 为 1,353 款、1,343 款已分类，`complete_brands=arcteryx,burton,patagonia` 且 `authoritative=true`。
- 联合探针命令：`python3 -m catalog.official_catalog --dry-run --delay 0.25 --timeout 30`；关键原文：`observed=1353 by_brand={'arcteryx': 370, 'burton': 495, 'patagonia': 488} categorized=1343 ... authoritative=true` 与 `dry-run: no files or remote tables changed`。
- 最终回归：`uv run --with-requirements requirements.txt python -m unittest discover -s tests -p 'test_*.py' -v` 为 `Ran 156 tests ... OK`；`node --test tests/test_product_names.js` 为 7/7；App `npm test` 为 35/35，`npm run typecheck`、`verify:config`、`verify:live-data` 和 iOS export 均退出 0；Ruff 为 `All checks passed!`。
- `npm run verify` 唯一中断点是既有 Expo Doctor 依赖漂移：`react-native-screens` 4.25.2 与 expo-router 内 4.27.0 重复（SDK 期望 ~4.26.0），另有 `react-dom`/`react-native` patch 偏差。本任务未改 `package.json`/lock，后续 live-data 与 iOS export 已单独通过；不在本任务扩大升级范围。
- 功能提交为 `b3bd153 feat: add three-brand official yearbook catalog`；随后无冲突合并 `origin/main` 的两个纯数据刷新提交。合并后复跑结果仍为 Python 156/156、Node 7/7、App 35/35 与 TypeScript 通过。

## 假设（待验证）

- Patagonia AU 是第一版可现场全量核验的官方市场；美国站目录接入仍需未来在可正常访问 Akamai 的执行环境单独验证，不能把 AU 价格当成 US 价格。
- “正价商品”定义为当前主线、非 sale/outlet 的官方款式；历史/折扣款继续留在 Deals，不进入 Yearbook 正价快照。

## 下一步

1. 生产 migration、Supabase 同步、部署、push 与 PR 留待单独授权。
2. 若获授权上线，先应用独立 catalog migration，再跑同一三品牌完整快照、执行显式 `--sync-supabase`，随后读回三品牌数量与随机样本；不得用 HTTP 200 代替业务验收。
3. Expo Doctor 的既有依赖漂移另开范围处理，不与正价目录发布绑在一起。
