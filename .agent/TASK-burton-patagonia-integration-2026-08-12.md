# TASK: Burton 与 Patagonia 接入（更新：2026-08-12 Asia/Taipei）

## Why（一句话）

让 GearDrop 从 Arc'teryx 单品牌数据与界面安全扩展到 Burton、Patagonia，并保留来源、品牌与价格证据，避免把跨品牌商品误归类或误写生产。

## 当前状态：Burton 官网与 Backcountry 本地接入、现场抓取和全量测试完成；生产迁移/同步/发布未授权、未执行

## 边界

- 在基于最新 `origin/main` 的独立工作树与分支中开发，不触碰主工作树的 App Store 未提交改动。
- 本任务不部署生产、不触发生产写入、不创建价格提醒、不提交对外 PR。
- 外部站点行为必须以本次官方页面/响应核验为准；无法验证的来源不得标为已接入。

## 自拟验收标准

1. Burton 与 Patagonia 都有明确、可追溯且可测试的采集/导入入口，输出统一产品 schema，并显式携带正确品牌。
2. 数据同步、Web 与 App 的产品模型不再把全部商品隐式视作 Arc'teryx；用户能按品牌识别或筛选，现有 Arc'teryx 行为保持兼容。
3. 两品牌的解析器、品牌隔离、SKU 稳定性与展示路径有定向测试；现有相关测试与静态检查通过。
4. 用真实但只读的官方/零售页面做最小运行时探针；若目标站阻断自动化，则保留失败关闭证据并明确未验证项。
5. Burton 商品必须同时覆盖官网 Outlet 与 Backcountry 的 Burton sale 集合；两个新来源各自拥有稳定 dealer/SKU、完整分页门和独立低水位，任一来源缺页不得发布该来源快照。

## 已确认事实

- 主工作树 `main` 有 9 项 App Store 相关未提交/未跟踪变更，且开工时落后 `origin/main` 224 个提交；来源：`git status --short --branch`（2026-08-12）。
- 独立工作树位于 `/private/tmp/geardrop-burton-patagonia-20260812.rs5mvZ/worktree`，分支 `codex/integrate-burton-patagonia-20260812` 基于 `origin/main=9779b14`；来源：`git worktree add` 输出及 `git status --short --branch`。
- 当前统一 dealer schema 在 `dealers/base.py` 中列出 dealer/url/name/image/price/currency/discount/in_stock 等字段，但该已读版本没有 `brand` 字段；来源：本会话 `codegraph explore` 对 `dealers/base.py` 的逐行源码输出。
- 已读 App `ProductRow` / `Product` 类型没有 `brand` 字段；来源：本会话 `codegraph explore` 对 `app/lib/types.ts` 的逐行源码输出。
- 干净工作树未包含 `.codegraph/`（该目录未纳入 Git）；已经向用户询问是否允许 `codegraph init -i`；来源：`codegraph status --json .` 返回 `initialized:false`。
- EVO 官方集合 `/collections/arcteryx`、`/collections/burton`、`/collections/patagonia` 均可由 Camoufox 读到真实商品；首次只读探针中 Burton 首屏 50 件/12 页、Patagonia 首屏 82 件/13 页，品牌与代表商品名解析正确；来源：本会话 `_fetch_browser_page` 运行输出。
- 完整三品牌只读探针在无跨页节流、单次重试配置下抓到 Arc'teryx 256、Burton 438、Patagonia 442 件，但 Patagonia 第 12、13 页收到 HTTP 429，因此 `complete=False`，未把缺页快照视为可发布；来源：本会话 `_scrape_browser` 原始输出。
- 基于上述现场证据，浏览器回退新增默认每页 5 秒节流和 10/20 秒递增重试等待；当前出口在探针后仍处于 429 窗口，尚未重新跑完一轮全量分页。
- Burton 官网旧 `/us/en/c/clearance` 会跳转到 `https://www.burton.com/en-us/collections/outlet`；公开 Shopify `products.json` 首次只读探针返回 HTTP 200、每页上限 250，集合元数据当前 `products_count=443`。来源：本会话浏览器 DOM 与 urllib 只读响应。
- Backcountry `https://www.backcountry.com/rc/burton-on-sale` 对 urllib 返回 HTTP 403、对 curl_cffi 返回 HTTP 202 挑战页，但浏览器可读；页面 `__NEXT_DATA__` 当前声明 `totalCount=159`、`totalPages=4`，第 1、2 页各 42 件且商品节点含稳定 `id`、Burton 品牌、库存、价格聚合、颜色、图片和 URL。来源：本会话应用内浏览器逐页只读 DOM/JSON 检查。
- Backcountry 的价格聚合若把 `minSalePrice` 与 `maxListPrice` 交叉配对会夸大部分商品折扣；接入必须保守配对 `minSalePrice` 与 `minListPrice`。来源：本会话首屏 42 件聚合字段对比。
- Burton 官网 Outlet 的折扣由 Regios 引擎动态渲染，Shopify `products.json` 中对应 variant 可仍是原价/原价；因此生产解析用 Shopify 目录核对 ID/vendor，价格则取官网渲染后的成对售价/划线价。来源：本会话官网 DOM 与 Shopify JSON 同 ID 对比。
- Burton 现场全量抓取完成：Shopify 目录 250+123=373 件，官网 16/16 页原始 ID 373/373 与目录集合完全相等；排除 Anon 和原价商品后输出 337 件折扣 Burton，`crawl_complete=true`。来源：`python -m dealers.burton` 与本地 partial 快照审计（2026-08-12）。
- Backcountry 公开只读 `/api/public/ux/graphql` 接口可绕开页面挑战而不绕过身份验证；现场全量抓取 4/4 页、159/159 条，输出 159 件 Burton，`crawl_complete=true`。来源：GraphQL HTTP 200 探针、`python -m dealers.backcountry` 与 partial 快照审计（2026-08-12）。

