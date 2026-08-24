# TASK: GearDrop 1.0 iPad 审核修复与 Build 9 重提（更新：2026-08-24 19:55 Asia/Taipei）

## Why（一句话）

在不合入新功能的前提下，修复 Build 8 的 iPad 键盘遮挡，并关闭同一审核基线中发现的筛选长文本与搜索首击问题，生成 Build 9 后重提 1.0。

## 当前状态：Build 9 已锁定精确候选并进入 EAS 队列，尚未上传 Apple

已在隔离分支 `codex/fix-ios-ipad-keyboard-20260824` 基于当前审核代码分支 `codex/ios-appstore-continue-20260809` 完成最小修复；不触碰主工作树，不合入新功能。用户已于 2026-08-24 授权生成并提交 1.0。EAS Build 9 已创建，App Store Connect 尚未写入。

## 已确认事实

- Apple 拒审截图 `Screenshot-0820-160431.png` 显示：iPad 上打开商品页 Price alert 底部弹窗并聚焦目标价时，数字键盘覆盖邮箱、目标价和操作区。（来源：2026-08-24 从 App Store Connect 下载并人工查看 `/Users/J/Downloads/Screenshot-0820-160431 (1).png`）
- 最新审核消息指定设备为 iPad Air 11-inch (M3)、iPadOS 26.6、版本 1.0 (8)，原文问题为 entry fields hidden behind keyboard。（来源：2026-08-24 App Store Connect 实时 DOM）
- 当前审核代码 `app/components/AlertModal.tsx` 在透明 `Modal` 内把卡片固定在底部，未使用 `KeyboardAvoidingView` 或滚动容器；两个输入框均位于该卡片内。（来源：本会话读取该文件）
- `AlertModal` 由商品详情 `app/app/product/[skuId].tsx` 渲染；CodeGraph 报告该组件有两个引用且无覆盖测试。（来源：`codegraph explore AlertModal` 与 `codegraph affected app/components/AlertModal.tsx`）
- Expo SDK 57 对应 React Native 0.86；React Native 0.86 文档说明 `KeyboardAvoidingView` 会按键盘高度调整高度、位置或底部 padding，并建议在 iOS/Android 显式设置 `behavior`。（来源：Expo 57 与 React Native 0.86 官方文档，2026-08-24 读取）

## 假设

- 最小可靠修复是在 `Modal` 内用平台明确的 `KeyboardAvoidingView` 承载底部卡片；若 iPad 兼容模式下剩余高度不足，再增加可滚动内容容器。
- iPhone-only 配置 `supportsTablet=false` 不免除 iPad 兼容模式可用性要求，本轮不扩大为原生 iPad 布局改造。

## 验收标准

1. 原 Apple 复现路径在 iPad 模拟器上打开 Price alert 并分别聚焦邮箱、目标价时，两个输入框和 Cancel / Save alert 均可见、可交互。
2. 新增机器契约能在移除键盘避让时失败。
3. `npm test`、`npm run typecheck`、`npm run verify:config` 通过；完整 `npm run verify` 如有外部服务阻塞则单列原文。
4. 德语等长文本下筛选内容可滚动，Reset / Done 始终可见；搜索键盘打开时一次点击商品卡即可进入详情。
5. 只修改审核修复必要的 App 文件与本任务档案；不合入新功能。
6. Build 9 必须来自本隔离分支的精确提交，上传后核验 bundle、版本、build number、签名与 App Store Connect 绑定对象；正式重提前执行动作时确认。

## 已完成且已验证

