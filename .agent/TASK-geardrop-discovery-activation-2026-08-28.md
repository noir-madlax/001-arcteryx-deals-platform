# TASK: GearDrop 主动收录与 AI 可见度复测闭环（更新：2026-08-28 22:24 Asia/Taipei）

## Why（一句话）

把已上线的 GearDrop GEO 技术资产从“可抓取”推进到“主动通知、平台可观测、按同一口径复测”，同时保留独立的 iOS 发布边界。

## 当前状态：进行中

代码、生产、IndexNow、Search Console 与复测调度已闭环；Bing Webmaster 在 in-app Browser 和 Chrome 都没有登录态，Chrome 已停在账号选择窗口等待用户本人登录。

## 边界

- 用户于 2026-08-28 回复“好的 做吧”，授权执行上一轮明确推荐的第一优先级：IndexNow、Bing/Search Console 闭环，以及第 7 天／第 14 天复测安排。
- 允许差异仅限：`001.100app.dev` 的 IndexNow 验证文件、仓库 `INDEXNOW_KEY`／`INDEXNOW_KEY_LOCATION` 两个 Actions Secret、Bing/Google 的该站点属性与 sitemap、当前线程覆盖第 7/14 天的复测自动化。
- 不改商品、价格、Supabase、DNS、App Store、iOS 签名／上传／提审；不读取、输出或记录现有凭证正文。
- 平台未登录时停在登录页，由用户本人完成登录；不代输密码或验证码。
- 回滚：revert 精确提交并重新部署；删除两个 GitHub Secret；从平台移除本次 sitemap／站点属性；删除复测自动化。

## 已确认事实

- 隔离分支 `codex/geardrop-discovery-activation-20260828` 起点为 `origin/main` `551e461ef0401239b7e81f155b729a10e350d6fb`。（来源：本会话 `git fetch`、`git worktree add`）
- AI 可见度第一阶段提交 `5eb4562601beefa401d7fcdb24f5e02fabfaa896` 是当前 `origin/main` 的祖先；随后两次自动数据提交没有覆盖它。（来源：本会话 `git log`、`git merge-base --is-ancestor`）
- 变更前生产部署为 `dpl_6miN8TjZrk1XWbSLNDxsYFvAGZCY`；本次提交 `14c2b8db24de1f447416f1acb4374a71c8c55ee6` 已快进到 `main`，生产部署 `dpl_2sDJNvTCH3iL49F8cmou1NKLTddb` 为 `READY`。（来源：本会话 `git push`、`git ls-remote`、`vercel inspect`）
- 仓库只有 `tools/notify_indexnow.py`，没有公开 IndexNow key 文件；Actions secrets／variables 中没有 `INDEXNOW_KEY` 或 `INDEXNOW_KEY_LOCATION`。（来源：本会话 `rg --files`、`gh secret list`、`gh variable list`）
- 首页有 Google site verification meta；仓库未发现 Bing verification marker。该标记只证明部署资产存在，不能证明控制台属性、sitemap 或报告状态。（来源：`index.html:21` 与本会话字面检查）
- 当前会话没有 Search Console 或 Bing Webmaster 专用 connector/API；控制台语义操作需要使用真实浏览器会话。（来源：本会话工具能力查询）
- Search Console 已有 `https://001.100app.dev/` URL-prefix 属性；`/sitemap.xml` 状态为成功，已发现 `8,431` 个网页，上次读取为 2026-08-21。概览显示 `1` 个网页已编入索引、`8,308` 个未编入索引；数据洞见过去 28 天没有点击，页面没有独立生成式 AI 报告。（来源：本会话新页面 DOM 读回）
- Bing Webmaster 在两个已连接浏览器都未登录；没有读取到站点／sitemap 状态，不得推定不存在。（来源：本会话新页面 DOM 读回）

## 假设（未验证；验证后移入上区）

- 用户完成 Bing 登录后，现有账号是否已包含该站点仍未知；必须从登录后的新页面读回。
- Search Console 当前未显示独立生成式 AI 报告；这只代表本属性当前页面未提供该报告，不能记为零 AI 曝光。

## 验收标准

1. 公网 key URL 返回精确 key；两个 GitHub Secret 只以名称读回存在，正文不进入日志、任务档案或对话。
2. `tools/notify_indexnow.py --check`、测试、构建通过；真实 IndexNow 请求取得规范成功回执，并可从后续刷新路径安全复用。
3. Bing／Google 对 `https://001.100app.dev/` 的站点属性、所有 sitemap 与可用报告从新页面读回；未登录／无权限／报告未开放必须明确标记，不能猜测。
4. 第 7 天和第 14 天各有一次可读、可删除的当前线程复测触发，提示使用冻结问题集并区分 readiness 与 observed visibility。
5. 生产代表页、robots、sitemap、机器人访问与目录计数在发布后独立回读；共享脏工作树不被修改。

