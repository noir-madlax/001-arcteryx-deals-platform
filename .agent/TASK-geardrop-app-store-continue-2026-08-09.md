# TASK: GearDrop App Store 上线继续（更新：2026-08-10 Asia/Taipei）

## Why（一句话）
把当前最新签名候选从 TestFlight 真机验收推进到 App Store 1.0 可提交／已提交状态，并用 Apple 实时读回证明每个外部步骤。

## 当前状态：进行中

已从 `codex/ios-pro-offer-code-20260805` 的提交 `41decd3` 创建隔离分支 `codex/ios-appstore-continue-20260809`；三个同 SDK 补丁升级后的 production build 7 已完成 EAS 签名构建、本地产物核验、Apple 上传处理和内部 TestFlight 分发，并补齐 build 7 的 en-US `What to Test`。App Store 1.0 仍绑定旧 build 5，App Store 截图为 0，三项首发 IAP 均缺 Review Information screenshot。目标 TestFlight tester 已按用户授权完成 GearDrop 单应用关系重置、同邮箱重建、重新入组和新邀请送达；但 iPhone 用新邀请兑换时，Apple 明确提示当前显示邮箱虽与收件邮箱一致，底层邀请却关联到另一个“原始 Apple 账户”（界面仅给出脱敏 QQ 邮箱提示）。用户报告已切换后再次实时核验，`媒体与购买项目 > 查看账户` 仍要求此前 Gmail Apple 账户的密码，证明切换尚未生效；当前仍阻塞于 Apple 账户身份映射，尚未完成 build 7 真机矩阵、绑定或 App Review 提交。

## 已确认事实

