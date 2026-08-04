# TASK: GearDrop 第一版 Logo 发布为 iOS build 4（2026-08-04）

## Why
把用户确认的第一版 GearDrop logo 从本地资源更新推进为可在 TestFlight 安装验证的签名 build 4，同时保持“真机交易与最终截图通过前不提审”的上线边界不变。

## 当前状态
- TestFlight / Apple 上最新二进制已为 `1.0.0 (4)`；Apple build resource / delivery ID 为 `a9601f62-78a4-4e52-9336-8934a0c57e85`，状态 `VALID` / `APP_STORE_ELIGIBLE` / `IN_BETA_TESTING`。
- 第一版 logo 更新已提交并推送到分支 `codex/ios-appstore-build4-logo-20260804`；build 4 已加入 `GearDrop Internal`，iOS 1.0 唯一 build relationship 已从 build 3 替换为 build 4。
- iOS 1.0 仍不得提交 App Review；真实 StoreKit 交易矩阵与最终截图仍是硬门。

## 已确认事实
- EAS 登录账户为 `noir-madlax`，目标项目为 `@noir-madlax/geardrop` / `ead43b0e-5dbf-44a2-838e-f65db29abb30`。（来源：本轮 `eas whoami` / `eas project:info`）
- 当前分支起点与 `origin/codex/ios-appstore-build3-20260804` 一致，fetch 后 ahead/behind 为 `0/0`。（来源：本轮 Git 原始输出）
- App、Web、H5、邮件和页面生成器已改用用户确认的第一版 logo；App 首页、付费页、隐私页及 Web 浅色/深色/移动版均已真实渲染回读。（来源：本轮本地浏览器与静态资源审计）
- 本地定向门已通过：39/39 tests、TypeScript、配置、1024×1024 无 alpha 图标、Expo Doctor 20/20、iOS/Web export、7 个 Web 页面资源引用和 `git diff --check`。（来源：本轮命令原始输出）
- 完整 `npm run verify` exit 0：39/39 tests、配置、资源、typecheck、Doctor 20/20、实时汇率、products `5,689`、price history `84,047`、启动预览 `200`、iOS export `1,497 modules / 5.4 MB`，最终原文 `verify_local_ok`。（来源：本轮完整命令原始输出）
- `npm audit --omit=dev --audit-level=high` exit 0；现有 11 项均为 Expo 构建工具链的 moderate，forced fix 会降级到 Expo 46.0.21，未执行。（来源：本轮 npm audit 原始输出）
- 品牌候选提交 `2e73e3b` 已推送，远端 branch SHA 与本地完整 SHA 一致。EAS production build `33fcb413-26c7-4282-9903-1021eeb40909` 读回 `IN_QUEUE`、App `1.0.0`、build `4`、源码提交 `2e73e3b`；EAS 自动把本地 `app.json` build number 从 3 递增为 4。（来源：本轮 Git 与 EAS build list 原始输出）
- EAS build `33fcb413-26c7-4282-9903-1021eeb40909` 最终读回 `FINISHED`，App `1.0.0 (4)`，源码提交完整 SHA `2e73e3b5553dca15c9658393d9ec866dbe1b6aa6`；等待约 5 秒、排队约 26 秒、构建约 345 秒。（来源：本轮 EAS build JSON）
- 同一 EAS 产物已下载为 30,078,471-byte IPA，SHA-256 为 `ebbfcd65a1fedcf0c444b102d0639b526dfb2dc5f68c29921c2fa8175d9df8d5`。`codesign --verify --deep --strict` 返回 `valid on disk` / `satisfies its Designated Requirement`；Info.plist 读回 bundle `dev.100app.geardrop`、version `1.0.0`、build `4`、最低 iOS 16.4、iPhone-only、非豁免加密为 false。（来源：本轮下载、codesign、PlistBuddy 与 shasum 原始输出）
- IPA 内运行时 logo / mark 与仓库源文件 SHA-256 精确一致；编译后的 AppIcon 为 1024×1024、Opaque true，启动 logo 包含 1x/2x/3x，背景精确为 `#F7F5EF`。提取的 120×120 AppIcon 无 alpha，人工回读为用户确认的深绿底、奶油色 G、珊瑚色向下箭头第一版。（来源：本轮 unzip、shasum、assetutil、sips 与视觉回读）
- build number 4 配置修正提交 `64d5543` 已推送，远端 branch SHA 与本地一致；EAS Submit `6bb5c579-120f-46a1-a2de-6031479ea7ff` 已锁定同一 build `1.0.0 (4)` 与 `GearDrop Internal`，2026-08-04 09:56 EDT 浏览器独立读回状态仍为 `Queued / Free Tier Queue`，尚无上传日志。（来源：本轮 Git、EAS Submit 输出与 Expo 提交详情实际 DOM）
- Apple Content Delivery 对同一 SHA-256 IPA 返回 `VERIFY SUCCEEDED with no errors`。EAS Submit 仍为 `Queued / Free Tier Queue` 且无日志，因此在直传前取消，刷新后独立读回 `Canceled`。（来源：本轮 altool 原始输出与 Expo 提交详情实际 DOM）
- Apple 官方直传返回 `UPLOAD SUCCEEDED with no errors`，完整传输 30,078,471 bytes，delivery ID `a9601f62-78a4-4e52-9336-8934a0c57e85`；带等待处理的终态输出为 `VALID` / `APP_STORE_ELIGIBLE` / `usesNonExemptEncryption=false` / 最低 iOS 16.4。（来源：本轮 altool 原始输出）
- 写前 Apple 官方 API 精确读回目标 App `6790165332` / bundle `dev.100app.geardrop`、build 4 `VALID`、内部组只含 build 2/3、iOS 1.0 仍绑定 build 3。随后 POST build 4 到 `GearDrop Internal` 和 PATCH iOS 1.0 build relationship 均返回 HTTP 204。（来源：本轮 App Store Connect API 原始响应）
- 写后关系 GET 读回内部组 build IDs 为 build 4 + build 3 + build 2、tester count `3`，iOS 1.0 唯一 build ID 为 build 4。全新进程再次独立读回 build 4 `VALID` / `APP_STORE_ELIGIBLE` / `IN_BETA_TESTING` / `READY_FOR_BETA_SUBMISSION`，版本仍为 `PREPARE_FOR_SUBMISSION`。（来源：本轮两次独立 App Store Connect API 读回）
- 发布档案已更新到 build 4；`git diff --check`、`npm run verify:config`（`buildNumber=4`）与 `npm run typecheck` 均 exit 0。（来源：本轮本机命令原始输出）

