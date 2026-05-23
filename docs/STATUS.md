# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
>
> ⚠️ **文档维护规则**：用户说「同步文档」时，执行以下全部操作：
> 1. 检查并更新 `CHANGELOG.md`（新版本条目 / 当前版本条目补充）
> 2. 检查并更新 `PRODUCT.md`（功能规格有变则同步）
> 3. 检查并更新 `STATUS.md`（版本号、分支、下一步有变则同步）
> 4. 检查并更新 `README.md`（版本概览表有变则同步）
> 5. **最终一步：commit 以上变更 + push**
>
> ⚠️ **调试规则**：用户说「调试」或贴了报错截图时，执行以下全部操作：
> 1. 先区分来源：Console 红字 → 前端问题；Network 红请求 → 后端问题
> 2. 同时自查代码一致性（API 路由与函数签名是否匹配、state.json 结构是否与文档一致、config.yaml 键是否被正确引用）
> 3. 给出本次变更的验收清单（3-7 条可操作检查项）
> 4. 异常时列出问题并给出修复；无异常则说「调试通过」
>
> 📋 **为什么操作规则放在这里**：以上「同步文档」「调试」属于 AI 工作方式，本质不属于 STATUS。但当前仅 2 条规则、STATUS 未超 100 行，放在 AI 第一个打开的文件里收益最大。**拆分成独立文件（如 AI_WORKFLOW.md）的触发条件**：
> - 规则超过 5 条
> - 或某条规则超过 10 行
> - 或 STATUS 总行数超过 100 行
>
> 满足任一条件时，所有 ⚠️ 操作规则移出，STATUS 恢复为纯状态文档。

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.2.4 |
| 分支 | v0.2.4 |
| 部署状态 | 🔧 开发中，未上线 |

---

> **已上线版本**（v0.1.0、v0.1.1）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.2.4 功能规格**（10个子系统）见 [PRODUCT.md](PRODUCT.md#二v024-当前功能)。

---

## 下一步

### 优先
- [ ] **v0.2.4 生产部署**：创建 v0.2.4 launchd plist，独立于 v0.1 运行，上线
- [ ] **v0.2.5 前端拆分**：index.html 超 2200 行，CSS → styles.css，JS → app.js，HTML 仅保留结构
- [ ] **Phase 7.5 后端重构**：engine.py 按功能拆分为子模块（预估1-2天）

### 暂缓
- [ ] **Phase 8 Tab 导航**：前端 6 个 Tab(采集/概览/成长/标签/行动/规则)，Alpine.js x-show 切换
- [ ] **v0.3 app.js 模块拆分**：capture.js / exchange.js / review.js，需解决 Alpine x-data 作用域

> **未来版本详情**（v0.3 赛季主题+模块拆分 / v0.4 自定义挑战 / v0.5 能力面板）见 `docs/PRODUCT.md#三后续版本计划`。

---

## 技术栈

- 前端：Alpine.js（单页长滚动）
- 后端：FastAPI + uvicorn
- 存储：Markdown(灵感笔记) + YAML(配置) + JSON(状态)
- 部署：launchd + localtunnel（公网）
- 仓库：github.com/phyziix/hunterhunter
