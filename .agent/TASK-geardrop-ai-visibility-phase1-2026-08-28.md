# TASK: GearDrop AI 可见度第一阶段（更新：2026-08-28 16:08 Asia/Taipei）

## Why（一句话）

把 GearDrop 从“技术上可抓取”推进到“能被搜索与生成式答案稳定识别、区分、引用”，优先补齐实体一致性、原创数据内容、英语信息层与目录新鲜度闭环。

## 当前状态：实现与本地验收完成，待发布

已在隔离 worktree 完成代码、生成资产、测试、Vercel 本地构建和真实浏览器验收；尚未提交、推送或修改生产、App Store Connect 与域名。

## 边界

- 用户于 2026-08-28 回复“好的 做吧”，授权执行上一轮明确列出的第一阶段：实体统一、正式 App Store 双向链接、目录新鲜度闭环、3 个原创数据页与 en-US 核心信息层。
- 不购买、选择或迁移品牌域名；在用户给出精确域名之前继续使用 `https://001.100app.dev/` 作为 canonical。
- 不伪造独立背书、用户评价、品牌授权、AI 提及或价格保证；内容事实只取 GearDrop 可复现数据与公开原始来源。
- 不批量生成同质化关键词页；首批只做可长期维护、能回答冻结问题面板的高价值页面。
- App Store 正式审核、版本提交和公开版本发布不在本任务内；只允许把既有公开 App Store 1.0 与网站实体安全互链。

## 已确认事实

- 隔离分支 `codex/geardrop-ai-visibility-phase1-20260828` 起点为最新 `origin/main` `cd88c3e0d992da6470a166f8cf64defef0f32f77`；共享主工作树的未跟踪审计资产未被修改。（来源：`git fetch`、`git worktree add`、`git status`）
- 2026-08-28 生产 `tools/check_geo_readiness.py --base-url https://001.100app.dev/` 输出 `passed=81 failed=0 total=81`；OAI-SearchBot、GPTBot、PerplexityBot 与 Googlebot 读取 `/about.html` 均为 HTTP 200。（来源：本会话命令原始输出）
- 同日公网 `catalog-status.json` 与 `sitemap-products.xml` 均声明 8,244 个 URL、快照时间 `2026-08-28T01:28:39+00:00`；实时只读目录为 8,225 行，`tools/generate_geo_catalog.py --online --check` 明确列出三个 GEO 资产 stale。（来源：本会话生产读回与命令原始输出）
- 当前首页只声明 `zh-CN` 与同 URL 的 `x-default`；静态 sitemap 有 11 条 URL，其中 1 个指南、3 个品牌页。Organization JSON-LD 没有 `sameAs`，首页只链接通用 TestFlight 应用而未链接 GearDrop 正式 App Store 页面。（来源：本会话生产 HTML/XML/JSON-LD 解析）
- Apple 公开 Lookup API 返回 `GearDrop: Outdoor Deals` 1.0、App ID `6790165332`，公开 US/TW App Store 页面存在；`sellerUrl=null`。（来源：2026-08-28 Apple Lookup 只读输出）
- 2026-08-14 留档 Gemini consumer-web 基线为 72/72 完成、52 次有效；无提示提及 0/41、提示品牌后完全正确 0/11。该历史基线不能替代本轮跨平台复测。（来源：`geo/audits/2026-08-14-gemini-exploratory/metrics.json`）
- Apple US storefront 的公开产品数据确认 App ID `6790165332` 的 `softwareInfo.supportUrl=https://001.100app.dev/support.html`、`privacyPolicyUrl=https://001.100app.dev/privacy.html`、`websiteUrl=null`；官网候选首页反向链接同一个正式 App Store 产品页，因此无需 App Store Connect 写入即可完成本阶段实体互链。（来源：2026-08-28 带 US storefront header 的 Apple 公共只读响应）
- 发布前再次 fetch 后，最新 `origin/main` 为 `bc948264427498d2a86d57ab3f6aadc580f60ad0`；相对开工点只多一次自动数据提交，修改 `.crawl_manifest.json`、`arcteryx_skus.json`、`data.js`、`global_data.json`、`publication.json`，不与本次代码文件重叠。（来源：`git fetch`、`git show`、`git diff --name-status`）

## 假设（未验证；验证后移入上区）

- IndexNow 生产密钥与 key location 尚未配置；脚本无凭证时明确输出 `skipped_missing_credentials`，不会伪报成功，也不阻断目录同步。
- 本阶段提升的是机器可发现性、实体一致性和可引用证据，不代表 GearDrop 已经获得新的 AI 提及、引用或推荐；实际效果必须另行重跑跨平台基线。

