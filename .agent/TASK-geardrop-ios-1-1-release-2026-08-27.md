# TASK: GearDrop 1.1 最新功能整合与提交（更新：2026-08-27 18:43 Asia/Taipei）

## Why（一句话）

在已上线且审核通过的 1.0 / Build 9 基线上，安全整合此前暂缓的下一版本功能与五语商店素材，形成可验证、可审计的 1.1 候选并提交 App Review。

## 当前状态：进行中（核心功能已整合并通过定向测试，尚未生成 Build 10，尚未修改 App Store Connect）

已从 `origin/codex/fix-ios-ipad-keyboard-20260824` 的提交 `a4af73a` 创建隔离分支 `codex/ios-1-1-yearbook-20260827`。共享主工作树保留现有未跟踪文件，不在本任务内修改。

## 已确认事实

- 2026-08-27 16:02 Asia/Taipei，Apple 官方 API 回读：App Store Version 1.0、Build 9、submission `893d3789-a4ba-4677-b7d9-b00f0fe9e7bb` 和 5 个审核项目均已通过；App 为 `READY_FOR_SALE`。Apple 公开 Lookup API 在美国和台湾均返回 GearDrop 1.0。（来源：本会话 API 原始输出）
- 发布基线分支 `origin/codex/fix-ios-ipad-keyboard-20260824` 为 Build 9，包含已审核的 iPad 键盘、搜索首击和长筛选滚动修复。（来源：`git log`、`.agent/TASK-geardrop-ipad-keyboard-2026-08-24.md`）
- `codex/yearbook-deals-overlay-20260812` 已实现三品牌 Yearbook、当前折扣叠加和 Outlet／历史款；原任务档案记录 App 测试、TypeScript、Web/iOS export 与生产只读匹配率验收，但其 App 基线早于完整 iOS/IAP/本地化发布分支，不能整分支覆盖。（来源：`.agent/TASK-yearbook-deal-overlay.md`、本会话 `git diff`）
- `codex/ios-next-version-aso-20260814` 的提交 `cad9db9` 包含五语 canonical metadata、6 槽位截图计划和失败关闭校验；明确仅用于下一版本。（来源：`.agent/TASK-geardrop-next-version-aso-2026-08-14.md`、`git show cad9db9`）
- 分享／深链功能仍无实现，且历史任务记录长期域名授权与 exact-SKU 行为未关闭，本轮不把它列入发布范围。（来源：本会话读取的项目记忆与分支列表）
- `origin/main` 的 App 代码缺少已上线分支中的 IAP、本地化、品牌资产与发布门；从 main 直接构建会回退已上线能力。（来源：本会话 `git diff codex/fix-ios-ipad-keyboard-20260824..origin/main -- app`）
- 2026-08-27 实时只读探针：`catalog_products` 有 1,353 个 active 当前款（Arc'teryx 370、Burton 495、Patagonia 488）；`products` 有 8,434 个 active 折扣商品，三品牌均有数据。`products` 当前不存在 `official_product_id` 列，Yearbook 因此使用官方 URL 款号优先、唯一规范化名称兜底的保守关联。（来源：本会话 Supabase REST 回读）

## 假设

- 新增完整 Yearbook 导航与多品牌发现属于功能级更新，候选营销版本采用 `1.1.0`，Build 采用线上下一号 `10`；正式 App Store 对象仍需 live 预检。
- 下一版范围为 Yearbook／折扣叠加／历史款、五语 ASO 和 Build 9 已审核修复；不顺带合入分享、深链或数据爬虫基础设施。
- 生产 `catalog_products` 和 `products.official_product_id` 已可支持 Yearbook；必须通过 live schema/data 探针重新验证，不能沿用 2026-08-12 历史结论。

## 验收标准

1. 保留 1.0 的 IAP、五语运行时、iPhone-only、品牌资产和三项审核修复；机器契约可阻止回退。
2. Yearbook 当前款、当前折扣与 Outlet／历史款在真实 live 数据上可读取、筛选、打开正确 Deal，无法关联时不模糊合并。
3. 五语下一版本 metadata 校验全绿；最终商店截图来自精确 1.1 签名候选，不复用旧候选冒充。
4. `npm test`、`npm run typecheck`、配置／资源／metadata／live-data 门、`npm run verify`、iOS export 和原生 Release 构建通过；行为改动完成模拟器关键路径验收。
5. Build 10 的 bundle、版本、签名、加密声明和源提交可独立核验；App Store 写入前锁定精确对象和允许差异，提交后用新会话独立回读。

## 已完成且已验证

- 已读取长任务协议、项目记忆、两份相关任务档案和分支差异。
- 已创建干净隔离 worktree `/private/tmp/geardrop-ios-1-1-20260827.iJNZfj/worktree` 与分支 `codex/ios-1-1-yearbook-20260827`，起点 `a4af73a`。
- 已在 Build 9 架构上整合三品牌规范化、品牌筛选、Yearbook 当前款、确定性实时折扣叠加、Outlet／历史款和五语 UI；保留原有 IAP、本地化、iPhone-only 与审核修复。
- `npm test`：55/55 通过；`npm run typecheck`：退出码 0。
- `npm run verify:live-data`：退出码 0；确定性关联当前款 Arc'teryx 143、Burton 186、Patagonia 55，保留 1,278 个未匹配历史款组；没有跨品牌模糊匹配。

## 下一步

1. 合入并更新五语 ASO 校验，升级 `1.1.0` / Build `10`，补强发布配置契约。
2. 完成全量本地、iOS export、原生 Release 和模拟器关键路径验收。
3. 生成 Build 10 并核验制品。
4. 展示精确 App Store 1.1 对象、metadata 与截图差异，取得动作时确认后写入并提审。

## 死路

- 仓库存在 `.codegraph/`，但本会话未暴露任何 `codegraph_*` MCP 工具；无法按项目约定调用结构索引，后续只对已由提交差异锁定的相关文件做定点读取，不用全仓 grep 重建调用图。
- 尝试完整 cherry-pick `c55cf6a` 时与现有 iOS/IAP/后端基线产生多文件冲突，已完整 abort；改为只按冻结接口手工移植 App 侧功能。
- 首次实时 schema 探针尝试查询 `products.official_product_id`，官方 REST 返回 `42703 column does not exist`；没有写入，随后以现有列重新只读验证并将缺列纳入匹配契约。
