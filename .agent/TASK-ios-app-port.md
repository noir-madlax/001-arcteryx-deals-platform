# 工单：把「值de / GearDrop」Web 前端移植成 iOS App（React Native + Expo）

> 执行者：codex ｜ 出单 + 复核：Claude Code ｜ 创建日期：2026-07-07
> 这份工单**自包含**：不依赖任何对话上下文，冷启动即可开工。
> 硬规则：**未读不引用**（没亲自读到的文件/字段不当事实）、**未跑不宣称**（没跑过只能说"已改未验证"）。

---

## 0. 一句话目标

把现有网站 `https://001.100app.dev`（户外装备多区域折扣比价，后端 Supabase）移植成一个 **Expo (React Native) iOS App**，第一版（MVP）能跑真实数据、三屏可用、含 1 个付费墙，面向**海外 App Store**。

---

## 1. 背景（self-contained）

- 产品：多品牌户外装备（当前主要 Arc'teryx）**全球 22 国 outlet + 经销商**折扣聚合 + 价格历史追踪。
- 后端：**Supabase**（PostgREST + Postgres）。前端只用 **anon key 只读**，写操作（价格提醒订阅）也走 anon key POST。
- 现有前端：纯 HTML/JS SPA（`index.html` 列表页 + `product-detail.html` 详情页），数据源**单一 = Supabase**（不读任何静态 JSON）。
- ⚠️ **不要参考 `miniprogram/`（微信小程序）的页面逻辑 / 信息架构 / 交互**——那套设计已被判定为差，本次要求**从头重新设计**（IA + 三屏 spec 见 §5）。小程序**唯一**可参考的是"同样的 Supabase 字段/查询怎么用"，页面结构一律不抄。
- 商业定位：**海外区为主**，英文名 **GearDrop**，中文区名 **值de**，slogan "Gear that's worth it."
- 品牌合规红线：App 名 / 副标题 / 关键词 **绝不出现** "Arc'teryx" / "始祖鸟" 商标；定位成"户外装备比价工具"，始祖鸟只是"收录品牌之一"。

---

## 2. 事实区（带来源，可直接用）

### 2.1 Supabase 配置（来源：`index.html` 第 ~40 行，anon key 本就公开在前端）
```
SUPABASE_URL  = https://bupqagkrcvrezjkdbald.supabase.co
SUPABASE_ANON = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHFhZ2tyY3ZyZXpqa2RiYWxkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NDU1NTMsImV4cCI6MjA5MjAyMTU1M30.oszdUJIEKMCvpD9XFzTYTCYXj078uwjzFx84tfStfRU
REST base    = ${SUPABASE_URL}/rest/v1
```
> anon key 只读 + 受 RLS 保护，放进客户端安全（现有网站/小程序已如此）。**严禁**把 service_role key 放进 App。

### 2.2 `products` 表字段（来源：本会话对 `/rest/v1/products?select=*` 实测）
```
id(int, PK)  sku_id(text, 稳定唯一键)  model(text)  full_name(text)  color(text)
sizes(text[])  size_stock(jsonb, {"M":"in_stock",...})  original_price(numeric)
sale_price(numeric)  discount_pct(int)  currency(text)  symbol(text)  gender(text: men/women/unisex)
region(text: us/ca/gb/de/... 13 个 outlet 区 + dealer 的 us/ca)  region_name(text 中文区名)
category(text 中文品类)  url(text 商品原始链接, 用于"去购买"跳转)  image_url(text 主图)
images(text[] 多图)  description(text)  last_updated(timestamptz)  created_at(timestamptz)
dealer(text: arcteryx_outlet/evo/mec/rei/ssense)  first_seen(timestamptz)
```
规模：约 6000 行。`dealer='arcteryx_outlet'` 约 5500 行（多区域），其余是经销商。

### 2.3 `price_history` 表（来源：本会话实测；anon 可读，已 GRANT）
```
id(bigint PK)  sku_id(text)  original_price(numeric)  sale_price(numeric)
discount_pct(int)  currency(text)  recorded_at(timestamptz)
```
约 68000+ 行，append-only。**这是产品数据护城河**（价格历史 = 付费墙核心）。

### 2.4 `price_alerts` 表（来源：`product-detail.html` 的 POST body + `check_price_alerts.py`）
anon 可 INSERT。字段：
```
email  sku_id  target_price  last_price_seen  currency  region
product_name  product_url  image_url  unsubscribe_token(uuid)  notified_at(nullable)
```
> ⚠️ **PII 风险**：该表含 email。当前 anon 可 SELECT *（本会话确认过，目前表空）。App 里**只做 INSERT，绝不 SELECT 别人的行**。后端 RLS 收紧另开工单，不在本工单范围。