- 已取得并查看 Apple 原始拒审截图，定位到 Price alert 弹窗而非搜索框或登录页。
- 已读取 Expo SDK 57 与 React Native 0.86 官方文档。
- 已建立隔离工作树和分支，起点为 `54607cc`。
- 已先在 `verify:config` 增加键盘避让契约；未改组件时按预期失败，原文为 `Price alert modal must move above the on-screen keyboard`。
- 已用平台明确的 `KeyboardAvoidingView` 承载 Price alert 卡片；`npm run verify:config` 与 `npm run typecheck` 已转绿。
- 已为 Deals 列表增加 `keyboardShouldPersistTaps="handled"`，搜索键盘打开时首击商品卡即可进入详情。
- 已把筛选的品牌、品类和性别区放入纵向 `ScrollView`，标题和 Reset / Done 操作区保持固定。
- 已为上述两条相邻交互增加 `verify:config` 机器契约。
- Release 模拟器构建成功（`xcodebuild ... ONLY_ACTIVE_ARCH=YES`，exit 0），重新打包 1,497 个 iOS JS 模块。
- iPad Air 11-inch (M3) / iOS 18.4：分别聚焦邮箱和目标价后，两个输入框与 Cancel / Save alert 均在可视区；空邮箱点击 Save alert 出现本地校验，点击 Cancel 成功关闭弹窗，未发送线上写入。
- iPad Air 11-inch (M4) / iOS 26.5：同一 Apple 商品与弹窗路径下，邮箱键盘、数字键盘均保持字段和两个操作按钮完整可见。证据：`/private/tmp/geardrop-ipad-keyboard-20260824.5D66ih/evidence/ipad-m4-ios26.5-email-keyboard.png` 与 `ipad-m4-ios26.5-price-keyboard.png`。
- 当前候选再次通过 `npm test`（40/40）、`npm run verify:config`、`npm run typecheck`、`git diff --check` 和原生 iOS Release 构建（原文 `** BUILD SUCCEEDED **`）。
- 当前候选 `npm run verify` 已完成单测、配置、Release 资源和 typecheck；Expo Doctor 为 19/20，唯一失败是仓库既有 8 个 Expo SDK 57 补丁版本低于当前建议版本。为保持审核修复最小范围，本轮未升级依赖。
- Doctor 之后的步骤已单独补跑：实时汇率通过（2026-08-24）、实时目录通过（8,643 products / 88,387 price_history）、iOS export 通过（1,497 modules）。
- iPad Air 11-inch (M4) / iOS 26.5 当前 Release 候选复验：搜索键盘打开时一次点击 Black Beta Insulated Jacket 即进入详情；邮箱键盘下两个输入框与 Cancel / Save alert 完整可见；德语筛选内容成功滚动到底部性别项，Reset / Done 全程固定可见。新增证据：`build8-candidate-ipad-m4-ios26.5-email-keyboard.png` 与 `build8-candidate-ipad-m4-ios26.5-german-filter-scrolled.png`。
- EAS production Build 9 已创建：ID `c181dc45-b2c3-4343-91bb-1ca1ddaad6c7`，版本 `1.0.0 (9)`，状态 `IN_QUEUE`；EAS 回读源提交为 `cb0f315c7ac70dc7b7f505b2bc6160073738c22b`、提交信息 `fix(ios): harden review interactions`。
- EAS 凭据回读：Distribution Certificate 有效至 2027-08-04；Provisioning Profile 状态 active。CLI 因 App Store Connect API Key 缺 Apple Team ID 未完成 Apple 侧在线校验，但复用了现有 Build 8 同一套凭据并成功进入构建队列，未新建或替换证书。

## 下一步

1. 等待 EAS production Build 9 完成，下载并核验签名、bundle `dev.100app.geardrop`、版本 `1.0.0` 与 build `9`。
2. 上传 Apple，确认处理完成并锁定 iOS 1.0 的 Build 9。
3. 在正式写入审核说明和执行 Resubmit 前，向用户展示精确对象与说明并进行动作时确认；随后独立回读审核状态。

## 假设清算与未验证项

- “最小键盘避让足够”已由 M3/iOS 18.4 与 M4/iOS 26.5 两套运行时证据确认，无需增加滚动容器。
- 本机未安装 Apple 审核使用的精确组合 M3 / iPadOS 26.6；精确 26.6 仍未验证，但已分别覆盖精确设备型号与相邻 26.x 系统。
- 精确 M3 / iPadOS 26.6 仍未验证；当前新候选在 M4 / iOS 26.5 完整复验，原键盘修复另有 M3 / iOS 18.4 证据。
- `npm run verify` 不是全绿：Expo Doctor 的 8 个补丁版本建议仍为已知未清项；升级依赖会扩大拒审修复范围，本轮明确不处理。
- EAS 已创建 Build 9；App Store Connect 与线上价格提醒截至本档更新仍未写入。

## 死路

- Chrome 下载事件等待超时，但文件实际已落到 Downloads；后续以文件 `stat` 和人工查看为准，不重复点击下载。
- 为本地重拍失败态启动的 Release 构建默认同时编译 arm64 与 x86_64；Apple 原始截图已经是更精确的失败基线，因此终止冗余双架构构建，保留缓存并改用 `ONLY_ACTIVE_ARCH=YES` 构建修复版。
