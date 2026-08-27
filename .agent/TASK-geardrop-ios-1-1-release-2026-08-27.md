# TASK: GearDrop 1.1 最新功能整合与提交（更新：2026-08-27 20:43 Asia/Taipei）

## Why（一句话）

在已上线且审核通过的 1.0 / Build 9 基线上，安全整合此前暂缓的下一版本功能与五语商店素材，形成可验证、可审计的 1.1 候选并提交 App Review。

## 当前状态：进行中（1.1 / Build 10 本地代码候选已提交为 `fc1dd2a`；最终差异审计、软件门、原生 Release 与模拟器关键路径均通过。尚未生成签名 Build 10，尚未修改 App Store Connect）

已从 `origin/codex/fix-ios-ipad-keyboard-20260824` 的提交 `a4af73a` 创建隔离分支 `codex/ios-1-1-yearbook-20260827`。共享主工作树保留现有未跟踪文件，不在本任务内修改。

## 已确认事实

- 2026-08-27 16:02 Asia/Taipei，Apple 官方 API 回读：App Store Version 1.0、Build 9、submission `893d3789-a4ba-4677-b7d9-b00f0fe9e7bb` 和 5 个审核项目均已通过；App 为 `READY_FOR_SALE`。Apple 公开 Lookup API 在美国和台湾均返回 GearDrop 1.0。（来源：本会话 API 原始输出）
- 发布基线分支 `origin/codex/fix-ios-ipad-keyboard-20260824` 为 Build 9，包含已审核的 iPad 键盘、搜索首击和长筛选滚动修复。（来源：`git log`、`.agent/TASK-geardrop-ipad-keyboard-2026-08-24.md`）
- `codex/yearbook-deals-overlay-20260812` 已实现三品牌 Yearbook、当前折扣叠加和 Outlet／历史款；原任务档案记录 App 测试、TypeScript、Web/iOS export 与生产只读匹配率验收，但其 App 基线早于完整 iOS/IAP/本地化发布分支，不能整分支覆盖。（来源：`.agent/TASK-yearbook-deal-overlay.md`、本会话 `git diff`）
- `codex/ios-next-version-aso-20260814` 的提交 `cad9db9` 包含五语 canonical metadata、6 槽位截图计划和失败关闭校验；明确仅用于下一版本。（来源：`.agent/TASK-geardrop-next-version-aso-2026-08-14.md`、`git show cad9db9`）
- 分享／深链功能仍无实现，且历史任务记录长期域名授权与 exact-SKU 行为未关闭，本轮不把它列入发布范围。（来源：本会话读取的项目记忆与分支列表）
- `origin/main` 的 App 代码缺少已上线分支中的 IAP、本地化、品牌资产与发布门；从 main 直接构建会回退已上线能力。（来源：本会话 `git diff codex/fix-ios-ipad-keyboard-20260824..origin/main -- app`）
- 2026-08-27 19:00 后实时只读探针：`catalog_products` 有 1,353 个 active 当前款，其中 1,352 个通过客户端合同（Arc'teryx 370、Burton 495、Patagonia 487）；唯一拒绝行为 `patagonia:rj`，官方 ID `RJ`，价格为 0。`products` 内容范围为 8,432 个 active 折扣商品；`products` 当前不存在 `official_product_id` 列，Yearbook 因此使用官方 URL 款号优先、唯一规范化名称兜底的保守关联。（来源：本会话 `npm run verify:live-data` 原始输出）
- 2026-08-27 19:45–19:50 Asia/Taipei，Apple 官方 API 再次只读回读：线上仍只有 `1.0`（`READY_FOR_SALE`），没有 `1.1` 版本对象，也没有 Build 10；Build 9 为 `VALID` / `APP_STORE_ELIGIBLE`，5 个 IAP 均为 `APPROVED`。（来源：本会话 API 原始输出；外部动作前仍须刷新）

## 假设

