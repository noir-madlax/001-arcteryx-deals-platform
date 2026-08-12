# TASK: GearDrop 官网三品牌刷新（更新：2026-08-12）

## Why（一句话）

让 GearDrop 官网真实展示最新 Logo、Arc'teryx / Burton / Patagonia 品牌筛选与来源平台，并提供与当前 App 发布状态一致的下载引导。

## 当前状态：生产发布完成并通过公开回读（2026-08-12）

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
- 用户已明确回复“确认上线”，授权本次生产迁移、数据同步、主分支推送与公开回读。（来源：本任务用户消息，2026-08-12）
- Supabase 管理 API 已应用并登记 `20260812_products_brand` 与 `20260812130000_three_brand_full_price_catalog`；回读确认 `products.brand` 非空、默认 `arcteryx`、约束与索引存在，目录表/RLS 策略存在。（来源：迁移 API 200 与只读 SQL 回读，2026-08-12）
- 生产折扣数据质量门：`rows=8322 active=8322`，Outlet 6306、Backcountry 158、Burton 337、EVO 1168、MEC 185、REI 112、SSENSE 56，三品牌/平台门禁 `OK`。（来源：`tools/check_data_quality.py --online ...`，2026-08-12）
- 官方正价目录完成一次完整权威三品牌同步：Arc'teryx 370、Burton 495、Patagonia 488，共 1353；匿名 RLS 回读当前表与快照表均为 1353。（来源：官方目录命令输出、管理 SQL 与匿名 REST 回读，2026-08-12）
- `main` 已发布到 `216adb8304e16018f2b6d2567d3f85c961cd094e`；公开首页、Logo 与 mark 内容哈希均与该提交一致。（来源：Git remote、HTTPS SHA 回读，2026-08-12）
- 真实生产浏览器美国区显示总计 8322；当前筛选池 Arc'teryx 739、Burton 932、Patagonia 474，Burton 官网 337、Backcountry 158、EVO 1168。390×844 下 `scrollWidth=390`，Logo/App 引导与 Patagonia 卡片可见。（来源：Chrome DOM/截图与移动视口回读，2026-08-12）

## 假设与未验证边界

- 用户所说的官网按仓库部署文档与现有 App 配置解释为 `https://001.100app.dev/`。
- 没有可验证的 GearDrop 公共 TestFlight 邀请链接；页面仅链接 Apple TestFlight 安装页，并要求已受邀用户从 Apple 邀请邮件打开 App。
- Expo Doctor 的 20 项检查中 19 项通过；剩余项是分支既有的 13 个 Expo SDK 57 补丁/次版本落后。本任务未扩大为整套 App 依赖升级。
- 生产浏览器唯一 warning 是防误报逻辑主动跳过“今日上新”弹窗：`1406 items marked new today ... likely false positive, skipping modal`；商品、筛选与 App 引导均已渲染。

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
- 生产 App 数据校验：`products_content_range=0-0/8322`、`paginated_products_loaded=8322`，退出码 0。
- 最新 main 合并后再次验收：Python `Ran 160 tests in 3.183s` / `OK`；Node 7/7；App 35/35；TypeScript 与内联脚本解析通过。

## 下一步（按序）

1. 后续自动抓取观察 Burton / Backcountry / EVO 的 36 小时新鲜度门与三品牌最低数量门。
2. App Store 审核通过并可公开查询后，把“即将上线”替换为真实 GearDrop App Store 链接；在此之前不伪造公开下载入口。
3. 单独安排 Expo SDK 57 的 13 个补丁/次版本升级与真机回归，不混入本次网站发布。

## 死路

- 原工作树 `/private/tmp/geardrop-burton-patagonia-20260812.rs5mvZ/worktree` 已被系统清理，无法原地继续；已从保留提交创建新 worktree。
- `check_data_quality.py --file dealers/results.json` 直接读原始抓取结构会因缺少同步后才生成的 `sku_id/symbol` 字段失败；改为使用生产同步实际调用的 `item_to_row` 转换后质量门，结果通过。
- `npm run verify` 最后停在 Expo Doctor：13 个 Expo SDK 57 包补丁/次版本落后；单测、配置、TypeScript 三个前置步骤均已通过，未将依赖升级混入本次网页任务。
- 系统 Python 3.14 缺少 `scrapling/playwright/requests`，直接发现测试会在 5 个模块导入处退出；改用仓库现有测试依赖环境后，160 项全套测试通过。
- Supabase 数据库直连从当前网络返回 TLS EOF/IPv6 无地址；改用已登录账户的官方 Management API 迁移端点，迁移成功且历史与结构均独立回读。
- 首轮折扣同步在 EVO 成功后遇到 PostgREST `SSLV3_ALERT_BAD_RECORD_MAC`：EVO 1154 已写，Backcountry 0、Burton 187。随后按 dealer、10 行批次、指数退避只重放 Backcountry/Burton，分别达到 158/158、337/337，最终线上质量门通过。
- 首轮官方目录完整抓取在 Arc'teryx `mens/insulated-jackets` 被远端断开，表保持 0/0；单独探测恢复 200 后，以更长 timeout/retry 完整重跑，1353/1353 同步成功。
- 首次 Vercel 发布时首页和 manifest 已更新，但 `assets/brand/*` 返回 404；根因是 `.vercelignore` 的 `brand/` 同时匹配嵌套目录。收窄为 `/brand/` 并发布 `216adb8` 后，Logo/mark 返回 200 且哈希一致。
