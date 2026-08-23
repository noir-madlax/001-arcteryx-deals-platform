# TASK: EVO UCP recovery（更新：2026-08-24 05:47 Asia/Taipei）

## Why（一句话）

把持续被 Cloudflare 阻断的 EVO 集合发现链路迁移到官方 UCP Catalog，并修正恢复熔断与公开发布状态，使生产数据和客户可见投影可以被独立、诚实地验收。

## 当前状态：完成

生产抓取、数据库质量、静态发布和客户可见页面均已独立验收通过。原始固定价格 cohort 保持不补样，其终态为 `inconclusive_lifecycle`，不冒充价格准确率通过。

## 边界

- 基于最新 `origin/main` 的隔离分支开发，不触碰主工作树未提交文件。
- 不手写生产数据库，不补样或复活固定价格 cohort，不把 403/429 算作正确。
- 本地验证通过前不触发生产 workflow；正式恢复只走仓库既有 workflow。

## 已确认事实（每条带来源）

- 分支基线为 `caacf5811d72918905513e2e0728fc5159b58ced`。（来源：`git rev-parse HEAD`，2026-08-24 01:35 Asia/Taipei）
- Dealer workflow `32653515896` 失败；原始日志为 EVO collection JSON HTTP 403，Camoufox 的 Arc'teryx/Burton/Patagonia 集合均为 0 条，最终 `EVO 0`，其余 dealer 仍完成同步。（来源：`gh run view 32653515896 --log-failed`）
- 终态质量门：Outlet `6409` OK；指定 Dealer `1394` FAIL；全量 `8279` FAIL；失败均为 12 条 stale EVO active row。（来源：三条 `tools/check_data_quality.py --online` 正式命令，2026-08-24 01:27 Asia/Taipei）
- EVO `/.well-known/ucp` 提供 storefront MCP endpoint；`search_catalog` 对 Arc'teryx、Burton、Patagonia 首批各返回 250 个商品并有下一页 cursor。已抽查 `250111`：UCP 与官方 `.js` 均为 `254.99/649.95 USD`。（来源：本轮只读 HTTP/MCP 探针）
- 真实 UCP 全分页已终止：Arc'teryx 2 页/262 unique handles、Burton 4 页/722、Patagonia 2 页/485。（来源：隔离分支 `Scraper._ucp_call` 只读分页探针，2026-08-24 02:43 Asia/Taipei）
- 全量 UCP-discovery + 每 handle PDP 确认只读执行完成：1469 件（Arc'teryx 262 / Burton 723 / Patagonia 484），全部 `price_source_quality=pdp`，`crawl_complete=true`，耗时 1725.9 秒。（来源：隔离分支完整 `Scraper.scrape()`，未写 partial，2026-08-24 03:08 Asia/Taipei）
- UCP 搜索与 `lookup_catalog/get_product` 价格不能直接发布：`263539-burton-reserve-2l-insulated-pants-women-s` 的三个 UCP 读数均为 144.99，而当前 PDP 为 114.99/229.95；因此最终实现只用 UCP 发现，仍逐 handle 取 PDP 价格。（来源：只读 UCP/PDP 对照，2026-08-24 03:10 Asia/Taipei）
- 固定 cohort replay 退出 2：`rei:235611, rei:243329, rei:249789` 不再 eligible；六次当前官方直连均为 403。（来源：正式 `tools/audit_price_accuracy.py --sample-file ...` 与两次/URL curl）
- 公网 Vercel 当前部署 commit 为 `c834c491...`，最新 origin 为 `caacf581...`；公网 `results.json` 仍是 `generated_at=2026-08-23 14:14:51`，EVO `refreshed_at=2026-08-20 18:35:21`。（来源：`vercel inspect`、公网 cache-busted GET、git）
- automation-5 已通过应用正式更新并独立回读：保留 ACTIVE/hourly/thread 绑定，新增同签名三次且跨两窗口熔断、两轮代码修复预算、`AUDIT_INCONCLUSIVE_LIFECYCLE` 与精确 publication marker 门。（来源：`codex_app__automation_update` 回执及 automation.toml readback，updated_at=1787510386377）
- PR #32 已通过检查并合入 `origin/main`，merge commit 为 `df4a11eb368d15f4b8a07dd2e16449aa0c5c57fd`，对应 Vercel production deployment 为 SUCCESS。（来源：GitHub PR/check 与 Vercel deployment readback）
- 合入后正式 dealer workflow `32660663814` 已完整完成 UCP 抓取与数据库同步：EVO 1469 件、1469/1469 upsert、0 batch errors；最终质量门仅因一个 active SKU `evo:products/286584-burton-fish-3d-splitboard-step-on-splitboard-bindings-2026` 缺图失败，故静态结果及 publication marker 未提交发布。（来源：该 run 完整原始日志）
- 缺图 SKU 是 `type:custom-bundle`；当前 UCP search/lookup/get_product 与 PDP `.js` 均无商品媒体。实时 UCP 目录中标题精确等于其去掉尾部 `2026` 的兄弟 bundle `286656-...` 提供官方 `variants[].media` 商品图；不是品牌/集合占位图。（来源：本轮只读 UCP/PDP 精确探针）
- 按生产 `query=Burton` 全分页重新只读验证为 4 页/821 unique handles，目标与兄弟 bundle 均在同一终止目录中；新解析器为目标解析到兄弟的官方 CDN 图，图片 GET 为 `200 image/jpeg`、74,498 bytes。（来源：隔离分支实时 UCP 全分页与 CDN GET，2026-08-24 04:12 Asia/Taipei）
- PR #33 图片补丁已合入 merge commit `5bcf60f5cd0612280872d609d82b627a64eaf18a`，对应 Vercel production status 为 SUCCESS。（来源：GitHub PR、commit status readback）
- 第二次正式 dealer workflow `32663840073` 未执行到 EVO 图片同步：UCP 已完成 Arc'teryx 262 与 Burton 721，但 Patagonia 第 1 页单次 HTTP 500 后立即 fail-closed；旧 collection/Camoufox 回退仍为 403/0 件。其余四个 dealer 同步成功，EVO 保留旧快照，最终仍由旧缺图行触发质量失败；commit/publication 步骤均 skipped。（来源：该 run 完整失败日志）
- 与失败请求相同的 `query=Patagonia`、`limit=250` 只读请求随后返回 HTTP 200/250 件并带下一页 cursor，证明该 500 是当前可恢复的瞬态服务错误。（来源：本轮 action-time 只读 UCP 探针，2026-08-24 04:44 Asia/Taipei）
- UCP 瞬态重试补丁 PR #34 已合入，merge commit 为 `1e73dfaa2feb054cb8f46ff5c5dc1e04557e5135`；幂等 UCP POST 对 408/429/500/502/503/504、网络异常和畸形 200 做有限重试，永久 403 与重试耗尽继续 fail-closed。（来源：PR #34、合入代码与测试）
- PR #34 合入后仅触发的一次正式恢复 run `32665516068` 已 `completed/success`：UCP 终止分页得到 Arc'teryx 262、Burton 721、Patagonia 485；EVO 数据库同步 1466/1466、0 batch errors，在线质量门 `OK`，随后写入数据 commit `d32d12ca5be62a1bb7a4b4055e56b6abe3ba4e9a`。（来源：该 run 完整原始日志与 `gh run view`）
- 该 run 的唯一发布标识为 `github-actions-32665516068-1`；公网第 3 次轮询同时匹配 marker 和本地静态文件 SHA-256 `4920842a313f9c44929b4d7eb239a1d7cd44e09fdc2cdc4ae1c689219beaccec`，Vercel 对数据 commit 的状态为 `success`。（来源：workflow 原始日志、公网 `publication.json` 与 GitHub commit status readback）
- 收尾独立在线质量门全部退出 0：Outlet `6407` 行 `OK`；MEC/EVO/REI/SSENSE `1743` 行 `OK`；全量 `8625` 行 `OK`，且无 JP region。（来源：三条正式 `tools/check_data_quality.py --online` 命令，2026-08-24 05:45 Asia/Taipei）
- 公网 `/`、`/data.js`、`/dealers/results.json`、`/publication.json` 均为 HTTP 200；静态 dealer 投影共 2215 件，其中 EVO 1466 件，目标 bundle 的官方图、`1549.9/976.43 USD` 与 `price_source_quality=pdp` 已公开。（来源：四个 cache-busted GET 与 `jq` readback）
- 在真实客户页面中搜索目标 bundle 后，结果卡和详情页均可见；详情显示 EVO、`$976.43/$1,549.9`、`-37%`，官方 CDN 图实际完成加载且 natural size 为 `1500x1500`。（来源：Codex in-app browser 的真实 fill/click/DOM readback，2026-08-24 05:44 Asia/Taipei）
- 从最新数据 commit 原样重放固定 cohort 退出 2，并写出 `gate.status=inconclusive_lifecycle`；仍是 `rei:235611, rei:243329, rei:249789` 不再 eligible，未补样、未复活、未宣称 PASS。（来源：`audit_price_accuracy.py --sample-file ... --output /tmp/arcteryx-fixed-cohort-replay-20260824-main.json`，2026-08-24 05:47 Asia/Taipei）

