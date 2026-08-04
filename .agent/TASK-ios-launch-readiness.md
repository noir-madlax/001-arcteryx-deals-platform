# TASK: iOS 上线准备（更新：2026-08-04）

## Why（一句话）
把当前可运行的 GearDrop / 值de iPhone App 收敛为可提交构建，并把代码内问题与必须在 Apple / App Store Connect 完成的外部步骤明确分开。

## 当前状态：含第一版 GearDrop logo 的 build 4 已完成 EAS production 签名构建、Apple 官方校验与直传、处理为 `VALID`、加入 3 人内部 TestFlight 组，并替换 build 3 绑定到 iOS 1.0；Apple 协议、银行、税务、商店元数据、隐私和非中国大陆 availability 已完成；build 4 真机 StoreKit 交易、最终截图和提审仍待完成

## 已确认事实
- 2026-08-04 EAS production build `33fcb413-26c7-4282-9903-1021eeb40909` 读回 `FINISHED`：App `1.0.0`、build `4`、源码提交 `2e73e3b5553dca15c9658393d9ec866dbe1b6aa6`。30,078,471-byte 签名 IPA SHA-256 为 `ebbfcd65a1fedcf0c444b102d0639b526dfb2dc5f68c29921c2fa8175d9df8d5`，codesign、Info.plist、AppIcon、Splash 与运行时 logo/mark 均通过校验。（来源：本轮 EAS JSON、IPA、assetutil、codesign 与 shasum 原始输出）
- 2026-08-04 EAS Submit `6bb5c579-120f-46a1-a2de-6031479ea7ff` 长时间停在 `Queued / Free Tier Queue` 且无日志；同一 IPA 经 Apple 官方校验返回 `VERIFY SUCCEEDED with no errors` 后取消队列，刷新独立读回 `Canceled`。（来源：本轮 Expo 实际 DOM 与 altool 原始输出）
- 2026-08-04 Apple delivery / build resource `a9601f62-78a4-4e52-9336-8934a0c57e85` 返回 `UPLOAD SUCCEEDED with no errors`，最终读回 `VALID` / `APP_STORE_ELIGIBLE` / `usesNonExemptEncryption=false` / 最低 iOS 16.4。官方 API 把 build 4 加入 `GearDrop Internal` 及绑定 iOS 1.0 均返回 HTTP 204；关系 GET 与全新进程独立读回内部组 build 2/3/4、3 testers、iOS 1.0 唯一 build 4、`IN_BETA_TESTING` / `READY_FOR_BETA_SUBMISSION`。（来源：本轮 Apple Content Delivery 与 App Store Connect API 原始输出）
- 2026-08-04 EAS production build `2e452513-21a1-4203-8b50-abf877ed3e41` 读回 `FINISHED`：App `1.0.0`、build `3`、源码提交 `6d28b0b`，签名 IPA 28,879,988 bytes。EAS 自动递增后的 `app.json` build number 3 已另行提交并推送为 `06a786b`。（来源：本轮 EAS build JSON、IPA Info.plist 与 Git 原始输出）
- 2026-08-04 EAS Submit `600b9758-ef08-41b6-848d-758d7ad14638` 进入 Free Tier Queue；上一次同类任务从 17:17 到 18:49 用时约 92 分钟。本轮先用 Apple Content Delivery tool 对同一 SHA-256 `2cc287c653dbd9538a69a689c514781c4cddd84d594e9e4f7f869ddfc99cc3a9` IPA 校验，得到 `VERIFY SUCCEEDED with no errors`，随后取消尚未启动的 EAS 队列并直传，得到 `UPLOAD SUCCEEDED with no errors`。（来源：本轮 EAS submission DOM/CLI、altool 原始输出）
- 2026-08-04 Apple delivery `a458f9ee-7a50-4e32-8a36-fb9760df3413` 最终读回 `VALID` / `APP_STORE_ELIGIBLE` / `usesNonExemptEncryption=false`，最低 iOS 16.4。官方 API 以同一 build ID 读回 `processingState=VALID`，并将其 POST 加入 `GearDrop Internal`（HTTP 204）及 PATCH 绑定 iOS 1.0（HTTP 204）；独立关系 GET 分别返回 build 2 + build 3，以及 iOS 1.0 当前唯一 build 3。（来源：本轮 Apple Content Delivery 与 App Store Connect API 原始输出）
- 2026-08-04 build 3 beta detail 独立读回 `internalBuildState=IN_BETA_TESTING`、`externalBuildState=READY_FOR_BETA_SUBMISSION`。内部组为 3 testers；浏览器在 build 3 加入前读回 Jerry 和 `5331627@qq.com` 已安装 build 2，Account Holder 仍为 Invited。（来源：本轮 App Store Connect API 与实际 TestFlight DOM）
- 2026-08-04 build 2 源提交 `bfc9103` 生成于 2026-08-03，祖先检查明确不含图片数据门提交 `abd642c` 或首次加载提交 `cbf29c`。旧 5 张 1206×2622 模拟器截图中的首页仍有缺图占位，且 README 明确要求从通过交易验收的签名候选重截；因此本轮未上传旧截图、未继续提审。（来源：Git ancestry、截图目视检查、`app/store-assets/iphone-6.3/README.md` 与 ASC Media Manager 实际 DOM）
- 2026-08-04 从 App Store 提交分支 `45841fb` 创建干净独立分支 `codex/ios-appstore-build3-20260804`。只移植启动预览、24 小时缓存、稳定全量分页和首轮信号窗口优化，保留原分支的 IAP、地区、多语言和发布配置；Expo Doctor 要求的 5 个 SDK 57 包仅升级兼容补丁版本。（来源：Git 工作树、diff 与 Expo Doctor 原始输出）
- 2026-08-04 build 3 候选完整 `npm run verify` exit 0：39/39 tests、config、release assets、typecheck、Expo Doctor 20/20、实时汇率、live products `5,803`、price history `84,040`、美国区启动预览 `200` 且全部通过图片断言、iOS export 1,494 modules / 5.4 MB，最终原文 `verify_local_ok`。（来源：本轮完整命令原始输出）
- 2026-08-04 `npm audit --omit=dev --audit-level=high` exit 0；仍有 10 moderate，根链为 Expo build tooling 的 `xcode -> uuid <11.1.1`，npm 的 forced fix 会破坏性降级到 Expo 46.0.21，未执行。（来源：本轮 npm audit 原始输出）
- 2026-08-04 App Information 的第三方内容权利已按用户确认保存，页面独立读回 `Saved` 与拥有必要权利；App Privacy 仍为 Published。Pricing and Availability 独立读回中国大陆为唯一 Not Available，Apple Silicon Mac 与 Vision Pro availability 已取消并保存，首版保持 iPhone-only。（来源：本轮 ASC 保存后实际 DOM）
- 2026-08-03 App Store Connect API access 已由 Account Holder 申请并即时获批；团队 API key `GearDrop EAS Build` 已创建为 Active / Admin，一次性 `.p8` 已下载且未读取或输出正文。该 key 的官方 App Store Connect API JWT 实测可读取现有 bundle ID `dev.100app.geardrop`。（来源：本轮 ASC 实际 DOM、文件 `stat` 与官方 API 200 响应）
- 2026-08-03 EAS production iOS Build `67577ec9-d05c-4085-86d2-f201f7dc707c` 已读回 `FINISHED`：App `1.0.0`、build `2`；Fastlane 原文 `Successfully exported and signed the ipa file`，产物 `GearDrop.ipa` 27.5 MB，全部上传阶段 result=success。（来源：本轮 EAS build JSON 与云端构建日志）
- 2026-08-04 Apple 官方 API 已独立读回 build 2：App `1.0.0`、`processingState=VALID`、未过期、最低 iOS 16.4；TestFlight beta detail 为 `READY_FOR_BETA_TESTING` / `READY_FOR_BETA_SUBMISSION`。App Store Connect UI 同时显示 `1.0.0 (2)`、`Ready to Submit` 和 90 天有效期。（来源：本轮 App Store Connect API 200 响应与实际 DOM）
- 2026-08-04 iOS 1.0 原先未绑定 build；通过 Apple 官方 App Store Connect API 把 build 2 绑定到版本，PATCH 返回 204，随后独立 relationship GET 返回同一 build resource ID `36ddf4a5-84c4-4a11-b969-330dd98e1b8f`。版本仍为 `PREPARE_FOR_SUBMISSION`，尚无 App Review submission。（来源：本轮 Apple 官方 API 写响应与独立读回）
- 2026-08-04 当前提交缺口已从 Apple 官方 API 与 TestFlight UI 读回：App Store screenshots 为 0；monthly、annual、lifetime 三项均为 `MISSING_METADATA`，且缺审核截图。（来源：本轮 App Store Connect API 200 响应与实际 DOM）
- 2026-08-04 内部 TestFlight 组 `GearDrop Internal` 已创建，关闭未来构建自动分发，build 2 已加入；测试说明已保存并读回。Account Holder 与 `i.jerry1985@gmail.com` 已加入，组详情独立读回为 `2 Testers` / `1 Build`，两项状态均为 `Invited`。Jerry 邮箱的 Apple 团队实名读回为 `JIANJUN HUANG`，角色 `DEVELOPER`、`allAppsVisible=true`。（来源：本轮 TestFlight 实际 DOM、Apple 官方 API 200 与保存后独立读回）
- 2026-08-04 `jason.wang0016@gmail.com` 的 App Store Connect 团队邀请已创建为 YING WANG / `DEVELOPER`；Apple 官方 API 返回一项 pending `userInvitation`，并独立读回唯一 visible app 为 `GearDrop: Outdoor Deals` / `dev.100app.geardrop`。该用户接受团队邀请前尚不能加入内部 TestFlight 组。（来源：本轮 Users and Access 实际 DOM与 Apple 官方 API 两次 200 响应）
- 2026-08-03 从发布提交 `c7277d7` 新建 `codex/ios-appstore-submit-20260803`，合并最新 `origin/main` `5129eed`；冲突仅在 `privacy.html` 的更新时间和 `tests/test_web_memory_guards.py` 的迁移文件名，均保留主线最新值。合并后网站定向单测 37/37 通过，提交为 `7d5a9db`。（来源：本轮 Git、冲突 diff 与 unittest 原始输出）
- 2026-08-03 完整 `npm run verify` exit 0：37/37 tests、config、release assets、typecheck、Expo Doctor 20/20、实时汇率、live products `5,803`、price history `83,982`、iOS export 1,492 modules / 5.4 MB 均通过，最终原文 `verify_local_ok`。（来源：本轮命令原始输出）
- 2026-08-03 EAS 只读复核：登录 `noir-madlax`（Owner），项目 `@noir-madlax/geardrop` / `ead43b0e-5dbf-44a2-838e-f65db29abb30`；iOS build list 为 `[]`；production/preview 均存在遮罩后的 Sensitive RevenueCat iOS key。（来源：本轮 EAS CLI 20.5.1 原始输出）
- 2026-08-03 `npm audit --omit=dev` 仍为 10 moderate / 0 high / 0 critical，根链为 Expo build tooling 的 `xcode -> uuid <11.1.1`；npm 建议的自动修复会把 Expo 降为 46.0.21，未执行破坏性 `--force`。（来源：本轮 npm audit JSON）
- 2026-08-03 App Store Connect 实时完成并读回：Free/Paid Apps Agreement、银行与 W-8BEN 均为 Active；版本文案、分类、年龄分级、内容权利、隐私问卷与隐私 URL 已保存，隐私状态为 Published；App Availability 为 174 个国家或地区，中国大陆为 Not Available，港澳台为 Available on App Release；审核联系人已保存且自动发布已选。三项 IAP 均为 Prepare for Submission，但仍缺审核截图；版本页仍无构建、无最终截图，尚未提交审核。（来源：本轮 ASC 实际 DOM）
- 2026-08-03 `https://001.100app.dev/support.html` 已从公开网络返回 HTTP 200，并已作为 Support URL 保存到版本元数据。（来源：本轮 curl 与 ASC 实际 DOM）
- 2026-08-02 已从最新 `origin/main` 创建 `codex/ios-appstore-launch-20260802`，把 2026-07-31 保存的五个 iOS/上线安全提交迁入；冲突仅在 `app/lib/catalog.ts` 与 `tests/test_web_memory_guards.py`，合并保留了最新 FI/IE catalog 覆盖、iOS 默认地区逻辑和 support/RPC 回归。（来源：本轮 `git cherry-pick`、冲突 diff 与提交日志）
- 2026-08-02 完整 `npm run verify` exit 0：37/37 tests、config、release assets、typecheck、Expo Doctor 20/20、汇率、live products `5,812`、price history `83,934`、iOS export 1,492 modules / 5.4 MB 均通过，最终原文 `verify_local_ok`；历史 `4,948 < 5,000` 数据门阻塞已由本轮实时结果关闭。（来源：本轮命令原始输出）
- 2026-08-02 EAS 只读复核：登录 `noir-madlax`，项目仍为 `@noir-madlax/geardrop` / `ead43b0e-5dbf-44a2-838e-f65db29abb30`；iOS build list 仍为 `[]`，production/preview 均显示遮罩后的 Sensitive RevenueCat public key。本机 `security find-identity` 仍只返回一张 Apple Development identity。（来源：本轮 EAS CLI 20.5.1 与 security 原始输出）
- 2026-08-02 `npm audit --omit=dev` exit 1，当前为 10 moderate，仍来自 `@expo/config-plugins -> xcode -> uuid <11.1.1`；npm 的唯一自动修复路径是 `--force` 并把 Expo 换成 46.0.21，属于破坏性降级，未执行。（来源：本轮 npm audit 原始输出）
- 2026-08-02 RevenueCat 实时复核：`default` offering 为 Active 且含 3 packages，三项真实 App Store 商品分别绑定 `$rc_monthly` / `$rc_annual` / `$rc_lifetime`；`Pro` entitlement 为 Active 且含 6 products（3 个 App Store + 3 个 Test Store）；GearDrop App Store app bundle 仍为 `dev.100app.geardrop`，IAP `.p8` 显示 `Valid credentials`，SDK compatibility 显示 `react-native-purchases 10.4.2`。Overview 仍无 sandbox transaction。（来源：本轮 RevenueCat 实际 DOM）
- 2026-08-02 10:46 EDT 用户完成 Chrome 登录后只读复核 App Store Connect：Free Apps Agreement `Active`，Paid Apps Agreement 为 `Pending User Info`，银行为 `Processing`，U.S. Form W-8BEN 为 `Missing Tax Info`。（来源：本轮 ASC Business 实际 DOM；个人与银行明细不写入档案）
- 2026-08-02 11:07 EDT 账号持有人亲自完成两项税务声明并点击 Submit；提交后的独立页面读回显示 W-8BEN `Active`、Paid Apps Agreement 已转为 `Processing`、银行仍为 `Processing`。页面提示银行更新预计 24 小时内反映。本档案不记录出生日期、税号或其他表单正文。（来源：本轮 ASC Business 提交后实际 DOM）
- 2026-08-02 iOS 1.0 仍为 `Prepare for Submission`，TestFlight 显示 `No Builds`，App Review 列表为空。版本页有 0 张截图，Description、Keywords、Support URL、Copyright、审核登录/联系人/Notes 均为空；App Information 还缺 Subtitle、Category、Content Rights、Age Ratings；App Privacy URL 为空且 questionnaire 未开始；App 本体价格和 availability 未设置。（来源：本轮 ASC 版本、App Information、App Privacy、Pricing、TestFlight、App Review 实际 DOM）
- 2026-08-02 ASC 三项真实商品仍分别为 monthly / annual / lifetime 精确 identifier，175 地区可售、价格和 English (U.S.) localization 已存在，但三项状态均为 `Prepare for Submission` 且 Review Information screenshot 均为空。首批 subscription/IAP 必须与新 App 版本一同送审。（来源：本轮 ASC subscription group 与三个商品详情页实际 DOM）
- 2026-08-02 ASC Media Manager 明确接受 iPhone 6.3-inch 的 1206x2622 截图；分支已有 5 张该尺寸本地截图，但 ASC 仍为 0 张，且档案要求在签名 sandbox/TestFlight candidate 通过后重截最终图。本轮未上传素材。（来源：本轮 ASC Media Manager DOM、`app/store-assets/iphone-6.3/README.md` 与 `sips`）
- 2026-08-02 线上 `https://001.100app.dev/` 与 `/privacy.html` 返回 HTTP 200，但 `/support.html` 返回 404；隐私页 Contact 只回链首页，首页没有实际客服渠道。独立分支内已有 support 页面与 RPC migration，但 support 尚未合入/部署，migration 也没有本轮生产读回或 smoke 证据。（来源：本轮 curl；分支 `support.html` 与 `supabase/migrations/20260719131646_geardrop_submission_security.sql`）
- Expo/EAS 已登录账号 `noir-madlax`；`eas project:info` 返回 `@noir-madlax/geardrop`、project ID `ead43b0e-5dbf-44a2-838e-f65db29abb30`。（来源：2026-07-12 本机只读命令）
- `eas build:list --platform ios --limit 5 --json --non-interactive` 返回 `[]`，当前没有 EAS iOS build 记录。（来源：2026-07-12 本机只读命令）
- 本机有一张有效 Apple Development identity：`Apple Development: Jenova Huang (BM8N8W2A26)`；没有本机 Apple Distribution identity。（来源：`security find-identity -v -p codesigning`）
- App bundle ID 是 `dev.100app.geardrop`，版本 `1.0.0`、build `1`；中文设备名通过 `zh-Hans` 本地化为“值de”。（来源：`app/app.json`）
- 2026-07-12 用户选择方案 B：首版接入 Apple IAP 后再上线。（来源：本任务对话中的用户选择）
- 当前 Pro 状态仅由 RevenueCat `Pro` active entitlement 决定；付费墙调用 `purchasePackage` / `restorePurchases`，价格来自 StoreKit offering，原本 AsyncStorage 本地解锁和 Me 页手动 Pro 开关已删除。（来源：`app/contexts/ProContext.tsx`、`app/lib/iap.ts`、`app/app/paywall.tsx`、`app/app/(tabs)/me.tsx`）
- IAP 固定契约为 entitlement `Pro`，商品 `dev.100app.geardrop.pro.monthly`、`.annual`、`.lifetime`。（来源：`app/lib/iap.ts` 与 RevenueCat 实际 identifier）
- 干净 Expo prebuild + `pod install` 已自动链接 `RNPurchases 10.4.2`、`PurchasesHybridCommon 18.19.0`、`RevenueCat 5.80.2`；iOS Simulator Release `xcodebuild` exit 0。（来源：2026-07-12 `/private/tmp/geardrop-signed-source` 原生命令输出）
- Release app 已安装并启动；故意注入无效 public key 后日志返回 `Invalid API Key`，付费墙展示本地化不可用状态，未崩溃且未授予 Pro；Me 页截图确认无本地 Pro toggle。（来源：2026-07-12 `simctl`、系统日志、`/private/tmp/geardrop-iap-paywall-unavailable.png`、`/private/tmp/geardrop-iap-me-no-toggle.png`）
- post-IAP 完整 `npm run verify` 实跑：36/36 tests、config、release assets、typecheck、Doctor 20/20、汇率通过；live 返回 products `4,970`、history `74,070` 后因 `expected at least 5000 products, got 4970` exit 1。（来源：2026-07-12 11:30 EDT 本机完整命令输出）
- 单独 iOS export exit 0：`iOS Bundled ... (1488 modules)`，HBC 5.3 MB；随后 `git diff --check` 单独重跑 exit 0。（来源：2026-07-12 本机命令输出）
- `npm audit --omit=dev` exit 1，报告 35 moderate，根链为 Expo build tooling `@expo/config-plugins -> xcode -> uuid <11.1.1`，原文 `No fix available`；未执行会破坏 Expo 依赖的 forced fix。（来源：2026-07-12 npm audit 原始输出）
- 2026-07-12 12:51 EDT 用户已授权开始 ASC / RevenueCat 外部配置；内置浏览器和 Chrome 均未发现可复用会话。ASC 返回 `/login?...authResult=FAILED`，RevenueCat 定位到 `/login`；两个 Chrome 页面已作为 handoff 保留，等待用户亲自完成密码和 2FA 登录。（来源：本轮浏览器实际页面 URL 与 DOM）
- 2026-07-12 13:03 EDT 两个后台均已登录。ASC Apps 列表只有 `Nuzzo` macOS app；GearDrop 尚无 app record，但 Bundle ID 下拉已存在 `XC dev 100app geardrop - dev.100app.geardrop`。新 App 表单已备妥：iOS-only、`GearDrop`、English (U.S.)、SKU `geardrop-ios`、Full Access，Create 尚未点击。（来源：ASC 实际 DOM）
- RevenueCat 账号处于首次项目问卷；表单已备妥为 `GearDrop` / Shopping / adding IAP to an existing app / Developer / Native Apple，Submit answers 尚未点击。（来源：RevenueCat 实际 DOM）
- 用户 action-time 确认后，RevenueCat 项目已创建：名称 `GearDrop`、project ID `f1ab7733`。（来源：创建后 URL `/projects/f1ab7733/get-started/create-offering` 与页面标题）
- ASC 首次用 `GearDrop` 创建失败，Apple 原文 `The app name you entered is already being used`，未生成记录；改为 `GearDrop: Outdoor Deals` 后创建成功，Apple ID `6790165332`、iOS 1.0 Prepare for Submission。（来源：ASC 创建校验错误与成功后 URL `/apps/6790165332/distribution`）
- Business 页面显示 Free Apps Agreement Active，但 Paid Apps Agreement 为 `New`，操作为 `View and Agree to Terms`；账号持有人必须亲自签署，Agent 不代签法律/税务条款。（来源：ASC Business 实际 DOM）
- 用户确认 US 价格 `$3.99/月`、`$23.99/年`、`$49.99 lifetime`，首版无试用。ASC 订阅组 `GearDrop Pro` ID `22227971` 已存在并加入 English (U.S.) group localization。（来源：2026-07-12 用户确认与 ASC 实际 DOM）
- 月付已创建并配置：Product ID `dev.100app.geardrop.pro.monthly`、Apple ID `6790166470`、1 month、175 地区、base US `$3.99`、English (U.S.) localization；无 free trial。（来源：ASC 产品页与定价确认页）
- 年付已创建并配置：Product ID `dev.100app.geardrop.pro.annual`、Apple ID `6790170309`、1 year、仅 `1 Year Upfront` 启用 175 地区、base US `$23.99`、English (U.S.) localization；未启用 Monthly with a 12-Month Commitment，且无 free trial。（来源：ASC 产品页与定价确认页）
- lifetime 已创建并配置：Product ID `dev.100app.geardrop.pro.lifetime`、Apple ID `6790168227`、Non-Consumable、175 地区、base US `$49.99`、English (U.S.) localization。（来源：ASC 产品页与定价确认页）
- 三项产品均仍显示 `Missing Metadata`，当前可见未完成项包含 Review Information screenshot；该状态不记为 Ready to Submit。（来源：ASC 三个产品页）
- RevenueCat onboarding 已创建 entitlement 名称 `Pro`、标准 Monthly/Yearly/Lifetime offering 组合，项目中保留 Test Store 配置；实际 identifier 与真实 App Store 商品绑定仍待核实。（来源：RevenueCat project `f1ab7733` 实际页面）
- RevenueCat 显示注册邮箱 `not yet confirmed`。（来源：RevenueCat alert）
- 2026-07-12 用户明确确认生成并上传 IAP 密钥。ASC In-App Purchase key `GearDrop RevenueCat` 已生成并显示 Active (1)，Key ID `X5HJRYHJW5`、Issuer ID `bb6b9105-54d1-4b11-91d5-e1af3ec7e7cc`；一次性文件已下载到本机 `/Users/J/Downloads/SubscriptionKey_X5HJRYHJW5.p8`，`stat` 返回 257 bytes、修改时间 2026-07-12 13:37:48 EDT。未读取或输出私钥正文。（来源：ASC 实际 DOM 与本机 `stat`）
- IAP `.p8`、Key ID 与 Issuer ID 已上传 RevenueCat 项目 `f1ab7733` 并保存为真实 App Store app `GearDrop (App Store)`，REST API Identifier `appc81815554d`；保存后 toast 为 `App created successfully`，IAP key 区显示 `Valid credentials`，bundle ID 为 `dev.100app.geardrop`。（来源：2026-07-12 13:49 EDT RevenueCat 保存后实际 DOM）
- RevenueCat 已手动创建三项真实 App Store 商品：monthly `prod5f80504464`（Subscription）、annual `prod7c9b65078d`（Subscription）、lifetime `prod17120226cb`（Non-consumable）；产品 identifier 与 ASC 三项完全一致。（来源：2026-07-12 RevenueCat 产品详情 DOM）
- RevenueCat onboarding entitlement 的实际 identifier 是大小写敏感契约 `Pro`，REST API Identifier `entl3a40305cb6`；三项真实 App Store 商品已附加，同时保留三项 Test Store 商品。App 常量与单测已同步为 `Pro`。（来源：RevenueCat entitlement DOM、`app/lib/iap.ts`、`app/__tests__/iap.test.ts`）
- default offering `ofrng8a7868ca2b` 的 `$rc_monthly`、`$rc_annual`、`$rc_lifetime` 已分别绑定真实 monthly/annual/lifetime 商品；保存后详情页逐项显示 `GearDrop (App Store)` 与精确 product ID。（来源：RevenueCat offering 保存后 DOM）
- GearDrop App Store app 的 RevenueCat public iOS SDK key 已取得，并以 Sensitive 变量 `EXPO_PUBLIC_REVENUECAT_IOS_API_KEY` 写入 EAS `production` 与 `preview`；`eas env:list` 两个环境均显示该变量为 `*****`。（来源：2026-07-12 EAS CLI create/list 原始输出；public key 正文不写入任务档案）
- `app/eas.json` 的 production submit profile 已配置 `ascAppId=6790165332`，并新增 verify-config 断言；`npm run verify:config` 与 `eas config --platform ios --profile production --non-interactive` 均 exit 0，后者确认 production 会加载 Sensitive RevenueCat 变量。（来源：2026-07-12 14:20 EDT 本机命令输出；Expo 官方 EAS Submit 文档）
- 2026-07-12 14:24 EDT ASC live 复查：Paid Apps Agreement 仍为 `New`，协议弹窗显示未勾选条款且 `Agree` disabled；页面同时要求 `Complete Compliance Requirements` 处理 EU DSA trader 状态。RevenueCat 页面仍显示注册邮箱 `not yet confirmed`。（来源：ASC Business 与 RevenueCat 实际 DOM）
- 2026-07-12 15:59 EDT 用户报告三个账号动作“好了”；随后现有 RevenueCat 页面 DOM 仍显示 `Your email address is not yet confirmed`，重发按钮显示 `Failed to re-send, try again`。刷新/新开页面连续超时，因此邮箱确认状态未验收，不能按用户报告或旧页面单独写成已完成/未完成。（来源：RevenueCat API keys 页面实际 DOM与后续刷新超时）
- 2026-07-12 16:01 EDT 同一真实 key Simulator offering 探针重跑：Storefront 为 USA，StoreKit 执行 `Products_SK2` 后 RevenueCat 仍返回 `None of the products registered in the RevenueCat dashboard could be fetched from App Store Connect`；未进入购买/恢复。（来源：`/private/tmp/geardrop-offering-post-agreement.log`）
- Apple Business 协议页仍停留在 agreement URL，但 Chrome 对该页的 DOM/screenshot 读取连续超时；本轮未取得 Paid Apps Agreement 或 DSA 的新页面状态，因此只记录“用户报告已操作”，不记录“已生效”。（来源：本轮 Chrome 实际 URL 与连续读取超时）
- 2026-07-13 11:36 EDT RevenueCat GearDrop Overview 页面刷新后已不含 `Your email address is not yet confirmed` 或重发失败提示，邮箱确认验收通过。（来源：RevenueCat Overview 页面实际 DOM）
- 2026-07-13 11:37 EDT Apple Business 页面可读：Paid Apps Agreement 有效期已生成，但状态为 `Pending User Info`；页面提示银行更新处理中、预计 24 小时内反映，并显示仍有一份税务信息待补。`Complete Compliance Requirements` / DSA 提示已不存在，因此 DSA 验收通过，但 Paid Apps Agreement 尚未 Active。（来源：Apple Business 页面实际 DOM；个人、地址与银行明细不写入档案）
- 2026-07-13 11:38 EDT 同一真实 key Simulator offering 探针再次重跑：USA Storefront、StoreKit `Products_SK2` 后仍返回 `None of the products registered in the RevenueCat dashboard could be fetched from App Store Connect`，未进入购买/恢复。（来源：`/private/tmp/geardrop-offering-2026-07-13.log`）
- ASC iOS 1.0 页面当前 iPhone screenshots `0 of 10`，Description、Keywords、Support URL、Copyright、App Review 联系信息等仍为空；Build 也尚未上传。三项 IAP/订阅先前均为 `Missing Metadata`，Apple 官方将该状态定义为尚缺 screenshot 或 metadata。（来源：ASC 版本页实际 DOM与 Apple IAP status 文档）
- 真实 RevenueCat public key 通过进程环境注入 `/private/tmp/geardrop-signed-source`，未写入仓库；干净 prebuild、pod install、arm64 iPhone 17 Simulator Release `xcodebuild` 日志为 `BUILD SUCCEEDED`，产物 bundle ID `dev.100app.geardrop`，安装/启动成功。（来源：2026-07-12 本机原生命令与 `/private/tmp/geardrop-live-build-arm64.log`）
- 真实 key 运行时付费墙仍显示“Apple 购买方案暂时不可用”；日志原文为 `None of the products registered in the RevenueCat dashboard could be fetched from App Store Connect`，不是 `Invalid API Key`。RevenueCat 官方说明 SDK 已从 RevenueCat API 取得 product identifiers 后仍须由设备商店取回实际商品；当前 StoreKit 取回失败，未运行购买/恢复。（来源：Simulator 截图 `/private/tmp/geardrop-live-iap-paywall.png`、系统日志、RevenueCat empty offerings 官方文档）
- 2026-07-12 14:10 EDT 完整 `npm run verify` 重跑：36/36 tests、config、release assets、typecheck、Doctor 20/20、汇率通过；live 返回 products `4,959`、history `74,070` 后因 `expected at least 5000 products, got 4959` exit 1。脚本未进入 iOS export；随后单独 `npx expo export --platform ios --output-dir dist-check` exit 0，1488 modules、HBC 5.4 MB，生成目录已清理。（来源：本轮命令原始输出）
- 2026-07-12 16:04 EDT 完整 `npm run verify` 再次重跑：36/36 tests、config、release assets、typecheck、Doctor 20/20、汇率通过；live 返回 products `4,948`、history `74,070` 后因 `expected at least 5000 products, got 4948` exit 1，未进入最终 iOS export。（来源：本轮命令原始输出）
- Apple Guideline 3.1.1 要求解锁 App 内数字功能必须使用 IAP；因此当前本地 Pro stub 不能作为收费版本提交。（来源：Apple App Review Guidelines，2026-07-12 查阅）
- `https://001.100app.dev/privacy.html` 与站点根 URL 当前均返回 HTTP 200；但根页面没有 support/contact/email 文案，不能视为已完成客服入口。（来源：2026-07-12 `curl` 与页面文本检查）
- 主图标是 1024×1024 PNG，但当前含 alpha 通道，实际 alpha 范围 70–255；Apple 上传会校验大图标不得透明或含 alpha。（来源：`sips`、Sharp 只读像素统计、Apple 官方错误说明）
- 配置当前声明支持 iPad，但现有任务档案和运行时证据只覆盖 iPhone；Apple 要求能在 iPad 运行的 App 提供 iPad 截图。（来源：`app/app.json`、既有任务档案、Apple screenshot specifications）
- 最近完整 `npm run verify` 的代码、配置、typecheck、Doctor、汇率阶段通过，但 live 商品实际 `4,959 < 5,000`，完整门仍退出 1。（来源：`.agent/TASK-ios-localization-currency.md`）
- 2026-07-12 本轮完整门重跑时 live 商品回升到 `4,970`，但仍因 `expected at least 5000 products, got 4970` 退出 1；33/33 tests、config、release assets、typecheck、Doctor 20/20、汇率均已在失败前通过。（来源：本轮 `npm run verify` 原始输出）
- EAS production profile 解析为 `credentialsSource=remote`、`distribution=store`、`autoIncrement=true`；production/preview 均含 Sensitive RevenueCat public key，production submit profile 已含 `ascAppId=6790165332`。（来源：`eas config`、`eas env:list` 与 `app/eas.json`）
- 价格提醒由客户端公开 anon key 直接 INSERT；仓库迁移定义 `CREATE POLICY anon_insert ... WITH CHECK (true)`，未见客户端前置的服务端限流或验证挑战。上线前需评估邮件滥用防护。（来源：`app/lib/priceAlerts.ts`、`dealers/supabase_migration_price_alerts.sql`）

