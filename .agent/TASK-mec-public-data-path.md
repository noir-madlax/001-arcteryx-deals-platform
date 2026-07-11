# TASK: MEC 公开数据路径逆向（完成：2026-07-11 13:31 EDT）

## Why（一句话）

找出 MEC 列表第 3 页阻断的真实原因和稳定公开数据入口，在不破解验证码或访问控制的前提下提高 MEC 数据新鲜度。

## 当前状态：已完成并通过生产验收

## 已确认事实

- 生产实跑第 1、2 页各返回 52 条，第 3 页长时间无推进；来源：2026-07-11 Lightsail `dealers.log`。
- `dealers/mec.py` 在 AWS IP 上先尝试 `curl_cffi`，失败后使用 Scrapling `StealthySession`；来源：CodeGraph 读取 `dealers/mec.py:25-77`。
- Scrapling shim 对单次请求设置至少 60 秒超时，但当前日志未保留响应 headers、最终 URL、CF Ray ID 或页面特征；来源：CodeGraph 读取 `dealers/mec.py:61-77`。
- 当前干净 worktree 基于 `origin/main` 提交 `1790619`；来源：`git worktree add` 输出。
- 本机同一 `curl_cffi` 会话请求 MEC 1/2/3 页均为 HTTP 200，命中数 52/52/24，总数 `nbHits=128`、`nbPages=3`；来源：2026-07-11 只读运行时实验。
- OCI 用生产虚拟环境和现有 `dealers.mec` 请求 1/2/3 页均成功，约 1.4 秒/页，命中数 52/52/24；来源：OCI 只读 Python 实验。
- Lightsail 对同样的 1/2/3 页全部返回 HTTP 403，响应约 6 KB；来源：Lightsail 只读 Python 实验。
- MEC Next.js 公开 JSON 路由 `/_next/data/<buildId>/en/products.json` 可返回同一列表数据；第 3 页 HTTP 200、24 条、约 500 KB；来源：本机只读实验。
- 部署前 `merge_partial` 会从上一轮静态结果播种，而 `dealers.supabase_sync` 会同步所有播种 dealer，并统一赋予本轮 `generated_at`；来源：读取部署前的 `dealers/merge_partial.py` 与 `dealers/supabase_sync.py`。这会把未实际刷新来源的时间戳伪装为新鲜，现已修复。
- PR #3 已合并，merge commit `95a565f`；OCI/Lightsail 已部署，数据提交 `ac74d9d`；来源：`gh pr view 3`、两台服务器 `git rev-parse`。
- 生产 MEC 完整抓取 128/128，Supabase upsert 128/128，生产活跃 MEC 155 条，质量门 `OK`；来源：OCI `server_run_mec.sh` 实跑和在线质量门。
- 生产数据库 MEC 最新时间为 17:29:45 UTC；EVO/REI/SSENSE 最新时间仍为 16:34:04 UTC；来源：生产 SQL 分组查询，证明保留快照未被伪装刷新。
- `crawler_leases.mec` 最终状态为 `success`，owner `oci-free-a1`；来源：生产 SQL 查询。
- GitHub Actions run `29163565662` 从 hosted runner 对 MEC 1/2/3 页均返回 HTTP 200，命中 52/52/24、总计 128；来源：`Diagnose MEC Egress` workflow 日志。
- 18:29 UTC Lightsail 复跑只有 REI 真实成功，因此静态 `fresh_dealers=["rei"]`、REI `refreshed_at=18:29:21`；EVO/SSENSE 空抓取继续为未知且数据库时间不推进；来源：远程运行日志、main 静态文件和生产 SQL。
- 18:30 UTC OCI 再次只读检查 MEC 仍为 52/52/24、总计 128；来源：OCI 生产环境只读 Python 实验。

## 假设（未验证；验证后移入上区）

- OCI 在未来仍可能被 Cloudflare 调整风险评分，因此仍需保存上一版数据和失败告警。

## 边界

- 不破解 CAPTCHA、不绕过账号/权限控制、不使用凭据或住宅代理轮换。
- 部署前只做只读请求和脱敏诊断；生产发布于用户明确确认后执行。
- 未清空现有 MEC 数据；未使用凭据或规避访问控制。

## 验收标准

1. 可复现并分类第 3 页失败信号（状态、超时、挑战页或响应结构）。
2. 找到并验证至少一个可持续的公开数据入口，或用证据排除该路径。
3. 若修改代码：定向测试通过，失败页仍保存已抓页面，0 条不得覆盖生产快照。

## 已完成且已验证

- 已建立独立分支 `codex/mec-reverse` 和干净 worktree `/tmp/arcteryx-mec-reverse`。
- 已排除分页参数/第 3 页数据结构问题；阻断与 Lightsail AWS 出口相关。
- 已验证 OCI 是当前可用的 MEC 主抓取出口，公开 Next.js JSON 路由可作为轻量候选入口。
- 已实现 MEC 首页 HTML → 后续公开 Next.js JSON → HTML fallback；在 OCI 临时目录实跑得到 52/52/24，共 128 条，断言通过。
- MEC partial 现在携带 `crawl_complete` 与 `expected_count`；OCI 新代码实跑为 `True/128/128`，不完整分页会在同步前被 runner 拒绝。
- 已实现 `fresh_dealers`/`refreshed_at`，Supabase sync 只处理本轮真实抓新的 dealer；空抓取和播种快照不更新时间。
- 已新增 OCI MEC runner/cron，并从 Lightsail/GitHub dealer fallback 的模块列表中移除 MEC。
- 已运行 13 个单元测试、Python 编译、4 个 shell 语法检查、workflow YAML 解析和 `git diff --check`；首次运行全部通过，ResourceWarning 已修正。
- 已部署 OCI shared repo lock + MEC cron、Lightsail 非 MEC dealer cron；两台原 crontab 均有时间戳备份。
- 生产完整链路完成：抓取、完整性闸门、merge、仅 MEC sync、质量门、Git push、飞书通知和 lease release 全部成功。
- 已新增只读 `Diagnose MEC Egress` 手动 workflow，并验证 GitHub runner 当前可作为候选 MEC 出口。

## 下一步（按序）

1. 由现有 freshness monitor 持续观察 MEC；如果 OCI 未来被 Cloudflare 拒绝，可把已验证的 GitHub runner 接成自动 MEC takeover。

## 死路

- 本机首次复用 `dealers.mec._next_data` 的临时 `uv` 环境未安装 Scrapling，导入失败；改用等价内联只读解析完成 Next.js JSON 路由验证，未重复安装重依赖。
- GitHub hosted runner 出口最初未验证；现已通过 run `29163565662` 验证可用，但自动 MEC takeover 尚未启用。
