# TASK: GearDrop 官网三品牌刷新（更新：2026-08-12）

## Why（一句话）

让 GearDrop 官网真实展示最新 Logo、Arc'teryx / Burton / Patagonia 品牌筛选与来源平台，并提供与当前 App 发布状态一致的下载引导。

## 当前状态：发布候选已完成；等待生产迁移、数据同步与部署授权

## 已确认事实

- 主工作树 `main` 在本次任务开始时显示 `behind 232` 且包含用户现场，不作为施工目录。（来源：`git status --short --branch`，2026-08-12）
- 上一轮三品牌分支提交仍存在于 `ced830103dcc1f7cbba4c3d980b588f540383189`，但原临时 worktree 路径已不存在。（来源：`git show -s ced8301` 与 `git worktree list --porcelain`，2026-08-12）
- 本任务在独立分支 `codex/geardrop-web-refresh-20260812` 与独立 worktree 中施工。（来源：`git worktree add ... -b codex/geardrop-web-refresh-20260812 ced8301`，2026-08-12）
- `https://001.100app.dev/` 当前响应内容与 `origin/main:index.html` 完全一致；线上仍显示 `ARC'TERYX / Deals Tracker`，无品牌筛选、无 App 引导，品牌资源与 `site.webmanifest` 返回 404。（来源：HTTP SHA/headers 与 Browser DOM/截图，2026-08-12）
- 线上 Supabase `products` 表查询 `brand` 返回 HTTP 400 / PostgreSQL `42703 column products.brand does not exist`，因此三品牌页面现在只能回退到静态数据。（来源：生产 Supabase 匿名只读查询，2026-08-12）
- 线上现有平台行数为 Outlet 6280、EVO 257、REI 108、SSENSE 56、MEC 185；Burton 官网与 Backcountry 均为 0。（来源：生产 Supabase 匿名只读分组查询，2026-08-12）
- Apple Lookup API 对 App ID `6790165332` 返回 `resultCount: 0`，当前没有可验证的公开 App Store 商品页，因此官网只能诚实展示“App Store 即将上线”和 TestFlight 安装说明。（来源：Apple Lookup API，2026-08-12）
- 最新完整抓取结果：Burton 官网 337、Backcountry Burton 158、EVO 1154；合并静态结果 1891。（来源：本次完整抓取命令输出与 `dealers/results.json`，2026-08-12）
- 同步前转换后的新增/刷新候选为 1649 个唯一 SKU：Burton 官网 337、Backcountry 158、EVO Arc'teryx 243 / Burton 437 / Patagonia 474；转换后质量门 `rows=1649 active=1649`、`OK`。（来源：`item_to_row` 预演与质量门输出，2026-08-12）

## 假设与未验证边界

- 用户所说的官网按仓库部署文档与现有 App 配置解释为 `https://001.100app.dev/`。
- 未执行任何生产数据库迁移、数据写入、远端合并、推送或 Vercel 发布；长任务协议要求先取得用户明确授权。
- 没有可验证的 GearDrop 公共 TestFlight 邀请链接；页面仅链接 Apple TestFlight 安装页，并要求已受邀用户从 Apple 邀请邮件打开 App。
- Expo Doctor 的 20 项检查中 19 项通过；剩余项是分支既有的 13 个 Expo SDK 57 补丁/次版本落后。本任务未扩大为整套 App 依赖升级。

## 验收标准

- 真实公开网址可见最新 GearDrop Logo 与 App 下载引导。
- 品牌筛选至少包含 Arc'teryx、Burton、Patagonia；来源平台筛选与线上实际数据一致。
- 页面功能在桌面和移动宽度下可操作，筛选不会因旧缓存或旧脚本失效。
- 静态检查、定向测试/构建与公开网址运行时验收均有原始输出；无法完成的生产写入或 App Store 状态明确列为未验证。

## 已完成且已验证

- 已恢复三品牌提交到新的干净隔离 worktree。
- 官网头部、详情页、H5、隐私/支持/退订页与邮件模板统一使用已确认的 GearDrop Logo，并补齐 favicon、PWA manifest 与社交分享图。
- 品牌筛选固定展示 Arc'teryx / Burton / Patagonia，平台固定展示 Outlet / Burton / Backcountry / SSENSE / MEC / EVO / REI；无数据项保留并标为 `(0)`、禁用，不再从界面消失。
- 新增 iPhone 下载引导：价格历史、收藏、降价提醒；公开上架前明确标注“App Store 即将上线”，TestFlight 文案不虚构邀请链接。
- 修复 EVO 无限滚动时读取到上一页残留 Shopify Analytics 商品的问题；完整重抓后 1154 行均有图片。
- 多品牌本地运行时使用本次真实商品样本验收：Arc'teryx 1、Burton 2、Patagonia 1；Burton 筛选 2、Backcountry 筛选 1、Patagonia 筛选 1。
- 390×844 移动验收：`innerWidth=390`、`scrollWidth=390`、App 引导宽 358、Logo 宽 118，无横向溢出。
- Python 全套测试：`Ran 160 tests in 3.116s` / `OK`；网页定向守卫 20 passed；App 单测 35/35；`tsc --noEmit` 与配置检查通过。
- 干净安装：`npm ci --ignore-scripts --no-audit --no-fund`，输出 `added 625 packages`，退出码 0。

## 下一步（按序）

1. 用户确认生产操作后，先应用 `dealers/supabase_migration_brand.sql`，回读列与旧数据品牌默认值。
2. 同步本次 1649 个三品牌折扣候选；如同时上线正价产品手册，再应用 `supabase/migrations/20260812130000_three_brand_full_price_catalog.sql` 并同步官方目录。
3. 获取最新 `origin/main`，合并/解决自动数据更新后推送，由 Vercel 发布官网。
4. 独立回读公开网址、Supabase 品牌/平台计数、Logo/manifest、三品牌筛选、App 引导和移动布局；任何失败执行回滚或保持旧发布。

## 死路

- 原工作树 `/private/tmp/geardrop-burton-patagonia-20260812.rs5mvZ/worktree` 已被系统清理，无法原地继续；已从保留提交创建新 worktree。
- `check_data_quality.py --file dealers/results.json` 直接读原始抓取结构会因缺少同步后才生成的 `sku_id/symbol` 字段失败；改为使用生产同步实际调用的 `item_to_row` 转换后质量门，结果通过。
- `npm run verify` 最后停在 Expo Doctor：13 个 Expo SDK 57 包补丁/次版本落后；单测、配置、TypeScript 三个前置步骤均已通过，未将依赖升级混入本次网页任务。
- 系统 Python 3.14 缺少 `scrapling/playwright/requests`，直接发现测试会在 5 个模块导入处退出；改用仓库现有测试依赖环境后，160 项全套测试通过。
