# 认知狩猎 - 产品规格说明书

> 本文档是产品设计的唯一事实来源，始终反映最新状态。机制定义 + 体验设计。
>
> **定位**：产品层。与 `PHILOSOPHY.md`（为什么做）配合阅读，与 `TECH.md`（怎么实现）联动修改。

---

## 一、v0.1 已上线基础功能

以下功能是系统起点，v0.24 保留并增强。

| 功能 | 状态 | 说明 |
|------|------|------|
| 灵感采集（倍数阶梯） | ✅ 保留 | 每日第1条1.0x / 第2条1.5x / 第3条2.0x / 第4条及以后0.2x |
| 基础星点 | ✅ 保留 | 10星点 |
| 标签规则 | ✅ 保留 | 必填至少一个标签，不限数量 |
| 周回顾 | ✅ 保留 | 200星点 |
| 月度战报 | ✅ 保留 | 500星点 |
| 内容输出 | ✅ 保留 | 750-1000星点，最多5次/轮 |
| 兑换系统（基础版） | ✅ 保留 | 消费券汇率1.0，基金汇率1.0+0.5基础奖励 |
| 勋章系统 | ✅ 保留并扩展 | 灵光乍现、周常猎人（config驱动） |
| 惩罚机制 | ✅ 已废除 | v0.22 废除，改为连续天数递增奖励 |

---

## 二、v0.24 当前功能

### 2.1 灵感采集

| 项目 | 规格 |
|------|------|
| 每日采集倍数 | 第1条1.0x / 第2条1.5x / 第3条2.0x / 第4条及以后0.2x |
| 基础星点 | 10星点（`config.yaml` 可配置） |
| 标签要求 | **必填至少一个标签**，不限数量 |
| 标签规则 | 连接力计算只取前5个，两两配对更新 `tag_graph` |
| 跨界采集加成 | 单篇笔记使用 ≥2 个**不同领域**标签，额外 +5 星点 |

**公正性保障**：标签由 AI 生成、用户粘贴。AI 不知道连接力规则，用户无法刻意操纵跨界组合。

---

### 2.2 任务与奖励

| 任务类型 | 奖励星点 | 触发时间 | 说明 |
|---------|---------|---------|------|
| 周回顾 | 200 | 次周任意时间 | 系统生成素材文件，用户编辑后提交 |
| 月度战报 | 500 | 次月任意时间 | 系统生成素材文件，用户编辑后提交 |
| 内容输出 | 750-1000 | 随时 | 每次发布，最多 5 次/轮 |

**回顾流程**：
1. 用户点击触发按钮
2. 后端扫描上一周期所有灵感笔记
3. 生成素材文件存入 Inbox/
4. 返回文件链接和内容预览
5. 用户撰写核心洞察并提交
6. 发放星点，更新完成状态

---

### 2.3 能力值系统

**设计意图**：引导用户从发散采集转向收敛思考。奖励密度而非广度——在已有标签之间反复缝合，而非不断开新标签。

**命名**：保留「能力值系统」作为模块名称，当前 v0.24 仅实现「连接力」一个维度。

#### 2.3.1 连接力（当前实现）

**计算公式**：

```
连接力 = 图密度 × 100 × log₂(节点数 + 1) × (跨界笔记占比 + 0.1)
```

| 因子 | 含义 |
|------|------|
| 图密度 | 标签之间实际连线占最大可能连线的比例 |
| × 100 | 把 0~1 的密度映射到常规刻度 |
| log₂(节点数+1) | 标签种类越丰富，连接力越高 |
| 跨界笔记占比 + 0.1 | 跨界笔记越多，连接力越高 |

**数值范围**：0.1 ~ 50

**星点奖励触发**：

| 连接力阈值 | 奖励 | 说明 |
|-----------|------|------|
| ≥ 5 | +50 星点 | 首次跨界连接 |
| ≥ 20 | +100 星点 | 跨界网络初具规模 |
| ≥ 50 | +200 星点 | 知识网络高度融合 |