## 假设
- Apple / TestFlight 状态会变化；上传、处理、分组与版本绑定必须在写后独立读回，不能沿用 build 3 的历史结果。

## 验收标准
1. 完整 `npm run verify` exit 0，且最终出现 `verify_local_ok`。
2. `npm audit --omit=dev --audit-level=high` 无 high/critical；不得执行破坏性 `--force` 修复。
3. 品牌变更提交并推送到 build 4 分支，构建工作树可追溯。
4. EAS production build 读回 `FINISHED`、App `1.0.0`、build `4`，并下载同一签名 IPA 做 Info.plist、图标资源和 SHA-256 核验。
5. Apple 上传后读回 `processingState=VALID` 与 `APP_STORE_ELIGIBLE`，再加入 `GearDrop Internal` 并把 iOS 1.0 build relationship 更新为 build 4；每项写操作独立 GET 回读。
6. 不上传旧截图、不提交 App Review；等待 build 4 真机 StoreKit 与最终截图验收。

## 下一步
1. 从 TestFlight 安装 build 4，完成首页、logo、冷启动预览与真实 StoreKit 交易矩阵。
2. 从通过验收的 build 4 重截 App Store 最终图及三项 IAP review screenshot；上传后独立读回，再单独决定是否提审。

## 死路 / 防回归
- 默认 npm cache 曾导致 EAS CLI 安装异常；本任务使用独立 cache `/private/tmp/geardrop-eas-npm-cache-build4`。
- 不使用 Apple ID 密码重试；沿用已配置的 App Store Connect API key / EAS 凭证路径。
- EAS Submit free-tier 队列可能长时间等待；只有在取得同一 IPA 哈希后，才可改用 Apple 官方上传工具，避免重复构建或重复上传。
