# TASK: GearDrop Pro 邀请码（更新：2026-08-05 EDT）

## Why（一句话）
在不绕过 Apple IAP 的前提下，让用户从付费墙打开 Apple 官方 Offer Code 输入页，兑换成功后由 StoreKit + RevenueCat 自动启用 `Pro`。

## 当前状态：包含兑换入口的 Build 6 已完成签名构建、Apple 校验/上传并进入 3 人内部 TestFlight 组；lifetime 免费 Offer 与 99 个可交付 sandbox 码已创建并独立读回；尚未执行真机兑换矩阵，尚无 production 码

## 已确认事实
- Apple App Review Guideline 3.1.1 要求 App 内数字功能解锁使用 IAP；因此不实现客户端硬编码邀请码、AsyncStorage 解锁或自建后端直接授予 Pro。（来源：2026-08-05 Apple 官方 App Review Guidelines）
- Apple Offer Code 现支持 auto-renewable subscription 与 non-consumable 等 IAP 类型；有效兑换会产生 StoreKit transaction，非消耗型 lifetime 商品可用于永久 Pro。（来源：2026-08-05 Apple StoreKit 官方文档）
- 当前 `react-native-purchases@10.4.2` 类型与 iOS bridge 均提供 `presentCodeRedemptionSheet()`；现有 `CustomerInfo` listener 会把 RevenueCat 的 `Pro` entitlement 更新到 UI。（来源：本轮本地 SDK 类型、bridge 与 `ProContext.tsx`）
- 本轮在付费墙新增“兑换 Pro 邀请码”，调用 Apple 系统兑换页；没有自定义输入框、没有在包内保存邀请码，也没有本地 `setPro(true)` 路径。（来源：本轮代码 diff）
- 无代理完整 `npm run verify` 最新一次 exit 0：40/40 tests、五语言完整、build number 6 配置、1024×1024 无 alpha 图标、TypeScript、Expo Doctor 20/20、2026-08-05 汇率、5,739 products、84,083 price-history rows、200 条启动预览、AU 16、iOS 1,497 modules / 5.4 MB，最终原文 `verify_local_ok`。（来源：本轮完整命令输出）
- `npm audit --omit=dev --audit-level=high` exit 0；11 项 moderate 仍来自 Expo 构建工具链，forced fix 是 breaking change，未执行。（来源：本轮 npm audit 原始输出）
- 2026-08-05 创建前 App Store Connect API 读回精确身份：App `6790165332` / `dev.100app.geardrop`，IAP `6790168227` / `dev.100app.geardrop.pro.lifetime` / `NON_CONSUMABLE` / `MISSING_METADATA`，初始 Offer 数为 0；iOS 1.0 为 `PREPARE_FOR_SUBMISSION`。（来源：本轮官方 API GET）
- 已创建 active 免费 Offer `PRO_INVITE_LIFETIME_20260805`（ID `f30be916-3b26-4408-b612-4822f9a595e4`），eligibility 覆盖 `NON_SPENDER`、`ACTIVE_SPENDER`、`CHURNED_SPENDER`；独立 GET 读回 `sandboxCodeCount=100`、`productionCodeCount=0`。（来源：本轮官方 API POST 201 + 独立 GET）
- Apple sandbox 批次 API 不接受 99，只接受 10 或 100/200/.../1000；因此创建 100 个 SANDBOX 一次性码（批次 `5da1ed3e-4ea5-4ccb-b191-3267942291ea`，active，到期 `2027-02-01`），交付文件保留 99 行，另 1 行隔离不分发。两文件均为 mode `600`，合并后与 Apple 返回的 100 个唯一 18 位值逐行一致。（来源：本轮 409 原文、随后 POST 201、批次/values 独立 GET 与本地 round-trip）
- Apple 正式 one-time-use code 每批最少 500，且生成正式码前 App 必须 `Ready for Distribution`、关联 IAP 必须 `Approved`；当前状态不满足，所以未创建 production 码。（来源：2026-08-05 Apple 官方 App Store Connect Help + 本轮 live 状态）
- EAS production build `c6082010-7861-4a02-a496-6d69aa629b9f` 最终为 `FINISHED`：App `1.0.0`、build `6`、fingerprint `9d3006f6e54418a86d8d0a867c4ee29e26bb86c5`；EAS 自动递增的 `app/app.json` build number 已提交并推送为 `df79c82d83111c157455d69e9d48faf6f79fbd2d`。（来源：本轮 EAS JSON、Git 与远端 SHA 回读）
- Build 6 IPA 为 30,081,045 bytes，SHA-256 `c60be686ca0e68f1112b2bbfff29a17dda355a5279227f1898e82ecfe1f41b72`；Info.plist 读回 `dev.100app.geardrop` / `1.0.0` / `6`，Distribution 签名 Team 为 `46H3U4N2U3`。（来源：本轮下载产物、shasum、plutil 与 codesign）
- Apple Content Delivery 对同一 IPA 返回 `VERIFY SUCCEEDED with no errors`、`UPLOAD SUCCEEDED with no errors`；delivery/build ID `7dce187b-30b2-4e50-b305-69e9a66615c2` 最终为 `VALID` / `APP_STORE_ELIGIBLE`，最低 iOS 16.4，`usesNonExemptEncryption=false`。（来源：本轮 altool 原始输出与官方 API GET）
- 写入前读回 Build 6 不在 `GearDrop Internal`；精确 relationship POST 返回 HTTP 204，随后全新进程读回该组包含 build 2/3/4/5/6、3 testers，Build 6 为 `IN_BETA_TESTING` / `READY_FOR_BETA_SUBMISSION`。（来源：本轮官方 API 写前、写响应与独立写后 GET）
- iOS 1.0 仍为 `PREPARE_FOR_SUBMISSION` 且仍绑定 build 5 ID `c76bab54-1175-4729-a161-981b48b4ebfe`；Build 6 未绑定 App Store 版本，本轮未创建 App Review submission。（来源：本轮官方 API 独立 GET 与执行边界）