**v0.24 规则**：
- 连接力**后台独立计算**，每次采集后更新
- 每个阈值**每赛季只触发一次**，赛季结算后重置触发状态
- **前端不展示连接力数值**，达到阈值时 Toast 提示
- 连接力是推动星点增长的**后台引擎**，而非直接展示的用户指标

#### 2.3.2 v0.5 前端展示计划

**能力面板内容**：展示「累计星点 + 当前档位增益 + 下一档位门槛」，而非连接力数值。

**用户看到的示例**：
> "你当前累计星点 1200，享受第 4 条倍率 0.4、基金加成 5%、发布下限 850"

**星点里程碑档位**（v0.5 实现）：

| 累计星点 | 增益效果 |
|---------|---------|
| ≥ 500 | 解锁称号「初露锋芒」 |
| ≥ 1000 | 第4条采集倍数 0.2 → 0.4 |
| ≥ 2000 | 内容输出奖励下限提升至 850 |
| ≥ 3000 | 基金加成额外 +5% |

**设计原则**：能力值系统的「能力」体现在**星点档位增益**上，连接力始终作为后台引擎运作，不直接向用户展示数值。

---

### 2.4 赛季系统

| 项目 | 规格 |
|------|------|
| 默认长度 | **15 天**（可配置） |
| 起始日期 | 每月1日、15日、16日至本月最后一日 |
| 自动开启 | 是 |
| 星点上限 | 每赛季 3000 星点 |
| 软重置比例 | 结算时保留 50% 进入下赛季 |

**赛季起始规则**：
- 1-14日 → 赛季从本月1日开始
- 15日 → 赛季从15日开始
- 16日至月底 → 赛季从16日开始

**赛季结算**：
- 冻结当前赛季数据，存入历史
- 生成赛季结算报告（含"致未来自己"段落）
- 重置赛季计数器（星点、活跃天数等）
- **不重置**：连续天数、能力值、基金池（终身累积）
- 下赛季结算时对比上赛季预测，建立连续性

**赛季主题系统**：标记为 v0.3 延展功能，当前版本不激活。

---

### 2.5 标签宇宙

| 功能 | 状态 |
|------|------|
| 标签云 | ✅ |
| 标签排行榜 | ✅ |
| 点击查看关联笔记 | ✅ |

- 标签云：字号按使用频次 `log(count+1)` 映射，颜色按共现连接度映射
- 点击标签 → 弹窗展示标签信息和关联笔记列表
- 关联标签可跳转，形成探索流

---

### 2.6 兑换系统

#### 2.6.1 兑换规则

- 用户每次兑换时自行选择路径（基金或消费券），无每周固定选择限制
- 所有星点兑换的增益减益均为**加减关系**（非乘除关系）

**基础汇率**：

| 路径 | 基础倍率 | 常设基础奖励 | 最终基础汇率 |
|------|---------|-------------|------------|
| 消费券 | 1.0 | 0 | 1.0 |
| 基金 | 1.0 | 0.5 | 1.5 |

- 基金基础奖励 0.5 为常设奖励，任何情况下都有，与其他加成叠加

#### 2.6.2 连续选择奖惩

| 连续选择 | 基金用户 | 消费券用户 |
|---------|---------|-----------|
| 连续 2 周 | 汇率 +0.05 | 汇率 -0.05 |
| 连续 4 周 | 汇率 +0.10 | 汇率 -0.10 |
| 连续 8 周 | 汇率 +0.15 | 汇率 -0.15 |
| 中断（换路径） | 汇率回到 1.0 | 汇率回到 1.0 |

**计算公式**：

- 消费券最终汇率 = 1.0 + 连续选择减益（负值）
- 基金最终汇率 = 1.0 + 0.5(基础奖励) + 连续选择加成 + 基金加成

#### 2.6.3 兑换锁定

- **动态锁定**：每日限制兑换一次，每日24时兑换次数重置
- **额度门槛**：基金兑换最低 500 星点