- 主工作树 `/Users/J/Projects/Desktop-Projects/hermes projects/001-arcteryx-deals-platform` 有既有未提交 App 资源改动，且本地 `main` 落后 `origin/main`；本轮不在主工作树编辑。（来源：2026-08-09 `git status --short --branch`）
- 隔离工作树为 `/private/tmp/geardrop-appstore-continue-20260809.dKiFOt/worktree`，分支 `codex/ios-appstore-continue-20260809`，起点 `41decd3`。（来源：2026-08-09 `git worktree add` 输出）
- 起点任务档案记录 build 6 已签名上传并进入内部 TestFlight，但 iOS 1.0 历史上仍绑定 build 5；真机交易／邀请码矩阵和最终审核截图未完成。该记录只是历史线索，本轮必须实时核验。（来源：`.agent/TASK-geardrop-pro-offer-code-2026-08-05.md`）
- 本轮开工时 EAS 账户读取成功；当时 `eas build:list` 返回最新完成的 iOS production 构建为 `1.0.0 (6)`，build ID `c6082010-7861-4a02-a496-6d69aa629b9f`，状态 `FINISHED`，源码提交 `edc6877`。该读回随后已被本轮 build 7 状态取代。（来源：本轮开工 EAS CLI JSON）
- 物理 iPhone `Jenova` 开工时被 CoreDevice 识别为 `unavailable` / offline，且 iPhone 镜像先因“iPhone 使用中”超时；用户随后完成 Mac 解锁与 iPhone 授权，iPhone 镜像已成功进入手机 UI。`devicectl` 仍显示 `unavailable`，所以当前真机操作证据来自 iPhone 镜像而不是有线 CoreDevice 通道。（来源：本轮 `devicectl` 与 iPhone 镜像实时读回）
- App Store Connect 的 Chrome 登录已由用户完成；当前 UI 可实时读取 TestFlight、版本、App Privacy 与 IAP 页面。内置浏览器旧登录失败记录不再是当前阻塞项。（来源：本轮 Chrome App Store Connect live DOM）
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
- App Store Connect UI 已实时复核 App Privacy 为已发布状态，页面显示约 6 天前发布，并列出 Customer Support、Email Address、Purchase History、Product Interaction 四类数据；此前“仍需 UI 复核”的假设已关闭。（来源：本轮 App Privacy live DOM）
- App Store 1.0 UI 与 API 一致：仍为 Prepare for Submission、0/10 iPhone screenshots、绑定 build 5、自动发布已选，`Add for Review` 可见但未点击。（来源：本轮版本页 live DOM）
- 内部组 UI 读回 3 testers / 6 builds；一台其他测试设备已安装 build 7，目标 `Jenova` 对应的 iPhone 16 Pro 仍记录为 build 6。iPhone TestFlight 设置里的当前账号与该 build 6 测试员记录精确一致，排除“登录错账号”；但 GearDrop 在列表内搜索仍为无结果。（来源：本轮 TestFlight 组 live DOM 与 iPhone 镜像）
- 对目标 tester + App 发送 `betaTesterInvitations` 前已断言精确 App、bundle、内部组与 build 7；Apple 返回 HTTP 409 / `STATE_ERROR.TESTER_INVITE.ALREADY_ACCEPTED`，证明邀请已接受而不是待接受。随后只把该 tester 从目标组关系移出并立即加回，DELETE/POST 均为 204；写后 GET 读回组关系存在、目标 tester 唯一、状态仍为 `INSTALLED`、组内仍为 3 testers。（来源：本轮 Apple 官方 API 写前、写响应与写后读回）
- iPhone Spotlight 中残留的一条旧 TestFlight invitation 深链打开后显示已撤销或无效，不能用于恢复；TestFlight 强制关闭、重启、下拉刷新和 App 内搜索后仍不显示 GearDrop。（来源：本轮 iPhone 镜像）
- 当前测试账号邮箱于 2026-08-09 21:43（Asia/Taipei）收到 Apple 官方、DKIM/SPF/DMARC 均通过的 build 7 可测试通知；邮件的官方 app 深链为 GearDrop App `6790165332`，证明新通知已送达正确账号。（来源：本轮 Gmail 精确搜索与单封邮件读取）
- iPhone Safari 已成功把该官方深链交给 TestFlight，但 TestFlight 连续返回 `App 不可用 / 此 App 不可用于你的 Apple 账户`。TestFlight 设置实时显示的账号与邀请收件账号精确一致；App Store Connect 同时读回目标 tester 为 `Installed 1.0.0 (6)`、17 sessions、设备 iPhone 16 Pro / iOS 26.5.2，build 7 在 `GearDrop Internal` 且另一 tester 已安装 build 7，因此当前是目标 tester 的 Apple 账户资格/绑定不一致，不是 URL、build 分组或登录邮箱错误。（来源：本轮 iPhone Safari/TestFlight 与 App Store Connect live DOM）
- 经用户明确同意，已在 iPhone `Apple 账户 > 媒体与购买项目` 退出并用同一 Apple 账户自动重新登录；写后再次打开菜单出现 `退出登录`，证明购买账号会话已恢复。强制关闭 TestFlight 后重新打开同一官方邀请，仍返回完全相同的 `App 不可用`，排除客户端 TestFlight 缓存和媒体购买会话。（来源：本轮 iPhone 镜像写前、确认提示、写后菜单与邀请重试）
- Apple 官方当前 API 把两种移除明确区分：`DELETE /v1/betaTesters/{id}` 会移除该 tester 测试所有 App 的能力；`DELETE /v1/apps/{appId}/relationships/betaTesters` 只移除指定 App 的全部组/build 访问。因此若继续服务端重置，必须优先使用 GearDrop app-specific relationship reset，禁止直接全局删除 tester。（来源：2026-08-09 Apple Developer Documentation live）
- 用户于 2026-08-10 明确接受 GearDrop 当前 17 sessions、设备/build 关联或可见性可能丢失，并授权执行 app-specific reset、把同一邮箱 tester 加回 `GearDrop Internal`、发送新邀请和独立读回；全程未调用全局 `DELETE /v1/betaTesters/{id}`。（来源：本轮用户授权与 API 调用路径）
- 写前全新 JWT 进程断言精确 App `6790165332` / `dev.100app.geardrop`、精确内部组、build 7 `VALID`、组内 3 testers，以及近一年指标中唯一 17 sessions 的目标 tester；该 tester 当时为 `INSTALLED`、只属于这一个 GearDrop 组，且没有其他 App 关系。（来源：本轮 Apple 官方 API 写前读回）
- app-specific `DELETE /v1/apps/{appId}/relationships/betaTesters` 返回 `202 Accepted`，不是此前预期的 204；异步完成后目标从 GearDrop 组消失。由于写前其他 App 关系为 0，旧 tester 资源也变为不可读，但没有调用全局删除 endpoint。（来源：本轮 Apple 官方 API 写响应与异步读回）
- 只读 Gmail 从已认证的 Apple build 7 邮件解析出精确收件账号后，`POST /v1/betaTesters` 以同一邮箱和精确 `GearDrop Internal` 关系返回 201；`POST /v1/betaTesterInvitations` 再返回 201。写后连续 10 秒以及全新 JWT 进程均读回：同邮箱 tester 唯一、`INVITED`、只关联 GearDrop 和该组、组内恢复为 3 testers、build 7 仍为 `VALID`。（来源：本轮 Gmail 只读与 Apple 官方 API 写入/独立读回）
- tester 重建与显式邀请各触发一封全新 Apple 邮件；两封均送达精确账号、包含 GearDrop App ID，且 DKIM/SPF/DMARC 全部通过。两封邮件指向同一个邀请，不存在“误用已被重发作废的旧码”。（来源：本轮 Gmail 精确搜索与两封邮件读取）
- Mac Safari 打开全新邀请后读回标题为 `GearDrop: Outdoor Deals 1.0.0 (7)`，并提供 TestFlight 内兑换路径。iPhone TestFlight 用该新邀请兑换时，Apple 明确返回当前 Apple 账户与邀请关联账户不符，并提示应使用另一个脱敏的原始 QQ 邮箱 Apple 账户；当前 TestFlight 显示邮箱仍与邀请收件邮箱精确一致。（来源：本轮 Mac Safari 与 iPhone 镜像）
- 已彻底划掉并冷启动 TestFlight，再次兑换同一新邀请仍得到完全相同的原始 Apple 账户关联错误。终态全新 JWT 进程读回 tester 仍唯一、`INVITED`、GearDrop/精确组关系完整、组内 3 testers、build 7 `VALID`，证明失败未破坏服务端恢复状态。（来源：本轮 iPhone 镜像与 Apple 官方 API 终态读回）
- 用户报告已完成账户切换后，本轮从 iPhone `Apple 账户 > 媒体与购买项目 > 查看账户` 做只读核验；系统仍进入此前 Gmail Apple 账户的密码验证页。未输入密码、未退出任何账户、未再次兑换邀请，因此这次账户切换实际未生效。（来源：2026-08-10 iPhone 镜像实时读回）
- IAP UI 与 API 一致：monthly、annual、lifetime 均为 Prepare for Submission、175 个地区可用、en-US localization 与 review notes 已存在，US 价格分别为 `$3.99`、`$23.99`、`$49.99`；三项 Review Information 都只显示 `Choose File`，截图为空。Lifetime Offer 仍为 production 0 / sandbox 100；本轮未购买、未生成新码、未添加审核项。（来源：本轮 App Store Connect IAP/subscription live DOM）

