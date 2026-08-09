# TASK: GearDrop App Store 上线继续（更新：2026-08-09 Asia/Taipei）

## Why（一句话）
把当前最新签名候选从 TestFlight 真机验收推进到 App Store 1.0 可提交／已提交状态，并用 Apple 实时读回证明每个外部步骤。

## 当前状态：进行中

已从 `codex/ios-pro-offer-code-20260805` 的提交 `41decd3` 创建隔离分支 `codex/ios-appstore-continue-20260809`；三个同 SDK 补丁升级后的 production build 7 已完成 EAS 签名构建、本地产物核验、Apple 上传处理和内部 TestFlight 分发，并补齐 build 7 的 en-US `What to Test`。App Store 1.0 仍绑定旧 build 5，App Store 截图为 0，三项首发 IAP 均缺 Review Information screenshot；物理 iPhone 当前离线且 Mac 锁定，尚未完成真机交易矩阵、绑定 build 7 或提交 App Review。

## 已确认事实

- 主工作树 `/Users/J/Projects/Desktop-Projects/hermes projects/001-arcteryx-deals-platform` 有既有未提交 App 资源改动，且本地 `main` 落后 `origin/main`；本轮不在主工作树编辑。（来源：2026-08-09 `git status --short --branch`）
- 隔离工作树为 `/private/tmp/geardrop-appstore-continue-20260809.dKiFOt/worktree`，分支 `codex/ios-appstore-continue-20260809`，起点 `41decd3`。（来源：2026-08-09 `git worktree add` 输出）
- 起点任务档案记录 build 6 已签名上传并进入内部 TestFlight，但 iOS 1.0 历史上仍绑定 build 5；真机交易／邀请码矩阵和最终审核截图未完成。该记录只是历史线索，本轮必须实时核验。（来源：`.agent/TASK-geardrop-pro-offer-code-2026-08-05.md`）
- 本轮开工时 EAS 账户读取成功；当时 `eas build:list` 返回最新完成的 iOS production 构建为 `1.0.0 (6)`，build ID `c6082010-7861-4a02-a496-6d69aa629b9f`，状态 `FINISHED`，源码提交 `edc6877`。该读回随后已被本轮 build 7 状态取代。（来源：本轮开工 EAS CLI JSON）
- 物理 iPhone `Jenova` 被 CoreDevice 识别但当前为 `unavailable` / offline；iPhone 镜像先显示“iPhone 使用中”，后因未锁屏而超时，Mac 随后锁定，尚不能执行真机矩阵。（来源：本轮 `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun devicectl list devices`、`xctrace list devices` 与 iPhone 镜像读回）
- App Store Connect 的内置浏览器和 Chrome 均进入 Apple 登录页；Chrome 已发起 Passkey 验证但仍等待用户本人确认。Apple API key 已允许独立读回 build/version/IAP/screenshots；浏览器登录仍是当前 App Privacy UI 复核与人工上传素材的入口。（来源：本轮页面 URL、DOM 与 Apple API 读回）
- 首次本轮 `npm run verify` 在 40/40 tests、配置、资源与 TypeScript 通过后，因 Expo Doctor 新要求 `expo ~57.0.11`、`expo-router ~57.0.11`、`expo-notifications ~57.0.9` 而退出 1；`npx expo install --check` 独立返回同一组三项漂移。（来源：本轮命令原始输出）
- 已只升级上述三个 SDK 57 补丁版本；`npx expo install --check` 随后返回 `Dependencies are up to date`，未执行 Expo/React Native 破坏性降级。（来源：`app/package.json`、`app/package-lock.json` 与本轮命令输出）
- 补丁升级后完整 `npm run verify` exit 0：40/40 tests、配置、1024×1024 无 alpha 图标、TypeScript、Expo Doctor 20/20、实时汇率、5,730 products、84,354 price-history rows、200 条启动预览、AU 16、iOS 1,497 modules / 5.4 MB，最终原文 `verify_local_ok`。（来源：本轮完整命令输出）
- 当前 `npm audit --omit=dev` 报 15 high / 8 moderate；high 链只落到 Metro 构建期依赖 `image-size@1.2.1` 的两项无限循环 DoS advisory，npm 给出的自动修复是破坏性降级 Expo/React Native/RevenueCat，未执行。该依赖不在运行时业务代码路径，但正式风险处置仍需记录。（来源：本轮 `npm audit --json` 与 `npm ls image-size`）
- 补丁升级提交 `b12c48476f5ebe450ed26af4b0bc8c8c6aec5947` 已推送到 `origin/codex/ios-appstore-continue-20260809`；EAS production build `b23dff43-aba6-4980-b231-b7588e1d0530` 读回 `FINISHED`、App `1.0.0`、build `7`、源码完整 SHA 与上述提交一致。（来源：本轮 Git push 与 EAS JSON）
- EAS 自动把本地 `app.json` build number 从 6 增至 7；定向配置检查先如实失败于测试契约仍期望 6。只把 `scripts/verify-config.ts` 的期望值和成功输出同步为 7 后，完整 `npm run verify` 再次 exit 0：40/40 tests、build 7 config、release assets、TypeScript、Expo Doctor 20/20、2026-08-09 汇率、5,730 products、84,357 price-history rows、200 条启动预览、AU 16、iOS 1,497 modules / 5.4 MB，最终原文 `verify_local_ok`。（来源：本轮失败输出、最小 diff 与最终完整命令输出）
- build 7 IPA 为 30,081,208 bytes，SHA-256 `60a139f3c89942738a73256127f311d0d0d5d2e4422aee3ba7d87f2f2b9afa97`；`codesign --verify --deep --strict` 通过，Info.plist 读回 `dev.100app.geardrop` / `1.0.0` / `7` / minimum iOS 16.4 / iPhone-only `[1]` / `ITSAppUsesNonExemptEncryption=false`，Distribution Team 为 `46H3U4N2U3`。（来源：本轮下载的同一 EAS IPA、本地 codesign/plist/shasum）
- EAS Submit `4e814bec-6888-4691-81c0-ae631922c8ba` 已针对精确 build 7 完成；Apple 独立读回 build ID `b79d5bcc-e3cf-46bd-9038-fc12cb548c09` 为 `VALID` / `APP_STORE_ELIGIBLE` / `IN_BETA_TESTING` / `READY_FOR_BETA_SUBMISSION`。（来源：本轮 `submit:view`、`submit:status` 与 Apple API）
- EAS `--groups` 未自动建立 build 7 与内部组的关系；本轮以精确 App `6790165332`、bundle `dev.100app.geardrop`、build 7 和内部组 `GearDrop Internal` 做写前断言，写前不含 build 7，添加后立即读回包含。全新进程再次读回 `already-present`，组内 build 为 2–7。（来源：本轮 Apple 官方 API 关系写入与两次独立读回）
- build 7 的 en-US beta localization 写前 `What to Test` 为空；只在仍为空时写入 396 字符的真机验收说明，随后同进程和全新进程均读回 `hasWhatsNew=true` / length 396 / exact match。内部组当前 3 testers：2 `INSTALLED`、1 `INVITED`，API 未返回具体安装 build number。（来源：本轮 Apple API 写前、写后与独立读回）
- App Store 1.0 实时读回为 `PREPARE_FOR_SUBMISSION`、`AFTER_APPROVAL`，仍绑定 build 5；en-US description、keywords、Support URL 和完整审核联系人均存在，App Store screenshot set 为空、总数 0，且没有 ready/in-progress review submission。（来源：本轮 Apple API）
- App Information 实时读回为 `PREPARE_FOR_SUBMISSION`，主分类 `SHOPPING`，en-US name/subtitle/Privacy Policy URL、年龄分级和 `USES_THIRD_PARTY_CONTENT` 声明存在；免费价格表以 USA 为基准。Apple 新 availability v2 API 返回 175 个地区中 174 个可用，中国大陆为不可用，`availableInNewTerritories=false`。（来源：本轮 Apple 官方 API 200 响应）
- 三项预期商品均存在；正式 v2 IAP/subscription 资源把 monthly、annual、lifetime 全部读回为 `MISSING_METADATA`。monthly/annual 的 Review Information screenshot 关系返回 200/null，lifetime 返回 404 not found，三者均证明截图不存在；Apple 当前 API key 路径不再支持旧 App Privacy publish-state 关系，当前发布状态仍需登录 UI 复核。（来源：本轮 Apple 官方 API）

