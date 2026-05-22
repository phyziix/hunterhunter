# 认知狩猎 - 技术实现规格

> 本文档是技术实现的唯一参考，始终反映最新状态。数据结构 + API + 前端组件。
>
> **定位**：技术层。与 `PRODUCT.md`（产品设计）联动修改，由 AI IDE 基于现有代码库补充具体实现细节。

---

## 一、项目结构

```
/
├── main.py                # FastAPI 路由层
├── engine.py              # 核心游戏逻辑
├── requirements.txt       # Python 依赖
├── README.md
├── docs/
│   ├── PHILOSOPHY.md
│   ├── PRODUCT.md
│   ├── TECH.md            # 本文档
│   ├── ROADMAP.md
│   └── CHANGELOG.md
├── static/
│   └── index.html         # 单页前端（Alpine.js）
└── data/inspire/
    ├── Inbox/             # 灵感笔记存储（.md）
    └── _狩猎系统/
        ├── state.json     # 游戏状态持久化
        ├── config.yaml    # 系统配置参数（运行时可调）
        ├── defaults.yaml  # 初始值模板（首次启动/重置时使用）
        └── exchange_log.md # 兑换记录
```

---

## 二、数据结构

### 2.1 state.json 完整结构

> ⚠️ **核心约束**：以下字段必须存在。AI IDE 请基于此结构补充完整 JSON Schema，并检查现有代码是否已包含这些字段。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "total_star": { "type": "number", "description": "总星点数" },
    "today_count": { "type": "integer", "description": "今日采集次数" },
    "last_capture_date": { "type": "string", "format": "date", "description": "最后采集日期 YYYY-MM-DD" },
    "streak_days": { "type": "integer", "description": "连续采集天数" },
    "active_days": { "type": "integer", "description": "总活跃天数" },
    "total_notes": { "type": "integer", "description": "总笔记数" },
    "penalty_active": { "type": "boolean", "description": "惩罚激活状态（已废弃，仅保留兼容）" },
    "penalty_days": { "type": "integer", "description": "惩罚天数（已废弃，仅保留兼容）" },
    "medals": { "type": "array", "items": { "type": "string" }, "description": "已获得勋章列表" },
    "monthly_medals": { "type": "integer", "description": "月度勋章数" },
    "gray_medal": { "type": "boolean", "description": "灰色勋章状态" },
    "last_weekly_review": { "type": "string", "description": "最后周回顾标识 YYYY-WW" },
    "last_monthly_report": { "type": "string", "description": "最后月战报标识 YYYY-MM" },
    "weekly_review_done": { "type": "boolean", "description": "本周回顾完成状态" },
    "monthly_report_done": { "type": "boolean", "description": "本月战报完成状态" },
    "completed_reports": { "type": "integer", "description": "已完成战报数" },
    "exchange_history": { "type": "array", "description": "兑换历史记录" },
    "exchange_path": { "type": "string", "enum": ["coupon", "fund", ""], "description": "本周选择的兑换路径" },
    "fund_pool": { "type": "number", "description": "基金独立池星点数" },
    "available_star": { "type": "number", "description": "可自由支配星点数" },
    "consumption_loss_this_month": { "type": "number", "description": "本月消费损失累计" },
    "path_streak_weeks": { "type": "integer", "description": "当前路径连续选择周数" },
    "last_path_choice": { "type": "string", "format": "date", "description": "上次路径选择日期" },
    "published_count": { "type": "integer", "description": "内容输出发布次数" },
    "total_output_star": { "type": "number", "description": "内容输出总星点" },
    "abilities": {
      "type": "object",
      "properties": {
        "hunt_power": { "type": "number", "description": "采集力" },
        "link_power": { "type": "number", "description": "连接力" },
        "output_power": { "type": "number", "description": "输出力" }
      }
    },
    "ability_changes": {
      "type": "array",
      "description": "能力值变更日志",
      "items": {
        "type": "object",
        "properties": {
          "date": { "type": "string", "format": "date-time" },
          "ability": { "type": "string" },
          "change": { "type": "number" },
          "reason": { "type": "string" }
        }
      }
    },
    "cross_domain_notes_count": { "type": "integer", "description": "跨界笔记计数" },
    "tag_graph": {
      "type": "object",
      "properties": {
        "nodes": {
          "type": "object",
          "description": "标签节点 {#tag: {count, first_seen}}"
        },
        "edges": {
          "type": "object",
          "description": "标签连接边 {#tagA<->#tagB: weight}"
        }
      }
    },
    "current_season": {
      "type": "object",
      "properties": {
        "id": { "type": "integer" },
        "name": { "type": "string" },
        "start_date": { "type": "string", "format": "date" },
        "end_date": { "type": "string", "format": "date" },
        "theme_tags": { "type": "array", "items": { "type": "string" } },
        "star_earned_this_season": { "type": "number" },
        "cross_domain_notes_this_season": { "type": "integer" },
        "active_days_this_season": { "type": "integer" }
      }
    },
    "season_history": { "type": "array", "description": "已结算赛季数据" }
  }
}
```

### 2.2 defaults.yaml 初始值模板

> `data/inspire/_狩猎系统/defaults.yaml` 定义首次启动或重置时的初始值模板。迁移脚本和重置接口从这里读取默认值，不在代码中硬编码。

```yaml
# defaults.yaml 示例结构
total_star: 0
today_count: 0
last_capture_date: null
streak_days: 0
active_days: 0
total_notes: 0
medals: []
monthly_medals: 0
gray_medal: false
last_weekly_review: null
last_monthly_report: null
weekly_review_done: false
monthly_report_done: false
completed_reports: 0
exchange_history: []
exchange_path: ""
fund_pool: 0
available_star: 0
consumption_loss_this_month: 0
path_streak_weeks: 0
last_path_choice: null
published_count: 0
total_output_star: 0
abilities:
  hunt_power: 5.0
  link_power: 0.1
  output_power: 0
