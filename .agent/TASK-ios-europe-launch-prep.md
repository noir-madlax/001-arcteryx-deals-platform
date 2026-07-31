# TASK: iOS 欧洲首发准备（更新：2026-07-19 12:55 EDT）

## Why（一句话）
在不填写或确认 W-8、也不提交 App Review 的边界内，把 GearDrop / 值de iPhone App 的代码、公开页面、元数据、IAP 审核资料与可验证构建准备到只剩 W-8 的状态。

## 当前状态：等待用户确认免费欧洲首发还是继续等待付费协议，并确认保存 ASC 准备项

## 已确认事实
- 当前仓库为 `/Users/J/Projects/Desktop-Projects/hermes projects/001-arcteryx-deals-platform`，分支 `main` 比 `origin/main` 落后 214 个提交，且已有大量用户未提交改动；必须保留这些改动并避免覆盖。（来源：2026-07-19 10:48 EDT `git status --short --branch`）
- 2026-07-19 本轮 `npm run verify` 已通过 36/36 tests、config、release assets 和 typecheck，但 Expo Doctor 为 19/20；13 个 Expo SDK 57 包低于当前要求的补丁版本，完整门 exit 1。（来源：本轮命令原始输出）
- 2026-07-19 `npm run verify:live-data` 通过：5,295 个可见商品；GB、DE、FR、NL、AT、BE、DK、IT、ES、SE、CH 各 385 个；抽检五个欧洲购买链接均 HTTP 200。（来源：本轮命令原始输出）
- EAS 当前登录 `noir-madlax`，项目为 `@noir-madlax/geardrop`；iOS build list 为 `[]`。（来源：2026-07-19 本轮 EAS CLI 只读命令）
- 用户明确纠正：当前账号侧只差 W-8；本任务把 W-8 作为唯一允许保留的阻塞项，但仍需对其他易变状态取得 live 证据。（来源：2026-07-19 用户指令）
- Apple 官方允许仅选择特定国家或地区发布；Expo SDK 57 官方要求使用与 SDK 匹配的包版本，SDK 57 对应 React Native 0.86、React 19.2.3、Node 22.13+。（来源：2026-07-19 Apple/Expo 官方文档读取）

## 假设
- “欧洲首发”先准备 DE、FR、AT、GB、CH；App Store Connect 实际 availability 在账号登录后按用户最终范围确认，不在未登录状态下猜测。
- 公开 support email 不能擅自使用 Apple/EAS 账号邮箱；优先实现不暴露私人邮箱、可实际工作的支持表单或现有已授权公开渠道。
- 用户的“把其他准备工作都做好”授权代码、静态站点、元数据草稿、截图素材和可逆的 TestFlight 准备；不授权代签税务/法律声明，不授权最终 App Review 提交。

## 验收标准
1. `npm run verify` 完整 exit 0，包括 Expo Doctor、实时汇率、实时数据与 iOS export。
2. `git diff --check` exit 0；新增/修改文件均属于本任务或明确保留的既有工作。
3. 公开 support URL 与 privacy URL 均 HTTP 200，support 页面有可实际提交且具备滥用保护的联系路径。
4. App Store 元数据、隐私答案、欧洲首发范围、审核说明与截图清单完整，且不包含未验证断言或私人信息。
5. 价格提醒不再依赖无约束的匿名直写；服务端入口具备可验证的限流/校验边界，客户端不暴露强凭证。
6. 签名构建链路和 EAS/ASC 目标配置通过；能上传 TestFlight 时取得 build 证据，否则明确记录唯一外部阻塞。
7. RevenueCat/StoreKit offering、商品元数据与 sandbox 购买/恢复能做的部分全部验证；受 W-8 直接阻塞的部分单独列出。
8. 不提交 App Review，不填写/确认 W-8，不发布未经用户授权的个人联系方式。

