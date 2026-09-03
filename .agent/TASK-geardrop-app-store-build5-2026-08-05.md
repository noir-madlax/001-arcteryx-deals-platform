# TASK: GearDrop App Store build 5（更新：2026-08-05 EDT）

## Why（一句话）
把 build 4 真机暴露的地区选择器与搜索自动纠错问题合并进一个可追溯的 build 5，完成 Apple 上传、内部 TestFlight 分组和 iOS 1.0 build 绑定，同时保留真机交易与最终截图通过前不提审的边界。

## 当前状态：build 5 已完成 EAS production 签名构建、Apple 官方校验与上传，处理为 `VALID`，加入 3 人内部 TestFlight 组并绑定 iOS 1.0；真机 StoreKit、最终商店截图与三项 IAP 审核图通过前不提交 App Review

## 已确认事实
- 当前隔离工作树位于 `/private/tmp/geardrop-region-sheet-20260804.vdrpWP/worktree`，发布分支为 `codex/ios-appstore-build5-20260805`；build 5 源码提交 `392a7e957fd00f06e6210f5f245272c35aeededa` 已推送并经 `git ls-remote` 回读一致，未合并到脏的本地主工作树。（来源：2026-08-05 Git 原始输出）
- `6c0c22c` 已修复 build 4 真机截图暴露的 FI/IE/AU 旗帜、动态地区持久化、长列表滚动与五语言地区名问题；上一轮记录的完整本地门为 40/40 tests、Doctor 20/20、实时目录 5,689、AU 15、iOS 1,497 modules、`verify_local_ok`，但本轮必须重新执行后才可作为 build 5 验收。（来源：本轮读取上一轮原始会话与提交）
- 独立提交 `b030527` 关闭了商品搜索框的自动填充、自动纠错和拼写检查，解决 iOS 把 `sabre` 改成 `saber` 导致美国区 0 结果的问题；该提交基于 build 3，未进入 build 4。本轮已把同一最小 diff 移植到 build 5 工作树。（来源：本轮读取 `b030527` diff、上一轮用户请求与当前文件）
- 2026-08-05 约 01:00 EDT，App Store Connect 官方 API 实时读回 GearDrop `1.0.0 (4)` 为 `VALID` / `APP_STORE_ELIGIBLE` / `IN_BETA_TESTING`，iOS 1.0 为 `PREPARE_FOR_SUBMISSION` 且唯一绑定 build 4，发布方式为 `AFTER_APPROVAL`。（来源：本轮官方 API GET）
- 同次官方 API 读回 App Store 截图为 0；monthly、annual、lifetime 三项均为 `MISSING_METADATA`，各自 Review Information screenshot 为 0。（来源：本轮官方 API GET）
- 本机识别到物理 iPhone `Jenova`，但当前状态为 `unavailable`，因此本轮开始时无法读取真机安装版本、执行 StoreKit 矩阵或截取最终素材。（来源：2026-08-05 `xcrun devicectl list devices`）
- EAS production build `e88a4ac2-88f8-4332-9b77-7ee9127cd355` 最终读回 `FINISHED`：App `1.0.0`、build `5`、源码完整 SHA `392a7e957fd00f06e6210f5f245272c35aeededa`；云端构建耗时 340,006 ms，fingerprint `010722a5d240b138f95a6333b98065576a987f53`。（来源：本轮 EAS JSON）
- 同一 EAS IPA 为 30,079,040 bytes，SHA-256 `196a7b09a0e7c830d53c04588be418038b12583f2ac36b5fc67a6b9bbc070a0c`；`codesign --verify --deep --strict` 通过，Info.plist 读回 bundle `dev.100app.geardrop`、version `1.0.0`、build `5`、最低 iOS `16.4`、iPhone-only `[1]`、`ITSAppUsesNonExemptEncryption=false`。（来源：本轮下载产物、codesign、plutil 与 shasum）
- Apple Content Delivery 对该 IPA 返回 `VERIFY SUCCEEDED with no errors`、`UPLOAD SUCCEEDED with no errors`，delivery/build resource `c76bab54-1175-4729-a161-981b48b4ebfe` 最终为 `VALID` / `APP_STORE_ELIGIBLE`。（来源：本轮 `xcrun altool` 原始输出）
- 写入前官方 API 读回 build 5 不在 `GearDrop Internal`，iOS 1.0 仍绑定 build 4；随后内部组 relationship POST 与版本 build relationship PATCH 均返回 HTTP 204。全新进程独立读回 build 5 为 `IN_BETA_TESTING` / `READY_FOR_BETA_SUBMISSION`，测试组含 build 2/3/4/5 与 3 testers，iOS 1.0 当前 build 为 build 5。（来源：本轮 App Store Connect API 写前、写响应与独立写后 GET）
- 2026-08-05 写后独立读回 App Store 截图仍为 0；monthly、annual、lifetime 三项均为 `MISSING_METADATA`，各自 Review Information screenshot 为 0；版本仍为 `PREPARE_FOR_SUBMISSION`，本轮未创建 App Review submission。（来源：本轮 App Store Connect API GET）

