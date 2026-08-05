# TASK: GearDrop Pro 邀请码（更新：2026-08-05 EDT）

## Why（一句话）
在不绕过 Apple IAP 的前提下，让用户从付费墙打开 Apple 官方 Offer Code 输入页，兑换成功后由 StoreKit + RevenueCat 自动启用 `Pro`。

## 当前状态：App 入口已本地实现并通过完整发布门；尚未创建 App Store Connect Offer Code，尚未生成包含该功能的新 TestFlight build

## 已确认事实
- Apple App Review Guideline 3.1.1 要求 App 内数字功能解锁使用 IAP；因此不实现客户端硬编码邀请码、AsyncStorage 解锁或自建后端直接授予 Pro。（来源：2026-08-05 Apple 官方 App Review Guidelines）
- Apple Offer Code 现支持 auto-renewable subscription 与 non-consumable 等 IAP 类型；有效兑换会产生 StoreKit transaction，非消耗型 lifetime 商品可用于永久 Pro。（来源：2026-08-05 Apple StoreKit 官方文档）
- 当前 `react-native-purchases@10.4.2` 类型与 iOS bridge 均提供 `presentCodeRedemptionSheet()`；现有 `CustomerInfo` listener 会把 RevenueCat 的 `Pro` entitlement 更新到 UI。（来源：本轮本地 SDK 类型、bridge 与 `ProContext.tsx`）
- 本轮在付费墙新增“兑换 Pro 邀请码”，调用 Apple 系统兑换页；没有自定义输入框、没有在包内保存邀请码，也没有本地 `setPro(true)` 路径。（来源：本轮代码 diff）
- 无代理完整 `npm run verify` exit 0：40/40 tests、五语言完整、配置、1024×1024 无 alpha 图标、TypeScript、Expo Doctor 20/20、2026-08-05 汇率、5,716 products、84,075 price-history rows、200 条启动预览、AU 16、iOS 1,497 modules / 5.4 MB，最终原文 `verify_local_ok`。（来源：本轮完整命令输出）
- `npm audit --omit=dev --audit-level=high` exit 0；11 项 moderate 仍来自 Expo 构建工具链，forced fix 是 breaking change，未执行。（来源：本轮 npm audit 原始输出）

## 假设
- 永久邀请码应绑定现有 lifetime non-consumable `dev.100app.geardrop.pro.lifetime`；若要限时 Pro，则应绑定 monthly 或 annual subscription offer。
- 共享 custom code 更易传播，生产创建前必须由用户确认 code 字符串、总兑换额度和到期日；更安全的默认方案是 Apple 生成的一次性码批次。

## 验收标准
1. 付费墙入口只调用 Apple/StoreKit redemption sheet，不在客户端校验或授予 Pro。
2. RevenueCat `CustomerInfo` 更新仍是唯一 Pro 权益来源。
3. 五种语言键完整；40/40 tests、配置、TypeScript、完整 `npm run verify` 与 `git diff --check` 通过。
4. 创建 sandbox Offer Code 后，在签名真机 build 验证：无效码不解锁、有效码自动解锁、重启与恢复购买仍保留。
5. 生产 custom/one-time-use code 的商品、额度、到期日由用户确认后再创建并独立读回。

## 下一步
1. 用户选择永久或限时、一次性或共享 custom code，并确认额度/到期日。
2. 在 App Store Connect 创建 sandbox code，生成新 TestFlight build 并完成真机兑换矩阵。
3. sandbox 通过后创建生产 code，再独立读回 offer、code 状态与 redemption 限制。

## 死路
- 首次完整门与一次单独汇率探针都在 8 秒后以 `AbortError` 失败；同一 URL 的 `curl` 立即返回 8 个币种。仅对验证进程取消本机 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 后，汇率探针和完整发布门均通过；未修改系统代理或应用代码。