## 假设

- 若 build 7 真机验收暴露代码缺陷，将在本隔离分支做最小修复并生成新 build；否则不无谓重建。
- GearDrop app-specific tester access reset 已按用户授权执行；旧 tester 资源变为不可读，新 tester 当前为 `INVITED`。旧 17 sessions 与设备/build 历史后续是否会重新聚合尚未验证。Apple 给出的原始账户提示表明，相同可见邮箱可能分别存在于不同 Apple 账户身份上；具体应切换到哪个账户或改用哪个新邮箱属于身份/登录选择，不能由任务自行推断。

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
- 已完成 App Privacy 当前发布状态、App Store 1.0 页面、TestFlight tester/device/build、三项 IAP localization/price/review screenshot 的登录 UI 复核。（来源：本轮 App Store Connect live DOM）
- 已确认 iPhone TestFlight 账号与目标 tester 一致，完成 tester-group 关系重建、官方新邮件/深链验证、TestFlight 强制重启及同一 Apple 账户的媒体购买会话退出/重登；当前仍受目标 tester 的 Apple 账户资格绑定异常阻塞。（来源：本轮 Apple API、Gmail、App Store Connect live DOM 与 iPhone 镜像）
- 已按用户授权完成 GearDrop app-specific tester access reset；处理 Apple 异步 202 后，以同一邮箱重建 tester、恢复精确组、发送新邀请，并在连续稳定读回与全新进程终态读回中确认服务端状态完整。（来源：本轮 Apple 官方 API 与 Gmail）
- 已在物理 iPhone 上用新邀请兑换并在 TestFlight 冷启动后复测；两次均由 Apple 明确判定当前 Apple 账户不是邀请关联的原始账户，排除了旧 tester ID、旧邮件、旧码和旧 App 进程缓存。（来源：本轮 Mac Safari 与 iPhone 镜像）

