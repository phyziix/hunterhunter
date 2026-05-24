# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
> **AI 操作规则**见 `docs/AI_WORKFLOW.md`（文档维护、部署、调试、方法论实验）。

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.3.2 |
| 分支 | v0.3.2-dev |
| 部署状态 | ✅ 已上线 (8003端口) |
| 下一版本 | v0.4（兑换模块 feature flag）|

---

> **已上线版本**（v0.1.0、v0.1.1、v0.2.4、v0.2.5、v0.3.2）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.3.1** 已打 tag，前端拆分完成。

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

## 后续：v0.4（兑换模块开发）

> v0.2.5 已下线，v0.4 正式剥离重构。代码不删，一行配置可恢复。（兑换代码拆分已在 v0.3.2 完成，v0.4 做功能级 feature flag 控制）

- [ ] **main.py feature flag**：`ENABLE_EXCHANGE` 用 `os.getenv("ENABLE_EXCHANGE", "false")` 读取
- [ ] **前端兑换板块隐藏**：`/api/config` 返回 `exchange_enabled`，前端 `x-show` 绑定
- [ ] **调试方案**（隐藏≠不能调）：
    1. 环境变量控制：`ENABLE_EXCHANGE=true uvicorn main:app` 恢复
    2. API 始终暴露：路由不删，`curl` 直接调 `/api/exchange/*`
    3. 前端调试入口：URL 加 `?debug=exchange` 临时显示
    4. 数据验证：看 `state.json` 中 `exchange_history` / `fund_pool` / `available_star`

---

## 后续：v0.5（自定义挑战）

- [ ] 用户自行设定挑战目标与奖励，系统自动追踪进度

---

## 后续：v0.6（赛季主题）

- [ ] **四主题系统**：开拓者 / 连线大师 / 深度矿工 / 分享者，每赛季随机或手动选择主题
- [ ] **app.js 按模块拆分**：capture / exchange / review 等模块独立文件

---

## 后续：v0.7（能力值面板）

- [ ] 星点里程碑档位制完善，前端能力面板可视化展示

---

## 后续：v0.8（Tab 导航）

- [ ] 前端 6 个 Tab（采集 / 概览 / 成长 / 标签 / 行动 / 规则），Alpine.js x-show 切换

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