ability_changes: []
cross_domain_notes_count: 0
tag_graph:
  nodes: {}
  edges: {}
current_season: null
season_history: []
```

### 2.3 config.yaml 关键参数

> ⚠️ **核心约束**：以下配置项必须支持。AI IDE 请补充完整 YAML 定义。

```yaml
# 采集
base_star: 10
daily_multipliers:
  - 1.0
  - 1.5
  - 2.0
  - 0.2

# 任务奖励
weekly_review_reward: 200
monthly_report_reward: 500
content_output_reward_min: 750
content_output_reward_max: 1000
content_output_max_times: 5

# 连续加成
streak_bonuses:
  - days: 7
    bonus_pct: 10
  - days: 30
    bonus_pct: 30
  - days: 90
    bonus_pct: 50

# 基金
fund:
  base_rate: 1.5
  lock_days: 30
  min_withdraw: 500

# 连续选择奖惩
path_bonuses:
  fund:
    - weeks: 2
      rate: 1.55
    - weeks: 4
      rate: 1.60
    - weeks: 8
      rate: 1.65
  coupon:
    - weeks: 2
      rate: 0.95
    - weeks: 4
      rate: 0.90
    - weeks: 8
      rate: 0.85

# 能力值解锁
ability_thresholds:
  hunt_power:
    - threshold: 30
      title: "采集达人"
    - threshold: 100
      effect: "daily_multiplier_4th_upgrade"
  link_power:
    - threshold: 5
      title: "连线新手"
    - threshold: 20
      effect: "fund_bonus_extra_5"
  output_power:
    - threshold: 10
      effect: "unlock_investment_coupon"
    - threshold: 50
      effect: "output_reward_floor_850"

# 赛季
seasons:
  default_length_days: 90
  auto_start: true
  themes:
    - name: "开拓者"
      id: "pioneer"
      bonus: {}
    - name: "连线大师"
      id: "connector"
      bonus:
        cross_domain_bonus: 5
      medal_condition:
        type: "cross_domain_count"
        threshold: 30
    - name: "深度矿工"
      id: "miner"
      bonus:
        depth_bonus: 10
      medal_condition:
        type: "depth_note_count"
        threshold: 20
    - name: "分享者"
      id: "sharer"
      bonus:
        publish_bonus: 100
      medal_condition:
        type: "publish_count"
        threshold: 10

