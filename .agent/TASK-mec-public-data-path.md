# TASK: MEC 公开数据路径逆向（更新：2026-07-11 12:38 EDT）

## Why（一句话）

找出 MEC 列表第 3 页阻断的真实原因和稳定公开数据入口，在不破解验证码或访问控制的前提下提高 MEC 数据新鲜度。

## 当前状态：实现完成，待生产部署确认

## 已确认事实

- 生产实跑第 1、2 页各返回 52 条，第 3 页长时间无推进；来源：2026-07-11 Lightsail `dealers.log`。
- `dealers/mec.py` 在 AWS IP 上先尝试 `curl_cffi`，失败后使用 Scrapling `StealthySession`；来源：CodeGraph 读取 `dealers/mec.py:25-77`。
- Scrapling shim 对单次请求设置至少 60 秒超时，但当前日志未保留响应 headers、最终 URL、CF Ray ID 或页面特征；来源：CodeGraph 读取 `dealers/mec.py:61-77`。
- 当前干净 worktree 基于 `origin/main` 提交 `1790619`；来源：`git worktree add` 输出。
- 本机同一 `curl_cffi` 会话请求 MEC 1/2/3 页均为 HTTP 200，命中数 52/52/24，总数 `nbHits=128`、`nbPages=3`；来源：2026-07-11 只读运行时实验。
- OCI 用生产虚拟环境和现有 `dealers.mec` 请求 1/2/3 页均成功，约 1.4 秒/页，命中数 52/52/24；来源：OCI 只读 Python 实验。
- Lightsail 对同样的 1/2/3 页全部返回 HTTP 403，响应约 6 KB；来源：Lightsail 只读 Python 实验。
- MEC Next.js 公开 JSON 路由 `/_next/data/<buildId>/en/products.json` 可返回同一列表数据；第 3 页 HTTP 200、24 条、约 500 KB；来源：本机只读实验。
- `merge_partial` 会从上一轮静态结果播种，但 `dealers.supabase_sync` 当前会同步所有播种 dealer，并统一赋予本轮 `generated_at`；来源：读取 `dealers/merge_partial.py` 与 `dealers/supabase_sync.py`。这会把未实际刷新来源的时间戳伪装为新鲜。

## 假设（未验证；验证后移入上区）

- GitHub Actions 出口是否能直连 MEC 尚未验证。
- OCI 在未来仍可能被 Cloudflare 调整风险评分，因此仍需保存上一版数据和失败告警。

## 边界

- 不破解 CAPTCHA、不绕过账号/权限控制、不使用凭据或住宅代理轮换。
- 先只做只读请求和脱敏诊断；确认路径后才修改爬虫。
- 不部署生产、不清空或覆盖现有 MEC 数据。

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

## 下一步（按序）

1. 最终重跑测试并提交本地分支。
2. 得到生产部署确认后创建 PR/合并，更新 OCI/Lightsail cron 和代码。
3. 生产实跑 MEC，验证 128 条、`fresh_dealers=["mec"]`、数据库时间戳和租约状态。

## 死路

- 本机首次复用 `dealers.mec._next_data` 的临时 `uv` 环境未安装 Scrapling，导入失败；改用等价内联只读解析完成 Next.js JSON 路由验证，未重复安装重依赖。
- 未把 GitHub Actions 声称为 MEC fallback：其 runner 出口尚未实测，且云厂商 IP 可能同样被 MEC/Cloudflare 拒绝。
