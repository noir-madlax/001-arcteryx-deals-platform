# TASK: GearDrop 第一版 Logo 发布为 iOS build 4（2026-08-04）

## Why
把用户确认的第一版 GearDrop logo 从本地资源更新推进为可在 TestFlight 安装验证的签名 build 4，同时保持 build 3 的 App Store 上线边界不变。

## 当前状态
- TestFlight / Apple 上现有最新二进制仍为 `1.0.0 (3)`，EAS build `2e452513-21a1-4203-8b50-abf877ed3e41`，源码提交 `6d28b0b`。
- 第一版 logo 更新位于分支 `codex/ios-appstore-build4-logo-20260804`，完整本地门已通过；尚未提交、尚未创建 build 4、尚未上传 Apple。
- iOS 1.0 仍不得提交 App Review；真实 StoreKit 交易矩阵与最终截图仍是硬门。

## 已确认事实
- EAS 登录账户为 `noir-madlax`，目标项目为 `@noir-madlax/geardrop` / `ead43b0e-5dbf-44a2-838e-f65db29abb30`。（来源：本轮 `eas whoami` / `eas project:info`）
- 当前分支起点与 `origin/codex/ios-appstore-build3-20260804` 一致，fetch 后 ahead/behind 为 `0/0`。（来源：本轮 Git 原始输出）
- App、Web、H5、邮件和页面生成器已改用用户确认的第一版 logo；App 首页、付费页、隐私页及 Web 浅色/深色/移动版均已真实渲染回读。（来源：本轮本地浏览器与静态资源审计）
- 本地定向门已通过：39/39 tests、TypeScript、配置、1024×1024 无 alpha 图标、Expo Doctor 20/20、iOS/Web export、7 个 Web 页面资源引用和 `git diff --check`。（来源：本轮命令原始输出）
- 完整 `npm run verify` exit 0：39/39 tests、配置、资源、typecheck、Doctor 20/20、实时汇率、products `5,689`、price history `84,047`、启动预览 `200`、iOS export `1,497 modules / 5.4 MB`，最终原文 `verify_local_ok`。（来源：本轮完整命令原始输出）
- `npm audit --omit=dev --audit-level=high` exit 0；现有 11 项均为 Expo 构建工具链的 moderate，forced fix 会降级到 Expo 46.0.21，未执行。（来源：本轮 npm audit 原始输出）

## 假设
- `eas.json` 使用 `appVersionSource=local` 与 production `autoIncrement=true`；以本地 build number 3 启动 production build 时，EAS 将候选递增为 build 4，并在本地留下需另行提交的 build-number 变更。
- Apple / TestFlight 状态会变化；上传、处理、分组与版本绑定必须在写后独立读回，不能沿用 build 3 的历史结果。

## 验收标准
1. 完整 `npm run verify` exit 0，且最终出现 `verify_local_ok`。
2. `npm audit --omit=dev --audit-level=high` 无 high/critical；不得执行破坏性 `--force` 修复。
3. 品牌变更提交并推送到 build 4 分支，构建工作树可追溯。
4. EAS production build 读回 `FINISHED`、App `1.0.0`、build `4`，并下载同一签名 IPA 做 Info.plist、图标资源和 SHA-256 核验。
5. Apple 上传后读回 `processingState=VALID` 与 `APP_STORE_ELIGIBLE`，再加入 `GearDrop Internal` 并把 iOS 1.0 build relationship 更新为 build 4；每项写操作独立 GET 回读。
6. 不上传旧截图、不提交 App Review；等待 build 4 真机 StoreKit 与最终截图验收。

## 下一步
1. 提交并推送第一版 logo 候选。
2. 创建 EAS production build 4，验证 IPA 后上传 Apple。
3. 等待 Apple VALID，加入内部 TestFlight 并绑定 iOS 1.0；更新发布档案。

## 死路 / 防回归
- 默认 npm cache 曾导致 EAS CLI 安装异常；本任务使用独立 cache `/private/tmp/geardrop-eas-npm-cache-build4`。
- 不使用 Apple ID 密码重试；沿用已配置的 App Store Connect API key / EAS 凭证路径。
- EAS Submit free-tier 队列可能长时间等待；只有在取得同一 IPA 哈希后，才可改用 Apple 官方上传工具，避免重复构建或重复上传。
