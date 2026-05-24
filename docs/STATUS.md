# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
> **AI 操作规则**见 `docs/AI_WORKFLOW.md`（文档维护、部署、调试、方法论实验）。

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.3.1-dev |
| 分支 | v0.3.1-dev |
| 部署状态 | 🔧 开发中 |
| 下一版本 | v0.3.2（后端拆分第一波） |

---

> **已上线版本**（v0.1.0、v0.1.1、v0.2.4、v0.2.5）见 [CHANGELOG](CHANGELOG.md)。

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

## 下一步：v0.3.2（后端拆分第一波）

### 目标：先拆核心模块，验证后再拆其余

| 模块 | 文件 | 包含功能 |
|------|------|
| [ ] **engine_core.py** | 状态/配置/日志/数据路径 |
| [ ] **engine_capture.py** | 采集/标签/连接力/去重/相似笔记 |
| [ ] **engine_exchange.py** | 兑换/基金池/汇率/动态锁定 |

---

## v0.3.3：后端拆分第二波（review + season + backup）

| 模块 | 文件 | 包含功能 |
|------|------|
| [ ] **engine_review.py** | 周/月回顾/生成/素材 |
| [ ] **engine_season.py** | 赛季系统/主题/进度 |
| [ ] **engine_backup.py** | 备份/iCloud 同步 |

### 预期效果

| 文件 | 拆分前 | 拆分后 |
|------|--------|--------|
| `index.html` | 2778 行 | ~1210 行 |
| `engine.py` | 2258 行 | ~377 行/模块（6个模块） |

### 技术保障

- uvicorn `--reload` 完全不受影响，改任意 .py 文件自动重启
- 每个模块拆完立即测试核心流程（采集 + 至少一个 API）

---

## 后续：v0.4（兑换模块开发）

> v0.2.5 已下线，v0.4 正式剥离重构。代码不删，一行配置可恢复。

- [ ] **兑换模块剥离**：从 `engine.py` 抽取所有兑换方法到新文件 `engine_exchange.py`
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