## 假设

- 若 build 7 真机验收暴露代码缺陷，将在本隔离分支做最小修复并生成新 build；否则不无谓重建。
- App Privacy 的历史已发布记录仍只是线索；因为当前 API 关系已失效，必须在恢复 App Store Connect 登录后从 UI 重新确认。

## 验收标准

1. 独立读回当前 Git/EAS/Apple build、版本、TestFlight 分组、IAP 与截图状态。
2. 在物理 iPhone 上验证 build 7 的地区、搜索、首屏／图片／Logo，以及 IAP 购买、取消、pending、恢复、离线和 Offer Code 权益链路；每项保留可复核证据。
3. 只从通过真机验收的签名候选生成并上传 App Store 截图和三项 IAP Review Information screenshot；上传后独立读回数量与商品状态。
4. 将最终 build 与三项首发 IAP 绑定 iOS 1.0，复核出口合规、审核信息、availability 和 release mode；只有所有硬门通过才提交 App Review。
5. 外部写入均记录写前状态、精确目标、响应与全新进程写后读回；不得把 HTTP 204 或队列状态单独当作成功。

## 已完成且已验证

- 已创建隔离工作树和分支，未覆盖主工作树既有改动。（来源：2026-08-09 Git 输出）
- 已完成三个 Expo SDK 57 补丁升级并在本轮重新通过完整本地发布门。（来源：本轮 `npm run verify`）
- 已完成 build 7 的 EAS 签名构建与同一 IPA 的哈希、签名和 Info.plist 验收。（来源：本轮 EAS 与本地产物命令）
- 已把 EAS 自动递增的 build 7 同步到发布配置契约，并在该最终本地状态重新通过完整 `npm run verify`。（来源：本轮最终完整命令）
- 已完成 build 7 的 Apple 上传处理、内部组关系和 `What to Test`；三个外部写入都已在全新进程独立读回。（来源：本轮 EAS/Apple API）
- 已完成当前 App Store 版本、元数据、availability、三项 IAP 和审核截图关系的 live 只读盘点；未绑定最终 build、未附加 IAP、未提交审核。（来源：本轮 Apple API）