## 已完成且已验证

- 已读取长任务协议与浏览器控制技能，并先查询专用 connector/API；没有可替代的 Search Console／Bing Webmaster 工具。
- 已冻结精确目标、允许差异和回滚方式，创建干净隔离 worktree。
- 已生成 64 位公开验证 token 文件 `indexnow-key.txt`；通知器会验证环境凭证与文件内容精确一致，`--check` 只输出布尔契约，不输出 token。
- 已补 `--credentials-stdin`，使一次性真实提交可通过 stdin 接收凭证，避免凭证进入命令行参数或输出。
- 本地验证通过：Python `218` 项、Node `13` 项、`py_compile`、`git diff --check`、Vercel preview build。
- 曾误让 Vercel CLI 自动创建空项目 `worktree`（`prj_QBOelbDTq8JvGOrM4uBhfz694Jvd`）；只读确认该项目无任何 deployment 后已永久删除，并把隔离 worktree 重新链接至真实项目 `arcteryx-deals-platform`（`prj_xRYhGGeWK40qlv4jEDg3PDbnaAcs`）。
- Git 集成 preview `dpl_5pmva8HNARdUddVyoT8APgE5yw96` 为 Ready；key 精确匹配，首页、robots 与 sitemap 均为 HTTP 200。生产 key 也精确匹配；11 个代表路径与 GPTBot、ChatGPT-User、OAI-SearchBot、Googlebot、Bingbot、PerplexityBot 访问均为 HTTP 200。
- 生产 GEO readiness 在显式 `certifi` CA 下为 `213 passed / 0 failed`，产品 sitemap 为 `8,212` 个唯一 URL，`observed_ai_visibility` 保持 `not_measured`。
- GitHub Secrets 已从不存在变为只按名称可见：`INDEXNOW_KEY`、`INDEXNOW_KEY_LOCATION`；正文未进入输出。真实 IndexNow 请求将 `8,221` 个近期 URL 单批提交并取得 HTTP `200`。
- Search Console 现有属性／sitemap／索引概览已按上区读回，因 sitemap 已为成功状态，没有重复提交。
- 当前线程自动化 `geardrop-ai-7` 已创建并读回；由于线程只允许一条 heartbeat，使用一条自动化在 2026-09-04 与 2026-09-11 10:00（Asia/Taipei）分别触发第 7/14 天复测，禁止未授权付费 API，并要求区分 `not_measured`、`blocked` 与零提及。

## 下一步（按序）

1. 用户本人完成 Chrome 中的 Bing Webmaster 登录。
2. 登录后从新页面核验是否已有 `001.100app.dev`；仅在缺失时添加站点并提交 `/sitemap.xml`，随后独立读回。
3. 重跑诊断补丁后的完整门、提交第二个最小提交并快进 `main`；确认生产仍 Ready、共享脏工作树未变化。

## 死路

- 新 worktree 首次执行 `vercel build --yes` 时，CLI 自动创建了错误的空项目 `worktree` 并按 Python 项目误检，报 `No python entrypoint found`。已核对无部署后删除空项目，再链接真实项目并成功构建；没有用户内容可恢复。
- 手动 `vercel deploy --prebuilt` 首次上传在 24.3/48.7MB 时遇到 TLS `bad record mac`；没有生成可验收部署。Git 集成随后对同一提交生成 Ready preview，并用 GitHub commit status 与 Vercel deployment id 双向绑定。
- 系统默认 Python 3.14 缺少项目依赖，首次完整发现只能加载 141 项并出现 6 个 import error；改用已有依赖完整的 Python 3.13 后 `218` 项全部通过。
- 生产 readiness 首轮因 Python 3.13 未绑定本机 CA 而全部读取失败；显式使用已安装 `certifi` CA 后 `213/213` 通过，与系统 curl 的 HTTPS 200 一致。
- 第一次真实 IndexNow 请求返回非成功 HTTP 回执，但旧工具只保留了 `HTTPError` 类型，未暴露安全状态码；补充仅输出状态码且不输出正文／凭证的诊断后，有界重试取得 HTTP 200。
- 调度器只允许当前线程绑定一条 heartbeat；第二条创建被拒绝且没有产生重复，随后把已创建的第一条更新为两次周五触发。
