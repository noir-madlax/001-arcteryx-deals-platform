# TASK: GearDrop App Store 上线继续（更新：2026-08-09 Asia/Taipei）

## Why（一句话）
把当前最新签名候选从 TestFlight 真机验收推进到 App Store 1.0 可提交／已提交状态，并用 Apple 实时读回证明每个外部步骤。

## 当前状态：进行中

已从 `codex/ios-pro-offer-code-20260805` 的提交 `41decd3` 创建隔离分支 `codex/ios-appstore-continue-20260809`；build 6 仍是 EAS 最新完成构建，但本轮 Expo Doctor 发现三个同 SDK 补丁漂移，已做最小升级并重新通过完整本地门。App Store Connect 登录与物理 iPhone 镜像仍等待用户本人完成登录／锁屏，尚未在本轮绑定新 build 或提交 App Review。

## 已确认事实

- 主工作树 `/Users/J/Projects/Desktop-Projects/hermes projects/001-arcteryx-deals-platform` 有既有未提交 App 资源改动，且本地 `main` 落后 `origin/main`；本轮不在主工作树编辑。（来源：2026-08-09 `git status --short --branch`）
- 隔离工作树为 `/private/tmp/geardrop-appstore-continue-20260809.dKiFOt/worktree`，分支 `codex/ios-appstore-continue-20260809`，起点 `41decd3`。（来源：2026-08-09 `git worktree add` 输出）
- 起点任务档案记录 build 6 已签名上传并进入内部 TestFlight，但 iOS 1.0 历史上仍绑定 build 5；真机交易／邀请码矩阵和最终审核截图未完成。该记录只是历史线索，本轮必须实时核验。（来源：`.agent/TASK-geardrop-pro-offer-code-2026-08-05.md`）
- 2026-08-09 EAS 账户读取成功；`eas build:list` 实时返回最新完成的 iOS production 构建仍为 `1.0.0 (6)`，build ID `c6082010-7861-4a02-a496-6d69aa629b9f`，状态 `FINISHED`，源码提交 `edc6877`。（来源：本轮 EAS CLI JSON）
- 物理 iPhone `Jenova` 被 CoreDevice 识别但当前为 `unavailable`；iPhone 镜像先显示“iPhone 使用中”，后因未锁屏而超时，尚不能执行真机矩阵。（来源：本轮 `xcrun devicectl list devices`、`xctrace list devices` 与 iPhone 镜像读回）
- App Store Connect 的内置浏览器和 Chrome 均进入 Apple 登录页；Chrome 已发起 Passkey 验证，但仍等待用户本人确认，故 Apple build/version/IAP/screenshots 的 2026-08-09 live 状态尚未读回。（来源：本轮页面 URL、DOM 与截图）
- 首次本轮 `npm run verify` 在 40/40 tests、配置、资源与 TypeScript 通过后，因 Expo Doctor 新要求 `expo ~57.0.11`、`expo-router ~57.0.11`、`expo-notifications ~57.0.9` 而退出 1；`npx expo install --check` 独立返回同一组三项漂移。（来源：本轮命令原始输出）
- 已只升级上述三个 SDK 57 补丁版本；`npx expo install --check` 随后返回 `Dependencies are up to date`，未执行 Expo/React Native 破坏性降级。（来源：`app/package.json`、`app/package-lock.json` 与本轮命令输出）
- 补丁升级后完整 `npm run verify` exit 0：40/40 tests、配置、1024×1024 无 alpha 图标、TypeScript、Expo Doctor 20/20、实时汇率、5,730 products、84,354 price-history rows、200 条启动预览、AU 16、iOS 1,497 modules / 5.4 MB，最终原文 `verify_local_ok`。（来源：本轮完整命令输出）
- 当前 `npm audit --omit=dev` 报 15 high / 8 moderate；high 链只落到 Metro 构建期依赖 `image-size@1.2.1` 的两项无限循环 DoS advisory，npm 给出的自动修复是破坏性降级 Expo/React Native/RevenueCat，未执行。该依赖不在运行时业务代码路径，但正式风险处置仍需记录。（来源：本轮 `npm audit --json` 与 `npm ls image-size`）

## 假设

- 当前物理 iPhone、Apple 登录态、build 关系、IAP 状态和截图数量可能已变化；未完成实时读回前不沿用 2026-08-05 结论。
- 若 build 6 真机验收暴露代码缺陷，将在本隔离分支做最小修复并生成新 build；否则不无谓重建。
- 同 SDK 补丁升级改变了签名候选源码，若保留该升级则需生成新的 build 7，并以 build 7 而非 build 6 完成最终真机和截图验收。

## 验收标准

1. 独立读回当前 Git/EAS/Apple build、版本、TestFlight 分组、IAP 与截图状态。
2. 在物理 iPhone 上验证 build 6 的地区、搜索、首屏／图片／Logo，以及 IAP 购买、取消、pending、恢复、离线和 Offer Code 权益链路；每项保留可复核证据。
3. 只从通过真机验收的签名候选生成并上传 App Store 截图和三项 IAP Review Information screenshot；上传后独立读回数量与商品状态。
4. 将最终 build 与三项首发 IAP 绑定 iOS 1.0，复核出口合规、审核信息、availability 和 release mode；只有所有硬门通过才提交 App Review。
5. 外部写入均记录写前状态、精确目标、响应与全新进程写后读回；不得把 HTTP 204 或队列状态单独当作成功。

## 已完成且已验证

- 已创建隔离工作树和分支，未覆盖主工作树既有改动。（来源：2026-08-09 Git 输出）
- 已完成三个 Expo SDK 57 补丁升级并在本轮重新通过完整本地发布门。（来源：本轮 `npm run verify`）

## 下一步

1. 提交并推送补丁升级，生成并核验 build 7；Apple 登录恢复后上传并加入内部 TestFlight。
2. 实时读取 App Store Connect、IAP 与截图状态；物理 iPhone 可用后完成 build 7 真机矩阵。
3. 生成并上传审核素材，绑定版本／IAP，完成最终读回与提审。

## 死路

- 内置浏览器与 Chrome 的 App Store Connect 会话均未自动恢复；Chrome 已停在 Passkey 验证，必须由用户本人确认，不能用旧页面状态代替 live 读回。
- iPhone 镜像因真机处于使用中而超时；在用户锁屏前无法通过工具模拟真机交易或截图。