# 勋章配置表
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
  - id: "hunt_apprentice"
    name: "采集达人"
    icon: "📚"
    trigger: "ability"
    ability: "hunt_power"
    threshold: 30
  - id: "link_novice"
    name: "连线新手"
    icon: "🔗"
    trigger: "ability"
    ability: "link_power"
    threshold: 5
  - id: "season_pioneer"
    name: "开拓者勋章"
    icon: "🗺️"
    trigger: "season"
    season_theme: "pioneer"

# 兑换
coupon_rate: 1.0
custom_fund_name: "我的投资账户"
```

---

## 三、API 端点

> ⚠️ **核心约束**：以下端点必须全部实现。AI IDE 请基于现有代码补充请求/响应示例和错误处理。

### 3.1 灵感采集

#### POST `/api/capture`

**请求体**：
```json
{
  "content": "今天的灵感内容",
  "tags": ["标签1", "标签2"],
  "folder": "Inbox"
}
```

**响应**：
```json
{
  "earned": 15.0,
  "total_star": 115.0,
  "today_count": 2,
  "message": "捕获成功！"
}
```

**错误响应**：
```json
{
  "detail": "必须至少添加一个标签"
}
```

### 3.2 游戏状态

#### GET `/api/status`

**响应**：
```json
{
  "total_star": 115.0,
  "today_count": 2,
  "streak_days": 5,
  "penalty_active": false,
  "medals": ["灵光乍现", "周常猎人"],
  "monthly_medals": 2,
  "gray_medal": false,
  "fund_bonus": 10,
  "weekly_review_done": false,
  "monthly_report_done": false,
  "published_count": 3,
  "abilities": {
    "hunt_power": 25.5,
    "link_power": 3.2,
    "output_power": 8.5
  },
  "current_season": {
    "id": 1,
    "name": "开拓者",
    "start_date": "2026-01-01",
    "end_date": "2026-03-31",
    "theme_tags": [],
    "star_earned_this_season": 2500,
    "cross_domain_notes_this_season": 15,
    "active_days_this_season": 30
  }
}
```

#### GET `/api/config`

**响应**：
```json
{
  "base_star": 10,
  "daily_multipliers": [1.0, 1.5, 2.0, 0.2],
  "weekly_review_reward": 200,
  "monthly_report_reward": 500,
  "content_output_reward_min": 750,
  "content_output_reward_max": 1000,
  "content_output_max_times": 5,
  "coupon_rate": 1.0,
  "fund_base_rate": 1.5,
  "custom_fund_name": "我的投资账户"
}
```

#### PUT `/api/config`

**请求体**：
```json
{
  "base_star": 15,
  "daily_multipliers": [1.0, 1.5, 2.0, 0.3]
}
```

**响应**：
```json
{
  "message": "配置更新成功"
}
```

### 3.3 兑换

#### POST `/api/exchange/path`

**请求体**：
```json
{
  "path": "fund"
}
```

**响应**：
```json
{
  "message": "本周已选择基金路径",
  "path": "fund",
  "rate": 1.5,
  "streak_weeks": 3
}
```

#### POST `/api/exchange/coupon`

**请求体**：
```json
{
  "amount": 100
}
```

**响应**：
```json
{
  "deducted_star": 100,
  "real_value": 95.0,
  "new_balance": 50.0,
  "message": "请手动转账",
  "opportunity_cost": {
    "fund_value": 150.0,
    "difference": 55.0,
    "monthly_loss": 230.0
  }
}
```

#### POST `/api/exchange/fund`

**请求体**：
```json
{
  "amount": 500
}
```

**响应**：
```json
{
  "deducted_star": 500,
  "real_value": 750.0,
  "new_balance": 0.0,
  "message": "请手动转账",
  "opportunity_cost": {
    "coupon_value": 500.0,
    "difference": -250.0,
    "monthly_gain": 0.0
  }
}
```

**错误响应**：
```json
{
  "detail": "基金池星点不足500，无法兑换"
}
```

### 3.4 回顾与战报

#### POST `/api/review/weekly`

**响应**：
```json
{
  "file_path": "/path/to/周回顾素材-2026年第20周.md",
  "filename": "周回顾素材-2026年第20周.md",
  "content": "# 周回顾素材 - 2026年第20周\n...",
  "week_label": "2026年第20周",
  "date_range": "2026-05-12（周一）至 2026-05-18（周日）",
  "note_count": 8
}
```

#### POST `/api/review/weekly/submit`

**请求体**：
```json
{
  "file_path": "/path/to/周回顾素材-2026年第20周.md",
  "insight": "本周的核心洞察是..."
}
```

**响应**：
```json
{
  "reward": 200,
  "new_balance": 315.0,
  "message": "周回顾完成！"
}
```

#### POST `/api/report/monthly`

**响应**：
```json
{
  "file_path": "/path/to/月度战报素材-2026年5月.md",
  "filename": "月度战报素材-2026年5月.md",
  "content": "# 月度战报素材 - 2026年5月\n...",
  "month_label": "2026年5月",
  "date_range": "2026-05-01 至 2026-05-31",
  "note_count": 35
}
```

#### POST `/api/report/monthly/submit`

**请求体**：
```json
{
  "file_path": "/path/to/月度战报素材-2026年5月.md",
  "insight": "本月的核心洞察是..."
}
```

**响应**：
```json
{
  "reward": 500,
  "new_balance": 815.0,
  "message": "月度战报完成！"
}
```

#### GET `/api/report/monthly/draft`

**响应**：
```json
{
  "draft": "本月已生成的草稿内容...",
  "has_draft": true
}
```

### 3.5 内容输出

#### POST `/api/content/verify`

**请求体**：
```json
{
  "url": "https://example.com/article"
}
```

**响应**：
```json
{
  "reward": 875,
  "total_star": 1190.0,
  "published_count": 4,
  "message": "发布成功！"
}
```

**错误响应**：
```json
{
  "detail": "已达到最大发布次数（5次）"
}
```

### 3.6 标签

#### GET `/api/tags`

**响应**：
```json
{
  "nodes": {
    "#生产力": { "count": 15, "first_seen": "2026-05-01" },
    "#冥想": { "count": 8, "first_seen": "2026-05-05" }
  },
  "edges": {
    "#生产力<->#冥想": 3,
    "#生产力<->#阅读": 5
  }
}
```

#### GET `/api/notes/by-tag?tag=生产力`

**响应**：
```json
{
  "tag": "#生产力",
  "notes": [
    {
      "title": "时间管理心得",
      "date": "2026-05-12",
      "tags": ["#生产力", "#时间管理"]
    },
    {
      "title": "番茄工作法实践",
      "date": "2026-05-15",
      "tags": ["#生产力", "#专注"]
    }
  ]
}
```

### 3.7 勋章

#### GET `/api/medals`

**响应**：
```json
{
  "medals": [
    {
      "id": "first_triple",
      "name": "灵光乍现",
      "icon": "💡",
      "trigger": "event",
      "condition": "单日完成3条采集",
      "earned": true,
      "earned_at": "2026-05-20"
    },
    {
      "id": "hunt_apprentice",
      "name": "采集达人",
      "icon": "📚",
      "trigger": "ability",
      "condition": "采集力 ≥ 30",
      "earned": false,
      "earned_at": null
    }
  ]
}
```

#### POST `/api/medals/check`

**说明**：触发勋章检查（通常由系统自动调用，也可手动触发）

**请求体**：
```json
{
  "trigger_type": "ability"
}
```

**响应**：
```json
{
  "checked": 3,
  "newly_earned": [
    {
      "id": "hunt_apprentice",
      "name": "采集达人",
      "icon": "📚"
    }
  ]
}
```

### 3.8 赛季

#### GET `/api/season/status`

**响应**：
```json
{
  "current_season": {
    "id": 1,
    "name": "开拓者",
    "start_date": "2026-01-01",
    "end_date": "2026-03-31",
    "theme_tags": [],
    "star_earned_this_season": 2500,
    "cross_domain_notes_this_season": 15,
    "active_days_this_season": 30
  },
  "comparison": {
    "last_season": {
      "star_earned": 1800,
      "cross_domain_notes": 10,
      "active_days": 25
    },
    "diff": {
      "star_earned": 700,
      "cross_domain_notes": 5,
      "active_days": 5
    }
  }
}
```

#### GET `/api/season/history`

**响应**：
```json
{
  "seasons": [
    {
      "id": 0,
      "name": "开拓者",
      "start_date": "2025-10-01",
      "end_date": "2025-12-31",
      "star_earned": 1800,
      "medals": ["开拓者勋章"]
    }
  ]
}
```

#### POST `/api/season/settle`

**响应**：
```json
{
  "message": "赛季结算完成",
  "season_report": {
    "id": 1,
    "star_earned": 2500,
    "medals": ["开拓者勋章", "连接者勋章"]
  }
}
```

---

## 四、关键函数签名

> AI IDE 请基于现有 engine.py 补充完整函数签名、参数类型、返回类型。

### 4.1 能力值计算

```python
def _calculate_hunt_power(self) -> float:
    """计算采集力
    公式：(total_notes^0.7) × log(active_days+1) × (1 + streak_days/100)
    返回: 5~200
    """
    pass

