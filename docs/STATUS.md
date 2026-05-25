# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
> **AI 操作规则**见 `docs/AI_WORKFLOW.md`（文档维护、部署、调试、方法论实验）。

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.4.0 |
| 分支 | v0.4-dev |
| 部署状态 | ✅ 已上线 (8003端口) |
| 下一版本 | v0.5（惊喜奖励模块）|

---

> **已上线版本**（v0.1.0、v0.1.1、v0.2.4、v0.2.5、v0.3.2、v0.4.0）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.3.1** 已打 tag，前端拆分完成。
>
> **v0.3.2** 已上线，后端拆分完成。

---

## 已完成：v0.2.5（Bug 修复）

> 已上线。完整功能点见 [CHANGELOG](CHANGELOG.md#v0252026-05-24✅-已上线)。

---

## 已完成：v0.3.1（前端拆分）

> 已完成并验证。

### 完成内容

| 任务 | 说明 | 状态 |
|------|------|:----:|
| **提取 style** | `<style>` 块 → `static/styles.css`（690行）| ✅ |
| **提取 script** | `<script>` 块 → `static/app.js`（834行）| ✅ |
| **精简 index.html** | 2778行 → 1215行，只保留 HTML + Alpine.js CDN + 外链引用 | ✅ |

### 修复的问题

- **Alpine.js 重复加载**：index.html 中 CDN 被引入两次，已删除冗余
- **重复样式定义**：styles.css 中 `.modal-overlay`、`@keyframes fadeIn`、`@keyframes scaleIn` 各重复一次，已清理
- **静态资源 404**：CSS/JS 路径 `/static/*` 之前只有一个根挂载，导致查找路径为 `static/static/*`。修复：在 `main.py` 增加独立 `app.mount("/static", StaticFiles(directory="static"))`
- **惩罚代码清理**：删除前端 penalty 相关死代码（惩罚已废除），涉及 index.html（`:class` 绑定+提示条）、styles.css（`.penalty-indicator`+`@keyframes pulse`）、app.js（`penalty_active` 初始值）

### 验证要点

- ✅ 零逻辑改动，纯剪切粘贴
- ✅ Console 无报错
- ✅ 页面背景正确显示紫蓝色渐变
- ✅ 核心交互功能正常

---

## 已完成：v0.3.2（后端拆分）✅

> ⚠️ **风险提示**：本版本涉及 `engine.py`（2258行）拆分为多个模块，属大规模重构。执行前需备份 `engine.py`，每拆完一个模块立即验证。

### 架构模式

采用 **Mixin 多重继承** 模式拆分，API 层零变更：

```python
# engine.py 最终形态
class HuntingEngine(EngineCore, EngineBackup, EngineSeason,
                     EngineReview, EngineExchange, EngineCapture):
    pass  # 所有方法通过 MRO 继承
```

### 拆分顺序（依赖最少的先拆）

| 步骤 | 模块 | 文件 | 核心方法 | 验证方式 |
|:----:|------|------|---------|---------|
| 0 | **Core** | `engine_core.py` | 基础方法（详见下文清单）| 启动无报错 |
| 1 | **Backup** | `engine_backup.py` | `backup/sync_to_icloud/start_icloud_sync` | `POST /api/backup` |
| 2 | **Season** | `engine_season.py` | `check_season_end/start_new_season/_generate_season_report` | `POST /api/season/check` |
| 3 | **Review** | `engine_review.py` | `generate_weekly_review/submit_weekly_review/...` | 触发周回顾 |
| 4 | **Exchange** | `engine_exchange.py` | `exchange_coupon/exchange_fund/_calculate_exchange_rate` | 兑换消费券+基金 |
| 5 | **Capture** | `engine_capture.py` | `process_daily_capture/_update_tag_graph/_find_related_notes` | 提交采集灵感 |

### Core 方法完整清单（~600+ 行）

| 类别 | 方法 |
|------|------|
| 存储 | `_load_state`, `_save_state`, `_load_config`, `_save_config`, `_write_default_config`, `_write_default_state` |
| 初始化 | `__init__`, `_init_system`, `_init_logging`, `_log_event` |
| 时间工具 | `_get_today_str`, `_get_week_str`, `_get_month_str`, `_get_season_start_date` |
| 迁移 | `_migrate_state_v022` |
| 勋章（共用）| `_check_medals`, `_check_event_medal`, `_check_ability_medal`, `_check_season_medal`, `get_all_medals`, `get_medal_status` |
| 标签图（共用）| `_init_tag_graph_from_notes`, `_init_tag_index_from_notes` |
| 聚合 API | `get_status`, `calculate_long_term_projection`, `process_publish`, `get_config`, `update_config` |
| 调试 | `reset_all`, `reset_daily_flags` |

> 勋章和标签图方法被多个模块调用（Capture/Review/Migration），归入 Core 避免循环依赖。

### 关于惩罚代码（v0.3.1 已清理前端）

- 前端 penalty 死代码（`:class` 绑定、提示条、`.penalty-indicator`）已在 v0.3.1 删除
- 后端 `engine.py` 中 `penalty_active` 相关字段和逻辑在拆分 Exchange/Capture 时一并清理

### 预期效果

| 文件 | 拆分前 | 拆分后 |
|------|--------|--------|
| `engine.py` | 2258 行 | ~50 行（仅 import + class 定义）|
| `engine_core.py` | - | ~650 行（基础方法+勋章+标签图）|
| `engine_capture.py` | - | ~800 行（采集+标签+发现）|
| `engine_exchange.py` | - | ~200 行 |
| `engine_review.py` | - | ~350 行 |
| `engine_season.py` | - | ~200 行 |
| `engine_backup.py` | - | ~80 行 |

---

## 进行中：v0.4-dev（消费记录与兑换优化）

> 当前开发分支：v0.4-dev

### 已完成任务

| 任务 | 说明 | 状态 |
|------|------|:----:|
| **消费记录功能** | 新增 `record_consumption()` / `get_consumption_history()` 方法 + `/api/consume` / `/api/consume/history` 端点 + 前端消费记录弹窗 | ✅ |
| **版本号显示** | 页面底部显示版本号，开发版本标注 `🚧 DEV` | ✅ |
| **兑换逻辑对齐** | 汇率规则与 PRODUCT.md 完全一致：消费 1.0、基金 1.5（1.0+0.5） | ✅ |
| **路径连续奖励** | 基金连续加成、消费连续惩罚，中断归零 | ✅ |
| **移除基金锁定** | 删除"首次兑换锁定30天"规则 | ✅ |
| **术语统一** | 所有"消费券"改为"消费" | ✅ |
| **错误提示优化** | 超额度时显示"额度不足，当前剩余 ¥XX.XX"而非通用"记录失败" | ✅ |

### 调试方案

- **环境变量控制**：`ENABLE_EXCHANGE=true uvicorn main:app` 启用兑换模块
- **API 始终暴露**：路由不删，`curl` 直接调 `/api/exchange/*`
- **数据验证**：查看 `state.json` 中 `exchange_history` / `fund_pool` / `coupon_pool` / `consumed_amount`

### 消费记录数据结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `coupon_pool` | float | 已兑换消费累计星点 |
| `consumed_amount` | float | 已消费金额 |
| `consumption_records` | list | 消费记录列表（content, amount, timestamp） |

---

## 后续：v0.5（惊喜奖励模块）

> 惊喜奖励是独立于赛季的每日随机加成系统，替换原赛季奖励机制。

### 核心设计

**四个主题与加成规则：**

| 主题 | 加成规则 | 图标 |
|------|---------|:---:|
| 开拓者 | 今日第1条采集 +1 星点 | ⛏️ |
| 连线大师 | 今日跨界采集额外 +3 星点 | 🔗 |
| 深度矿工 | 今日单篇 ≥500 字额外 +5 星点 | ⛏️ |
| 分享者 | 今日媒体发布额外 +50 星点 | 📢 |

**关键规则：**
- 四个主题随机几率均等（各 25%）
- 每天可重随一次（可能抽到同一主题）
- 每天 0 点自动刷新主题和重随机会
- 加成独立于赛季，与其他加成叠加生效

### 开发任务

| 任务 | 说明 | 状态 |
|------|------|:----:|
| **后端状态字段** | 新增 `daily_bonus` 存储今日主题、重随是否已使用 | [ ] |
| **随机抽取逻辑** | 实现随机抽取算法，四个主题等概率 | [ ] |
| **重随功能** | 实现重随接口，消耗重随机会重新随机 | [ ] |
| **每日重置** | 0 点自动重置主题、重随机会、加成失效 | [ ] |
| **采集加成** | 采集时检查今日主题，叠加相应加成 | [ ] |
| **发布加成** | 内容发布时检查今日主题，叠加分享者加成 | [ ] |
| **配置支持** | 在 `config.yaml` 中添加 `daily_bonus` 配置段 | [ ] |
| **前端展示** | 仪表盘展示今日惊喜（名称 + 加成说明 + 重随按钮） | [ ] |
| **API 端点** | 新增获取/重随今日惊喜的 API | [ ] |

### 和其他模块的关系

- 独立于赛季，不参与赛季结算
- 与采集倍数、连续加成、跨界采集默认 +5 叠加生效
- 与基金/消费兑换无关

---

## 后续：v0.6（赛季规则优化）

> 优化现有赛季系统，与惊喜奖励模块配合使用。

- [ ] **赛季结算规则优化**：明确赛季奖励计算方式，与惊喜奖励叠加逻辑
- [ ] **赛季主题简化**：保留赛季框架，主题系统与惊喜奖励合并
- [ ] **app.js 按模块拆分**：capture / exchange / review 等模块独立文件

---

## 后续：v0.7（能力值面板）

- [ ] 星点里程碑档位制完善，前端能力面板可视化展示

---

## 后续：v0.8（Tab 导航）

- [ ] 前端 6 个 Tab（采集 / 概览 / 成长 / 标签 / 行动 / 规则），Alpine.js x-show 切换

---

## 后续：v0.9（自定义挑战）

- [ ] 用户自行设定挑战目标与奖励，系统自动追踪进度

---

## 已完成 / 长期

- [x] **AI_WORKFLOW.md 拆分**：⚠️ 操作规则移至独立文件，STATUS 恢复纯状态文档
- [ ] **方法论收割**：项目关闭时，从 AI_WORKFLOW/DEPLOYMENT/STATUS 提炼通用骨架 → `METHODOLOGY.md`

---

## 技术栈

- 前端：Alpine.js（单页长滚动）
- 后端：FastAPI + uvicorn
- 存储：Markdown(灵感笔记) + YAML(配置) + JSON(状态)
- 部署：launchd + localtunnel（公网）
- 仓库：github.com/phyziix/hunterhunter
