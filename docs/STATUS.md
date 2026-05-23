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
| 部署状态 | ✅ 已上线 (8003端口 + hunterhub.loca.lt) |

---

> **已上线版本**（v0.1.0、v0.1.1）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.2.4 功能规格**（10个子系统）见 [PRODUCT.md](PRODUCT.md#二v024-当前功能)。

---

## 下一步

### 优先
- [x] **v0.2.4 生产部署**：创建 v0.2.4 launchd plist，独立于 v0.1 运行，上线
- [ ] **v0.2.5 前端拆分**：index.html 超 2600 行，CSS → styles.css，JS → app.js，HTML 仅保留结构
- [ ] **v0.3 后端重构**：engine.py 按功能拆分为子模块（预估1-2天）

### 暂缓
- [ ] **v0.4 赛季主题**：开拓者/连线大师/深度矿工/分享者 四主题 + **方案B**：app.js 按模块拆分（capture/exchange/review）
- [ ] **v0.5 自定义挑战**：用户自行设定挑战目标与奖励，自动追踪进度
- [ ] **v0.6 能力值面板**：星点里程碑档位制 + 前端能力面板展示
- [ ] **v0.7 Tab 导航**：前端 6 个 Tab(采集/概览/成长/标签/行动/规则)，Alpine.js x-show 切换
- [x] **AI_WORKFLOW.md 拆分**：触发条件（任一满足时执行）→ 规则超过 5 条 / 某条超 10 行 / STATUS 超 100 行。将顶部 ⚠️ 操作规则移出到独立文件，STATUS 恢复纯状态文档

---

## 技术栈

- 前端：Alpine.js（单页长滚动）
- 后端：FastAPI + uvicorn
- 存储：Markdown(灵感笔记) + YAML(配置) + JSON(状态)
- 部署：launchd + localtunnel（公网）
- 仓库：github.com/phyziix/hunterhunter
