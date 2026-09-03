# TASK: GearDrop 下一版本 ASO（更新：2026-08-14 Asia/Taipei）

## Why（一句话）

把 GearDrop 的基础上架文案升级为可搜索、可本地化、可度量的 ASO 包，并只随下一 App 版本应用，不触碰当前审核版本。

## 当前状态：已完成（本地 ASO 包待下一版本发布窗口应用）

已从 `origin/codex/ios-appstore-continue-20260809` 的 build 8 源码基线创建隔离分支 `codex/ios-next-version-aso-20260814` 和隔离 worktree，并完成五语元数据、机器校验、截图转化文案和发布/监测边界。当前审核版本与 App Store Connect 均未改动。

## 已确认事实

- 隔离 worktree 为 `/private/tmp/geardrop-aso-next-20260814.eZAnRZ/worktree`，起点为 `54607cc04227e48e30fbc17648fa6acdb2ee2f53`。（来源：本轮 `git worktree add` 与 `git log -1`）
- App 运行时已支持 `en`、`zh-Hans`、`de`、`fr`、`ja`，对应标签为 `en-US`、`zh-CN`、`de-DE`、`fr-FR`、`ja-JP`。（来源：`app/lib/i18n.ts` 的 `LANGUAGE_OPTIONS` / `LANGUAGE_TAGS`）
- 品牌合规红线要求 App 名、副标题、关键词不出现受保护商标，产品定位为户外装备比价工具。（来源：`.agent/TASK-ios-app-port.md` §1）
- Apple 当前限制为：名称最多 30 字符、副标题最多 30 字符、推广文本最多 170 字符、描述最多 4000 字符、关键词最多 100 bytes；关键词不得使用未授权商标或竞品名。（来源：2026-08-14 读取 Apple Developer `Creating Your Product Page`、`App information`、`Platform version information`）
- Apple 说明无 App Preview 时，搜索结果会优先显示前 1–3 张截图，因此下一版本截图顺序必须先表达发现折扣、判断低价、跨区比较三项核心价值。（来源：2026-08-14 读取 Apple Developer `Creating Your Product Page`）
- 2026-08-14 的美国区 iTunes Search API 中，`price tracker` 前列包括 Keepa、ShopSavvy、Reprice；`outdoor gear deals` 前列主要是 REI、Academy、品牌直营和 Backcountry；该排序只作为相关性代理，不冒充搜索量。（来源：本轮公开 API 查询输出）
- 当前 `app/store-assets/iphone-6.3/` 只有 5 张 1206×2622 历史截图；下一版本最终商店图必须从最终签名候选重新截取，不能把旧图当作下一版本完成证据。（来源：本轮 `find` / `file` 与 `app/store-assets/iphone-6.3/README.md`）
- 本轮未读取或修改 App Store Connect live 状态，也未对当前审核版本执行任何外部写入。（来源：本轮操作边界）

## 假设（未验证）

- “后一个版本”尚无最终版本号，因此仓库产物使用 `next-version` 目标，不把 `1.0.1` 或 `1.1.0` 写死。
- 下一版本仍保留当前五种 App 语言；如果发布前删减运行时语言，应同步删减对应商店本地化，而不是提交语言不一致的截图。
- 精确关键词搜索量无法从公开 App Store 页面获得；正式投放前如启用 Apple Ads，可再用 Search Match / Search Terms 数据校准优先级。

## 验收标准

1. 新增单一 canonical manifest，覆盖 `en-US`、`zh-Hans`、`de-DE`、`fr-FR`、`ja` 五个 locale，并含名称、副标题、推广文本、描述、关键词、URL 与 6 张截图文案。
2. `npm run verify:store-metadata` 对 Apple 长度/byte 限制、EULA 单次出现、URL、locale 完整性、关键词格式、受保护/竞品词和截图槽位做失败关闭校验。
3. 元数据校验加入 `npm run verify`，`APP_STORE_METADATA.md` 改为下一版本权威入口，旧的“尚未提交”状态不再冒充当前事实。
4. 研究报告明确竞品定位、关键词取舍、截图顺序、PPO 测试与 7/14/28 天监测口径，并区分公开事实与判断。
5. 运行 `npm ci`、定向元数据校验、单测、TypeScript、配置检查、`git diff --check`；条件允许时运行完整 `npm run verify`。
6. 不修改 App Store Connect、不提交审核、不上传旧截图、不改变当前 build/version。

## 已完成且已验证

- 已建立隔离分支/worktree，未覆盖共享主工作树或当前审核分支。（来源：本轮 Git 输出）
- 已读取 Expo SDK 57 版本化文档；本轮不引入 Expo API 或依赖变更。（来源：`https://docs.expo.dev/versions/v57.0.0/`）
- 已新增 `app/store-metadata/next-version.json`：五个 locale 均含名称、副标题、推广文本、描述、关键词和六张截图文案；发布边界明确为 `applyToCurrentReview=false`。（来源：本轮文件读取）
- 已新增失败关闭校验并接入 `npm run verify`。`npm run verify:store-metadata` 输出 `store_metadata_ok target=next-app-version locales=5 screenshots=6 currentReview=false`；英文关键词恰为 100 bytes，其余 locale 也均不超过上限。（来源：本轮命令输出）
- `npm test` 输出 `tests 40`、`pass 40`、`fail 0`；`npm run typecheck` 无错误；`npm run verify:config` 与 `npm run verify:release-assets` 均输出 `*_ok`。（来源：本轮命令输出）
- `npm run verify:rates` 成功读取 2026-08-13 EUR 基准汇率；`npm run verify:live-data` 成功读取 8,218 个分页产品和 86,845 条价格历史计数；`npx expo export --platform ios --output-dir dist-check` 成功导出 iOS bundle。（来源：本轮命令输出）
- manifest 中的 Support、Privacy、Apple 标准 EULA 三个 URL 经重定向后的 HTTP 状态均为 200。（来源：本轮 `curl -L` 输出）
- `git diff --check` 无输出。（来源：本轮命令输出）

## 已知验收红项

- 完整 `npm run verify` 在 `expo doctor` 停止：基线中的 `expo`、`expo-constants`、`expo-notifications`、`expo-router`、`expo-splash-screen` 各落后 SDK 57 当前期望版本一个 patch；此前步骤全部通过。该问题不是本轮元数据改动引入，本轮未扩大范围修改依赖。（来源：本轮 `npm run verify` 原始输出）
- `npm ci` 成功安装 659 个包，但 npm audit 报告 8 个 moderate、15 个 high 依赖漏洞；本轮未做依赖升级。（来源：本轮 `npm ci` 原始输出）

## 下一步

1. 下一版本号和最终签名候选确定后，先读取 App Store Connect 的 live 版本、localization、IAP 与审核状态，确认存在新的可编辑版本。
2. 从该签名候选重截五语六槽位素材，核对真实价格、语言和可见声明；当前仓库中的历史截图不能当作最终素材。
3. 先获得元数据编辑授权并逐字段读回；提交审核是另一项单独授权。发布分支还需处理 Expo patch 偏差后再跑完整 `npm run verify`。

## 死路

- `chatgpt-web-research` 的 Chrome 扩展接管连续两次超时；Computer Use 切到同一 Chrome 后，窗口持续被用户的 X 标签页重新聚焦。为避免抢占用户浏览，停止该路径，改用 Apple 官方文档、App Store 商品页与公开 iTunes Search API；未把该 skill 的未完成结果当作研究证据。
