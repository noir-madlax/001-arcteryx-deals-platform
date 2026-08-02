# TASK: GearDrop Support 上线（更新：2026-08-02 11:23 EDT）

## Why（一句话）

为 App Store 上线提供公开、可用、隐私披露一致的客服入口，同时不把整个 iOS 开发分支带入生产网站。

## 当前状态：进行中

## 边界

- 仅上线 `support.html`、相关公开链接、隐私说明、价格提醒 RPC 客户端切换及对应回归测试。
- 不提交 App Store，不触发 EAS/iOS 构建，不修改其他生产功能。
- Supabase 只在 live 对象缺失或与仓库定义不一致时做最小 DDL；若已一致则不重复迁移。
- 不使用真实客户邮箱制造持久化测试记录；生产烟测使用 honeypot 非持久化路径并前后读回行数。

## 已确认事实

- 基线为 `origin/main` 的 `f529393fda8cb22adc8557e961f390f7cd0710d0`（命令：`git rev-parse HEAD`）。
- 生产 Supabase 项目为 `bupqagkrcvrezjkdbald`；`supabase_migrations.schema_migrations` 已有 `20260719161928_geardrop_submission_security`（Supabase `execute_sql` live 读回）。
- `public.submit_support_request`、`public.register_price_alert`、`public.unsubscribe_alert` 与 `private.consume_public_request_quota` 均为 `SECURITY DEFINER` 且 `search_path` 为空（Supabase `execute_sql` live 读回）。
- `anon`/`authenticated` 对 `public.support_requests`、`public.price_alerts` 无底层表权限，对 `private` schema 无 `USAGE`；三项公开 RPC 有 `EXECUTE`（Supabase `execute_sql` live 读回）。
- 开工时 `public.support_requests` 行数为 0（Supabase `execute_sql` live 读回）。

## 假设

- GitHub 到 Vercel 的既有生产 Git 集成仍有效；需由 PR 预览和合并后的 live 部署回读验证。
- `https://001.100app.dev` 仍映射到本仓库生产项目；需由 Vercel 项目元数据和 HTTP live 回读验证。

## 已完成且已验证

- 已创建隔离 worktree `/private/tmp/geardrop-support-deploy-20260802.UAS23n` 与分支 `codex/support-deploy-20260802`，从最新 `origin/main` 开始。
- 已核对 Supabase live 迁移、函数定义、安全属性、权限、RLS 与行数；没有执行 DDL。
- 已回补与 live 版本号一致的迁移源文件；四个函数的本地 PL/pgSQL body 与生产 `pg_proc.prosrc` 逐字匹配。
- `python3 -m unittest tests.test_web_memory_guards -v`：8 项全部通过。
- 本地 HTTP 读回：`/`、`/support.html`、`/privacy.html`、`/product-detail.html` 均为 200，所需链接、表单 ID 与 RPC 路径存在。
- Node `vm.Script` 编译：主页 1 个、详情页 2 个、Support 页 1 个可执行 inline script 均语法通过。
- 生产 honeypot RPC 返回 HTTP 200 与 UUID 形状；前后 `public.support_requests` 行数均为 0。

## 下一步

1. 检查完整 staged diff，提交并推送分支。
2. 创建 draft PR，验证 Vercel Preview。
3. 合并到 `main`，验证生产部署及公开页面。

## 死路

- `python3 -m unittest discover -s tests -v` 共运行 64 项，其中 5 个模块在导入时失败：临时环境缺少 `scrapling`、`playwright`、`requests`；本次目标测试单独运行 8/8 通过，因此未为静态网页发布安装整套爬虫运行时。
- 首次 inline-script 语法检查把 `application/ld+json` 误当 JavaScript，出现 `Unexpected token ':'`；加入 script type 过滤后，四个可执行脚本均编译通过。
