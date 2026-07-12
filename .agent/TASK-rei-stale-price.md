# TASK: REI 旧折扣价错误保活（更新：2026-07-12 05:40 EDT）

## Why（一句话）

修正 REI 242856 的旧 `$49.83` 折扣价，并让 REI PDP 复核、失败信号和单品新鲜度门能够阻止同类旧价继续显示。

## 当前状态：已完成

## 已确认事实

- REI PDP 242856 当前显示 `$200.00`，嵌入 SKU 数据的 `price.value` 与 `compareAt.value` 均为 200；来源：Lightsail Camoufox 真实页面读取。
- 修复前 Supabase `rei:242856` 为 sale 49.83 / original 200 / discount 75，最后更新时间 2026-07-08；来源：生产 Supabase。
- 最新 REI 搜索抓取只有 17–18 条，该商品不在列表中；Supabase stale buffer 保留了旧 active 行；来源：`dealers.log` 与 `dealers/results.json`。
- 每日 REI PDP 复核曾为 ok=0 / err=46，但 wrapper 吞掉核心失败；来源：Lightsail `revalidate.log`。
- 修复后生产 `rei:242856` 为 sale 200 / original 200 / discount 0，并写入价格历史；来源：生产 Supabase。
- REI 全量复核 46 条中 34 条成功、11 条发生价格修正，后 12 条受限流保护性跳过；来源：2026-07-12 手动生产复核。
- 新 72 小时单品质量门当前识别 5 条 REI stale active 行并返回失败；来源：生产 `check_data_quality.py --online`。

## 已完成且已验证

- 适配 REI 当前 buy-box 和嵌入 SKU `price/compareAt` 结构，只使用当前商品的 AVAILABLE 变体。
- REI 页面替换或短过渡页时等待完整 DOM，不把 2.7KB stub 当商品页。
- 旧折扣保留兜底限制为 MEC，REI 当前满价不会再被旧折扣覆盖。
- dealer 复核低于 70% 成功率时任务失败；REI 按最旧更新时间优先并默认 3 秒节流。
- server wrapper 不再吞掉复核失败；所有 dealer 质量门启用 72 小时 active 单品新鲜度检查。
- 27 个单元测试、Python 编译、shell 语法和 workflow YAML 验证通过。
- PR #13–#18 已合并；Lightsail 已部署到 `48b25be`。

## 未验证/后续观察

- 尚未观察下一轮定时 revalidate 的完整结果。
- 5 条超过 72 小时的 REI 行仍待站点限流解除后复核；当前质量门保持红色，不再伪装为健康。

## 边界

- PDP 读取失败、过渡页或限流时不更新生产价格。
- 不用推测价格覆盖生产；只有结构化 SKU 或明确 buy-box 价格成功解析后才写入。
- OCI 正执行 Outlet 全量 SKU，本次不并行启动 Camoufox 争用资源。