def _calculate_link_power(self) -> float:
    """计算连接力
    公式: 密度 × 100 × log₂(节点数+1) × (跨界占比+0.1)
    返回: 0.1~50
    """
    pass

def _calculate_output_power(self) -> float:
    """计算输出力
    公式: (published_count^0.6) × (1 + reports/10) × log(输出总星点+1)
    返回: 0~100
    """
    pass

def get_abilities(self) -> dict:
    """聚合三个能力值
    返回: {"hunt_power": float, "link_power": float, "output_power": float}
    """
    pass

def _update_ability_changes(self, ability: str, change: float, reason: str) -> None:
    """维护能力值变更日志
    参数:
        ability: 能力值名称 ("hunt_power", "link_power", "output_power")
        change: 变化值（正数增加，负数减少）
        reason: 变更原因描述
    """
    pass
```

### 4.2 勋章系统

```python
def check_medals(self, trigger_type: str = None) -> list:
    """检查并发放勋章
    参数:
        trigger_type: 触发类型筛选 ("event", "ability", "season")，None 表示检查所有
    返回:
        [
            {
                "id": str,
                "name": str,
                "icon": str,
                "earned": bool,
                "earned_at": str or None
            }
        ]
    """
    pass

def get_all_medals(self) -> list:
    """获取所有勋章定义和状态
    返回:
        [
            {
                "id": str,
                "name": str,
                "icon": str,
                "trigger": str,
                "condition": str or None,
                "earned": bool,
                "earned_at": str or None
            }
        ]
    """
    pass