## 下一步

1. 用户解锁 Mac、锁屏并保持 iPhone 在线后，通过 iPhone Mirroring 从 TestFlight 安装 build 7，完成 UI、StoreKit、恢复、pending、离线与 Offer Code 矩阵。
2. 从通过真机验收的 build 7 截取最终 App Store 图和 paywall 图，上传 App Store screenshot set 与三项 IAP Review Information screenshot，并独立读回数量和商品状态。
3. 在登录 UI 中复核 App Privacy 发布状态；全部硬门通过后才把 iOS 1.0 从 build 5 切到 build 7、附加三项 IAP，做最终 readback 后提交审核。

## 死路

- 内置浏览器与 Chrome 的 App Store Connect 会话均未自动恢复；Chrome 已停在 Passkey 验证，必须由用户本人确认，不能用旧页面状态代替 live 读回。
- iPhone 镜像因真机处于使用中而超时；在用户锁屏前无法通过工具模拟真机交易或截图。
- 首次 `eas submit` 带 `--json` 时 CLI 21.7.0 以 `Nonexistent flag: --json` 在本地退出 1，未创建外部提交；去掉该 flag 后才成功调度 submission。
- EAS `submit:status` 起初因本机时间比 Apple `Date` 头快约 29 秒而返回 401；本轮只对该进程注入 -60 秒 `Date` shim 后读回成功，未改系统时钟。
- `@expo/apple-utils` 的旧 `dataUsagePublishState` 和 `availableTerritories` 关系已被 Apple 移除；availability 已改用 Apple 官方 `appAvailabilityV2` + v2 territory endpoint，App Privacy publish state 仍需 UI 登录复核。
