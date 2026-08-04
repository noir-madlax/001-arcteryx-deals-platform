# TASK: GearDrop 首页图片修复（更新：2026-08-04 04:05 EDT）

## Why（一句话）
让当前 TestFlight Build 2 的首页重新显示真实商品图，并阻止 SSENSE 图片模板占位符再次进入生产数据。

## 当前状态：已完成（代码与生产数据均通过独立回读）

## 已确认事实
- 当前工作树基于最新 `origin/main` `08f5b2d175220e75d5a516f051193008af05612e`，分支为 `codex/fix-home-images-20260804`；来源：本轮 `git fetch`、`git rev-parse HEAD`。
- App 启动时直接分页读取生产 Supabase `products`，首页默认美国区并按折扣降序；来源：`app/lib/supabase.ts:17-30`、`app/app/(tabs)/index.tsx:23-33,54-77`。
- 生产只读复现为总行数 5,789、美国区 752；54 条图片 URL 含字面量 `__IMAGE_PARAMS__`，均为 SSENSE，美国区折扣前 10 条有 7 条命中；来源：本轮 Supabase anon REST 200 分页读回与本地确定性统计。
- 代表性坏 URL `https://res.cloudinary.com/ssenseweb/image/upload/__IMAGE_PARAMS__/261340F110002_1.jpg` 实测 HTTP 404；将占位符替换为 `w_480,q_auto` 后同一资源 HTTP 200 `image/jpeg`。Arc'teryx Imgix、REI、Evo Shopify 代表图也均为 HTTP 200；来源：本轮公网 GET 原始响应。
- SSENSE 解析器当前把 JSON-LD `image` 原样复制，`dealers/supabase_sync.py` 再原样写入 `image_url` 和 `images`；来源：`dealers/ssense.py:286-296`、`dealers/supabase_sync.py:145-162`。
- `DealCard` 只取 `product.image_url || product.images[0]`，第一次加载失败后切换到文字占位；首页 Hero 只排除 REI 域名，非空的 SSENSE 坏 URL 会被当作稳定图；来源：`app/components/DealCard.tsx:18-33`、`app/app/(tabs)/index.tsx:84-92,161-163`。

## 假设（未验证；验证后移入上区）
- 无。

## 已完成且已验证
- 已完成根因复现；原坏 URL 404，确定性参数替换后的 URL 200。
- SSENSE parser 会把精确 Cloudinary 模板前缀规范化为 `w_480,q_auto`，普通 URL 与 `None` 保持不变。
- 线上质量门现在读取 `image_url`/`images`，会拒绝活跃商品中的 `__IMAGE_PARAMS__`；定向 34 测试和全量 117 测试均通过。
- 已将 `dealers/results.json` 的 44 个模板值机械规范化，仓库内剩余占位符为 0。
- Supabase 项目身份读回为 `008 / bupqagkrcvrezjkdbald`、状态 `ACTIVE_HEALTHY`；写前查询为 54 行、全部 SSENSE、54 个不同 SKU。完整 before-state 保存在 `/private/tmp/geardrop-ssense-before.0W1fIz/affected-54.json`。
- 生产事务仅更新 `image_url`/`images`，并在事务内断言目标数为 54 且无非 SSENSE 行。写后目标数为 0，规范化行数为 54；SKU digest 写前写后均为 `5f9ec73813ff79375d6534b8f1f07648`，非图片字段 digest 均为 `2f924a7eae7cb2b4a72febe0d2daf7cf`。
- App 匿名权限独立读回：SSENSE 57 行、模板占位符 0、规范化 54、非图片字段逐行规范化哈希不变；美国区折扣前 10 行占位符 0、9 行有图片；代表性修复图 GET 为 `200 image/jpeg`、32,271 bytes。
- 工作流同款线上门禁命令读回 427 行（evo 269、rei 101、ssense 57）并返回 `[quality] OK`。

## 验收标准
1. SSENSE parser 单测证明 `__IMAGE_PARAMS__` 被规范化为可用 Cloudinary 变体；普通 URL 保持不变。
2. 数据质量门会拒绝活跃商品中的未解析图片模板，定向测试与完整测试通过。
3. 生产写前精确读回受影响 SKU 为 54 并保存 before-state；写后同一过滤条件为 0，非目标字段不变。
4. 默认美国区折扣前 10 条不再包含模板占位符；至少一条原坏 URL 新地址实时 GET 返回 200 `image/*`。
5. 修复提交进入 `origin/main`，以保证后续爬虫不会重新写回坏值。

## 下一步
- 无；本文件随修复提交进入 `origin/main`。

## 死路
- CodeGraph MCP 工具在本轮可用工具集中未暴露；`.codegraph/` 存在，因此改用已读的精确文件与字面量搜索继续，不重新初始化索引。