def get_medal_status(self, medal_id: str) -> dict:
    """获取指定勋章状态
    参数:
        medal_id: 勋章 ID
    返回:
        {
            "earned": bool,
            "earned_at": str or None
        }
    """
    pass
```

### 4.3 标签图更新

```python
def _update_tag_graph(self, tags: list) -> None:
    """灵感提交时更新标签共现图
    参数:
        tags: 标签列表，截断取前5个
    逻辑:
        - 两两配对更新 edges 权重
        - 更新 nodes 计数
        - 检测跨界笔记（不同领域标签）
    """
    pass

def get_tag_cloud_data(self) -> dict:
    """返回标签云渲染数据
    返回:
        {
            "nodes": {"#tag": {"count": N, "first_seen": "YYYY-MM-DD"}},
            "edges": {"#tagA<->#tagB": N}
        }
    """
    pass

def get_notes_by_tag(self, tag: str) -> list:
    """扫描 Inbox/ 匹配标签，按日期倒序
    参数:
        tag: 标签名（带#或不带#均可）
    返回:
        [
            {
                "title": str,
                "date": "YYYY-MM-DD",
                "tags": list,
                "filename": str
            }
        ]
    """
    pass
```

### 4.4 兑换相关

```python
def _calculate_exchange_rate(self, path: str) -> float:
    """计算当前汇率（含连续选择奖惩）
    参数:
        path: "coupon" 或 "fund"
    返回: 当前汇率
    """
    pass

def calculate_opportunity_cost(self, amount: float, from_path: str) -> dict:
    """计算镜像对比数据
    参数:
        amount: 兑换金额
        from_path: 当前选择的路径 ("coupon" 或 "fund")
    返回:
        {
            "fund_value": float,  # 等值基金价值
            "coupon_value": float,  # 等值消费价值
            "difference": float,  # 差异（正数表示当前路径更优）
            "monthly_loss": float,  # 本月累计消费损失
            "monthly_gain": float  # 本月累计克制收益
        }
    """
    pass

