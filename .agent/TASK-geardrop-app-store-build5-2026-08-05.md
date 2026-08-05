# TASK: GearDrop App Store build 5（更新：2026-08-05 EDT）

## Why（一句话）
把 build 4 真机暴露的地区选择器与搜索自动纠错问题合并进一个可追溯的 build 5，完成 Apple 上传、内部 TestFlight 分组和 iOS 1.0 build 绑定，同时保留真机交易与最终截图通过前不提审的边界。

## 当前状态：进行中，build 5 尚未创建或上传

## 已确认事实
- 当前隔离工作树位于 `/private/tmp/geardrop-region-sheet-20260804.vdrpWP/worktree`，分支 `codex/fix-ios-region-sheet-20260804`，开始本任务时工作树干净；HEAD `6c0c22c` 比 `origin/codex/ios-appstore-build4-logo-20260804` 精确领先 1 个提交。（来源：2026-08-05 `git status`、`git rev-parse`、`git rev-list --left-right --count`）
- `6c0c22c` 已修复 build 4 真机截图暴露的 FI/IE/AU 旗帜、动态地区持久化、长列表滚动与五语言地区名问题；上一轮记录的完整本地门为 40/40 tests、Doctor 20/20、实时目录 5,689、AU 15、iOS 1,497 modules、`verify_local_ok`，但本轮必须重新执行后才可作为 build 5 验收。（来源：本轮读取上一轮原始会话与提交）
- 独立提交 `b030527` 关闭了商品搜索框的自动填充、自动纠错和拼写检查，解决 iOS 把 `sabre` 改成 `saber` 导致美国区 0 结果的问题；该提交基于 build 3，未进入 build 4。本轮已把同一最小 diff 移植到 build 5 工作树。（来源：本轮读取 `b030527` diff、上一轮用户请求与当前文件）
- 2026-08-05 约 01:00 EDT，App Store Connect 官方 API 实时读回 GearDrop `1.0.0 (4)` 为 `VALID` / `APP_STORE_ELIGIBLE` / `IN_BETA_TESTING`，iOS 1.0 为 `PREPARE_FOR_SUBMISSION` 且唯一绑定 build 4，发布方式为 `AFTER_APPROVAL`。（来源：本轮官方 API GET）
- 同次官方 API 读回 App Store 截图为 0；monthly、annual、lifetime 三项均为 `MISSING_METADATA`，各自 Review Information screenshot 为 0。（来源：本轮官方 API GET）
- 本机识别到物理 iPhone `Jenova`，但当前状态为 `unavailable`，因此本轮开始时无法读取真机安装版本、执行 StoreKit 矩阵或截取最终素材。（来源：2026-08-05 `xcrun devicectl list devices`）

## 假设
- EAS production 的 `autoIncrement=true` 会从 Apple 已有 build 4 创建 build 5，并在本地把 `app.json` build number 更新为 5；必须以 EAS JSON、IPA Info.plist 和 Apple 处理结果为准。
- Apple/TestFlight 状态会变化；每次写入后必须用全新 API 进程独立读回，不能沿用本文件的历史状态。

## 验收标准
1. 合并地区选择器和搜索自动纠错修复后，`npm run verify` exit 0 并出现 `verify_local_ok`；`npm audit --omit=dev --audit-level=high` 无 high/critical；`git diff --check` exit 0。
2. 修复提交推送到远端 build 5 分支，远端 SHA 与本地一致。
3. EAS production build 读回 `FINISHED`、App `1.0.0`、build `5`，下载同一 IPA 并核验 SHA-256、codesign、bundle ID、版本、build、最低 iOS、iPhone-only 与非豁免加密。
4. Apple 官方验证与上传成功，最终读回 build 5 `VALID` / `APP_STORE_ELIGIBLE`。
5. build 5 加入 `GearDrop Internal` 并替换 iOS 1.0 build relationship；写后及全新进程读回 group/build/version 关系。
6. 不上传 build 4 旧截图，不提交 App Review；build 5 真机 StoreKit 与最终截图仍作为后续硬门。

## 已完成且已验证
- 地区选择器修复与搜索自动纠错关闭已合并在同一候选；本轮 `npm run verify` exit 0：40/40 tests、配置、1024×1024 无 alpha 图标、TypeScript、Doctor 20/20、2026-08-05 实时汇率、5,719 products、84,072 price-history rows、200 条启动预览、AU 16、iOS 1,497 modules / 5.4 MB，最终原文 `verify_local_ok`。（来源：本轮完整命令输出）
- `npm audit --omit=dev --audit-level=high` exit 0；仅有 11 项 Expo 构建工具链 moderate，`--force` 会破坏性降级 Expo 到 46.0.21，未执行。`git diff --check` exit 0。（来源：本轮命令输出）

## 下一步
1. 提交并推送组合修复分支。
2. 创建、验证并上传 EAS production build 5。
3. 等待 Apple `VALID`，加入内部组并绑定 iOS 1.0，随后独立读回。
4. 等真机重新可用后安装 build 5，完成交易矩阵并重截 App Store 与三项 IAP 审核图。

## 死路
- Chrome 的 App Store Connect 标签页在本轮连续两次只读加载超时；未发生平台写入，改用已验证的 App Store Connect 官方 API实时核对。
- 公开 API 不提供 build 4 的 beta 安装指标关系；测试组中两人状态为 `INSTALLED`，但不能据此断言安装的是 build 4。
