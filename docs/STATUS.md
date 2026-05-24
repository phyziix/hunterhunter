# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
> **AI 操作规则**见 `docs/AI_WORKFLOW.md`（文档维护、部署、调试、方法论实验）。

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.2.5 |
| 分支 | v0.2.5 |
| 部署状态 | ✅ v0.2.5 已上线 (8003端口) |
| 下一版本 | v0.3（结构调整） |

---

> **已上线版本**（v0.1.0、v0.1.1）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.2.5 功能规格**见 [PRODUCT.md](PRODUCT.md#二v025-当前功能)。

---

## 已完成：v0.2.5（Bug 修复）

> 以下功能点已完成修复：

- [x] **兑换模块下线**：通过 feature flag 关闭前端入口和路由暴露，代码不动
- [x] **赛季模块下线**：同兑换模块，通过 feature flag 关闭前端入口
- [x] **重复提交提示优化**：检测到重复提交后，弹出「建议情况」对话框告知用户，提升体验
- [x] **标签提取过滤 `##`**：正文标签提取正则会匹配到 `## 标题` 等 Markdown 格式，已过滤
- [x] **相关灵感匹配规则优化**：IDF 上限截断、标签/内容权重7:3、排序调整、新增单标签支持
- [x] **标签宇宙优化**：字号对数映射、标签详情加载状态、tag_index 性能优化

---

---

## 下一步：v0.3（结构调整）

> v0.3 专注代码结构优化，不做功能变更。

### 设计决策

- v0.3 只做**结构迁移**，不动任何逻辑
- v0.4 再做**兑换重构**，两版本递进关系：v0.3 搬代码，v0.4 改代码
- 兑换体系代码暂不删，通过结构优化实现下线，日后一行配置即可恢复

### 任务分解

#### 前端拆分（~30分钟）

- [ ] **前端：提取 style**：`index.html` 的 `<style>` 块 → `static/styles.css`
- [ ] **前端：提取 script**：`index.html` 的 `<script>` 块 → `static/app.js`
- [ ] **前端：精简 index.html**：只保留 HTML 结构 + Alpine.js CDN + 外链引用

#### 后端拆分（2-3小时，每模块拆完即测）

- [ ] **后端：engine_core.py**：状态/配置/日志基础方法
- [ ] **后端：engine_capture.py**：采集 + 标签 + 连接力
- [ ] **后端：engine_exchange.py**：兑换 + 基金池（v0.4 重构基础）
- [ ] **后端：engine_review.py**：周/月回顾
- [ ] **后端：engine_season.py**：赛季系统
- [ ] **后端：engine_backup.py**：备份同步

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
