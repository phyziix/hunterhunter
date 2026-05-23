# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
> **AI 操作规则**见 `docs/AI_WORKFLOW.md`（文档维护、部署、调试、方法论实验）。

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.2.4 |
| 分支 | v0.2.4 |
| 部署状态 | ✅ v0.2.4 已上线 (8003端口 + hunterhub.loca.lt) |
| 下一版本 | v0.2.5（Bug 修复） |

---

> **已上线版本**（v0.1.0、v0.1.1）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.2.4 功能规格**（10个子系统）见 [PRODUCT.md](PRODUCT.md#二v024-当前功能)。

---

## 下一步：v0.2.5（Bug 修复）

> v0.2.4 已上线但以下功能点仍需修复，归入 v0.2.5。

- [ ] **兑换模块下线**：兑换体系过于复杂，暂不维护。v0.2.5 先通过 feature flag 关闭前端入口和路由暴露，代码不动；拆分/剥离并入后续 v0.4 兑换开发
- [ ] **重复提交检测修复**：当前去重机制不正确，仍可重复提交相同内容。修复后端去重逻辑
- [ ] **重复提交提示优化**：检测到重复提交后，弹出「建议情况」对话框告知用户，提升体验
- [ ] **标签提取过滤 `##`**：正文标签提取正则会匹配到 `## 标题` 等 Markdown 格式，需过滤
- [ ] **相关灵感匹配规则优化**：当前 `_find_related_notes()` 的 IDF 加权 Jaccard 匹配结果仍不合理，需进一步打磨

---

## 下一步：v0.3（结构调整）

> v0.3 专注代码结构优化，不做功能变更。

### 设计决策

兑换体系（连续选择奖惩 / 镜像对比 / 基金池 / 动态锁定）当前过于复杂，暂不维护。
**代码不删**——通过结构优化（抽取独立模块 + feature flag）实现下线，日后一行配置即可恢复。

### 优先

- [ ] **采集 + 星点模块清理**：去重逻辑完善、`_calculate_stars` 计算链透明化、相似笔记匹配打磨
- [ ] **前端精简**：兑换中心 / 赛季兑换面板按 feature flag 隐藏
- [ ] **前端文件拆分**：index.html 超 2600 行，`<style>` → `styles.css`，`<script>` → `app.js`
- [ ] **后端重构**：engine.py 按功能拆分为子模块（采集/星点/标签/赛季等）

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
