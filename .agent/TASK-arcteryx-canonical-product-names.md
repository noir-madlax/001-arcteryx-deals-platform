# TASK: 始祖鸟商品标准名称（更新：2026-08-10 00:06 CST）

## Why（一句话）

让 GearDrop 的每个始祖鸟商品在网页列表、详情页和 App 中使用同一套可辨识、可追溯、不会因启发式截断而损坏的标准商品名称。

## 当前状态：已完成

## 已确认事实

- 用户要求基于始祖鸟全部商品型号建立标准商品名称，而不是继续使用通用大小写猜测。（来源：2026-08-09 当前用户指令）
- 原工作区 `main` 落后远端且包含用户未提交的 App 配置和品牌资源改动；本任务在 `/tmp/geardrop-canonical-names.1eHC1j` 的独立分支执行。（来源：`git status --short --branch`；`git worktree add` 输出）
- 开工基线为 `origin/main=326cf06`。（来源：`git worktree add` 输出）
- `cleanName` 在 App 中有 13 个调用方，覆盖首页、收藏、详情、提醒等用户界面。（来源：`codegraph explore "product name flow scraper database normalization cleanName cards detail app"`）
- 当前名称字段来自 `ProductRow.model` / `ProductRow.full_name`，并在 UI 侧调用 `cleanName`。（来源：`app/lib/types.ts:1-26`；CodeGraph 调用关系）
- 2026-08-09 生产 `active` 全量为 5,716 行、813 个原始唯一名称；5 个来源分别为 outlet 5,096、Evo 256、MEC 179、REI 128、SSENSE 57。（来源：只读 Supabase REST 全分页盘点脚本输出）
- 当前 `cleanName` 产生 78 组原本不存在的名称歧义，主要原因是删除 `Men's` / `Women's` 后把不同商品 URL 合并；例如男、女 `Beta SL Jacket`。（来源：同一全量盘点的 raw URL 与 cleaned name 分组）
- 当前通用语言前缀规则会把合法型号 `Diene Shirt LS Women's` 的开头 `Die` 误删，产出 `ne Shirt LS Women's`。（来源：全量盘点异常 first-token 输出与当前正则）
- 全量商品中的容量 token 与 URL slug 比对为 0 个不一致，容量必须原样保留。（来源：全量盘点 volume mismatch 输出）
- 生产数据至少混入 1 条非始祖鸟 SSENSE 商品：Marc Jacobs `The Glam Mirror Satchel`；因此“仅始祖鸟”不能当作未经校验的输入前提。（来源：生产 active 行的名称、dealer 与 URL 品牌路径只读核验）

## 假设

- 标准显示名去掉重复的 `Arc'teryx` 品牌前缀，保留官方型号、版本、容量、服装类型和规范化性别后缀；性别不能只留在独立元数据中，否则会造成可观测的同名歧义。
- SSENSE 等来源的颜色前缀只能在识别出其后的始祖鸟型号时删除；未知名称采用保守原样回退，不做猜测性截断。
- “全部型号”以当前生产全量商品加仓库快照为可验证基线，并采用可扩展词典/规则支持后续新型号；不声称这是品牌历史上永远封闭的型号全集。
- 原始 `model` / `full_name` 不回写、不破坏；标准名称是展示层派生值。

## 验收标准

- 网页列表、详情页与 App 对同一输入产出一致的标准名称。
- 当前生产全量 active 商品转换后无空名称；不会丢失容量、数字、GTX、SV/LT/AR、LiTRIC 等型号区分 token。
- 名称转换不得新增“同平台、不同商品 URL、相同标准名称”的歧义碰撞；现存真实同名商品需量化并区分于新增碰撞。
- 至少覆盖 LiTRIC、SuperLight、StormHood、DownWord、Arc'Word、Veilance、容量与性别后缀的回归样本。
- 定向测试、App 全部单测、TypeScript typecheck、Web guard 通过。
- 行为性改动必须完成生产式页面运行时验证：搜索、卡片、详情、购买 CTA 全链路名称一致。

## 已完成且已验证

