# TASK: EVO UCP recovery（更新：2026-08-24 03:16 Asia/Taipei）

## Why（一句话）

把持续被 Cloudflare 阻断的 EVO 集合发现链路迁移到官方 UCP Catalog，并修正恢复熔断与公开发布状态，使生产数据和客户可见投影可以被独立、诚实地验收。

## 当前状态：进行中

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

## 假设（未验证；验证后移入上区）

- 为 UCP 使用 Shopify 官方公开 profile fixture 可先恢复服务；生产长期应发布 GearDrop 自有、稳定的 JSON profile。
- Vercel 漏掉 `caacf58` 的原因可能是 Git webhook/部署触发缺口；原因尚未定位。
- 500ms PDP 节流 + EVO 3600 秒 timeout 的最终组合未再做一次完整 30-40 分钟本地运行；相同全量逻辑已在无额外节流时 1725.9 秒通过，最终组合需由正式 workflow 验收。

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

## 下一步（按序）

1. 提交并推送隔离修复分支，等待远端检查。
2. 合入主干后先确认代码部署，再按正式 dealer workflow 做生产恢复。
3. 复核三道质量门、唯一 publication marker 与固定 cohort 的 lifecycle-inconclusive 工件。

## 死路（试过不行的，附失败原因）

- 重跑既有 EVO collection JSON + Camoufox fallback：连续失败且同一 403/0-item 指纹，不能改变来源契约。
- 直接发布 UCP search/lookup 价格：实测存在 144.99 vs PDP 114.99 的陈旧价，已拒绝。
- 以新样本替换固定 cohort：违反 exact-sample 证据契约，禁止。