## 假设
- 首个 App Store 版本只支持 iPhone；若要支持 iPad，需要恢复 `supportsTablet` 并新增 iPad 布局和截图验收。
- RevenueCat entitlement/offering/public SDK key 已配置，但真实 StoreKit 价格、购买、恢复和 entitlement 激活仍未验证。
- 公开 support email 不能使用未验证或未明确同意公开的私人邮箱。
- Paid Apps Agreement、银行、税务和 IAP 状态已于 2026-08-02 实时复核；后续任何变化仍需从 App Store Connect 重新读回，不以操作报告代替结果。

## 验收标准
1. `app.json` 明确首版 iPhone-only，配置校验覆盖该约束。
2. 1024×1024 App Store icon 不含 alpha/tRNS；自动脚本可阻止回归。
3. `npm run verify:release-assets`、`npm run verify:config`、`npm run typecheck` 和 `git diff --check` 通过。
4. 完整 `npm run verify` 实跑并如实记录；live 数据不足时不得标记通过。
5. 发布档案更新为当前 EAS/Apple、隐私、截图、IAP 和支持渠道状态。
6. 外部清单包含收费模式、ASC app record/Apple ID、Distribution 凭证、公开客服邮箱、内容权利、隐私答案、截图、TestFlight 和审核提交。
7. IAP SDK 必须通过单元测试、TypeScript、配置校验、干净 prebuild/CocoaPods 和 iOS Release 原生编译；真实交易必须另以 sandbox/TestFlight 证据验收。