def _update_path_streak(self, path: str) -> None:
    """更新路径连续选择计数
    参数:
        path: 本周选择的路径
    逻辑:
        - 与上周相同: streak_weeks + 1
        - 与上周不同: streak_weeks 归零
    """
    pass
```

### 4.5 赛季相关

```python
def _init_season(self) -> None:
    """初始化新赛季
    逻辑:
        - 检查当前赛季是否结束
        - 如结束则结算并创建新赛季
        - 设置赛季主题（如配置）
    """
    pass

def _settle_season(self) -> dict:
    """结算当前赛季
    返回:
        {
            "id": int,
            "star_earned": float,
            "medals": list,
            "report": str  # 结算报告内容
        }
    """
    pass

def _get_season_comparison(self) -> dict:
    """本赛季 vs 上赛季对比数据
    返回:
        {
            "last_season": {...},
            "diff": {...}
        }
    """
    pass
```

### 4.6 采集/回顾/战报

```python
def process_daily_capture(self, content: str, tags: list = None, folder: str = "Inbox") -> dict:
    """处理每日灵感采集
    参数:
        content: 灵感内容
        tags: 标签列表
        folder: 存储文件夹
    返回:
        {
            "earned": float,
            "total_star": float,
            "today_count": int,
            "message": str
        }
    """
    pass

def generate_weekly_review(self) -> dict:
    """生成上周素材文件
    返回:
        {
            "file_path": str,
            "filename": str,
            "content": str,
            "week_label": str,
            "date_range": str,
            "note_count": int
        }
    """
    pass

def submit_weekly_review(self, file_path: str, insight: str) -> dict:
    """提交周回顾总结
    参数:
        file_path: 素材文件路径
        insight: 用户核心洞察
    返回:
        {
            "reward": int,
            "new_balance": float,
            "message": str
        }
    """
    pass

def generate_monthly_report(self) -> dict:
    """生成上月素材文件
    返回:
        {
            "file_path": str,
            "filename": str,
            "content": str,
            "month_label": str,
            "date_range": str,
            "note_count": int
        }
    """
    pass

def submit_monthly_report(self, file_path: str, insight: str) -> dict:
    """提交月度战报总结
    参数:
        file_path: 素材文件路径
        insight: 用户核心洞察
    返回:
        {
            "reward": int,
            "new_balance": float,
            "message": str
        }
    """
    pass

def process_publish(self, url: str) -> dict:
    """处理内容输出验证
    参数:
        url: 内容链接
    返回:
        {
            "reward": int,
            "total_star": float,
            "published_count": int,
            "message": str
        }
    """
    pass