### 2.5 前端取数 / 交互逻辑（来源：`index.html` / `product-detail.html`，需照抄语义）
- **列表取数**：`db.from('products').select('*').range(offset, offset+999)` 分页 1000，拼全量（`offset>50000` 保险停）。
- **筛选维度（state）**：`q`(搜索) `platform`(dealer) `region` `gender` `category` `series` `sort`(默认 `discount_desc`)。
- **价格历史取数**：
  ```
  GET ${REST}/price_history?select=sale_price,original_price,recorded_at
      &sku_id=eq.<SKU>&recorded_at=gte.<90天前ISO>&order=recorded_at.asc
  headers: apikey / Authorization: Bearer <ANON>
  ```
  取回后把"当前价"当作今天的节点补进数组再画图。
- **需照搬的纯函数**（在 `index.html` / `product-detail.html` 里，移植成 TS util）：
  - `cleanName()`：去掉商品名里的 "Arc'teryx" 前缀 / "- Men's" 后缀
  - `inferCategory(name, url)`：category 为空/"其他"时的兜底分类规则（正则表）
  - `releaseSeason(p)`：从 image_url 的 `/F25-` `/S22-` 码解析"发售季度"（正则 `/([FSWfsw])(\d{2})(?=[-_/])/`，F/W=秋冬 S=春夏）
  - 价格展示：sale/original(划线)/discount_pct，货币符号用 `symbol` 字段
  - `platformKey()` / dealer→展示名映射

---

## 3. 技术栈（锁定，别自选）

- **Expo (managed workflow)** + React Native + **TypeScript**
- 取数：`@supabase/supabase-js`（v2）——直接复用 2.1 的 URL/anon key
- 导航：`expo-router`（file-based）
- 图表（价格历史）：`react-native-svg` 手绘折线（跟现有 web 版一样是 inline SVG，别引重库）；或 `victory-native`，二选一，优先 svg 手绘保持轻量
- 本地存储（收藏）：`@react-native-async-storage/async-storage`
- 推送：`expo-notifications`（接 APNs）
- 打包/提审：**EAS Build + EAS Submit**（不手动碰 Xcode）
- 状态：React hooks + Context 足够，别上 Redux

---

## 4. 仓库位置

- 在**现有仓库**新建 `app/` 目录（Expo 项目根）。理由：跟 Supabase schema、小程序放一起，后端改动一处同步。
- `app/` 自带独立 `package.json` / `node_modules` / `.gitignore`（node_modules 不提交）。
- 不动仓库现有任何文件（`dealers/`、`index.html`、`miniprogram/` 等）。

---

## 5. MVP 范围 + 重新设计规范（本工单只做这些）

> 本次是**重新设计**，不是照搬旧 UI。Claude 已出可视化 mockup 并经用户认可，下面是该设计的落地 spec。核心理念一句话：**信号优先（signal over catalog）——每个商品都要说清"为什么现在值得看"，而不是一个静态价签。**

### 5.0 三条设计原则（贯穿所有屏，codex 必须遵守）
1. **信号 > 目录**：每张卡片除了价格，必带一句"信号句"说明当前状态（跌了多少 / 是不是史低 / 平稳）。见 §5.4 信号文案规则。
2. **详情页围绕"该不该买"造**：价格历史图 + 一句买入判断（verdict）是详情页的主角，不是附属。
3. **原生手感**：底部 Tab 导航、下拉刷新、骨架屏 loading、筛选用**横滑 chip**（不是弹窗墙）、保存/提醒有轻 haptic 反馈。

### 5.1 导航：底部 3 Tab（`app/(tabs)/`，expo-router file-based）
| Tab | 文件 | 作用 |
|---|---|---|
| **Deals**（发现，默认） | `(tabs)/index.tsx` | 排序过的折扣流 + 史低置顶 |
| **Watchlist**（关注） | `(tabs)/watchlist.tsx` | 收藏 + 价格提醒，带"自收藏以来"状态 |
| **Me**（我的） | `(tabs)/me.tsx` | Pro 状态、通知设置、关于（本期简版即可）|

详情是 push 屏（`app/product/[skuId].tsx`），不是 Tab。

### 5.2 屏规范

