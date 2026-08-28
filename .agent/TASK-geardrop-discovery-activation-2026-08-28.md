# TASK: GearDrop 主动收录与 AI 可见度复测闭环（更新：2026-08-28 22:02 Asia/Taipei）

## Why（一句话）

把已上线的 GearDrop GEO 技术资产从“可抓取”推进到“主动通知、平台可观测、按同一口径复测”，同时保留独立的 iOS 发布边界。

## 当前状态：进行中

已在隔离 worktree 完成本地候选与验证；尚未推送／部署、写入 GitHub Secrets、请求真实 IndexNow、改 Bing Webmaster／Google Search Console 或创建自动化。

## 边界

- 用户于 2026-08-28 回复“好的 做吧”，授权执行上一轮明确推荐的第一优先级：IndexNow、Bing/Search Console 闭环，以及第 7 天／第 14 天复测安排。
- 允许差异仅限：`001.100app.dev` 的 IndexNow 验证文件、仓库 `INDEXNOW_KEY`／`INDEXNOW_KEY_LOCATION` 两个 Actions Secret、Bing/Google 的该站点属性与 sitemap、当前线程的两次复测自动化。
- 不改商品、价格、Supabase、DNS、App Store、iOS 签名／上传／提审；不读取、输出或记录现有凭证正文。
- 平台未登录时停在登录页，由用户本人完成登录；不代输密码或验证码。
- 回滚：revert 精确提交并重新部署；删除两个 GitHub Secret；从平台移除本次 sitemap／站点属性；删除两次复测自动化。

## 已确认事实

- 隔离分支 `codex/geardrop-discovery-activation-20260828` 起点为 `origin/main` `551e461ef0401239b7e81f155b729a10e350d6fb`。（来源：本会话 `git fetch`、`git worktree add`）
- AI 可见度第一阶段提交 `5eb4562601beefa401d7fcdb24f5e02fabfaa896` 是当前 `origin/main` 的祖先；随后两次自动数据提交没有覆盖它。（来源：本会话 `git log`、`git merge-base --is-ancestor`）
- 当前生产部署 `dpl_6miN8TjZrk1XWbSLNDxsYFvAGZCY` 为 `READY`。（来源：本会话 `vercel inspect https://001.100app.dev`）
- 仓库只有 `tools/notify_indexnow.py`，没有公开 IndexNow key 文件；Actions secrets／variables 中没有 `INDEXNOW_KEY` 或 `INDEXNOW_KEY_LOCATION`。（来源：本会话 `rg --files`、`gh secret list`、`gh variable list`）
- 首页有 Google site verification meta；仓库未发现 Bing verification marker。该标记只证明部署资产存在，不能证明控制台属性、sitemap 或报告状态。（来源：`index.html:21` 与本会话字面检查）
- 当前会话没有 Search Console 或 Bing Webmaster 专用 connector/API；控制台语义操作需要使用真实浏览器会话。（来源：本会话工具能力查询）

## 假设（未验证；验证后移入上区）

- 现有浏览器可能已登录 Google 或 Microsoft；若未登录则需要用户本人接管。
- IndexNow 公开 key 可按规范由本任务新生成；提交成功必须以 API HTTP 回执和公网 key 文件读回同时成立。
- Search Console 的生成式 AI 报告仍处于分批开放；站点可能没有该报告，缺失不能记为零曝光。

## 验收标准

1. 公网 key URL 返回精确 key；两个 GitHub Secret 只以名称读回存在，正文不进入日志、任务档案或对话。
2. `tools/notify_indexnow.py --check`、测试、构建通过；真实 IndexNow 请求取得规范成功回执，并可从后续刷新路径安全复用。
3. Bing／Google 对 `https://001.100app.dev/` 的站点属性、所有 sitemap 与可用报告从新页面读回；未登录／无权限／报告未开放必须明确标记，不能猜测。
4. 第 7 天和第 14 天各有一条可读、可删除的当前线程复测自动化，提示使用冻结问题集并区分 readiness 与 observed visibility。
5. 生产代表页、robots、sitemap、机器人访问与目录计数在发布后独立回读；共享脏工作树不被修改。

## 已完成且已验证

- 已读取长任务协议与浏览器控制技能，并先查询专用 connector/API；没有可替代的 Search Console／Bing Webmaster 工具。
- 已冻结精确目标、允许差异和回滚方式，创建干净隔离 worktree。
- 已生成 64 位公开验证 token 文件 `indexnow-key.txt`；通知器会验证环境凭证与文件内容精确一致，`--check` 只输出布尔契约，不输出 token。
- 已补 `--credentials-stdin`，使一次性真实提交可通过 stdin 接收凭证，避免凭证进入命令行参数或输出。
- 本地验证曾通过：Python `218` 项、Node `13` 项、`py_compile`、`git diff --check`、Vercel preview build；最终同步主分支后需按同一口径重跑。
- 曾误让 Vercel CLI 自动创建空项目 `worktree`（`prj_QBOelbDTq8JvGOrM4uBhfz694Jvd`）；只读确认该项目无任何 deployment 后已永久删除，并把隔离 worktree 重新链接至真实项目 `arcteryx-deals-platform`（`prj_xRYhGGeWK40qlv4jEDg3PDbnaAcs`）。

## 下一步（按序）

1. 重跑本地门、审阅允许差异并提交／推送；从 preview 与生产独立读回公开 key 和代表页面。
2. 只在公网 key 生效后配置两个 GitHub Secret并执行真实 IndexNow 提交。
3. 使用真实浏览器核验／接入 Bing Webmaster 与 Search Console，提交 sitemap 并读回。
4. 创建两次复测自动化并独立查看；收尾生产与平台证据。

## 死路

- 新 worktree 首次执行 `vercel build --yes` 时，CLI 自动创建了错误的空项目 `worktree` 并按 Python 项目误检，报 `No python entrypoint found`。已核对无部署后删除空项目，再链接真实项目并成功构建；没有用户内容可恢复。