#### 2.6.4 镜像对比

每次兑换确认页**强制展示**三层信息：

**选消费时**：
- 等值对比：消费额度 vs 基金额度
- 时间维度：基金未来增值预估 vs 消费品折旧
- 累计损失：本周/本月消费损失总额

**选基金时**：
- 等值对比：基金额度 vs 消费额度
- 累计克制收益：连续选择基金的增值累计

#### 2.6.5 基金池

- `fund_pool` 与 `available_star` 分离存储
- 基金池内星点不可逆向转回消费券
- `coupon_pool` 记录消费兑换累计星点

---

### 2.7 连续加成

废除惩罚机制，改为连续天数递增奖励。中断后加成归零但基础收益不变。

| 连续天数 | 加成 |
|---------|------|
| 7 天 | 每日第1条采集额外 +10% |
| 30 天 | 每日第1条采集额外 +30% |
| 90 天 | 每日第1条采集额外 +50% |

**设计意图**：不是威胁（"不做就打你"），而是诱惑（"做了就有奖励"）。压力来自内部而非外部。

---

### 2.8 三层反馈体系

#### 2.8.1 微观反馈（采集瞬间）

每次采集成功，前端反馈：
1. **行为确认**：笔记标题 + 今日第N条
2. **连接增量**：本次产生的新标签连接（如有）
3. **能力值更新**：采集力、连接力、输出力变化
4. **相似笔记**：基于标签重叠的关联笔记（最多3条）

#### 2.8.2 中观确认（能力值与周期回顾）

- 能力值面板 + 最近7天变更日志
- 周回顾/月战报中的一句话数据叙事
- 峰值时刻高亮（最佳连接、最长笔记、最跨界灵感）

#### 2.8.3 宏观推演与预测

- **长期推演仪表**：基于当前速度，预测6个月后的笔记数、连接数、基金价值
- **赛季结算"致未来自己"**：赛季末生成预测，下赛季结算时对比回顾

---

### 2.9 勋章系统

所有勋章统一由 `config.yaml` 的 `medals` 配置表驱动，无需修改引擎代码。

**当前勋章配置**：

```yaml
medals:
  - id: "first_triple"
    name: "灵光乍现"
    icon: "💡"
    trigger: "event"
    event: "daily_capture_count"
    condition: "count >= 3"
    once: true

  - id: "weekly_hunter"
    name: "周常猎人"
    icon: "🏹"
    trigger: "event"
    event: "weekly_review_streak"
    condition: "streak >= 4"

  - id: "link_master"
    name: "连线大师"
    icon: "🕸️"
    trigger: "event"
    event: "monthly_report_cross_domain"
    condition: "count >= 3"
    once: true

  - id: "link_novice"
    name: "连线新手"
    icon: "🔗"
    trigger: "ability"
    ability: "link_power"
    threshold: 5
```

**勋章触发类型**：

| 类型 | 说明 |
|------|------|
| `event` | 特定事件触发 |
| `ability` | 能力值达到阈值时触发 |

---

### 2.10 前端界面

**当前布局**：单页长滚动结构

**主要板块**：
- 灵感捕获区：textarea + 标签输入 + 捕获按钮
- 仪表盘：总星点、今日战果、连续天数、获取记录按钮
- 勋章墙：展示所有已获得勋章
- 兑换中心：消费券/基金兑换入口、赛季兑换情况、水位进度条
- 赛季信息：赛季名称、进度、结算入口

**获取记录**：
- 仪表盘右上角「获取记录」按钮
- 弹窗展示所有星点获取历史（来源、数量、时间）

**赛季兑换情况面板**：
- 显示本赛季兑换情况（消费兑换星点、基金兑换星点）
- 消费水位/基金水位进度条（基于上限5000星点）
- 今日兑换状态（可兑换/已兑换）
- 最低提取额度、基金加成

**Tab 导航**：标记为 Phase 8 延展功能

---

## 三、后续版本计划