**① Deals `(tabs)/index.tsx`**
- 顶部：标题 "Deals" + 搜索图标（点开搜索 `q`）
- **横滑 filter chip 行**：Region / Category / Gender / Sort（默认 `discount_desc`）。选中态用 accent 底色，未选 hairline 边。
- **Hero 区**："New all-time low" 标签 + 1 张最有价值的史低商品卡（用 price_history 判断，见 §5.4）
- **折扣列表**：卡片 = 主图(圆角) + cleanName 名 + **信号句** + sale 价(`symbol`+价, danger 色) + original 划线价 + 折扣 badge `-XX%`
- 数据新鲜度：`last_updated` >3 天的商品，信号句区域标注"X 天前"（web 版有此逻辑，语义照搬）
- 交互：下拉刷新、点卡片 → 详情屏、列表懒加载（先加载头部 ~500 条渲染，其余分页后台补，别一次性卡 6000 条 UI）

**② 详情 `app/product/[skuId].tsx`**（转化核心，按 mockup 的纵向顺序）
1. 返回 chevron + 收藏 heart（右上）
2. 商品图（`images` 可横滑轮播）
3. 名（cleanName）+ 色 + 性别
4. 价格区：sale(大, danger) / original(划线) / `-XX%` badge
5. ⭐ **价格历史折线图**：inline SVG（同 web 版风格），画折线 + **虚线标史低** + 当前点标红。取数见 §2.5。
6. ⭐ **买入判断 verdict**（一句，带底色 pill）：绿=可入 / 中性=再等等。判断规则见 §5.4。
7. **跨区比价条**：`Also cheaper: UK £142 · DE €165` —— 同 model 查其他 region 的更低价（用现有 products 数据，同 `model` 不同 `region`，折算展示原币种即可，本期**不做汇率/落地价计算**，只并排列出）
8. CTA：`Alert`（设提醒）+ `Buy`（accent）
   - Buy → **收口到 `openBuyUrl(url)` 单一函数**（`expo-web-browser` 打开 `url`；为后续联盟返佣包一层预留，本期直跳）
   - Alert → 填目标价 → INSERT `price_alerts`（见 §2.4，**只 INSERT，绝不 SELECT 别人的行**）

**③ Watchlist `(tabs)/watchlist.tsx`**
- AsyncStorage 存收藏 sku_id 列表
- 每行：主图 + 名 + **"自收藏以来"状态**（`↓22% since you saved` 绿 / `No change since saved` 中性；对比收藏时存的价格快照）+ 当前价
- 已设提醒的商品显示提醒行（`Alert at $150`）
- 底部内嵌 Pro 引导（"Unlimited alerts with Pro"），点开 paywall

**④ Me `(tabs)/me.tsx`**（本期简版）
- Pro 状态（读 `usePro()`）+ "Upgrade to Pro" 入口（打开 paywall 屏）
- 通知开关（本地）、关于/隐私政策链接

### 5.3 需照搬的纯函数（移植成 `app/lib/*.ts`，来源见 §2.5）
`cleanName` / `inferCategory` / `releaseSeason` / 价格展示（symbol+划线）/ `platformKey`(dealer→展示名)。

### 5.4 信号文案规则（signal copy —— 这是"信号优先"的落地，codex 按此实现）
对每个商品，用它的 `price_history`（近 90 天，同 §2.5 查询）算出信号，优先级从高到低取第一个命中：
1. **史低**：当前 sale ≤ 历史最低 → `All-time low` / Hero 用 `New all-time low`（绿）
2. **近期低点**：当前 sale ≤ 近 90 天最低 → `90-day low`（绿）
3. **刚降价**：当前 sale < 最近一条历史记录的 sale → `↓ $X today`（绿，X=差额）
4. **平稳**：其余 → `Steady · not a low`（中性灰）
5. **数据不足**（history <2 点）→ 不显示信号句，只显示折扣

**买入 verdict（详情页）**：史低/90天低 → `Good time to buy — at/near all-time low`（success 底）；否则 → `Often cheaper — consider waiting`（中性底）。

### 5.5 原生功能（满足 App Store 审核 4.2「不能是纯网页壳」）
- ✅ 原生列表/详情/图表（RN 组件 + SVG，**不是 WebView**）
- ✅ 本地收藏（AsyncStorage）+ "自收藏以来"价格 diff
- ✅ 价格到价提醒：`expo-notifications` 先打通**本地通知**链路（APNs 远程推送留第二期）
- ✅ 下拉刷新、骨架屏、haptic 反馈

---

## 6. 计费点（MVP 只做 1 个付费墙）