- 已读取长任务协议正本并建立本任务档案。
- 已创建干净独立 worktree 和分支，未触碰用户 dirty worktree。
- 已建立 151 个型号族的共享命名运行时；根目录为正本，Expo 使用字节一致副本并由同步检查门禁防漂移。
- 网页列表、详情页和 App 已统一调用 `standardProductName`；名称保留性别、容量、数字和技术/版本 token，SSENSE 仅在品牌 URL 与型号族均确认时删除颜色前缀。
- SSENSE 抓取器改为精确品牌归一化和 Arc'teryx URL 双校验；同步前预检、数据质量检查和三端可见性过滤形成三层拦截。
- 初始生产 active 全量审计为 5,716 输入、5,715 接受、1 拒绝；该拒绝项是历史 Marc Jacobs 行。完成隔离和新型号登记后的最终严格审计为 5,716 接受、0 拒绝、空名 0、未知型号族 0、关键 token 丢失 0、性别不一致 0。（来源：`node tools/audit_product_names.mjs --online --strict-source`）
- App 28/28 测试通过，TypeScript `tsc --noEmit` 通过；名称/审计运行时 5/5 Node 测试、完整 Python `unittest discover` 最终 127/127 通过。
- 本地浏览器运行时验证：总数 5,715；`Diene` 15 张卡均未被截断；Micon 搜索返回 32L/42L 两项，卡片、详情、提醒 data-name 一致且 CTA 指向对应 EVO；SSENSE Black/Navy 两色均显示 `Beta Insulated Jacket Men's`，Marc Jacobs 搜索为 0。
- 首次强制刷新 `31320538705` 证明 SSENSE 新抓 43/43 和同步成功，但历史行因 36 小时 PDP 200 宽限仍为 active；随后提交 `da80eec` 让已证实违反来源契约的 URL 立即隔离，而普通缺席商品继续保留宽限。
- 第二次强制刷新 `31321641710` 输出 `source_contract_quarantined=1`，经销商质量门 `OK`；严格名称门随后按预期拒绝新发现的合法型号 `AR-385a Harness Women's`。登记 `AR-385a` 后，最终在线严格审计恢复 `OK`，且默认 CI 输出已会打印未知型号名称和 URL。
- 最终经销商独立质量回读：441 行均为 active，Evo 256、REI 129、SSENSE 56，`[quality] OK`。生产共享运行时 SHA-1 与提交 `19cb5b1` 本地文件一致：`1119f8d333a064e62b0f3756b06f42129c2918fe`。
- 最终生产浏览器回读：总数 5,716；`Glam Mirror` 为 0；`AR-385a` 唯一结果显示 `AR-385a Harness Women's`；Micon 只返回 32L/42L，32L 详情 CTA 精确指向 EVO `263885-arc-teryx-micon-litric-32l-airbag-pack`。

## 下一步

- 无必须后续动作。后续新型号若未登记，计划刷新会 fail-closed，并直接打印型号名称与来源 URL；核准后加入共享注册表即可。

## 死路

- 初始假设“性别继续只由独立元数据展示”已被全量碰撞分析否定：该做法新增 78 组歧义，因此改为在标准名称中保留规范化性别。
- 通用多语言冠词/前缀删除不可继续使用：无词边界的 `Die` 规则会损坏合法型号 `Diene`，且当前 813 个生产原始名称均为英文。
- 系统 Python 初次运行完整爬虫测试时缺少 `scrapling` / `curl_cffi` / `camoufox`；改用一次性 Python 3.13 虚拟环境安装锁定 `requirements.txt` 后，完整 126 项测试均通过。最初的依赖缺失不是代码失败。
- 第一次刷新后，单纯依赖“列表缺席”不能立即下线污染行，因为近期 PDP 200 是普通商品的正确防误杀机制；将来源契约违规作为独立的确定性隔离条件后解决。
- 第二次刷新不是回归失败，而是新型号 fail-closed 生效：`AR-385a` 在本轮 REI 完整列表/PDP 核验中新增，登记为第 151 个型号族后最终全量审计通过。没有为让门变绿而放宽未知型号规则。

## 风险与回滚

- 风险：过度标准化可能合并不同容量、版本或季节商品。控制：保留原始字段、全量 token 保真和新增碰撞门。
- 当前生产严格源数据门与经销商质量门均已独立回读为绿色。最新完整刷新记录本身停在新型号 fail-closed；最终注册表提交后未再重复整轮约 22 分钟抓取，但同一生产数据已用最终代码运行完全相同的严格审计并通过。
- 回滚：单提交回退名称标准化代码；不涉及生产数据库写入或数据迁移。