| 版本 | 功能 | 状态 |
|------|------|------|
| v0.3 | 赛季主题系统（开拓者/连线大师/深度矿工/分享者） | ❌ |
| v0.4 | 自定义挑战 | ❌ |
| v0.5 | 能力值系统完整上线 - 星点里程碑档位制 + 能力面板前端展示 | ❌ |
| Phase 8 | 前端 Tab 导航 | ❌ |
| 后续 | engine.py 拆分、前端组件化 | ❌ |

**v0.5 能力值系统详情**：
- **星点里程碑**：累计星点档位制（500/1000/2000/3000 四档）
- **能力面板**：展示「累计星点 + 当前档位增益 + 下一档位门槛」
- **设计原则**：连接力始终作为后台引擎，不直接向用户展示数值

---

## 四、配置参数

```yaml
# 基础配置
base_star: 10
daily_multipliers: [1.0, 1.5, 2.0, 0.2]

# 跨界采集加成
cross_domain_bonus: 5

# 连接力星点奖励
link_power_rewards:
  - {threshold: 5, reward: 50}
  - {threshold: 20, reward: 100}
  - {threshold: 50, reward: 200}

# 赛季星点限制
season_star_cap: 3000
season_soft_reset_ratio: 0.5

# 连续加成
streak_bonuses:
  - {days: 7, bonus_pct: 10}
  - {days: 30, bonus_pct: 30}
  - {days: 90, bonus_pct: 50}

# 基金
fund:
  base_rate: 1.5
  lock_days: 30
  min_withdraw: 500

# 连续选择奖惩
path_bonuses:
  fund: [{weeks: 2, rate: 1.55}, {weeks: 4, rate: 1.60}, {weeks: 8, rate: 1.65}]
  coupon: [{weeks: 2, rate: 0.95}, {weeks: 4, rate: 0.90}, {weeks: 8, rate: 0.85}]

# 赛季
seasons:
  default_length_days: 15
  auto_start: true
```

---

## 五、三层配置体系

| 文件 | 定位 | 修改方式 |
|------|------|---------|
| `defaults.yaml` | 静态模板：首次启动或重置时的初始值 | 手动编辑 |
| `config.yaml` | 运行时可调：倍率、阈值、汇率、解锁条件 | 编辑或 `/api/config` |
| `state.json` | 运行时累积：用户实际数据 | 系统自动更新 |

**读取顺序**：首次启动从 `defaults.yaml` 生成 `state.json`；迁移脚本从 `defaults.yaml` 读取默认值；运行时优先使用 `config.yaml`，缺失项回退到 `defaults.yaml`。

---

## 六、技术架构与工程约定

### 6.1 Pydantic 数据模型

当前 `state.json` 使用裸字典操作，后续将引入 Pydantic 模型实现类型安全：

```python
class TagNode(BaseModel):
    count: int
    first_seen: str

class TagGraph(BaseModel):
    nodes: Dict[str, TagNode] = {}
    edges: Dict[str, int] = {}  # key: "tagA<->tagB", value: weight

class AbilityState(BaseModel):
    link_power: float = 0.0

class SeasonState(BaseModel):
    id: int = 0
    name: str = "开拓者"
    start_date: str = ""
    end_date: str = ""
    star_earned: float = 0.0
    active_days: int = 0

class GameState(BaseModel):
    total_star: float = 0.0
    available_star: float = 0.0
    fund_pool: float = 0.0
    streak_days: int = 0
    active_days: int = 0
    total_notes: int = 0
    exchange_path: str = ""          # "coupon" / "fund"
    path_streak_weeks: int = 0
    fund_first_opened_at: Optional[str] = None
    link_power_rewards_earned: List[int] = []
    consumption_loss_this_month: float = 0.0
    medals: List[str] = []
    tag_graph: TagGraph = TagGraph()
    abilities: AbilityState = AbilityState()
    current_season: SeasonState = SeasonState()
    season_history: List[SeasonState] = []
    exchange_history: List[dict] = []
    published_count: int = 0
    completed_reports: int = 0
    total_output_star: float = 0.0
    cross_domain_notes_count: int = 0
```