## 已完成且已验证
- App Store Connect API access/key、Apple Distribution certificate、App Store provisioning profile 与首个 production iOS 签名构建均已完成；EAS build 记录读回 `FINISHED`，build 2 的 27.5 MB `.ipa` 已生成并上传为构建产物。
- 2026-08-02 上线代码已恢复到最新远端基线的独立分支；完整 App 门、网站 guard 测试与 `git diff --check` 均通过，RevenueCat/EAS 只读状态已刷新。
- 2026-07-12 已完成 EAS 登录、项目绑定、EAS iOS build 列表、Apple 本机签名身份、线上 URL、图标尺寸/alpha 和 Apple 当前规则的只读审计；结果见“已确认事实”。
- `app.json` 已收敛为 `supportsTablet=false`；`expo config --type public` 与 EAS production config 均解析为 iPhone-only。
- 主图标已移除 alpha，视觉构图未改；`sips` 返回 `1024×1024 / hasAlpha: no`，`npm run verify:release-assets` 返回 `release_assets_ok icon=1024x1024 colorType=2 alpha=false`。
- 新增 `app/scripts/verify-release-assets.ts` 并接入完整 verify，防止 1024 尺寸或 alpha/tRNS 回归。
- `npm run typecheck`、`npm run verify:config` 均 exit 0。
- `npx expo export --platform ios --output-dir dist-release-check` exit 0：`iOS Bundled ... (1460 modules)`、HBC `3.9MB`；生成目录已清理。
- 完整 `npm run verify` 已实跑，除 live `4,970 < 5,000` 外的已执行阶段全部通过；未降低门槛。
- `app/RELEASE_READINESS.md` 与 `app/APP_STORE_METADATA.md` 已更新为当前状态，明确禁止把本地 Pro stub 作为收费版本提交。
- `react-native-purchases@10.4.2` 已接入；新增 IAP 契约/单测，重做 ProContext 和付费墙购买/恢复路径，移除本地 Pro 解锁。`npm test` 36/36、`npm run typecheck`、`npm run verify:config`、Expo Doctor 20/20 均 exit 0。（来源：2026-07-12 本机命令输出）
- 干净 prebuild、CocoaPods 自动链接、iOS Simulator Release 原生构建、无效 key 运行时降级均已验证；失败日志明确为 RevenueCat `Invalid API Key`，不是 native module 缺失或 JS crash。
- Apple IAP key 已上传并通过 RevenueCat 凭证校验；真实 RevenueCat App Store app `appc81815554d` 已创建。（来源：RevenueCat `App created successfully` / `Valid credentials`）
- 三项真实商品、`Pro` entitlement、default offering 与 EAS production/preview public key 已配置；同步代码后 `npm test` 36/36、`npm run typecheck`、`npm run verify:config`、`git diff --check` 均 exit 0。（来源：2026-07-12 本轮 RevenueCat DOM 与本机命令输出）
- EAS submit 已固定目标 ASC app；真实 key 的 arm64 Simulator Release 原生构建、安装、启动与不可用态截图均已验证。该运行明确失败于 StoreKit 无法取回 ASC 商品，因此不算 sandbox 交易通过。（来源：2026-07-12 本机命令、日志与截图）
- post-config 完整门已实跑且如实失败于 live `4,959 < 5,000`；单独 iOS export 1488 modules / 5.4 MB HBC 通过。（来源：2026-07-12 14:10 EDT 本机命令输出）
- 新增 `app/IAP_SETUP.md`，记录 ASC、RevenueCat、EAS 环境和 10 项 sandbox 交易验收步骤；未创建账号侧资源，未产生 EAS build，未上传 TestFlight。
- post-IAP 完整门已实跑且如实失败于 live `4,970 < 5,000`；单独 iOS export 和 `git diff --check` 通过。依赖审计的 Expo build-tooling moderate advisory 已记录为未解决风险。