```

---

## 五、前端组件结构

> AI IDE 请基于 `static/index.html` 补充实际 Alpine.js 组件划分和关键 data/methods。

### 5.1 核心组件划分

```javascript
function appData() {
    return {
        // ===== 状态数据 =====
        status: {
            total_star: 0,
            today_count: 0,
            streak_days: 0,
            penalty_active: false,
            medals: [],
            monthly_medals: 0,
            gray_medal: false,
            fund_bonus: 0,
            weekly_review_done: false,
            monthly_report_done: false,
            published_count: 0,
            abilities: {
                hunt_power: 0,
                link_power: 0,
                output_power: 0
            },
            current_season: {}
        },
        
        config: {},
        
        // ===== 采集表单 =====
        captureForm: {
            content: '',
            tags: []
        },
        tagInput: '',
        showEarned: false,
        
        // ===== 回顾弹窗 =====
        reviewModal: {
            show: false,
            type: 'weekly',  // 'weekly' or 'monthly'
            content: '',
            insight: '',
            file_path: '',
            copied: false
        },
        
        // ===== 兑换弹窗 =====
        exchangeModal: {
            show: false,
            type: 'coupon',  // 'coupon' or 'fund'
            amount: 0,
            opportunity_cost: null
        },
        
        // ===== 标签弹窗 =====
        tagModal: {
            show: false,
            tag: '',
            notes: []
        },
        
        // ===== 勋章定义 =====
        allMedals: [
            { name: '灵光乍现', emoji: '💡', condition: '单日完成3条采集' },
            { name: '周常猎人', emoji: '🏹', condition: '连续4周完成回顾' },
            { name: '连线大师', emoji: '🕸️', condition: '单篇战报连接3个领域' },
            { name: '采集达人', emoji: '📚', condition: '采集力≥30' },
            { name: '连线新手', emoji: '🔗', condition: '连接力≥5' }
        ],
        
        // ===== 初始化 =====
        async init() {
            await this.loadStatus();
            await this.loadConfig();
        },
        
        // ===== API 调用 =====
        async loadStatus() {
            const res = await fetch('/api/status');
            this.status = await res.json();
        },
        
        async loadConfig() {
            const res = await fetch('/api/config');
            this.config = await res.json();
        },
        
        // ===== 采集相关 =====
        async submitCapture() {
            if (!this.captureForm.content.trim() || this.captureForm.tags.length === 0) {
                return;
            }
            
            const res = await fetch('/api/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: this.captureForm.content,
                    tags: this.captureForm.tags
                })
            });
            
            const result = await res.json();
            this.status.total_star = result.total_star;
            this.status.today_count = result.today_count;
            this.showEarned = true;
            setTimeout(() => this.showEarned = false, 500);
            
            this.captureForm.content = '';
            this.captureForm.tags = [];
            this.showNotification('success', `获得 ${result.earned} 星点！`);
        },
        
        addTag() {
            const tag = this.tagInput.trim();
            if (tag && !this.captureForm.tags.includes(tag)) {
                this.captureForm.tags.push(tag);
                this.tagInput = '';
            }
        },
        
        removeTag(index) {
            this.captureForm.tags.splice(index, 1);
        },
        
        // ===== 回顾相关 =====
        async generateReview(type) {
            const endpoint = type === 'weekly' ? '/api/review/weekly' : '/api/report/monthly';
            const res = await fetch(endpoint, { method: 'POST' });
            const result = await res.json();
            
            if (result.error) {
                this.showNotification('error', result.error);
                return;
            }
            
            this.reviewModal.type = type;
            this.reviewModal.content = result.content;
            this.reviewModal.file_path = result.file_path;
            this.reviewModal.insight = '';
            this.reviewModal.show = true;
            this.reviewModal.copied = false;
        },
        
        async submitReview() {
            const endpoint = this.reviewModal.type === 'weekly' 
                ? '/api/review/weekly/submit' 
                : '/api/report/monthly/submit';
            
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_path: this.reviewModal.file_path,
                    insight: this.reviewModal.insight
                })
            });
            
            const result = await res.json();
            this.status.total_star = result.new_balance;
            this.reviewModal.show = false;
            this.showNotification('success', result.message);
            await this.loadStatus();
        },
        
        copyReviewContent() {
            navigator.clipboard.writeText(this.reviewModal.content);
            this.reviewModal.copied = true;
            setTimeout(() => this.reviewModal.copied = false, 2000);
        },
        
        // ===== 兑换相关 =====
        async openExchangeModal(type) {
            this.exchangeModal.type = type;
            this.exchangeModal.amount = 0;
            this.exchangeModal.opportunity_cost = null;
            this.exchangeModal.show = true;
        },
        
        async confirmExchange() {
            const endpoint = this.exchangeModal.type === 'coupon' 
                ? '/api/exchange/coupon' 
                : '/api/exchange/fund';
            
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: this.exchangeModal.amount })
            });
            
            const result = await res.json();
            if (result.error) {
                this.showNotification('error', result.error);
                return;
            }
            
            this.status.total_star = result.new_balance;
            this.exchangeModal.show = false;
            this.showNotification('success', result.message);
            await this.loadStatus();
        },
        
        // ===== 标签相关 =====
        async showTagDetail(tag) {
            const res = await fetch(`/api/notes/by-tag?tag=${encodeURIComponent(tag)}`);
            const result = await res.json();
            
            this.tagModal.tag = tag;
            this.tagModal.notes = result.notes;
            this.tagModal.show = true;
        },
        
        // ===== 工具方法 =====
        formatNumber(num) {
            return num.toFixed(1);
        },
        
        getMedalClass(name) {
            if (this.status.medals.includes(name)) return '';
            return 'locked';
        },
        
        showNotification(type, message) {
            // 实现通知显示逻辑
        }
    };
}
```

### 5.2 关键交互要求

- **兑换确认页**：必须展示镜像对比（等值对比 + 时间维度 + 历史累计）
- **基金池**：CSS 水位动画，星点增加时微涨
- **能力面板**：进度条 + 最近变更日志摘要
- **标签云**：字号按 `log(count+1)` 映射
- **标签点击弹窗**：展示关联笔记列表，支持标签跳转
- **赛季卡片**：进度显示 + 上赛季对比
- **微观反馈**：采集成功后展示三要素 + 相似笔记

### 5.3 模态窗规范

- **回顾弹窗**：已实现（参考现有代码）
- **镜像对比弹窗**：兑换确认页强制展示
- **标签详情弹窗**：点击标签触发
- **赛季结算弹窗**：赛季结束时展示

---

## 六、算法细节

### 6.1 连接力计算

```python
import math