### 免费 vs Pro 对照（本期只实现 ★ 的门）
| 功能 | Free | Pro |
|---|---|---|
| 浏览当前折扣 / 搜索 / 筛选 | ✅ | ✅ |
| ★ 价格历史曲线 | 只看**近 30 天** | **全部历史 + 跨季对比** |
| ★ 历史最低价信号（"5 年最低 / 90 天最低"badge） | ❌ | ✅ |
| 本地收藏 | ✅（上限 20） | 无限 |
| 价格提醒 | 1 个 | 无限（下一期）|
| 即时推送 | 每日 | 即时（下一期）|
| 跨区落地价计算器 | ❌ | ✅（下一期）|

### 本期实现
- 详情屏价格历史图：Free 只渲染最近 30 天数据点 + 图上盖一层"升级看完整历史 + 史低信号"的模糊遮罩 CTA。
- "史低 badge"（对比 price_history 最低值）Pro 才显示。
- **付费墙用 stub**：先做 `usePro()` hook（读本地一个 flag，暂时可手动切 true/false 测试两种态），**真实 Apple IAP 接入留下一期**（需要 Apple Developer 账号，属用户侧阻塞）。
- 定价文案（写死在 paywall 屏，暂不接支付）：`Pro $3.99/月 · $23.99/年 · Lifetime $49.99`。

---

## 7. 验收标准（codex 自测 + Claude 复核都按这个跑）

1. `cd app && npx expo start` 能起，手机 Expo Go 扫码能打开，**无红屏报错**。
2. **底部 3 Tab**（Deals / Watchlist / Me）可切换，Deals 为默认。
3. Deals 屏：真实加载 ≥ 5000 条 Supabase 商品；默认按折扣降序；横滑 filter chip 可切 region（切 de 商品变欧元价 `symbol=€`）；搜 "beta" 有结果；**卡片显示信号句**（史低/90天低/↓$X today/Steady 之一，来自真实 price_history）；顶部有 "New all-time low" hero。
4. 详情屏：点商品进入，显示价格历史折线（真实 price_history，非 mock）+ 虚线史低 + **买入 verdict 一句** + **跨区比价条**（同 model 其他 region 更低价）；`usePro()=false` 只显示 30 天 + 遮罩，`=true` 显示完整曲线 + 史低 badge。
5. Watchlist：收藏后 kill App 重开仍在（AsyncStorage 持久化）；每行显示"自收藏以来" price diff。
6. 价格提醒：填目标价提交 → Supabase `price_alerts` 新增 1 行（anon key INSERT，2xx）；本地通知链路能触发一条测试通知。
7. "Buy"：点击经 `openBuyUrl(url)` 用系统浏览器打开该商品 `url`。
8. `npx tsc --noEmit` 无类型错误；`npx expo-doctor` 无致命问题。
9. 提交前 `app/` 下 `node_modules` 未被 git add。

> 交付时在工单末尾"进度/交付"区**贴出每条验收的实际运行结果**（截图或日志），未跑过的不许写"通过"。

---

## 8. 明确不做的事（scope guard）

- ❌ 不接真实 Apple IAP / StoreKit（等 Apple Developer 账号，另开工单）
- ❌ 不接 APNs 远程推送（本期只做本地通知打通链路）
- ❌ 不接联盟返佣链接改写（预留 `openBuyUrl()` 收口即可）
- ❌ 不改任何后端 / Supabase schema / RLS（price_alerts 的 PII 收紧另开工单）
- ❌ 不动仓库现有文件（`dealers/`、`*.html`、`miniprogram/`、workflows）
- ❌ 不做 Android 适配（本期只 iOS，但 Expo 本就跨平台，别为 Android 额外花时间）
- ❌ 不做多语言 i18n（先中文，英文文案第二期）

---

## 9. 假设区（需 Claude/用户确认，codex 先按默认走）

- [默认] 代码放现有仓库 `app/` 目录（未经用户明确拍板，但 Claude 已推荐此方案）。
- [默认] 价格历史图沿用 web 版的 inline SVG 手绘风格（轻量优先）。
- [默认] Free 收藏上限 20、价格历史 30 天——具体数字可后续调，先按此实现。
- [默认] Bundle ID 用 `dev.100app.geardrop`（待用户注册 Apple 账号后可能调整，先占位）。
- [待确认] App 图标 / 启动图 / 截图素材由用户提供或后续单独做（本期用占位图）。

---

## 10. 进度 / 交付（codex 在此追加）

<!-- codex: 每完成一个阶段在此记录：做了什么、跑了什么验收命令、结果。未跑不宣称。 -->