## 假设
- EAS production 的 `autoIncrement=true` 已把本地 `app.json` build number 更新为 5；后续 build number 仍必须以 EAS JSON、IPA Info.plist 和 Apple 处理结果为准。
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
- 组合修复源码已提交并推送，远端 SHA 独立回读一致；EAS 已把本地 `app.json` build number 从 4 自动递增为 5。（来源：本轮 Git、EAS 输出与本地 diff）
- EAS build 5、签名 IPA、Apple 官方验证/上传与 Apple `VALID` 处理全部完成，且源码提交、bundle/version/build 与签名身份逐项匹配。（来源：本轮 EAS、IPA 与 Apple 原始输出）
- build 5 已加入 `GearDrop Internal` 并替换 iOS 1.0 的 build 4 relationship；两次写入均为 HTTP 204，随后全新 API 进程独立读回 build 5 位于测试组且为版本当前 build。（来源：本轮 App Store Connect API 原始输出）
- 提审边界被保留：未上传旧截图、未附加缺图的三项 IAP、未提交 App Review。（来源：本轮官方 API GET）

## 下一步
1. 等真机 `Jenova` 重新可用后从 TestFlight 安装 build 5，验证 FI/IE/AU 地区显示和滚动、地区持久化、美国区搜索 `sabre`、首屏图片/启动预览与 logo。
2. 在 build 5 完成 localized price、monthly/annual/lifetime、取消、pending、entitlement、重装恢复、无购买恢复与离线恢复矩阵。
3. 从通过真机交易验收的 build 5 重截并上传 App Store 最终图及三项 IAP Review Information screenshot，独立读回截图和商品状态。
4. 把三项首发商品附加到 iOS 1.0，最终复核出口合规和审核信息后，再单独授权提交 App Review。

## 死路
- Chrome 的 App Store Connect 标签页在本轮连续两次只读加载超时；未发生平台写入，改用已验证的 App Store Connect 官方 API实时核对。
- 公开 API 的 build-specific tester filter 对 build 5 返回 0，同时测试组中两人状态为 `INSTALLED`；该接口语义不足以断言两人已经安装 build 5。
- 首次 EAS `--wait --json` 调用只返回未验证证书提示，exit 0 但未创建 build，build list 与 `app.json` 均证明无外部产物。改用上一轮成功的无代理 `--no-wait` 路径后，build 5 才真实创建。
- EAS 凭据检查仍显示 Distribution Certificate 与 Provisioning Profile 的 team 标签不同，并因非交互模式无法补录 Apple Team ID；本轮未据提示推断成功，最终以 build 5 的 codesign、Info.plist、Apple 官方 `VERIFY SUCCEEDED` 与 `VALID` 处理终态完成验收。