## 假设
- sandbox 码尚未在签名真机上兑换；在完成 Build 6 与真机矩阵前，不把 API 创建成功等同于 Pro 权益链路已通过。

## 验收标准
1. 付费墙入口只调用 Apple/StoreKit redemption sheet，不在客户端校验或授予 Pro。
2. RevenueCat `CustomerInfo` 更新仍是唯一 Pro 权益来源。
3. 五种语言键完整；40/40 tests、配置、TypeScript、完整 `npm run verify` 与 `git diff --check` 通过。
4. sandbox Offer 与 99 个交付码已由 API 创建、导出和独立读回；仍需在签名真机 build 验证：无效码不解锁、有效码自动解锁、重启与恢复购买仍保留。
5. production one-time-use code 只在 App `Ready for Distribution`、lifetime IAP `Approved`、sandbox 真机矩阵通过后按 Apple 最小 500 个创建并独立读回。

## 下一步
1. 从 `GearDrop Internal` 安装 Build 6，用隔离的 sandbox 码在真机完成无效码、有效码、自动 entitlement、重启与 Restore Purchases 矩阵；不要把 sandbox 文件发给正式用户。
2. 补齐 lifetime IAP metadata 与 Review Information screenshot，并独立读回商品状态。
3. App 与 IAP 获批且 sandbox 通过后，生成 Apple 允许的最小 500 个 production one-time-use codes，再独立读回 offer、批次、有效期与 values 数量。

## 死路
- 首次完整门与一次单独汇率探针都在 8 秒后以 `AbortError` 失败；同一 URL 的 `curl` 立即返回 8 个币种。仅对验证进程取消本机 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 后，汇率探针和完整发布门均通过；未修改系统代理或应用代码。
- 首次 Offer POST 用普通 UUID 作为 inline price ID，被 Apple 以 HTTP 409 `ENTITY_ERROR.INCLUDED.INVALID_ID` 拒绝；该请求未创建 Offer。改用 Apple 要求的 `${local-id}` 格式后 POST 201。
- 首次 sandbox batch POST 请求 99 个，被 Apple 以 HTTP 409 `ENTITY_ERROR.ATTRIBUTE.INVALID.UNSUPPORTED_NUMBER_OF_CODES` 拒绝，并明确只支持 `[10, 100, 200, ..., 1000]`；该请求未创建批次。随后创建 100 个并拆分为 99 交付 + 1 隔离保留。
- values endpoint 返回 100 行纯 18 位代码且无 CSV 表头；首次按“表头 + 100 行”断言而本地中止，未写文件。随后先只读确认 `lineCount=100`、`uniqueCount=100`、无逗号/表头，再完成 99 + 1 拆分。
- EAS CLI 20.5.1 在非交互证书提示后 exit 0 却没有创建 build；`build:list` 与未变的 build number 证明无外部产物。临时安装当前 21.5.0 并使用 `--freeze-credentials --no-wait` 后才真实创建 Build 6；没有修改项目依赖或 Apple 凭据。
- 首次 Apple build readback 使用 API 不支持的 `filter[buildNumber]` 返回 HTTP 400；改为按 App 获取 builds 后在客户端精确筛选 version 6。首次 beta detail 路径误用复数 `/betaBuildDetails` 返回 404；从 build relationships 读回正确的 `/buildBetaDetail` 后得到 TestFlight 终态。
