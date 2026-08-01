# TASK: automation-5 精确价格样本远端复核（更新：2026-08-01 21:03 UTC）

## Why（一句话）

让远端只读价格审计真正重放首次固定 100-SKU 工件，并把官方读取可靠性恢复到 `verified >= 90`，不换样、不写生产价格。

## 当前状态：完成

## 边界

- 用户主 checkout 保持不动；仅在 `/tmp/arcteryx-a5-exact-20260801.52VkVH/worktree` 基于最新 `origin/main` 操作。
- 价格探针只读；不可验证不算正确；首次样本工件不可替换。
- 不手工写生产数据库、不伪造 secret；生产价格修复仍只走既有 revalidation/refresh workflow。

## 已确认事实（每条带来源）

- `git fetch origin` 后基线为 `3619c54d2e1645112971a7a9523ad6fda31d01ed`；用户主 checkout `ffd565d2` 干净且落后 35。来源：git 原始输出。
- 必须保留的首次样本工件是 `/Users/J/.codex/automations/automation-5/audit-price-20260801T1305Z-13e85c6.json`，seed `8300222867769095196`、分层 `60/10/10/10/10`。来源：automation memory 与工件读回（待本轮再次校验哈希）。
- 上轮本地固定样本最终为 `100/85/85/0/15`；失败集中于 2 个 Outlet ProxyError、4 个 Evo 429/浏览器失败、9 个 REI `cf_stub`。来源：automation memory；本轮将以工件重读与可重复测试复核。
- 现有远端 workflow 只接收 `run_start` / `origin_sha`；同 seed 在生产候选池变化后重抽了不同 SKU 集合。来源：上轮工件集合比较；本轮需亲读 workflow/脚本和测试后再定位实现原因。
- CodeGraph 目录存在，但本回合没有可调用的 `codegraph_*` 工具；结构探索将使用定点源码读取与现有测试，不把索引不可用当作代码事实。
- 用首次 `run_start/origin_sha` 对当前 live 候选池重新抽样，seed 仍为 `8300222867769095196`，但与首次 100 条仅重叠 5 条；`same_order=false`、`same_set=false`。来源：正式 `sample_rows` + live `load_online_rows` 只读复现。
- 首次 JSON 为 65,870 bytes，gzip+base64 后 8,384 字符；GitHub workflow input 总 payload 官方上限为 65,535 字符，`gh workflow run --json` 可从 stdin 传 inputs。来源：`wc`/gzip 实测与 GitHub 官方 workflow/CLI 文档。
- `read_outlet_pass`、`read_evo_pass`、`read_rei_pass` 等 dealer reader 返回瞬态 `_err` 后，`run_official_pass` 原实现不重试；REI 第二轮 `cf_stub` 因而直接进入不可验证。来源：`tools/audit_price_accuracy.py` 定义与调用方、固定样本工件。

## 假设（未验证；验证后移入上区）

- 无。

## 验收标准

1. 远端 workflow 的 JSON 工件与首次工件 `sku_id` 集合和顺序完全一致，仍为 `60/10/10/10/10`。
2. 正式远端工件满足 `sampled=100`、`verified >= 90`、`confirmed_wrong=0`；不可验证不计正确。
3. 新接口保持只读凭据边界，不接受任意不可信文件/路径，不输出 secret。
4. 受影响测试、完整 Python 测试、compile/YAML/diff 校验通过；推送后 workflow 和生产三个质量门有原始输出。
5. 用户主 checkout 不变，临时 worktree 在完成后清理；任务档案随修复提交保留。

## 已完成且已验证

- 已读取 automation memory、Obsidian 项目线索与长任务协议。
- 已 fetch 并创建最新远端基线的隔离 worktree。
- 已实现 hash-bound exact-sample input：base64/gzip 解码、20,000 字符输入上限、1 MB 解压上限、SHA-256、100 个唯一 SKU 与 `60/10/10/10/10` 分层均 fail closed，之后 workflow 调用正式 `--sample-file`。
- 已实现 dealer pass 瞬态失败 fresh-session 重试一次；只重试 Proxy/timeout/429/`cf_stub`/browser 等标记，不重试 `color_variant_not_found`。
- 定向 14 tests、完整 108 tests、compileall、workflow YAML parse、`git diff --check` 和首次真实工件 materialize+`cmp` 均 exit 0。`actionlint` / `shellcheck` 本机不可用，未宣称执行。
- 修复提交 `ce0ae4464eb0842982388efb0bc64a4cea6e56d9` 已推分支并快进推入 `main`；随后定时 dealer 静态数据提交 `c4d946ce1e5dd8a388b607874040f6d23c69acb4` 保留该提交为祖先。
- 分支远端只读审计 run `30717169272` 成功；输入工件 SHA-256 `75ad5a8f5b9099e5ea5c13c7b818e1b345ac302fdb86f2b576308376a03d2a5e`，输出与首次 100 个 `sku_id` 顺序完全一致，结果 `100/100/100/0/0`。
- `main` 部署后只读审计 run `30717690864` 成功；输出再次与首次样本顺序完全一致，结果仍为 `100/100/100/0/0`，五个 dealer 准确率均为 100%。
- 定时 dealer 刷新 run `30717244494` 成功后，最终三门均 exit 0：Outlet `5186`；dealers `508`（Evo 249 / MEC 147 / REI 68 / SSENSE 44）；全量 `5694`。
- 最终静态读回：`/`、`/data.js`、`/dealers/results.json` 均 HTTP 200；`data.js` 5186 条，dealer JSON 507 条、`generated_at=2026-08-01 20:56:21`，无 rejected dealer。

## 下一步（按序）

1. 更新 automation memory。
2. 移除本任务创建的临时 worktree，确认用户主 checkout 的 HEAD/clean 状态未变。

## 死路

- 仅传相同 `run_start` / `origin_sha` 不能保证固定样本：候选池变化后会重抽不同 SKU；禁止再次把同 seed 当作同样本证据。
