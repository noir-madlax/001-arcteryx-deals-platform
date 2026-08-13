# GearDrop 下一版本 ASO 研究与决策

- 研究日期：2026-08-14
- 市场：iOS App Store，美国为主；同步覆盖简体中文、德国、法国、日本本地化
- 交付目标：下一 App 版本，不修改当前审核版本
- 证据方法：Apple 官方开发者文档、公开 App Store 商品页、公开 iTunes Search API
- 限制：公开搜索结果只能作为相关性代理，不能当成关键词搜索量

## 结论

GearDrop 不应与大型综合优惠 App 拼“优惠券最多”，也不应与单一商家 App 拼交易闭环。最清晰的增长位置是：**户外装备专用的跨地区价格历史与买入判断工具**。

下一版本使用名称承接 `outdoor deals`，副标题承接 `price tracker` 与 `buy signals`，关键词补足装备、活动和跟踪意图；首三张图依次证明“发现降价 → 判断真假低价 → 跨地区比较”。

## 当前搜索结果线索

2026-08-14 公开 iTunes Search API 的美国区结果：

| 查询 | 前列结果 | 可用判断 |
|---|---|---|
| `price tracker` | Keepa、AnyTracker、ShopSavvy | `price tracker` 是明确功能意图，但竞争强 |
| `price drop alerts` | Price Drop Alerts、BuySense、dips | `drop` + `alert` 是可组合的次级意图 |
| `outdoor gear deals` | REI、Academy、品牌直营、Backcountry | 结果以零售商为主，独立多商家价格工具存在定位空位 |
| `hiking gear deals` | REI、Backcountry、AllTrails | 活动词会混入内容/导航 App，适合放关键词而非主承诺 |
| `ski gear deals` | OnTheSnow、Backcountry、REI | `ski` / `snowboard` 有季节性，可放关键词与自定义产品页 |
| `shopping deals` | Slickdeals、Flipp、DealSeek | 过于宽泛，不应作为 GearDrop 主战场 |

