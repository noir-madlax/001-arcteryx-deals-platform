# TASK: Web 首屏加载提速（更新：2026-08-13）

## Why（一句话）

让生产网页像 App 一样先展示可用商品，再在后台补齐完整目录，消除用户长时间停留在“加载数据中…”的等待。

## 当前状态：已发布并验证

## 已确认事实

- 改动前生产 `https://001.100app.dev/` 的 `index.html` SHA-256 与当时的 `origin/main:index.html` 一致；来源：2026-08-13 本会话 `curl | shasum` 与 `git show origin/main:index.html | shasum`，均为 `8c89ede967d6cde362063337030e5d5b043c4a006e79c739f3e90a57c6a4433b`。
- 浏览器禁用缓存冷加载：文档 load 约 1.47 秒，第一张商品卡约 12.85 秒；来源：2026-08-13 Browser/CDP 实测。
- 生产页顺序请求 Supabase `products` 9 批（offset 0–8000），合计 8,347 行、约 1,171,045 编码字节、请求时长相加约 10.85 秒；来源：同一轮 Network 事件读回。
- Web 只在完整循环结束后赋值 `products = loadedProducts` 并调用 `render()`；来源：`index.html:1785-1817`。
- App 会先读 24 小时、最多 200 件的 AsyncStorage 预览缓存，再请求 200 件 US 预览并立即 `setProducts`，最后后台拉完整目录；来源：`app/lib/productPreview.ts:3-7`、`app/lib/supabase.ts:19-28`、`app/contexts/ProductsContext.tsx:44-69`。
- 本地 `.vercel/project.json` 与 Vercel CLI 均确认项目为 `arcteryx-deals-platform`（`prj_xRYhGGeWK40qlv4jEDg3PDbnaAcs`）；`vercel inspect https://001.100app.dev` 确认该域名当前指向此项目的 production deployment。

## 假设（未验证；验证后移入上区）

- 无。

## 验收标准

1. 无缓存时先请求 200 件预览并渲染，不等待完整目录；完整目录在后台补齐后结果数与线上 Supabase 一致。
2. 有效缓存时同步读取最多 200 件预览，不缓存完整 8,000+ 行目录；缓存超过 24 小时或结构非法时忽略。
3. 预览失败不阻塞完整请求；完整 Supabase 请求失败时仍保留已有预览并尝试 `data.js` 兜底。
4. JavaScript 语法检查、定向加载逻辑测试、现有相关测试/静态门通过。
5. 发布后独立读回 HTML 哈希；禁用缓存浏览器复测第一张卡明显早于完整目录，并记录原始时序。

## 已完成且已验证

- 已在 `origin/main` 建立隔离分支 `codex/web-startup-loading-20260813`。
- 已实现地区级、24 小时、最多 200 行的 Web 预览缓存；`node --test tests/test_web_product_preview.js` 为 3/3 通过。
- 已实现 200 行地区预览先渲染、完整目录后台补齐、首批完整数据降级渲染、静态 `data.js` 最终兜底；`python3 -m unittest ...test_web_memory_guards.py` 为 17/17 通过。
- `uv run --with-requirements requirements.txt python -m unittest discover -s tests -v`：`Ran 161 tests ... OK`。
- 内联脚本及新增脚本已通过 Node 语法编译；共享商品命名测试 `node --test tests/test_product_names.js` 为 7/7。
- 本地页面连接真实 Supabase、禁用缓存：第一张预览卡 2.998 秒，完整目录 22.247 秒；最终 `phase=complete`、总数 8,347、US 结果 2,157、60 张卡、控制台无 warning/error。
- 同一轮请求顺序为 1 个 `region=eq.us&limit=200&order=discount_pct.desc,sku_id.asc` 预览请求，然后 9 个 offset 0–8000 的完整请求；预览缓存为 200 行、165,602 字节。
- 二次访问从预览缓存显示 60 张卡用时 1.409 秒；缓存状态为 `phase=preview`，随后后台补齐。
- 人工阻断 `limit=200` 预览请求后，首批完整数据在 9.217 秒显示并最终 `phase=complete`、总数 8,347，证明预览失败不阻断权威目录。
- 人工阻断全部 Supabase products 请求后，缓存预览在 0.804 秒显示，随后 `data.js` 兜底进入 `phase=fallback`，60 张卡可用。
- 完整目录下品牌筛选从 US 2,157 件切到 Burton 932 件，仍保持 60 张分页卡；首卡详情链接有效生成。
- 在线商品名审计读取当前 8,347 个 active 商品，`rejected=0`、`blank=0`、`lost_tokens=0`、`gender_mismatch=0`，但因 28 个既存 `unknown_family`（例如 Cusec）返回退出码 1；该审计只读线上商品数据，本次未改商品命名逻辑。
- 实现提交 `ddd261ebeeea55d99c23978ea0ba5aa0169c00a4` 已无强推快进至 `main`，Vercel production deployment `dpl_CdorPM5Yib3NF1oUCH3mqk8PXSRa` 状态为 Ready，域名别名包含 `https://001.100app.dev`。
- 发布后独立读回：线上 `index.html` SHA-256 为 `48027e252e3d507dd534563340ffb3cb042afb466ab41788e1739ef8b7710850`，`web-product-preview.js` 为 `0533addfe4b960a40e4d1a7d0b4525fda2843c5a6f3ebf39c3708d5bf41a6d6f`，均与本地发布文件一致。
- 生产浏览器禁用 HTTP 缓存且移除预览缓存后，导航 1.729 秒进入 `phase=preview` 并展示 60 张卡/200 个预览结果，11.087 秒进入 `phase=complete`；相对改动前 12.85 秒才出现首卡，首屏提前约 11.12 秒。
- 生产 Network 事件确认 GET 顺序为一个 `region=eq.us&limit=200&order=discount_pct.desc,sku_id.asc` 预览请求（804 毫秒收到响应），随后九个 offset 0–8000、`limit=1000&order=sku_id.asc` 的完整目录请求。
- 生产最终状态为 `products=8347`、US `filtered=2157`、60 张分页卡；localStorage 只有 200 行 US 预览（165,602 字节），Burton 筛选返回 932 条且详情链接有效，控制台日志为空。
- 生产热缓存复测 1.486 秒展示 60 张预览卡/200 个结果，10.393 秒补齐 US 2,157 个结果；测试结束已删除测试预览缓存并恢复浏览器 HTTP 缓存设置。

## 下一步

- 无；任务关闭。

## 死路

- 直接运行 `node tools/audit_product_names.mjs` 失败：工具要求明确 `--online` 或 JSON `--file`；`--help` 也不是受支持参数。
- `--file data.js` 失败，因为该文件是 `const PRODUCTS = ...` JavaScript，不是工具要求的纯 JSON；改用 `--online`。
- 系统 Python 直接跑全量 unittest 因缺 `scrapling`、`playwright`、`requests` 出现 5 个导入错误；按仓库依赖使用 `uv run --with-requirements requirements.txt` 后 161/161 通过，确认不是代码回归。

## 风险与回滚

- 不改 Supabase schema、抓取器或 App。
- 回滚单位为本任务单个 Web 提交；生产发布后若完整目录、筛选或兜底异常，立即回退该提交。