## 已完成且已验证
- 已建立本任务档案并固定边界与验收标准。
- 已用 Expo SDK 57 官方安装器把兼容补丁升级写入 `app/package.json` / `app/package-lock.json`，并将 Doctor 固定为可正常处理当前含空格路径的 `expo-doctor@1.20.0`；`1.20.1` 在本路径错误打印子进程失败却返回 0，未采用。（来源：2026-07-19 `npx expo install --fix`、两版 Doctor 对照）
- 2026-07-19 完整 `npm run verify` exit 0：36/36 tests、config、release assets、typecheck、Doctor 20/20、实时汇率、5,295 个实时商品、iOS 1489 modules / 5.4 MB HBC export 全部完成，末行 `verify_local_ok`。（来源：本轮命令原始输出）
- 已新增 `support.html`，并把网站首页、App Me 页和 App 内隐私页接到固定 Support URL；隐私政策和 App Store 元数据草稿已覆盖支持表单数据与滥用防护用途。（来源：本轮文件读取与修改）
- 已生成正式 Supabase migration `20260719131646_geardrop_submission_security.sql`：匿名/登录用户不再直写 `price_alerts`，由 `register_price_alert` 校验、限流、服务端派生商品字段和退订 token；`unsubscribe_alert` 收紧 ACL/search_path 并兼容旧 UUID token；新增私有支持请求队列与 `submit_support_request`。（来源：本轮 migration 文件）
- 迁移已在一次性 PostgreSQL 16 容器真实执行并通过行为验收：`anon_direct_price_alert_insert=false`、`anon_support_select=false`、active alert 去重为 1、support rows=1、限流按预期触发；容器退出后已自动删除。（来源：本轮命令原始输出）
- App 价格提醒、网站价格提醒和支持页均已切换到受控 RPC。App 定向验证通过：37/37 tests、`tsc --noEmit`、`verify:config`；网站防回归测试 6/6 通过。（来源：本轮命令原始输出）
- 2026-07-19 10:48 EDT 最终完整 `npm run verify` 再次 exit 0：37/37 tests、config、release assets、typecheck、Expo Doctor 20/20、实时汇率、5,294 个当前可见商品、13 个欧洲/北美区域数据、iOS 1482 modules / 5.3 MB HBC export，末行 `verify_local_ok`；网站定向测试同时 6/6 通过。（来源：本轮命令原始输出）
- 已从 `npx expo prebuild` 生成原生项目，并在无空格隔离路径完成 unsigned iPhone 16 Pro Release simulator build：`xcodebuild` exit 0，产物 bundle `dev.100app.geardrop`、version `1.0.0 (1)`、71 MB。第一次含空格路径失败和第二次复制缓存失败均已定位并在隔离构建面消除。（来源：本轮 Xcode 原始输出与产物读取）
- Release 产物已实际安装并启动于 iOS 18.4 iPhone 16 Pro 模拟器。运行时验证了 5,295 条当时实时商品、德国区 385 条欧元商品、价格详情/判定、4 项 Watchlist 与隐私页；应用 error/fault 日志只有 UIKit focus 缓存诊断，无 crash。（来源：本轮 `simctl`、截图与 `log show` 输出；商品总数随后实时刷新为 5,294）
- 已生成并逐张目视检查 5 张 1206×2622 iPhone 6.3-inch 截图：Deals、Germany、Product detail、Watchlist、Privacy；未伪造或截取无真实 StoreKit 商品的付费墙图。（来源：`app/store-assets/iphone-6.3/` 与本轮 `sips`/图像检查）
- 已从最新 `origin/main` 提交 `72ae3ec` 建立隔离 Vercel worktree，只加入 support/privacy/footer/受控提醒 RPC；本地 Vercel build exit 0，preview deployment `dpl_GLkEXuQNdak7uMgpZtr1wD9HBiiZ` 为 `READY`，预览 Support DOM 与四个静态页面断言全部通过。生产尚未发布。（来源：Vercel CLI、浏览器 DOM、本轮预览探针）
- 同一隔离 worktree 的 production-target Vercel prebuilt output 已生成并通过逐文件检查：Support/Privacy 与源文件完全一致，Product detail 仅含受控 RPC 且无旧匿名直写 endpoint，首页 footer 含 Support/Privacy；执行生产 migration 后可直接部署该产物。（来源：本轮 `vercel build --prod` 与 `.vercel/output/static` 断言）
- 初次 preview 被 Vercel 拦截的原因是数据提交作者邮箱 `bot@arcteryx-deals.local` 不属于 Git 账号；仅在隔离 worktree 增加有效作者的本地空提交后重新部署成功，未改全局 Git 配置、未推送主分支。（来源：Vercel Deployment Details live DOM 与第二次 deploy 输出）
- EAS live credentials 菜单显示 `No credentials set up yet!`，且 EAS 账号内没有 App Store Connect API Key；iOS build list 仍为 `[]`。本机只有 Apple Development identity。（来源：2026-07-19 本轮 EAS CLI 与 `security find-identity`）
- 本地自动签名 device archive 已真实尝试但 exit 65：Xcode Keychain 账号缺 `Xcode-Username`、Xcode Accounts 无可用账号，且没有 `dev.100app.geardrop` provisioning profile。因此签名 archive 需要用户重新登录 Apple/Xcode 或参与 EAS Apple 登录；这不是 W-8 导致的代码阻塞。（来源：本轮 `xcodebuild archive -allowProvisioningUpdates` 原始错误）
- 用户明确授权后，生产 Supabase migration 已作为 `20260719161928 geardrop_submission_security` 成功应用。生产复核显示 `price_alerts` / `support_requests` RLS 均启用，anon 对两张表 SELECT/INSERT 均为 false，公开角色不能执行 3 个函数，anon/authenticated 只能调用显式授予的受控 RPC，3 个 SECURITY DEFINER 函数均固定空 `search_path`，活动提醒重复组为 0。（来源：2026-07-19 Supabase migration/list/aggregate verification）
- 隔离 worktree 的 production prebuilt 已发布为 Vercel deployment `dpl_F7mRDYCSDbZaBkrNw8JWFVMUpZyM`，target `production`、state `READY`，并 alias 到 `https://001.100app.dev`。首页、Support、Privacy、Product detail 均 HTTP 200；非法支持邮箱 RPC 返回 400，受控 Support/Price Alert 烟测均返回 200。烟测产生的 1 条 support 和 1 条 alert 已删除，复核剩余烟测行均为 0；限流表保留 4 条无身份指纹。（来源：Vercel inspect、live curl、Supabase cleanup verification）
- 正确 Team ID 为证书 OU 与 profile 一致的 `46H3U4N2U3`，不是证书 CN 括号中的个人标识。使用该 Team ID 的本地 Release device archive 成功，产物为 `dev.100app.geardrop`、`1.0.0 (1)`、arm64、220 MB；`codesign --verify --deep --strict` 通过，embedded development profile 有效至 2027-07-12。（来源：2026-07-19 archive metadata、codesign、mobileprovision 读取）
- 已新增并 lint 通过 `.agent/geardrop-app-store-export-options.plist`。App Store export 真实尝试 exit 70：Xcode 仍报告 `No Accounts`、缺 `iOS Distribution` certificate 和 App Store profile，因此 development archive 不能直接导出/上传 TestFlight。EAS credentials 和 ASC API Key 也仍未配置，且 TestFlight live 页面为 `No Builds`。（来源：2026-07-19 `xcodebuild -exportArchive`、EAS/ASC live evidence）
- Chrome 的 App Store Connect 登录会话已成功读取真实账号状态：Free Apps Agreement 为 Active；Paid Apps Agreement 为 `Pending User Info`；银行账户为 `Processing`；W-8BEN 为 `Missing Tax Info`；Digital Services Act 对 27 个国家/地区为 Active，且该 app 已识别为 trader。（来源：2026-07-19 ASC Business/App Information live DOM）
- GearDrop ASC 实际仍有多项非 W-8 准备未保存：iOS 1.0 列表元数据/截图为空，Sign-in required 被勾选但 app 无账户登录，Pricing 与 Availability 未设置；App Information 缺 subtitle、content rights、primary category 和 age rating；App Privacy URL 为空且问卷未开始。Lifetime IAP、Monthly/Annual subscription 产品 ID 已存在并为 Prepare for Submission，但本地化和审核截图未完成。（来源：2026-07-19 ASC 各页面 live DOM）