## 下一步
1. 从 TestFlight 安装或升级到 build 4，验证第一版 logo、首页无缺图占位和冷启动预览，并按 `app/IAP_SETUP.md` 完成真实 StoreKit offering、sandbox 购买、恢复和 entitlement 矩阵。
2. 从通过交易验收的 build 4 重截 App Store 最终图和三项 IAP review screenshot，上传后独立读回。
3. 把三项 IAP/订阅附加到 iOS 1.0，逐页复核版本、构建、出口合规与审核信息后一起提交审核。

## 死路
- 2026-08-03 Apple ID 密码登录在清理 Keychain并升级 EAS CLI 后仍连续返回 `Apple 302 detected`，Apple 官方状态无故障；改用 Account Holder 新建的 App Store Connect API key，不再要求用户重复输入密码。
- 本机 `HTTP_PROXY` / `HTTPS_PROXY` 令 `@expo/apple-utils` 对正确的 App Store Connect API URL收到 HTML 404；同时本机时钟比 Apple 响应快约 20 秒，令按本机时间签发的 JWT 收到 401。仅对本次 EAS 进程取消代理变量并将 `Date.now()` 偏移 -60 秒后，同一 `BundleId.findAsync` 精确返回现有 bundle ID；未修改系统代理或系统时间。
- 2026-08-02 直接用默认 npm cache 启动 EAS CLI 时，大量 tarball integrity retry 后 3 分钟无结果；中止后改用独立空 cache，`eas-cli/20.5.1` 正常安装并完成全部只读查询。该问题是本机 npm cache 路径，不是 EAS 登录失败。
- `eas credentials --platform ios --non-interactive`：EAS CLI 20.5.1 不支持 `--non-interactive`，原文 `Nonexistent flag: --non-interactive`；未进入交互菜单，也未改凭证。
- 首次临时 Release 构建把 `node_modules` symlink 回含空格的 workspace，ExpoModulesJSI 报 `fatal error: 'hermes/hermes.h' file not found`。改为 `/private/tmp/geardrop-signed-source` 实体依赖后同一 Release 配置 exit 0，确认是临时路径/symlink 问题而非 RevenueCat 兼容问题。
- 2026-07-12 ASC 内置浏览器与 Chrome 都返回 `authResult=FAILED`，RevenueCat 也无现成登录会话；不绕过登录，也不读取浏览器凭据，改为保留登录页等待用户亲自完成认证。
- ASC 公开名 `GearDrop` 已被其他开发者占用；同一表单改为 `GearDrop: Outdoor Deals` 后成功创建，后续英文 App Store 元数据以该名称为准，中文本地化仍可使用“值de”。
- RevenueCat 首次文件选择器 `setFiles` 返回 `Not allowed`；Chrome 插件文档要求开启 `Allow access to file URLs`。用户开启后扩展连接短暂失效，重新建立 Chrome 会话后同一上传流程成功，RevenueCat 最终显示 `Valid credentials`。（来源：2026-07-12 浏览器工具原始错误、Chrome 诊断与保存后 DOM）
- RevenueCat entitlement identifier 创建后不可编辑；尝试新增小写 `pro` 时提交无结果，现有大写 `Pro` 仍唯一存在。为避免删除已配置 entitlement，改为让 App 契约匹配实际 `Pro`，并增加小写 `pro` 不应解锁的单测。（来源：RevenueCat entitlement DOM 与本轮单测）
- `eas env:list production --non-interactive` / `preview --non-interactive` 返回 `Nonexistent flag: --non-interactive`；去掉该 flag 后两个只读查询均 exit 0。（来源：2026-07-12 EAS CLI 原始输出）
- 首次真实 key Simulator 构建使用双架构默认值，已完成 arm64 后继续编译无必要的 x86_64；主动中止并以 `ONLY_ACTIVE_ARCH=YES ARCHS=arm64` 复用缓存，最终日志 `BUILD SUCCEEDED`。构建包装脚本随后因 zsh 的 `status` 为只读变量退出 1，但不改变 xcodebuild 已成功的原始日志和完整 `.app` 产物。（来源：本机进程、build log、Info.plist 与安装结果）