## 下一步

1. 用户需在 iPhone `Apple 账户 > 媒体与购买项目` 先退出此前 Gmail Apple 账户，再亲自登录错误提示中的“原始 Apple 账户”，或明确提供一个未绑定到该原始身份的新测试邮箱；登录凭据与 2FA 不由任务代填。切换后先用 `查看账户` 验证已不再进入此前 Gmail 账户，再兑换当前新邀请并安装 build 7，完成 UI、StoreKit、恢复、pending、离线与 Offer Code 矩阵。
2. 从通过真机验收的 build 7 截取最终 App Store 图和 paywall 图，上传 App Store screenshot set 与三项 IAP Review Information screenshot，并独立读回数量和商品状态。
3. 全部真机与截图硬门通过后才把 iOS 1.0 从 build 5 切到 build 7、附加三项 IAP，做最终 readback 后提交审核。

## 死路

- 重发已接受的邀请会被 Apple 以 `STATE_ERROR.TESTER_INVITE.ALREADY_ACCEPTED` 拒绝；移出并立即加回同一内部组虽成功读回，但 tester 状态仍为 `INSTALLED`，TestFlight 本机列表仍未恢复。
- iPhone 上残留的旧 TestFlight invitation 页面已经撤销或失效，不能代替新的邀请深链。
- 新收到的 Apple 官方 build 7 邮件及其 app 深链本身有效，但目标账号打开后稳定返回 `此 App 不可用于你的 Apple 账户`；退出并重新登录同一 `媒体与购买项目` 账号以及强制重启 TestFlight 均不能修复。
- 完整 app-specific reset、同邮箱 tester 重建、两封全新认证邮件和新兑换路径也不能修复；Apple 最终明确指出邀请属于另一个原始 Apple 账户。继续重发同一邮箱邀请或重启 TestFlight 不会改变底层账户映射。
- 首次 `eas submit` 带 `--json` 时 CLI 21.7.0 以 `Nonexistent flag: --json` 在本地退出 1，未创建外部提交；去掉该 flag 后才成功调度 submission。
- EAS `submit:status` 起初因本机时间比 Apple `Date` 头快约 29 秒而返回 401；本轮只对该进程注入 -60 秒 `Date` shim 后读回成功，未改系统时钟。
- `@expo/apple-utils` 的旧 `dataUsagePublishState` 和 `availableTerritories` 关系已被 Apple 移除；availability 已改用 Apple 官方 `appAvailabilityV2` + v2 territory endpoint，App Privacy publish state 已改由登录 UI 实时复核并确认已发布。