## 验收标准

1. 网站与 App Store 实体互链：可见正式 App Store CTA，Organization/SoftwareApplication 图谱只连接真实受控对象，不连接品牌或零售商为 `sameAs`。
2. 三个原创数据页和 en-US 核心页具备可读正文、唯一 H1、canonical、双向 hreflang、元描述、开放图谱和可解析 JSON-LD；来源、时间和边界可见。
3. 每个成功数据刷新路径都原子重生成 `sitemap-products.xml`、`catalog-status.json`、`catalog-status.html`；变更 URL 可经 IndexNow 脚本通知，凭证不进仓库，失败状态可审计。
4. GEO 内容生成检查、目录生成检查、定向测试、全量 Python/Node 测试、生产构建和桌面/390px 运行时验收通过。
5. 发布前冻结提交、文件清单、生产允许差异与回滚点；发布后从新请求独立回读代表页、sitemap、App Store 链接、语言关系和生产 GEO 合同。

## 已完成且已验证

- 已读取长任务协议、内容研究写作技能、项目长期记忆、既有 GEO 任务档案与本轮只读诊断证据。
- 已同步最新远端并创建干净隔离 worktree；未触碰共享主工作树。
- 已实现中文／英文核心信息层、正式 App Store 实体关系、Organization／SoftwareApplication JSON-LD、canonical 与双向 hreflang；静态内容生成器当前管理 20 个页面资产。
- 已实现 3 个基于当前 GearDrop 第一方目录快照的原创分析：目录覆盖、品牌 × 零售来源、地区 × 品牌。页面公开观察时间、测量边界和方法链接，不做跨币种虚假价格比较。
- 已把动态目录状态页扩展为中英文共 8 个页面，并生成独立 `sitemap-insights.xml`；最近一次在线快照为 `2026-08-28T08:34:50+00:00`、8,204 个活动产品 URL。
- 已让 EC2 更新脚本与三个 GitHub 刷新工作流在成功目录刷新后重生成完整 GEO 数据资产；新增 IndexNow 通知器的 check／dry-run／缺凭证可审计分支。
- 已修正 Vercel 静态产物边界，根目录运维脚本、SQL、Markdown 与状态文件不会被复制为公网资产。首次未链接 worktree 的 `vercel build --yes` 曾误建一个空项目；已核对其无部署／生产 URL 后删除，并把本地链接恢复到既有 `arcteryx-deals-platform` 项目。
- 全量 Python 测试输出为 `Ran 218 tests ... OK`；Node 测试输出为 `tests 13, pass 13, fail 0`；GEO readiness 本地输出为 `passed=213 failed=0 total=213`。
- `vercel build --yes` 在既有项目配置下成功；浏览器验收覆盖 1440×900 与 390×844、6 条代表路由，输出 `passed=12 failed=0 total=12`。首页目录加载进入 `complete` 且渲染 60 张商品卡；页面无 body 横向溢出、无 console/page error，移动端 App Store CTA 高 44px，矩阵表可横向滚动。
- 最终一致性复核输出：内容 `20 generated files` current；在线目录 `products=8204` current；GEO readiness `passed=213 failed=0 total=213`；IndexNow check `valid=true`、dry-run `url_count=8213 batch_count=1`；`bash -n`、`py_compile`、`git diff --check` 均退出 0。
- 最终全量测试再次输出 Python `Ran 218 tests in 3.575s / OK`、Node `tests 13 / pass 13 / fail 0`；最终 Vercel 构建输出 `status=ok`。构建包审计为 `forbidden_root_assets=[]`、`missing_required_assets=[]`；最终浏览器复跑仍为 `passed=12 failed=0 total=12`。

## 下一步（按序）

1. 重跑最终内容／目录一致性、全量测试、构建、浏览器、shell 与 diff 闸门，记录最新原文。
2. 以 `bc948264427498d2a86d57ab3f6aadc580f60ad0` 为生产回滚点，提交本次精确差异并 rebase 到该点；重新生成／构建验收。
3. 推送隔离分支，发布预览并独立回读。
4. 合入生产路径，等待实际发布完成，再从新请求独立回读代表页、sitemap、机器人访问、App Store 链接与语言关系。

## 死路

- 项目存在 `.codegraph/` 线索，但本会话没有暴露任何 `codegraph_*` 工具；不能按项目约定调用结构索引。本轮仅对生成器、工作流及其定向测试做定点读取，不用全仓 grep 重建调用图。
