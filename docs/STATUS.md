# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
> **AI 操作规则**见 `docs/AI_WORKFLOW.md`（文档维护、部署、调试、方法论实验）。

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.2.5 |
| 分支 | v0.2.4 |
| 部署状态 | ✅ v0.2.5 已上线 (8003端口 + hunterhub.loca.lt) |
| 下一版本 | v0.2.5 继续开发（兑换模块剥离等） |

---

> **已上线版本**（v0.1.0、v0.1.1）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.2.4 功能规格**（10个子系统）见 [PRODUCT.md](PRODUCT.md#二v024-当前功能)。

---

## 下一步：v0.2.5 规划

### 设计决策

兑换体系（连续选择奖惩 / 镜像对比 / 基金池 / 动态锁定）当前过于复杂，暂不维护。
**代码不删**——通过结构优化（抽取独立模块 + feature flag）实现下线，日后一行配置即可恢复。

### 优先

- [ ] **兑换模块剥离**：从 `engine.py` 抽取 `set_exchange_path` / `exchange_coupon` / `exchange_fund` 等所有兑换方法到新文件 `engine_exchange.py`。原代码 move 不改逻辑，`main.py` 加 `ENABLE_EXCHANGE = False` 控制路由暴露，前端兑换板块同步隐藏
    - **调试方案**（隐藏≠不能调）：
      1. **环境变量控制**：`ENABLE_EXCHANGE` 不要写死，用 `os.getenv("ENABLE_EXCHANGE", "false")` 读取。本地 `ENABLE_EXCHANGE=true uvicorn main:app` 即恢复正常，线上不加就是 false
      2. **API 始终暴露**：路由不删，`curl` 直接调 `/api/exchange/*` 即可测试逻辑，前端隐藏不影响后端调试
      3. **前端调试入口**：URL 加 `?debug=exchange` 参数临时显示隐藏模块，或 `/api/config` 返回 `exchange_enabled` 让 Alpine.js 用 `x-show` 绑定
      4. **数据验证**：直接看 `data/inspire/_狩猎系统/state.json` 中 `exchange_history` / `fund_pool` / `available_star` 字段验证结果
- [ ] **采集 + 星点模块清理**：去重逻辑观察完善、`_calculate_stars` 计算链透明化、相似笔记匹配打磨、星点收支记录清晰化
- [ ] **前端精简**：兑换中心 / 赛季兑换面板按 feature flag 隐藏（后端 `/api/config` 返回 `exchange_enabled: false`，前端 Alpine.js `x-show` 绑定）

### 暂缓（原 v0.2.5 计划移入）

- [ ] **前端文件拆分**：index.html 超 2600 行，CSS → styles.css，JS → app.js（结构优化优先级更高，先做 module 拆分再管文件拆分）
- [ ] **v0.3 后端重构**：engine.py 按功能拆分为子模块（预估1-2天）

### 远期

- [ ] **v0.4 赛季主题**：开拓者/连线大师/深度矿工/分享者 四主题 + **方案B**：app.js 按模块拆分（capture/exchange/review）
- [ ] **v0.5 自定义挑战**：用户自行设定挑战目标与奖励，自动追踪进度
- [ ] **v0.6 能力值面板**：星点里程碑档位制 + 前端能力面板展示
- [ ] **v0.7 Tab 导航**：前端 6 个 Tab(采集/概览/成长/标签/行动/规则)，Alpine.js x-show 切换
- [x] **AI_WORKFLOW.md 拆分**：触发条件（任一满足时执行）→ 规则超过 5 条 / 某条超 10 行 / STATUS 超 100 行。将顶部 ⚠️ 操作规则移出到独立文件，STATUS 恢复纯状态文档
- [ ] **方法论收割**：项目关闭时，从 AI_WORKFLOW/DEPLOYMENT/STATUS 提炼通用骨架 → `METHODOLOGY.md`（当前阶段不做通用化，规则只管 hunterhunter 怎么跑）

---

## 技术栈

- 前端：Alpine.js（单页长滚动）
- 后端：FastAPI + uvicorn
- 存储：Markdown(灵感笔记) + YAML(配置) + JSON(状态)
- 部署：launchd + localtunnel（公网）
- 仓库：github.com/phyziix/hunterhunter