## 假设（未验证；验证后移入上区）

- 为 UCP 使用 Shopify 官方公开 profile fixture 可先恢复服务；生产长期应发布 GearDrop 自有、稳定的 JSON profile。
- Vercel 漏掉 `caacf58` 的原因可能是 Git webhook/部署触发缺口；原因尚未定位。
- 最终成功 run 没有实际遇到 UCP transient status，因此生产重试分支没有端到端触发；500-then-200、永久 403 与重试耗尽边界已由本地自动化测试覆盖。

## 验收标准

- UCP discovery 分页、品牌严格过滤、可售变体归一化、异常/不完整 fail-closed 均有定向测试。
- EVO 既有 sold-out variant 价格回归保持通过；旧集合路径仅作为受控回退，不再对持久 403 无限重试。
- 连续同签名外部失败进入熔断，只读探针与写 workflow 分离；固定 cohort 可进入明确的 lifecycle-blocked 终态而不被冒充通过。
- `merge_partial` 对 retained/rejected/stale dealer 状态不丢失；客户可见验证要求唯一 `publication_id` 和本地 marker 字节哈希一致，而非 HTTP 200。
- 本地相关测试、compile/YAML/JSON 校验通过；远端 workflow 后三道质量门、公网投影和 Vercel SHA 均有独立读回。