## 假设（未验证；验证后移入上区）

- 生产执行环境配合新增节流/退避后能够避免本地探针末尾的 EVO 429；需要在下一次获准的正式抓取中以 `crawl_complete=true` 和品牌计数回读确认。

## 已完成且已验证

- 已读取长任务协议正本。
- 已从远端 fetch 最新 `origin/main` 并建立干净独立工作树；`git status` 仅显示干净分支跟踪关系。
- 已实现 Python 与 JavaScript 共享的三品牌 canonical 契约；显式未知品牌或品牌/名称冲突均失败关闭，历史无品牌字段的记录继续解释为 Arc'teryx。
- EVO JSON 与 Camoufox 两条路径均按品牌过滤并输出 `brand`，完整性同时检查分页成功率和 Arc'teryx ≥100、Burton ≥20、Patagonia ≥20。
- Supabase schema、迁移、dealer/outlet 同步、质量门禁和 Arc'teryx 名称审计均已接入品牌字段；未执行生产迁移或写入。
- Web 与 Expo App 已增加品牌名称、品牌筛选、跨品牌搜索和品牌安全的商品名称；旧 App 预览缓存升级到 v2，避免无 `_brand` 的旧缓存闪现。
- 全量本地验收：Python `131 passed, 18 subtests passed`；Node 命名/品牌测试 `7 passed`；App `tsc --noEmit` 通过且 `30 passed`；两份 HTML 内联脚本可解析；`git diff --check` 通过。
- App 后续门禁：`verify:config` 通过；生产只读探针返回 products 5,863、price_history 84,814，分页/信号样本通过；iOS export 成功生成 3.9MB Hermes bundle，随后已把 `dist-check` 移到 Trash。
- 新增 `dealers/burton.py` 与 `dealers/backcountry.py`；两个来源拥有独立 dealer、稳定 source-ID SKU、严格品牌/URL 契约、分页完整性与低水位门禁，已接入主/回退运行脚本、GitHub Actions、Supabase 转换、Web/App 平台标签和定向测试。
- 本轮全量验收：Python `138 passed, 20 subtests passed`；Node `7 passed`；App `tsc --noEmit` 通过且 `30 passed`；HTML 内联脚本 1+2 份可解析；共享 runtime copies identical；`bash -n` 与 `git diff --check` 通过。
- 两个现场 partial 转换后共 496 行/496 唯一 SKU（Burton 337、Backcountry 159）；本地质量门输出 `dealers=backcountry:159, burton:337`、`brands=backcountry/burton:159, burton/burton:337`、`[quality] OK`。

## 下一步（按序）

1. 待用户明确授权后，先执行生产 `brand` 迁移并回读 schema/品牌分组。
2. 部署代码后运行 Burton、Backcountry 与 EVO 正式抓取/同步，按 dealer/brand 回读数量、价格和来源契约。
3. 通过生产质量门和 Web/App 实际显示验收后，才宣告线上接入完成。

## 死路（试过不行的，附失败原因）

- 当前工具会话没有暴露 `codegraph_*` MCP 调用；clean worktree 的 CodeGraph CLI 因 `.codegraph/` 未初始化不可查询。已临时只用旧主工作树索引识别候选入口，并要求后续读取最新工作树源码或在获准后重建索引。
- Patagonia 官方站在本地 HTTP 与应用内浏览器出口分别返回 Akamai 故障/拦截页，无法作为本次可靠直连抓取源；首版改用已验证可读的 EVO Patagonia 品牌集合。
- 完整 EVO 探针刻意用单次重试运行，末两页触发 429 并被完整性门禁拒绝；随后单页默认三次重试仍在同一限流窗口内失败。已根据证据加入跨页节流和递增退避，但没有把未重跑的配置称为现场已验证。
- `npm run verify` 在 Expo doctor 停止：仓库当前依赖树含 `react-native-screens` 4.25.2/4.27.0 重复，且 SDK 57 期望 screens ~4.26.0、react-native 0.86.2、react-dom 19.2.3；本任务未修改依赖锁。doctor 之后被跳过的 live-data 与 iOS export 已单独运行成功。
- 生产 Supabase 只读 `select=sku_id,brand` 当前返回 HTTP 400 / PostgreSQL 42703 `column products.brand does not exist`，所以迁移尚未执行，生产尚不能称为已接入；必须先执行 `dealers/supabase_migration_brand.sql` 再部署读取该字段的前后端。
- Backcountry 页面的 Camoufox 现场抓取连续返回 HTTP 202 挑战页；后续从官网 Next.js query 定义中找到同源公开只读 Product GraphQL，因此正式实现改用 GraphQL，不保留必然失败的页面路径。
- Burton 第一版仅依赖 Shopify variant `price/compare_at_price`，现场结果是 373 个目录商品但 0 个折扣；DOM 对比证明折扣由 Regios 动态渲染，因此修正为目录对账 + 渲染成对价。Outlet 还混入少量原价 Burton 与 Anon，它们保留在原始 ID 完整性计数中但不进优惠快照。