- 新增完整 Yearbook 导航与多品牌发现属于功能级更新，候选营销版本采用 `1.1.0`，Build 采用线上下一号 `10`；正式 App Store 对象仍需 live 预检。
- 下一版范围为 Yearbook／折扣叠加／历史款、五语 ASO 和 Build 9 已审核修复；不顺带合入分享、深链或数据爬虫基础设施。
- 生产 `catalog_products` 可支持 Yearbook；`products.official_product_id` 当前不存在，关联只能使用官方 URL 款号和唯一规范化名称。必须通过 live schema/data 探针重新验证，不能沿用 2026-08-12 历史结论。

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
- 已绑定候选 `1.1.0` / Build `10`；EAS 使用本地版本源且 production `autoIncrement=false`，避免远端把精确 Build 10 自动增加为 11。
- 已补齐五语 What’s New、五语官方品类与时间/价格本地化，下一版 metadata 明确绑定 1.1.0 / Build 10；商店截图目标为 iPhone 16 Pro Max 6.9 英寸、1320x2868、每语 6 张且无 alpha。
- 已修复当前款、折扣与未关联区对 `Arc'teryx` / `Arc teryx` 等空格、标点和重音差异的统一搜索；折扣搜索也纳入规范品牌字段。定向测试 14/14 通过。
- 已将 Expo / React Native 原生兼容依赖固定为 `react-native-reanimated@4.5.1` 与 `react-native-worklets@0.10.1`。首次原生构建发现 npm 漂移安装 4.6.0 / 0.12.1，与 `expo-modules-core@57.0.14` 不兼容；固定后 `npm ls` 干净、`expo install --check` 显示依赖最新、Expo 模块自动链接验证通过。
- 首次 Yearbook Release 模拟器点击触发 `TypeError: undefined cannot be used as a constructor`，崩溃日志定位到 Hermes 环境没有 `Intl.RelativeTimeFormat`。`yearbookFreshnessLabel` 现先探测构造器并提供五语确定性回退；新增“构造器缺失”回归测试，重建后关联折扣行显示 `updated today`，未再产生新 GearDrop 崩溃报告。
- 最终差异审计又发现生产中 1,467 个商品的全部图片候选均为 `//cdn.shopify.com/...` 协议相对地址（Arc'teryx 259、Burton 724、Patagonia 484）；iOS 会把它们解析为本地 `file://` 并显示占位图。客户端标准化现统一补为 `https:`，预览缓存读取也会重新规范化旧候选数据，并新增单测及 live-data 的绝对 HTTPS 图片门。缓存修复后 61/61 测试、TypeScript 与 live-data 再次通过；35,483 个 live 图片候选中非法绝对 URL 为 0。
- 最终 `npm run verify`：退出码 0；61/61 测试通过、配置与素材契约通过、五语 metadata 通过、TypeScript 退出码 0、Expo Doctor 20/20、汇率与 live-data 门通过、iOS HBC export 完成，原始末行 `verify_local_ok`。
- `npm run verify:live-data`：退出码 0；确定性关联 offer 数为 official ID 1,683、唯一精确名称 788，关联当前款 Arc'teryx 142、Burton 186、Patagonia 55；未匹配 offer 5,347，分组为 1,275 个未关联折扣款。唯一零价官方行被显式拒绝且低于 0.1% 容错上限，没有跨品牌模糊匹配。
- `npm run doctor`：20/20 通过。`npm audit --omit=dev --audit-level=high`：退出码 0；仅余 Expo 配置链中的 11 个 moderate `uuid<11.1.1`，`npm audit fix --force` 会破坏性降级 Expo，未执行。
- `npm run verify:store-screenshots`：按设计退出码 1，精确列出 5 语共 30 张签名候选截图尚缺失；此门不以旧 6.3 英寸或本地假图绕过。
- 最终原生 Release 构建命令 `xcodebuild ... -configuration Release ... CODE_SIGNING_ALLOWED=NO ONLY_ACTIVE_ARCH=YES build -quiet` 退出码 0。成品 `GearDrop.app` 回读为 bundle `dev.100app.geardrop`、版本 `1.1.0`、Build `10`、`UIDeviceFamily=[1]`、非豁免加密 `false`、arm64 simulator；共 142 个文件，主 bundle 为 5,471,778 bytes、SHA-256 为 `757f267d4649b62679b8f0430ccbda877f46b7c9c46d256382ab2b1544d99162`。该成品仅为 ad-hoc 模拟器签名，不是可上传分发包。
- iPhone 16 Pro Max（iOS 18.4）实机模拟器关键路径显示 live Deals 8,432／筛选后 2,450、Yearbook 1,352 个当前款／1,275 个未关联款／383 个当前款含关联折扣；多币种关联行、未关联列表和精确 Deal 详情均成功打开。相同 iPhone-only 成品也在 iPad (A16, iOS 18.4) 的 Designed-for-iPhone 兼容框中启动并加载真实数据。保留旧候选缓存重新安装最终成品后，协议相对图片在 feed 与精确详情页正常显示；自 20:39:39 起两台模拟器日志均无新增 `file:////cdn.shopify.com`、`NSURLError` 或 `TypeError`。
- 已将代码、依赖锁、五语 metadata、校验脚本与素材计划本地提交到分支 `codex/ios-1-1-yearbook-20260827`，代码候选提交为 `fc1dd2a`（`fix(ios): harden 1.1 build 10 candidate`）；没有推送、没有 EAS／Apple 外部写入。

## 下一步

1. 在用户针对精确 SHA、`1.1.0` / Build `10`、bundle `dev.100app.geardrop` 和外部动作范围明确确认后，刷新 App Store Connect 只读状态，再生成／上传 EAS production 签名包。
2. 从精确签名候选生成并校验 30 张商店截图，完成 StoreKit sandbox 购买／恢复验证。
3. 再次取得精确 metadata、版本对象、审核备注、发布方式与提审写入确认后，才创建 1.1 对象、绑定 Build 10、写入 metadata 并提交审核；写入后独立回读。建议采用手动发布，避免审核通过后自动客户可见。

## 死路

- 仓库存在 `.codegraph/`，但本会话未暴露任何 `codegraph_*` MCP 工具；无法按项目约定调用结构索引，后续只对已由提交差异锁定的相关文件做定点读取，不用全仓 grep 重建调用图。
- 尝试完整 cherry-pick `c55cf6a` 时与现有 iOS/IAP/后端基线产生多文件冲突，已完整 abort；改为只按冻结接口手工移植 App 侧功能。
- 首次实时 schema 探针尝试查询 `products.official_product_id`，官方 REST 返回 `42703 column does not exist`；没有写入，随后以现有列重新只读验证并将缺列纳入匹配契约。