**收益**：IDE 自动补全、类型检查、重构安全。

---

### 6.2 engine.py 拆解计划

当前 `engine.py` 承担多类职责，计划拆分为：

```
app/
├── engine.py          # 核心调度器：状态加载/保存、模块协调
├── capture.py         # 灵感采集：_calculate_stars、process_daily_capture
├── exchange.py        # 兑换逻辑：exchange、_calculate_exchange_rate
├── connection.py      # 连接力：_calculate_link_power、_update_tag_graph
├── season.py          # 赛季管理：_init_season、_settle_season
├── migration.py       # 数据迁移：_migrate_state_v022
├── review.py          # 回顾与战报：generate_weekly_review
├── projection.py      # 长期推演：calculate_long_term_projection
└── models.py          # Pydantic 数据模型
```

**拆解时机**：所有 v0.24 功能稳定后、Phase 8 之前，预计工期 1-2 天。

---

### 6.3 前端组件化方向

```
static/
├── index.html          # 主入口 + Alpine.js 全局状态
├── js/
│   ├── capture.js      # 采集模块
│   ├── exchange.js     # 兑换模块
│   ├── tagcloud.js     # 标签云组件
│   ├── season.js       # 赛季面板
│   └── dashboard.js    # 仪表盘
└── css/
    └── main.css        # 独立样式
```

**Tab 导航**：Phase 8 实现，使用 Alpine.js `x-show` 切换。

---

### 6.4 API 端点规范

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/api/status` | GET | ✅ | 获取当前状态 |
| `/api/capture` | POST | ✅ | 采集灵感 |
| `/api/exchange` | POST | ✅ | 星点兑换 |
| `/api/exchange/path` | POST | ✅ | 设置兑换路径 |
| `/api/publish` | POST | ✅ | 内容发布 |
| `/api/review/{type}` | POST | ✅ | 生成回顾 |
| `/api/projection` | GET | ✅ | 长期推演 |
| `/api/tags` | GET | ✅ | 获取标签数据 |
| `/api/medals` | GET | ✅ | 获取勋章数据 |
| `/api/season/check` | POST | ✅ | 检查赛季结束 |
| `/api/season/status` | GET | ✅ | 获取赛季状态 |
| `/api/config` | GET/PUT | ✅ | 获取/更新配置 |
| `/api/reset` | POST | ✅ | 重置数据 |
| `/api/version` | GET | ✅ | 获取版本信息 |

---

### 6.5 state.json 关键字段

| 字段 | 类型 | 用途 | 状态 |
|------|------|------|------|
| `total_star` | float | 累计星点 | ✅ 使用中 |
| `available_star` | float | 可用星点 | ✅ 使用中 |
| `fund_pool` | float | 基金池 | ✅ 使用中 |
| `streak_days` | int | 连续天数 | ✅ 使用中 |
| `active_days` | int | 活跃天数 | ✅ 使用中 |
| `total_notes` | int | 总笔记数 | ✅ 使用中 |
| `exchange_path` | str | 当前兑换路径 | ✅ 使用中 |
| `path_streak_weeks` | int | 路径连续周数 | ✅ 使用中 |
| `tag_graph` | dict | 标签共现图 | ✅ 使用中 |
| `abilities` | dict | 能力值状态 | ✅ 使用中 |
| `current_season` | dict | 当前赛季 | ✅ 使用中 |
| `season_history` | list | 赛季历史 | ✅ 使用中 |
| `medals` | list | 已获得勋章 | ✅ 使用中 |
| `penalty_active` | bool | 惩罚激活（废弃） | ⚠️ 保留 |
| `penalty_days` | int | 惩罚天数（废弃） | ⚠️ 保留 |

---

> **版本**：v0.24
>
> **关联文档**：`PHILOSOPHY.md`（为什么这样设计）、`TECH.md`（技术实现细节）、`ROADMAP.md`（开发进度）