## 已完成且已验证

- UCP 发现/分页/严格标题过滤/PDP 确认/重复 cursor fail-closed 的定向测试通过。
- 真实 UCP endpoint 三品牌全分页与 1469-handle 全 PDP 确认完成；UCP 陈旧价差异已 fail-closed，未写 partial。
- `merge_partial` unresolved rejection 保留与 trusted refresh 清除的定向测试通过。
- 固定样本失效写出 `gate.status=inconclusive_lifecycle` 的定向测试通过。
- 三条静态刷新 workflow 均生成并等待唯一 publication marker；marker/hash 单元测试通过。
- automation-5 新状态机已正式更新并从落盘配置独立回读。
- 仓库 Python 全量 `202 tests` 通过；Node 全量 `13 tests` 通过；5 个修改 Python 文件 compile 通过；3 个 refresh workflow YAML parse 通过。
- 首次合入后的正式 workflow 已证明 UCP 发现、1469-handle PDP 确认和 Supabase 同步成功；当前为新的单 SKU 缺图签名，未重复盲跑。
- custom-bundle 图片补丁定向 `2 tests`、dealer scraper `37 tests`、仓库 Python `203 tests`、App Node `35 tests` 均通过；5 个 Python 文件 compile、3 个 workflow YAML 与 `git diff --check` 通过。
- 第二次正式 workflow 保持了完整快照 fail-closed，但暴露 `_post_ucp_json` 仅重试 429、不会重试瞬态 5xx 的可用性缺口；未盲目重复运行。
- 瞬态重试补丁的 500-then-200、永久 403 不重试与 503 重试耗尽边界测试通过；仓库 Python 全量 `206 tests`、App Node `35 tests`、5 个 Python 文件 compile、3 个 workflow YAML 与 `git diff --check` 通过。
- PR #34 合入后，正式 run `32665516068`、精确 publication marker/hash、Vercel production、三组在线质量门、四个公网入口与客户页面搜索/详情交互均通过。
- 最新 `origin/main` 原样重放固定 cohort，工件明确为 `inconclusive_lifecycle`；该门按既定契约终止，不阻塞已独立证明的抓取/同步/发布恢复。

## 后续非阻塞事项

1. 为 GearDrop 发布自有且稳定的 UCP JSON profile，替代当前 Shopify 官方公开 profile fixture。
2. automation-5 后续继续轮询既有固定 cohort 的生命周期状态；不得用新样本替换这份历史证据。

## 死路（试过不行的，附失败原因）

- 重跑既有 EVO collection JSON + Camoufox fallback：连续失败且同一 403/0-item 指纹，不能改变来源契约。
- 直接发布 UCP search/lookup 价格：实测存在 144.99 vs PDP 114.99 的陈旧价，已拒绝。
- 以新样本替换固定 cohort：违反 exact-sample 证据契约，禁止。
- 在没有 UCP 5xx 有限重试的情况下盲跑：`32663840073` 已证明单次瞬态 500 会丢弃整份 EVO 快照，已拒绝继续重复。