## 下一步
1. 用户选择发布路径：A) 先发欧洲免费版，移除/隐藏付费墙和 Pro gate，按 Free Apps Agreement 提交；B) 保持 Paid v1，等待 W-8 与银行处理完成后再做 StoreKit/TestFlight。
2. 经用户在浏览器保存动作前确认后，写入并保存已有草稿的 subtitle、category、description、keywords、Support/Privacy URL、content rights、age rating、App Privacy，以及欧洲 availability；不点击 Add for Review。
3. 用户在 Xcode Settings > Accounts 真正添加 Apple ID（当前本机账户列表仍为空），或明确授权可能产生用量的 EAS build 并在本机交互完成 Apple/2FA；随后创建 Distribution certificate/profile、导出 IPA、上传 TestFlight。
4. Paid v1 路径在协议激活后补齐三项 IAP 本地化/审核截图，验证真实 StoreKit offering、sandbox purchase、restore，再补第 5 张 paywall 截图。

## 死路
- 2026-07-19 系统 Python 缺 `requests`，`tools/check_data_quality.py --online` 无法启动；已改用 App 自带的 Node 实时探针取得等价的当前产品/区域数据证据。
- 2026-07-19 内置浏览器仍跳转 `authResult=FAILED`，但同轮 Chrome 已有有效 App Store Connect 登录并完成 live 复核；后续 ASC 操作固定使用该 Chrome 会话。
- `expo-doctor@1.20.1` 在当前含空格的绝对路径错误打印 `expo config ... exited with non-zero code: 1`，自身却 exit 0；同一路径直接 `expo config` 正常，`expo-doctor@1.20.0 --verbose` 为 20/20，故发布门固定 1.20.0，避免假绿。
- 根目录全量 Python unittest 因系统 Python 缺既有依赖 `requests`，在导入 `tests/test_product_lifecycle.py` 时失败；本任务新增/修改的网站测试已单独执行 6/6 通过。该环境问题不作为本任务改坏代码的证据，也不冒充全量通过。
- 初次 Vercel preview 因 HEAD 的 bot 提交作者邮箱不被 Vercel 识别而 `BLOCKED`；隔离 worktree 的有效作者空提交已使第二次 preview `READY`。该处理仅用于部署身份，不会推送或混入生产代码提交。
- 本地 device archive 因 Xcode Accounts 的 Keychain 凭据无效且缺 provisioning profile 而 exit 65；EAS 同时确认 build credentials 与 ASC API Key 均未设置。必须由用户完成 Apple 登录/2FA，不能把此项误报为已完成或归因于 W-8。
- 使用正确 Team ID 后 development archive 已成功，但 App Store export 仍因 Xcode Accounts 为空、无 Distribution certificate/profile 而 exit 70；“浏览器已登录 ASC”不等于“Xcode Accounts 已登录”。