查询入口示例：[price tracker](https://itunes.apple.com/search?term=price%20tracker&country=us&entity=software&limit=10)、[outdoor gear deals](https://itunes.apple.com/search?term=outdoor%20gear%20deals&country=us&entity=software&limit=10)、[price drop alerts](https://itunes.apple.com/search?term=price%20drop%20alerts&country=us&entity=software&limit=10)。

## 竞品位置

| 产品 | 商店定位 | GearDrop 应避开的正面竞争 | GearDrop 的差异点 |
|---|---|---|---|
| [Keepa](https://apps.apple.com/us/app/keepa-price-tracker/id1518541385) | Amazon 价格历史与提醒 | 大规模单平台历史数据 | 户外专用、多来源、多地区 |
| [ShopSavvy](https://apps.apple.com/us/app/shopsavvy-shopping-assistant/id338828953) | 广泛零售商比价、条码和购买建议 | 通用品类覆盖与扫描 | 不需要先扫描；直接浏览户外折扣与价格信号 |
| [Slickdeals](https://apps.apple.com/us/app/slickdeals-deals-discounts/id584632814) | 社区优惠、优惠券和提醒 | 社区规模与全品类促销 | 更少噪音；用历史数据判断是否真低价 |
| [REI](https://apps.apple.com/us/app/rei-co-op-shop-outdoor-gear/id404849387) | 单一户外零售商购物闭环 | 会员、库存、结账 | 独立比较多个地区和来源 |
| [Whisprice](https://apps.apple.com/us/app/whisprice-smart-price-tracker/id6748636341) | 用户粘贴链接的全网关注清单 | 任意 URL 跟踪 | App 内已有可搜索户外目录和低价信号 |

## 元数据决策

Apple 当前说明：名称与副标题各最多 30 字符，推广文本最多 170 字符，描述最多 4000 字符，关键词最多 100 bytes；关键词应避免重复、类别词、竞品名和无授权商标。名称、副标题、关键词和公司名参与 App Store 搜索，推广文本不参与关键词排名。

权威来源：[Creating Your Product Page](https://developer.apple.com/app-store/product-page/)、[App information](https://developer.apple.com/help/app-store-connect/reference/app-information/app-information)、[Platform version information](https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information)。

### 英文主字段

```text
Name: GearDrop: Outdoor Deals
Subtitle: Price Tracker & Buy Signals
Keywords: gear,sale,discount,watchlist,alert,history,hiking,ski,snowboard,camping,climbing,outlet,compare,drop
```

英文关键词为 100 UTF-8 bytes。名称/副标题覆盖高意图组合后，关键词不再重复 `outdoor`、`deals`、`price`、`tracker`，而是补齐用途、活动和跟踪词。

排除项：

- 商家/品牌商标与竞品名：合规风险，且不属于产品自有品牌。
- `app`、`shopping`：Apple 明确建议避免 App/类别词。
- `coupon`、`cashback`：当前产品不提供，不用不相关流量换低转化。
- “best”“guaranteed savings”等绝对化承诺：没有可持续证明。

五语完整字段保存在 `app/store-metadata/next-version.json`，并由机器检查 byte/字符限制。

## 截图转化路径

Apple 说明无预览视频时，搜索结果通常首先展示前 1–3 张截图，因此下一版本固定为：

1. 今日户外降价：先回答“这里有什么”。
2. 真假低价判断：再回答“为什么值得点开”。
3. 跨地区价格：最后证明差异化能力。

后续三张展示关注清单、Pro 完整价格历史、地区/币种/语言。旧的隐私页截图属于审核证明，不适合作为主要转化位，下一版本用 Display Preferences 替换。

Apple 允许最多 10 张图，并建议每张突出一个核心利益；完整规则见 [Creating Your Product Page](https://developer.apple.com/app-store/product-page/) 与 [Upload app previews and screenshots](https://developer.apple.com/help/app-store-connect/manage-app-information/upload-app-previews-and-screenshots)。

## 本地化

商店元数据与 App 已支持语言对齐：英语、简体中文、德语、法语、日语。Apple 说明本地化关键词可用于相应国家/地区的搜索；没有匹配语言时才回退到主语言。[Localize app information](https://developer.apple.com/help/app-store-connect/manage-app-information/localize-app-information)

本地化不是英文直译：德语强调 `Preisvergleich / Preisalarm`，法语强调 `suivi de prix / alertes`，日语强调 `価格履歴 / 値下げ通知 / 買い時`，中文强调 `比价 / 价格历史 / 降价提醒`。

## 发布与监测

下一版本应用前：

1. 读取当前 live 版本与审核状态，确认新版本可编辑。
2. 保存发布前 28 天的 App Store impressions、product page views、downloads、conversion rate，并按 territory / source 拆分。
3. 从最终签名 build 重截五语素材，上传后逐字段和逐截图读回。
4. 元数据编辑与提交审核分开授权；不要修改已在审核中的版本。

上线后：

- 第 7 天：只看错误、异常国家/语言和明显转化崩塌，不因小样本频繁改词。
- 第 14 天：比较 Search 来源 product page conversion 与基线，标记方向，不急于宣布胜负。
- 第 28 天：按 locale / territory 复盘 impressions、downloads、conversion、Pro paywall visits；决定关键词微调。
- 有足够流量后，再用 Apple Product Page Optimization 单独测试截图顺序；一次只测试截图故事，不同时重写全部文本。

Apple 的 Product Page Optimization 可测试最多三个替代产品页版本，指标在 App Analytics 中读取：[Product Page Optimization](https://developer.apple.com/app-store/product-page-optimization/)。美国区上线后还应检查 App Store Connect 自动建议的 App Tags；Apple 当前说明 Tags 只在美国展示：[Manage app tags](https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-tags/)。

## 未验证边界

- 未获得 Apple Ads 的关键词流量/竞价数据，因此没有声称精确搜索量。
- 未修改 App Store Connect，也未验证当前 live 审核状态。
- 未生成下一版本最终截图，因为最终签名 build 和对应 StoreKit 状态尚不存在；当前只冻结了六槽位和五语文案。
