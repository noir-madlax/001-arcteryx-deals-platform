# TASK: GearDrop iPad 键盘避让修复（更新：2026-08-24 18:48 Asia/Taipei）

## Why（一句话）

让 App Review 使用 iPad 兼容模式打开 Build 8 的价格提醒弹窗时，邮箱、目标价和操作按钮不会被系统键盘遮挡。

## 当前状态：实现与本地验收完成，未上传/未重提审核

已在隔离分支 `codex/fix-ios-ipad-keyboard-20260824` 基于当前审核代码分支 `codex/ios-appstore-continue-20260809` 开工；不触碰主工作树，不上传构建，不重新提交审核。

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
4. 只修改本修复必要的 App 文件与本任务档案；不上传 EAS、不修改 App Store Connect、不重提审核。

## 已完成且已验证

- 已取得并查看 Apple 原始拒审截图，定位到 Price alert 弹窗而非搜索框或登录页。
- 已读取 Expo SDK 57 与 React Native 0.86 官方文档。
- 已建立隔离工作树和分支，起点为 `54607cc`。
- 已先在 `verify:config` 增加键盘避让契约；未改组件时按预期失败，原文为 `Price alert modal must move above the on-screen keyboard`。
- 已用平台明确的 `KeyboardAvoidingView` 承载 Price alert 卡片；`npm run verify:config` 与 `npm run typecheck` 已转绿。
- Release 模拟器构建成功（`xcodebuild ... ONLY_ACTIVE_ARCH=YES`，exit 0），重新打包 1,497 个 iOS JS 模块。
- iPad Air 11-inch (M3) / iOS 18.4：分别聚焦邮箱和目标价后，两个输入框与 Cancel / Save alert 均在可视区；空邮箱点击 Save alert 出现本地校验，点击 Cancel 成功关闭弹窗，未发送线上写入。
- iPad Air 11-inch (M4) / iOS 26.5：同一 Apple 商品与弹窗路径下，邮箱键盘、数字键盘均保持字段和两个操作按钮完整可见。证据：`/private/tmp/geardrop-ipad-keyboard-20260824.5D66ih/evidence/ipad-m4-ios26.5-email-keyboard.png` 与 `ipad-m4-ios26.5-price-keyboard.png`。
- `npm run verify` 已完成单测（40/40）、配置、Release 资源、typecheck；Expo Doctor 为 19/20，唯一失败是仓库既有 8 个 Expo SDK 57 补丁版本低于当前建议版本。为保持审核修复最小范围，本轮未升级依赖。
- Doctor 之后的步骤已单独补跑：实时汇率通过（2026-08-24）、实时目录通过（8,644 products / 88,386 price_history）、iOS export 通过（1,497 modules）。

## 下一步

1. 用户另行授权后再生成新 Build、上传并重新提交 App Review。

## 假设清算与未验证项

- “最小键盘避让足够”已由 M3/iOS 18.4 与 M4/iOS 26.5 两套运行时证据确认，无需增加滚动容器。
- 本机未安装 Apple 审核使用的精确组合 M3 / iPadOS 26.6；精确 26.6 仍未验证，但已分别覆盖精确设备型号与相邻 26.x 系统。
- App Store Connect、EAS、线上价格提醒均未写入；本轮只完成代码和本地运行时验收。

## 死路

- Chrome 下载事件等待超时，但文件实际已落到 Downloads；后续以文件 `stat` 和人工查看为准，不重复点击下载。
- 为本地重拍失败态启动的 Release 构建默认同时编译 arm64 与 x86_64；Apple 原始截图已经是更精确的失败基线，因此终止冗余双架构构建，保留缓存并改用 `ONLY_ACTIVE_ARCH=YES` 构建修复版。