def calculate_link_density(nodes_count, edges_count):
    """计算图密度"""
    if nodes_count < 2:
        return 0
    max_possible_edges = nodes_count * (nodes_count - 1) / 2
    return edges_count / max_possible_edges

def calculate_link_power(nodes_count, edges_count, cross_domain_ratio):
    """计算连接力"""
    density = calculate_link_density(nodes_count, edges_count)
    return density * 100 * math.log2(nodes_count + 1) * (cross_domain_ratio + 0.1)
```

### 6.2 标签共现图更新

```python
def _update_tag_graph(self, tags):
    """灵感提交时更新标签共现图"""
    tags = tags[:5]  # 只取前5个
    
    # 更新节点计数
    for tag in tags:
        if tag not in self.state["tag_graph"]["nodes"]:
            self.state["tag_graph"]["nodes"][tag] = {
                "count": 0,
                "first_seen": self._get_today_str()
            }
        self.state["tag_graph"]["nodes"][tag]["count"] += 1
    
    # 两两配对更新边权重
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            edge_key = f"{tags[i]}<->{tags[j]}"
            if edge_key not in self.state["tag_graph"]["edges"]:
                self.state["tag_graph"]["edges"][edge_key] = 0
            self.state["tag_graph"]["edges"][edge_key] += 1
    
    # 检测跨界笔记（按前缀判定）
    domains = set()
    for tag in tags:
        domain = tag.split('/')[0] if '/' in tag else tag
        domains.add(domain)
    
    if len(domains) >= 2:
        self.state["cross_domain_notes_count"] += 1
```

### 6.3 连续选择奖惩

```python
def _calculate_exchange_rate(self, path):
    """计算当前汇率（含连续选择奖惩）"""
    config = self.config["path_bonuses"][path]
    base_rate = self.config["fund"]["base_rate"] if path == "fund" else 1.0
    
    streak_weeks = self.state["path_streak_weeks"]
    rate = base_rate
    
    for bonus in config:
        if streak_weeks >= bonus["weeks"]:
            rate = bonus["rate"]
    
    return rate

def _update_path_streak(self, path):
    """更新路径连续选择计数"""
    last_choice = self.state.get("last_path_choice", "")
    last_week = self._get_week_str()
    
    if last_choice == path:
        self.state["path_streak_weeks"] += 1
    else:
        self.state["path_streak_weeks"] = 0
    
    self.state["exchange_path"] = path
    self.state["last_path_choice"] = last_week
```

---

> **AI IDE 补充指引**：
> 1. 检查 `state.json` 当前结构，对比本文档 2.1 节，补充缺失字段，保留已有数据
> 2. 检查 `config.yaml` 当前结构，对比本文档 2.2 节，补充缺失配置项
> 3. 检查 API 端点实现情况，对比本文档第三节，标记未实现的端点
> 4. 检查 `engine.py` 函数，对比本文档第四节，补充缺失的函数签名和实现
> 5. 补充第五节前端组件划分（基于 `static/index.html` 实际代码）
> 6. 补充所有 API 的请求/响应示例和错误码说明
>
> **注意**：产品设计以 `PRODUCT.md` 为准，心理内核以 `PHILOSOPHY.md` 为准。技术实现不得偏离这两个文档的设计意图。
