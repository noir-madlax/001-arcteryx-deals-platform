# TASK: iOS 多语言与显示币种切换（更新：2026-07-12 07:38 EDT）

## Why（一句话）
让同一地区商品流可以独立切换界面语言与显示币种，服务跨国用户，同时不改变商品来源地区和后端原币价格契约。

## 当前状态：功能与最终物理机 smoke 已完成；完整 verify 仍受 live 商品总量门槛阻塞

## 已确认事实
- App 已有持久化全局 RegionContext；Region 决定商品来源，不能与显示币种合并。（来源：`app/contexts/RegionContext.tsx`、`app/app/(tabs)/index.tsx`）
- 商品、提醒 payload 和历史价格均保存原币金额与币种；价格提醒写入不得改为换算币种。（来源：`app/lib/types.ts`、`app/lib/priceAlerts.ts`）
- Expo SDK 57 官方推荐 `expo-localization ~57.0.0` 读取设备 locale；Hermes 支持 `Intl.NumberFormat`。（来源：Expo SDK 57 localization 官方文档，2026-07-12 查阅）
- Frankfurter v2 公共 API 无需 key，提供日参考汇率；本期只作为显示换算数据源。（来源：`https://frankfurter.dev/`，2026-07-12 查阅）

## 假设
- 首版语言：System、English、简体中文、Deutsch、Français、日本語。
- 首版显示币种：Original、USD、CAD、EUR、GBP、JPY、CHF。
- 设置入口放在 Me；Region 仍只放 Deals 标题栏。
- 汇率请求失败时使用本机缓存；无缓存时回退原币显示，不伪造汇率。

## 验收标准
1. 语言与显示币种选择均持久化，kill/relaunch 后保持。
2. System 能读取设备语言；缺失翻译回退 English。
3. Deals、详情、Watchlist、Me、Paywall、AlertModal 主流程文案随语言切换。
4. Original 显示商品原币；指定币种后 Deals/详情/Watchlist/价格历史金额统一换算并使用 `Intl.NumberFormat`。
5. Region 与 currency 独立：DE + USD 仍只看 DE 商品，但金额显示 USD。
6. Alert 提交和目标价校验仍使用商品原币，界面明确标注。
7. 汇率缓存包含日期；网络失败时缓存可用，无缓存回退原币。
8. 单测、typecheck、expo-doctor、iOS export、签名真机构建通过；行为改动需物理 iPhone 截图。

## 已完成且已验证
- 已新增 `PreferencesProvider`，把语言、显示币种和汇率快照持久化到 AsyncStorage；RegionContext 保持独立。
- 已接入 System / English / 简体中文 / Deutsch / Français / 日本語；Deals、详情、Watchlist、Me、Paywall、AlertModal、隐私页文案和目录分类均已覆盖。`app/__tests__/preferences.test.ts` 会断言每个发布语言具备完整键集。
- 已接入 Original / USD / CAD / EUR / GBP / JPY / CHF；Deals、详情、Watchlist 和价格图表走统一换算/格式化。提醒目标值、校验和 payload 继续使用商品原币。
- 已接入 Frankfurter v2 EUR 基准日汇率、24 小时缓存与失败回退。2026-07-12 实时探针返回日期 `2026-07-13`，包含 USD/CAD/GBP/JPY/CHF/SEK/DKK/AUD。
- `npm test`：33 tests / 33 pass / 0 fail。
- `npm run typecheck`：exit 0。
- `npm run verify:config`：通过，插件列表包含 `expo-localization`。
- `npm run doctor`：20/20 checks passed。
- `npx expo export --platform ios`：通过，1460 modules，iOS HBC 3.9 MB。
- Apple Development Release 真机构建：`** BUILD SUCCEEDED **`；`codesign --verify --deep --strict` 通过；Team ID `46H3U4N2U3`，profile UUID `6956f8db-04f2-43e3-9993-dcd8ff4e4b65`。
- 物理 iPhone 16 Pro / iOS 26.4.2 已无线覆盖安装并启动。首屏截图确认 System 解析为中文，Deals/排序/筛选/信号/分类/tab 使用中文；`geardrop://me` 截图确认设置页显示 Language=System、Currency=商品原币。
- iPhone 17 / iOS 26.5 Simulator Release UI 自动化：XCTest 实际点击 `语言 -> 日本語`、`表示通貨 -> JPY`，返回日文 Deals，terminate 后 relaunch，再断言 `言語` value=`日本語`、`表示通貨` value=`JPY`；43.074 秒，0 failure，`** TEST SUCCEEDED **`。
- 重启后的设置页截图显示 `言語=日本語`、`表示通貨=JPY`、参考汇率日期 `2026-07-13`；日文 Deals 截图仍为 US region、679 件商品，但 USD 原价已换算为 `¥41,488` 等 JPY 金额，证明 Region 与显示币种独立。
- 偏好行和选项已补 `button`、label、value/selected accessibility 语义；这是 XCTest 能稳定定位的前提，也使 VoiceOver 可读出当前选择。
- 上述 accessibility 调整后的最终 Apple Development Release 再次 `** BUILD SUCCEEDED **`，`codesign --verify --deep --strict` 通过，并已无线覆盖安装到物理 iPhone。
- 简体中文品牌名已改为“值de”；其他语言和默认产品名继续使用 GearDrop。Expo prebuild 生成的 `zh-Hans.lproj/InfoPlist.strings` 及最终 `.app` 均实测为 `CFBundleDisplayName = 值de`、`CFBundleName = 值de`。
- 解锁后重新生成并签名最终 Release：`** BUILD SUCCEEDED **`；`codesign --verify --deep --strict` 输出 `valid on disk`、`satisfies its Designated Requirement`，Team ID `46H3U4N2U3`，profile UUID `6956f8db-04f2-43e3-9993-dcd8ff4e4b65`。
- 最终 Release 已无线覆盖安装并用 `--activate --display 1` 在物理 iPhone 前台启动。Deals 截图显示中文双列卡、`4,959` 已加载、US `679` 条；`geardrop://me` 截图显示“值de · 值得买的装备。”和“关于值de”。证据：`/private/tmp/geardrop-value-de-active.png`、`/private/tmp/geardrop-value-de-me-active.png`。
- 完整 `NPM_CONFIG_CACHE=/tmp/geardrop-npm-cache npm run verify` 已按要求再次运行但仍未通过：33/33 测试、配置、typecheck、Doctor、实时汇率均通过，live data probe 实际加载 `4,959`，因 `expected at least 5000 products, got 4959` 退出；未降低门槛。

## 下一步
1. 数据侧恢复到至少 5,000 条可见商品后重跑 `npm run verify`；当前实际为 4,959。物理机启动阻塞已经关闭。

## 死路
- 临时 XCTest 最初按 tab/button 文本定位失败：iOS 26 原生 tab 不暴露标准 TabBar；改为底部命中扫描并以页面唯一标题确认导航。
- 偏好行最初没有显式 accessibility 语义，XCTest 无法定位。已在产品代码补齐 button/label/value/selected 后重测通过。
